import fs from 'node:fs';
import path from 'node:path';
import book from '@/data/lessons.json';

type Quote = {
  topic: string;
  title: string;
  headline: string;
  source: string;
  href: string;
};

type Hit = Quote & {
  chapterId: string;
  chapterTitle: string;
};

type CorpusHit = Quote & {
  chapterId: 'corpus';
  chapterTitle: 'Complete archive';
};

type Essay = {
  title: string;
  url: string;
  body: string;
};

type Tweet = {
  text: string;
  url: string;
  type: string;
  created_at: string;
};

const STOP = new Set([
  'a',
  'an',
  'and',
  'are',
  'be',
  'for',
  'from',
  'how',
  'in',
  'is',
  'it',
  'of',
  'on',
  'or',
  'that',
  'the',
  'to',
  'what',
  'why',
  'with',
  'you',
]);

function tokens(text: string) {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((word) => word.length > 2 && !STOP.has(word));
}

function score(quote: Quote, query: string[]) {
  const hay = `${quote.topic} ${quote.title} ${quote.headline} ${quote.source}`.toLowerCase();
  let points = 0;
  for (const word of query) {
    if (quote.topic.toLowerCase() === word) points += 4;
    if (hay.includes(word)) points += 2;
  }
  return points;
}

function scoreText(text: string, query: string[]) {
  const hay = text.toLowerCase();
  return query.reduce((points, word) => points + (hay.includes(word) ? 1 : 0), 0);
}

function sourceDate(value: string) {
  return value.slice(0, 7);
}

function readJsonLines<T>(name: string): T[] {
  const file = path.join(process.cwd(), 'data', name);
  return fs
    .readFileSync(file, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((line) => JSON.parse(line) as T);
}

function excerpts(text: string) {
  return text
    .replace(/\s+/g, ' ')
    .split(/(?<=[.!?])\s+/)
    .map((excerpt) => excerpt.trim())
    .filter(Boolean);
}

let archive: CorpusHit[] | undefined;

function completeArchive() {
  if (archive) return archive;

  const essays = [
    ...readJsonLines<Essay>('essays.jsonl'),
    ...readJsonLines<Essay>('misc.jsonl'),
  ];
  const essayEntries = essays.flatMap((essay) =>
    excerpts(essay.body).map((headline) => ({
      topic: 'Archive',
      title: essay.title,
      headline,
      source: essay.title,
      href: essay.url,
      chapterId: 'corpus' as const,
      chapterTitle: 'Complete archive' as const,
    })),
  );
  const postEntries = readJsonLines<Tweet>('tweets.jsonl')
    // Replies, reposts, and quoted posts can contain someone else's words.
    // Keep only material authored by Graham so every result is correctly attributed.
    .filter((tweet) => tweet.type === 'original' && tweet.text.trim())
    .map((tweet) => ({
      topic: 'Archive',
      title: '@paulg',
      headline: tweet.text.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&').trim(),
      source: '@paulg',
      href: tweet.url,
      date: sourceDate(tweet.created_at),
      chapterId: 'corpus' as const,
      chapterTitle: 'Complete archive' as const,
    }));

  archive = [...essayEntries, ...postEntries];
  return archive;
}

export function findLessons(question: string, limit = 5): Array<Hit | CorpusHit> {
  const query = tokens(question);
  if (query.length === 0) return [];

  const hits: { hit: Hit; points: number }[] = [];
  for (const chapter of book.chapters) {
    for (const quote of chapter.quotes) {
      const points = score(quote, query);
      if (points > 0) {
        hits.push({
          hit: {
            ...quote,
            chapterId: chapter.id,
            chapterTitle: chapter.title,
          },
          points,
        });
      }
    }
  }

  const selectedText = new Set(hits.map((item) => item.hit.headline.toLowerCase()));
  const archiveHits = completeArchive()
    .map((hit) => ({ hit, points: scoreText(`${hit.headline} ${hit.source}`, query) }))
    .filter((item) => item.points > 0 && !selectedText.has(item.hit.headline.toLowerCase()));

  return [...hits, ...archiveHits]
    .sort((a, b) => b.points - a.points || a.hit.headline.length - b.hit.headline.length)
    .slice(0, limit)
    .map((item) => item.hit);
}

export function formatLessonContext(hits: Array<Hit | CorpusHit>) {
  if (hits.length === 0) return '';
  return hits
    .map(
      (hit) =>
        `${hit.headline}\n— ${hit.source}, ${hit.chapterTitle} (${hit.topic})`,
    )
    .join('\n\n');
}

export function answerFromBook(question: string) {
  const hits = findLessons(question, 1);
  const best = hits[0];
  if (!best) {
    return 'That is not in these notes. Try a topic like determination, ideas, users, or fundraising.';
  }

  return `${best.headline}\n\n— ${best.source}, ${best.chapterTitle}`;
}
