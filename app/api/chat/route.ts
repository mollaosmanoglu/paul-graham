import { findLessons, formatLessonContext } from '@/lib/lesson-search';

const SYSTEM = `You talk about Paul Graham. Use the supplied source excerpts when they fit. Quote him and cite the essay or post.
Think for yourself: expand, connect, and answer even when the notes are thin. Do not refuse. Do not say the notes don't cover something.
Write markdown — short paragraphs, **bold** for his wording, lists when listing.`;

const DEFAULT_MODEL = process.env.OPENROUTER_MODEL ?? 'google/gemini-3.7-flash';
const FALLBACK_MODEL = process.env.OPENROUTER_FALLBACK_MODEL ?? 'google/gemini-3.5-flash';
const RETRY_STATUSES = new Set([408, 409, 429, 500, 502, 503, 504]);

function publicError(status?: number) {
  if (status === 429) return 'Too many questions at once. Wait a moment.';
  return 'Could not reach the notes. Try again.';
}

type Turn = { role: 'user' | 'assistant'; content: string };

function priorTurns(value: unknown): Turn[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is Turn => {
      if (!item || typeof item !== 'object') return false;
      const turn = item as { role?: unknown; content?: unknown };
      return (
        (turn.role === 'user' || turn.role === 'assistant') &&
        typeof turn.content === 'string' &&
        turn.content.trim().length > 0
      );
    })
    .slice(-12)
    .map((item) => ({ role: item.role, content: item.content.trim() }));
}

async function complete(
  key: string,
  model: string,
  messages: Turn[],
  sourceContext: string,
  signal: AbortSignal,
) {
  return fetch('https://openrouter.ai/api/v1/chat/completions', {
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
      reasoning: { effort: 'minimal' },
      provider: { sort: 'latency' },
      messages: [
        { role: 'system', content: `${SYSTEM}\n\nSource excerpts:\n${sourceContext}` },
        ...messages,
      ],
    }),
    signal,
  });
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as {
    message?: unknown;
    history?: unknown;
  } | null;
  const message = typeof body?.message === 'string' ? body.message.trim() : '';
  if (!message) {
    return new Response(JSON.stringify({ error: 'Say something first.' }), { status: 400 });
  }

  const key = process.env.OPENROUTER_API_KEY;
  const model = DEFAULT_MODEL;
  if (!key) {
    return new Response(JSON.stringify({ error: 'Ask is not configured yet.' }), {
      status: 500,
    });
  }

  const messages: Turn[] = [...priorTurns(body?.history), { role: 'user', content: message }];
  const sourceContext = formatLessonContext(findLessons(message, 16));

  const signal = AbortSignal.timeout(90_000);
  let upstream = await complete(key, model, messages, sourceContext, signal).catch(() => null);

  if (!upstream || !upstream.ok) {
    await upstream?.body?.cancel().catch(() => undefined);
    if (upstream && RETRY_STATUSES.has(upstream.status)) {
      await new Promise((resolve) => setTimeout(resolve, 400));
      upstream = await complete(key, model, messages, sourceContext, signal).catch(() => null);
    }
  }

  if ((!upstream || !upstream.ok) && FALLBACK_MODEL !== model) {
    await upstream?.body?.cancel().catch(() => undefined);
    upstream = await complete(key, FALLBACK_MODEL, messages, sourceContext, signal).catch(() => null);
  }

  if (!upstream?.ok || !upstream.body) {
    return new Response(JSON.stringify({ error: publicError(upstream?.status) }), {
      status: 502,
    });
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

            let chunk: {
              error?: { message?: string };
              choices?: {
                delta?: {
                  content?: string;
                  reasoning?: string;
                  reasoning_content?: string;
                };
              }[];
            };
            try {
              chunk = JSON.parse(raw);
            } catch {
              continue;
            }

            if (chunk.error) {
              send({ error: publicError() });
              controller.enqueue(encoder.encode('data: [DONE]\n\n'));
              return;
            }

            const delta = chunk.choices?.[0]?.delta;
            const thinking = delta?.reasoning ?? delta?.reasoning_content;
            if (thinking) send({ thinking });
            if (delta?.content) send({ content: delta.content });
          }
        }
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      } catch {
        send({ error: publicError() });
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
