import Image from 'next/image';
import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

const MONTHS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

function formatDate(date?: string) {
  if (!date) return null;
  const [year, month] = date.split('-');
  if (!year) return null;
  if (!month) return year;
  return `${MONTHS[Number(month) - 1] ?? month} ${year}`;
}

function Verified() {
  return (
    <svg
      viewBox="0 0 22 22"
      width="18.75"
      height="18.75"
      className="ml-0.5 shrink-0"
      aria-label="Verified"
    >
      <path
        fill="#1D9BF0"
        d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"
      />
    </svg>
  );
}

type NoteProps = {
  kind?: 'tweet' | 'essay';
  source: string;
  href: string;
  date?: string;
  children: ReactNode;
};

export function Note({ kind = 'essay', source, href, date, children }: NoteProps) {
  const when = formatDate(date);
  const isTweet = kind === 'tweet';

  return (
    <article className="note not-prose border-b border-fd-border py-3 first:pt-0">
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="flex no-underline text-inherit transition-transform duration-[var(--duration-press)] [transition-timing-function:var(--ease-out)] active:scale-[0.97]"
      >
        <div className="mr-2 flex w-10 shrink-0 justify-center">
          {isTweet ? (
            <Image
              src="/paulg.jpg"
              alt=""
              width={40}
              height={40}
              className="size-10 rounded-full bg-black object-cover object-center"
            />
          ) : (
            <Image
              src="/pg-favicon.png"
              alt=""
              width={18}
              height={18}
              className="mt-0.5 size-[18px]"
            />
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col">
          {isTweet ? (
            <div className="flex min-w-0 items-center">
              <span className="truncate text-[15px] font-normal leading-5 text-fd-foreground">
                Paul Graham
              </span>
              <Verified />
              <span className="ml-1 truncate text-[15px] leading-5 text-fd-muted-foreground">
                {source}
              </span>
              {when ? (
                <>
                  <span className="shrink-0 px-1 text-[15px] leading-5 text-fd-muted-foreground">
                    ·
                  </span>
                  <span className="shrink-0 text-[15px] leading-5 text-fd-muted-foreground">
                    {when}
                  </span>
                </>
              ) : null}
            </div>
          ) : null}
          {children ? (
            <div
              className={cn(
                'note-quote text-[15px] font-normal leading-6 text-fd-foreground [&_p]:m-0 [&_p]:text-fd-foreground',
                isTweet && 'mt-2',
              )}
            >
              {children}
            </div>
          ) : null}
          {!isTweet ? (
            <p
              className={cn(
                'm-0 truncate text-[13px] font-normal leading-5 text-fd-muted-foreground',
                children && 'mt-1',
              )}
            >
              {source}
              {when ? ` · ${when}` : ' · paulgraham.com'}
            </p>
          ) : null}
        </div>
      </a>
    </article>
  );
}
