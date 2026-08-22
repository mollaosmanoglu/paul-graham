#!/usr/bin/env python3
"""Write Fumadocs MDX chapters from book/data.json."""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = json.loads((ROOT / "book" / "data.json").read_text())
OUT = ROOT / "content" / "docs"


def escape_mdx(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("<", "&lt;")
    )


def escape_attr(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.mdx"):
        stale.unlink()

    pages: list[str] = ["!index"]
    by_section: OrderedDict[str, list[dict]] = OrderedDict()
    for chapter in BOOK["chapters"]:
        by_section.setdefault(chapter["section"], []).append(chapter)

    index_parts = []
    for section, chapters in by_section.items():
        links = "\n".join(
            f"- [{chapter['title']}](/docs/{chapter['id']})" for chapter in chapters
        )
        index_parts.append(f"## {section}\n\n{links}\n")

    (OUT / "index.mdx").write_text(
        f"""---
title: {BOOK["title"]}
description: {BOOK["dek"]}
---

{BOOK["subtitle"]}. {BOOK["dek"]}

{BOOK["disclaimer"]}

Sources: {", ".join(BOOK["sources"])}.

{"\n".join(index_parts)}
"""
    )

    for section, chapters in by_section.items():
        pages.append(f"---{section}---")
        for chapter in chapters:
            pages.append(chapter["id"])
            quotes = []
            last_topic = None
            for quote in chapter["quotes"]:
                kind = quote.get("kind") or "essay"
                topic = quote.get("topic") or ""
                excerpt = quote.get("headline") or quote.get("title") or ""
                source = escape_attr(quote["source"])
                href = escape_attr(quote["href"])
                date = escape_attr(quote.get("date") or "")
                date_attr = f' date="{date}"' if date else ""
                if topic and topic != last_topic:
                    quotes.append(f"### {escape_mdx(topic)}\n\n")
                    last_topic = topic
                quotes.append(
                    f'<Note kind="{kind}" source="{source}" href="{href}"{date_attr}>\n'
                    f"{escape_mdx(excerpt)}\n"
                    f"</Note>\n\n"
                )
            (OUT / f"{chapter['id']}.mdx").write_text(
                f"""---
title: {chapter["title"]}
description: {chapter["section"]} · {chapter["num"]}
---

{"".join(quotes)}
"""
            )

    (OUT / "meta.json").write_text(json.dumps({"pages": pages}, indent=2) + "\n")
    print(f"wrote {len(BOOK['chapters'])} chapters to {OUT}")


if __name__ == "__main__":
    main()
