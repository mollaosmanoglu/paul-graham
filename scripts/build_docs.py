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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.mdx"):
        stale.unlink()

    pages: list[str] = ["index"]
    by_section: OrderedDict[str, list[dict]] = OrderedDict()
    for chapter in BOOK["chapters"]:
        by_section.setdefault(chapter["section"], []).append(chapter)

    (OUT / "index.mdx").write_text(
        f"""---
title: {BOOK["title"]}
description: {BOOK["dek"]}
---

{BOOK["subtitle"]}. {BOOK["dek"]}

{BOOK["disclaimer"]}

Sources: {", ".join(BOOK["sources"])}.
"""
    )

    for section, chapters in by_section.items():
        pages.append(f"---{section}---")
        for chapter in chapters:
            pages.append(chapter["id"])
            quotes = []
            for quote in chapter["quotes"]:
                body = escape_mdx(quote["headline"])
                source = escape_mdx(quote["source"])
                href = quote["href"]
                date = f" · {quote['date']}" if quote.get("date") else ""
                quotes.append(f"> {body}\n>\n> [{source}]({href}){date}\n\n")
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
