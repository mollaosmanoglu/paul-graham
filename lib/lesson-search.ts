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

export function findLessons(question: string, limit = 5): Hit[] {
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

  hits.sort((a, b) => b.points - a.points);
  return hits.slice(0, limit).map((item) => item.hit);
}

export function formatLessonContext(hits: Hit[]) {
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
