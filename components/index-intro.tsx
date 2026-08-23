import book from '@/data/lessons.json';

const lessonCount = book.chapters.reduce((total, chapter) => total + chapter.quotes.length, 0);

export function IndexIntro() {
  return (
    <div className="index-intro not-prose">
      <div className="index-intro-photo">
        <img src="/pg-index.jpg" alt="Paul Graham" width={104} height={128} />
      </div>
      <div className="index-intro-copy">
        <p>LESSONS & NOTES. 231 essays. {lessonCount} lessons. In his own words.</p>
        <p>Personal reader. Not affiliated with Paul Graham or Y Combinator.</p>
        <p>Sources: paulgraham.com, @paulg.</p>
      </div>
    </div>
  );
}
