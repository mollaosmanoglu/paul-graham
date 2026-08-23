'use client';

import { useEffect, useRef, useState } from 'react';
import type { Components } from 'react-markdown';
import { AnimatePresence, motion, useReducedMotion, type Transition } from 'motion/react';
import { Send } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from '@/components/ui/empty';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { cn } from '@/lib/cn';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

const enter: Transition = { type: 'spring', bounce: 0, visualDuration: 0.14 };
const leave: Transition = { type: 'spring', bounce: 0, visualDuration: 0.1 };

function formatThoughtDuration(ms: number) {
  return `Thought for ${Math.max(1, Math.round(ms / 1000))}s`;
}

function useNarrow() {
  const [narrow, setNarrow] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(max-width: 767px)');
    const sync = () => setNarrow(media.matches);
    sync();
    media.addEventListener('change', sync);
    return () => media.removeEventListener('change', sync);
  }, []);

  return narrow;
}

const markdown: Components = {
  p: ({ children }) => <p>{children}</p>,
  strong: ({ children }) => <strong>{children}</strong>,
  em: ({ children }) => <em>{children}</em>,
  ul: ({ children }) => <ul>{children}</ul>,
  ol: ({ children }) => <ol>{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  blockquote: ({ children }) => <blockquote>{children}</blockquote>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
  h1: ({ children }) => (
    <p>
      <strong>{children}</strong>
    </p>
  ),
  h2: ({ children }) => (
    <p>
      <strong>{children}</strong>
    </p>
  ),
  h3: ({ children }) => (
    <p>
      <strong>{children}</strong>
    </p>
  ),
  code: ({ children }) => <code>{children}</code>,
};

function ChatMarkdown({ children }: { children: string }) {
  return (
    <div className="book-chat-md">
      <Markdown remarkPlugins={[remarkGfm]} components={markdown}>
        {children}
      </Markdown>
    </div>
  );
}

function chatErrorMessage(error: unknown) {
  const raw = error instanceof Error ? error.message : '';
  const lower = raw.toLowerCase();
  if (lower.includes('say something')) return raw;
  if (lower.includes('empty reply')) return 'No answer came back. Try that again.';
  if (lower.includes('too many questions')) return raw;
  if (lower.includes('not configured')) return raw;
  return 'Could not reach the notes. Try again.';
}

export function BookChat() {
  const reduceMotion = useReducedMotion();
  const narrow = useNarrow();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState('');
  const [pending, setPending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [thoughtMs, setThoughtMs] = useState<number | null>(null);
  const thoughtStarted = useRef<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' });
  }, [messages, pending]);

  async function send() {
    const message = value.trim();
    if (!message || pending) return;

    const userId = crypto.randomUUID();
    const assistantId = crypto.randomUUID();
    setValue('');
    setMessages((current) => [...current, { id: userId, role: 'user', content: message }]);
    setPending(true);
    thoughtStarted.current = Date.now();
    setThoughtMs(null);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      if (!response.ok || !response.body) {
        const data = (await response.json().catch(() => null)) as { error?: string } | null;
        throw new Error(data?.error ?? 'Could not answer that.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let reply = '';

      const append = (chunk: string) => {
        reply += chunk;
        if (thoughtStarted.current != null) {
          setThoughtMs(Date.now() - thoughtStarted.current);
          thoughtStarted.current = null;
        }
        setMessages((current) => {
          const existing = current.some((item) => item.id === assistantId);
          if (!existing) {
            return [...current, { id: assistantId, role: 'assistant', content: reply }];
          }
          return current.map((item) =>
            item.id === assistantId ? { ...item, content: reply } : item,
          );
        });
      };

      const applyEvent = (line: string) => {
        if (!line.startsWith('data: ')) return;
        const raw = line.slice(6).trim();
        if (!raw || raw === '[DONE]') return;
        let payload: {
          content?: string;
          thinking?: string;
          error?: string;
        };
        try {
          payload = JSON.parse(raw);
        } catch {
          return;
        }
        if (payload.error) throw new Error(payload.error);
        if (payload.content) append(payload.content);
      };

      while (true) {
        const { done, value: bytes } = await reader.read();
        if (done) break;
        buffer += decoder.decode(bytes, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';
        for (const line of lines) applyEvent(line);
      }
      if (buffer) applyEvent(buffer);

      if (!reply) throw new Error('Empty reply from the model.');
    } catch (error) {
      const text = chatErrorMessage(error);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: 'assistant', content: text },
      ]);
    } finally {
      if (thoughtStarted.current != null) {
        setThoughtMs(Date.now() - thoughtStarted.current);
        thoughtStarted.current = null;
      }
      setPending(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <Button
            variant="default"
            className={cn(
              'book-chat-trigger fixed right-0 z-40 rounded-none px-4 max-md:bottom-[max(1rem,env(safe-area-inset-bottom))] max-md:h-11 md:top-1/2 md:-translate-y-1/2',
              open && 'max-md:hidden',
            )}
          />
        }
      >
        Ask
      </SheetTrigger>
      <SheetContent
        side={narrow ? 'bottom' : 'right'}
        className={cn(
          'book-chat-panel gap-0 rounded-none border-0 p-0 shadow-none',
          narrow ? 'h-[min(36rem,90dvh)] w-full max-w-none' : 'max-sm:w-full sm:max-w-md',
        )}
      >
        <SheetHeader>
          {narrow ? (
            <div className="book-chat-handle mx-auto mb-3 h-1 w-10 bg-border" aria-hidden />
          ) : null}
          <SheetTitle>Ask the notes</SheetTitle>
          <SheetDescription>Answers from Graham’s sentences.</SheetDescription>
        </SheetHeader>
        <ScrollArea className="min-h-0 flex-1">
          <div className="flex flex-col gap-3 px-4 py-4">
            {messages.length === 0 && !pending ? (
              <Empty className="min-h-64 border-0 p-2">
                <EmptyHeader>
                  <EmptyTitle>Ask a lesson</EmptyTitle>
                  <EmptyDescription>
                    Determination, ideas, users, fundraising — whatever you are
                    reading.
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : (
              <AnimatePresence initial={false}>
                {messages.map((message, index) => {
                  const last = index === messages.length - 1;
                  const showThought =
                    message.role === 'assistant' && last && thoughtMs != null && !pending;
                  return (
                    <div key={message.id} className="flex flex-col gap-1">
                      {showThought ? (
                        <motion.p
                          initial={reduceMotion ? false : { opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={enter}
                          className="text-[13px] leading-5 text-muted-foreground"
                        >
                          {formatThoughtDuration(thoughtMs ?? 0)}
                        </motion.p>
                      ) : null}
                      <motion.div
                        initial={reduceMotion ? false : { opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={enter}
                        className={cn(
                          'max-w-[90%] px-2.5 py-2 text-[15px] leading-6 font-normal',
                          message.role === 'user'
                            ? 'self-end whitespace-pre-wrap bg-primary text-primary-foreground'
                            : 'self-start bg-secondary text-secondary-foreground',
                        )}
                      >
                        {message.role === 'assistant' ? (
                          <ChatMarkdown>{message.content}</ChatMarkdown>
                        ) : (
                          message.content
                        )}
                      </motion.div>
                    </div>
                  );
                })}
              </AnimatePresence>
            )}
            <AnimatePresence initial={false}>
              {pending ? (
                <motion.p
                  key="thinking"
                  initial={reduceMotion ? false : { opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={reduceMotion ? undefined : { opacity: 0, transition: leave }}
                  transition={enter}
                  className={cn(
                    'text-[13px] leading-5 text-muted-foreground',
                    !reduceMotion && 'shimmer',
                  )}
                >
                  Thinking…
                </motion.p>
              ) : null}
            </AnimatePresence>
            <div ref={endRef} />
          </div>
        </ScrollArea>
        <SheetFooter>
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void send();
            }}
          >
            <Input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Ask about a lesson"
              aria-label="Ask about a lesson"
              className="rounded-none"
              disabled={pending}
            />
            <Button
              type="submit"
              size="icon"
              className="rounded-none"
              disabled={pending || !value.trim()}
              aria-label="Send"
            >
              <Send />
            </Button>
          </form>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
