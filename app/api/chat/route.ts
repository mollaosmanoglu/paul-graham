import { findLessons, formatLessonContext } from '@/lib/lesson-search';

const SYSTEM = `You answer questions about Paul Graham using only the notes provided.
Speak plainly. Quote him when you can. Cite the essay or tweet.
If the notes do not cover the question, say so. Do not invent essays.`;

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { message?: unknown } | null;
  const message = typeof body?.message === 'string' ? body.message.trim() : '';
  if (!message) {
    return new Response(JSON.stringify({ error: 'Say something first.' }), { status: 400 });
  }

  const key = process.env.OPENROUTER_API_KEY;
  const model = process.env.OPENROUTER_MODEL ?? 'stealth/ox-alpha';
  if (!key) {
    return new Response(JSON.stringify({ error: 'Missing OPENROUTER_API_KEY.' }), {
      status: 500,
    });
  }

  const notes = formatLessonContext(findLessons(message));
  const content = notes
    ? `Notes:\n\n${notes}\n\nQuestion: ${message}`
    : `No matching notes were found.\n\nQuestion: ${message}`;

  const upstream = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://github.com/mollaosmanoglu/paul-graham',
      'X-Title': 'Paul Graham',
    },
    body: JSON.stringify({
      model,
      stream: true,
      messages: [
        { role: 'system', content: SYSTEM },
        { role: 'user', content },
      ],
    }),
  });

  if (!upstream.ok || !upstream.body) {
    const data = (await upstream.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    return new Response(
      JSON.stringify({ error: data?.error?.message ?? 'OpenRouter request failed.' }),
      { status: 502 },
    );
  }

  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const stream = new ReadableStream({
    async start(controller) {
      const reader = upstream.body!.getReader();
      let buffer = '';

      const send = (payload: Record<string, string>) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
      };

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.slice(6).trim();
            if (!raw || raw === '[DONE]') continue;
            const chunk = JSON.parse(raw) as {
              choices?: {
                delta?: {
                  content?: string;
                  reasoning?: string;
                  reasoning_content?: string;
                };
              }[];
            };
            const delta = chunk.choices?.[0]?.delta;
            const thinking = delta?.reasoning ?? delta?.reasoning_content;
            if (thinking) send({ thinking });
            if (delta?.content) send({ content: delta.content });
          }
        }
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      } catch (error) {
        const text = error instanceof Error ? error.message : 'Stream failed.';
        send({ error: text });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
