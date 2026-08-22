import Image from 'next/image';
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex flex-1 items-center px-6 py-16 md:px-10">
      <div className="mx-auto grid w-full max-w-5xl items-center gap-10 md:grid-cols-[minmax(0,1fr)_minmax(240px,38%)] md:gap-14">
        <div className="max-w-xl">
          <p className="mb-3 text-xs font-medium tracking-[0.14em] text-fd-primary">
            ESSAYS & NOTES
          </p>
          <h1 className="mb-4 text-5xl font-light tracking-tight text-fd-foreground md:text-7xl">
            Paul Graham
          </h1>
          <p className="mb-3 text-lg text-fd-foreground/70">
            231 essays. 17 chapters. In his own words.
          </p>
          <p className="mb-2 text-sm text-fd-muted-foreground">
            Personal reader. Not affiliated with Paul Graham or Y Combinator.
          </p>
          <p className="mb-8 text-sm text-fd-muted-foreground">
            paulgraham.com · @paulg
          </p>
          <Link
            href="/docs/start"
            className="cover-cta inline-flex bg-fd-primary px-5 py-2.5 text-sm text-fd-primary-foreground transition-transform duration-[var(--duration-press)] [transition-timing-function:var(--ease-out)] active:scale-[0.97]"
          >
            Read the book
          </Link>
        </div>
        <figure className="m-0 aspect-[4/5] max-w-xs overflow-hidden bg-black md:max-w-none">
          <Image
            src="/pg.jpg"
            alt="Paul Graham"
            width={1120}
            height={1400}
            className="h-full w-full object-cover object-[58%_18%]"
            priority
          />
        </figure>
      </div>
    </div>
  );
}
