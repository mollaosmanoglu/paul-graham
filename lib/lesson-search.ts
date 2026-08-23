import fs from 'node:fs';
import path from 'node:path';
import book from '@/book/data.json';

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

type Indexed = {
  hit: Hit | CorpusHit;
  topic: string;
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

function archiveEnabled() {
  return process.env.BOOK_CHAT_ARCHIVE === '1';
}

function readJsonLines<T>(name: string): T[] {
  const file = path.join(process.cwd(), 'data', name);
  if (!fs.existsSync(file)) return [];
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

const catalog: Indexed[] = [];
const invert = new Map<string, number[]>();

function indexHit(hit: Hit | CorpusHit, extra = '') {
  const i = catalog.length;
  catalog.push({ hit, topic: hit.topic.toLowerCase() });
  const words = new Set(
    tokens(`${hit.topic} ${hit.title} ${hit.headline} ${hit.source} ${hit.chapterTitle} ${extra}`),
  );
  for (const word of words) {
    const ids = invert.get(word);
    if (ids) ids.push(i);
    else invert.set(word, [i]);
  }
}

for (const chapter of book.chapters) {
  for (const quote of chapter.quotes) {
    indexHit(
      {
        ...quote,
        chapterId: chapter.id,
        chapterTitle: chapter.title,
      },
      chapter.section,
    );
  }
}

let archiveReady = false;

function indexArchive() {
  if (archiveReady || !archiveEnabled()) return;
  archiveReady = true;

  try {
    const essays = [
      ...readJsonLines<Essay>('essays.jsonl'),
      ...readJsonLines<Essay>('misc.jsonl'),
    ];
    for (const essay of essays) {
      for (const headline of excerpts(essay.body)) {
        indexHit({
          topic: 'Archive',
          title: essay.title,
          headline,
          source: essay.title,
          href: essay.url,
          chapterId: 'corpus',
          chapterTitle: 'Complete archive',
        });
      }
    }

    for (const tweet of readJsonLines<Tweet>('tweets.jsonl')) {
      if (tweet.type !== 'original' || !tweet.text.trim()) continue;
      indexHit({
        topic: 'Archive',
        title: '@paulg',
        headline: tweet.text.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&').trim(),
        source: '@paulg',
        href: tweet.url,
        chapterId: 'corpus',
        chapterTitle: 'Complete archive',
      });
    }
  } catch {
    archiveReady = true;
  }
}

export function findLessons(question: string, limit = 8): Array<Hit | CorpusHit> {
  indexArchive();
  const query = tokens(question);
  if (query.length === 0) return [];

  const scores = new Map<number, number>();
  for (const word of query) {
    for (const i of invert.get(word) ?? []) {
      const item = catalog[i];
      if (!item) continue;
      scores.set(i, (scores.get(i) ?? 0) + (item.topic === word ? 6 : 2));
    }
  }

  return [...scores.entries()]
    .sort((a, b) => {
      const byScore = b[1] - a[1];
      if (byScore !== 0) return byScore;
      return catalog[a[0]].hit.headline.length - catalog[b[0]].hit.headline.length;
    })
    .slice(0, limit)
    .map(([i]) => catalog[i].hit);
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

export function formatBookContext() {
  return book.chapters
    .map((chapter) => {
      const lines = chapter.quotes
        .map((quote) => `${quote.headline}\n— ${quote.source}`)
        .join('\n\n');
      return `## ${chapter.section} / ${chapter.title}\n\n${lines}`;
    })
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
