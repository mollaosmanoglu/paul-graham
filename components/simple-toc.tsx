'use client';

import { useTOCItems } from 'fumadocs-ui/components/toc';
import * as Primitive from 'fumadocs-core/toc';

export function SimpleToc() {
  const items = useTOCItems();
  if (items.length === 0) return null;

  return (
    <nav
      id="nd-toc"
      className="sticky top-(--fd-docs-row-1) flex h-[calc(var(--fd-docs-height)-var(--fd-docs-row-1))] w-(--fd-toc-width) flex-col pt-12 pe-4 pb-2 [grid-area:toc] max-xl:hidden xl:layout:[--fd-toc-width:220px]"
    >
      <p className="text-sm text-fd-muted-foreground">On this page</p>
      <div className="flex min-h-0 flex-col overflow-y-auto pt-3 [scrollbar-width:none]">
        {items.map((item) => (
          <Primitive.TOCItem
            key={item.url}
            href={item.url}
            className="py-1.5 text-sm text-fd-muted-foreground transition-colors hover:text-fd-foreground data-[active=true]:text-fd-primary"
          >
            {item.title}
          </Primitive.TOCItem>
        ))}
      </div>
    </nav>
  );
}
