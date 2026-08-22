#!/usr/bin/env python3
"""Label every quote in book/data.json with OpenRouter. Writes data/lesson_labels.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from labels import CHAPTER_TOPICS, classify_missing, load_cache  # noqa: E402


def main() -> None:
    book = json.loads((ROOT / "book" / "data.json").read_text())
    jobs = []
    for chapter in book["chapters"]:
        cid = chapter["id"]
        if cid not in CHAPTER_TOPICS:
            continue
        for quote in chapter["quotes"]:
            jobs.append((cid, chapter["title"], quote.get("headline") or quote.get("title") or ""))
    jobs = [(c, t, x) for c, t, x in jobs if x]
    cache = load_cache()
    from labels import cache_key

    todo = [job for job in jobs if cache_key(job[0], job[2]) not in cache]
    print(f"{len(jobs)} quotes, {len(todo)} unlabeled")
    if not todo:
        return
    classify_missing(todo, cache=cache)
    cache = load_cache()
    lessons = sum(1 for v in cache.values() if v.get("is_lesson"))
    print(f"cache {len(cache)}  is_lesson={lessons}")


if __name__ == "__main__":
    main()
