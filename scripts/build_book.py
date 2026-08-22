#!/usr/bin/env python3
"""Build a short-quote book from local essays.jsonl + tweets.jsonl."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "book"
OUT.mkdir(exist_ok=True)

CHAPTERS = [
    {
        "id": "start",
        "section": "STARTUPS",
        "title": "How to Start",
        "slugs": ["start", "notnot", "before", "ycstart", "badeconomy"],
        "keywords": (
            "start a startup",
            "starting a startup",
            "not not start",
            "just start",
            "found a startup",
        ),
    },
    {
        "id": "want",
        "section": "STARTUPS",
        "title": "Something People Want",
        "slugs": ["want", "organic", "startupideas", "getideas"],
        "keywords": (
            "people want",
            "make something",
            "users want",
            "startup idea",
        ),
    },
    {
        "id": "scale",
        "section": "STARTUPS",
        "title": "Do Things That Don't Scale",
        "slugs": ["ds"],
        "keywords": (
            "don't scale",
            "doesnt scale",
            "unscalable",
            "manually",
            "do things that",
            "recruit users",
        ),
    },
    {
        "id": "growth",
        "section": "STARTUPS",
        "title": "Growth",
        "slugs": ["growth", "aord"],
        "keywords": ("startup = growth", "default alive", "default dead", "growth"),
    },
    {
        "id": "fundraising",
        "section": "STARTUPS",
        "title": "Fundraising",
        "slugs": ["fundraising", "startupfunding", "hiresfund", "future"],
        "keywords": ("fundraising", "investors", "raise money", "yc "),
    },
    {
        "id": "schlep",
        "section": "STARTUPS",
        "title": "Schlep Blindness",
        "slugs": ["schlep", "startuplessons", "startupmistakes", "13sentences"],
        "keywords": ("schlep", "unglamorous", "hard parts", "avoid the", "boring"),
    },
    {
        "id": "founders",
        "section": "STARTUPS",
        "title": "Founders",
        "slugs": ["founders", "foundermode", "control", "5founders", "relres"],
        "keywords": ("founder", "relentlessly resourceful", "founder mode"),
    },
    {
        "id": "maker",
        "section": "WORK",
        "title": "Maker's Schedule",
        "slugs": ["makersschedule", "boss"],
        "keywords": (
            "maker's schedule",
            "manager's schedule",
            "makers schedule",
            "uninterrupted",
            "meetings destroy",
            "one meeting",
        ),
    },
    {
        "id": "great-work",
        "section": "WORK",
        "title": "Great Work",
        "slugs": ["greatwork", "love", "when"],
        "keywords": ("great work", "do what you love", "hard work", "work on"),
    },
    {
        "id": "taste",
        "section": "WORK",
        "title": "Taste",
        "slugs": ["taste", "goodtaste", "copy"],
        "keywords": ("good taste", "taste for", "design"),
    },
    {
        "id": "writing",
        "section": "MIND",
        "title": "Writing",
        "slugs": ["essay", "best", "talk", "simply", "writes", "useful"],
        "keywords": ("write", "essay", "writing", "write simply"),
    },
    {
        "id": "ideas",
        "section": "MIND",
        "title": "Ideas",
        "slugs": ["ideas", "getideas", "ambitious"],
        "keywords": ("new ideas", "good ideas", "idea "),
    },
    {
        "id": "identity",
        "section": "MIND",
        "title": "Keep Your Identity Small",
        "slugs": ["identity", "say", "mean"],
        "keywords": ("identity small", "can't say", "mean people"),
    },
    {
        "id": "wealth",
        "section": "LIFE",
        "title": "How to Make Wealth",
        "slugs": ["wealth", "winc"],
        "keywords": ("make wealth", "wealth is", "get rich"),
    },
    {
        "id": "cities",
        "section": "LIFE",
        "title": "Cities and Ambition",
        "slugs": ["cities", "hubs", "america", "startuphubs"],
        "keywords": ("cities and ambition", "silicon valley", "startup hub"),
    },
    {
        "id": "young",
        "section": "LIFE",
        "title": "What You'll Wish You'd Known",
        "slugs": ["hs", "mit", "nerds"],
        "keywords": ("high school", "wish you'd known", "young"),
    },
    {
        "id": "nerds",
        "section": "LIFE",
        "title": "Nerds",
        "slugs": ["nerds", "fn", "icad"],
        "keywords": ("nerd", "lisp", "hackers"),
    },
]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def essay_lede(body: str) -> str:
    text = re.sub(r"Want to start a startup\?.*?\n+", "", body, flags=re.I)
    lines = [ln.strip() for ln in text.splitlines()]
    while lines and (
        re.match(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\b", lines[0])
        or re.match(r"^\d{4}\b", lines[0])
        or len(lines[0]) < 12
    ):
        lines.pop(0)
    blob = " ".join(lines)
    blob = re.sub(r"\s+", " ", blob).strip()
    parts = re.split(r"(?<=[.!?])\s+", blob)
    lede = " ".join(parts[:2]).strip()
    if len(lede) > 280:
        lede = lede[:277].rsplit(" ", 1)[0] + "…"
    return lede


def is_aphorism(text: str) -> bool:
    t = text.strip()
    if not (48 <= len(t) <= 260):
        return False
    if re.search(r"https?://|t\.co/|www\.", t):
        return False
    if t.startswith("@") or t.startswith("RT "):
        return False
    if t.count("@") > 1:
        return False
    if t.lower().startswith(("just posted", "new essay", "link:", "my essay")):
        return False
    return bool(re.search(r"[.!?]$", t) or len(t.split()) >= 10)


def month_label(iso: str | None) -> str:
    if not iso:
        return ""
    return iso[:7]


def main() -> None:
    essays = {e["slug"]: e for e in load_jsonl(DATA / "essays.jsonl")}
    tweets = load_jsonl(DATA / "tweets.jsonl")
    originals = [
        t
        for t in tweets
        if t.get("type") == "original" and is_aphorism(t.get("text") or "")
    ]

    used_ids: set[str] = set()
    book_chapters = []
    for i, ch in enumerate(CHAPTERS, 1):
        quotes = []
        for slug in ch["slugs"]:
            essay = essays.get(slug)
            if not essay:
                continue
            lede = essay_lede(essay.get("body") or "")
            if len(lede) < 40:
                continue
            quotes.append(
                {
                    "headline": lede,
                    "source": essay["title"],
                    "href": essay["url"],
                    "kind": "essay",
                    "date": "",
                }
            )
        keys = tuple(k.lower() for k in ch["keywords"])
        for t in originals:
            if t["id"] in used_ids:
                continue
            blob = t["text"].lower()
            if not any(k in blob for k in keys):
                continue
            used_ids.add(t["id"])
            quotes.append(
                {
                    "headline": t["text"].strip(),
                    "source": "@paulg",
                    "href": t.get("url") or f"https://x.com/paulg/status/{t['id']}",
                    "kind": "tweet",
                    "date": month_label(t.get("created_at")),
                }
            )
            if sum(1 for q in quotes if q["kind"] == "tweet") >= 8:
                break
        book_chapters.append(
            {
                "num": f"{i:02d}",
                "id": ch["id"],
                "section": ch["section"],
                "title": ch["title"],
                "quotes": quotes[:10],
            }
        )

    payload = {
        "title": "PAUL GRAHAM",
        "subtitle": "ESSAYS & NOTES",
        "dek": f"{len(essays)} essays. {len(book_chapters)} chapters. In his own words.",
        "disclaimer": "Personal reader. Not affiliated with Paul Graham or Y Combinator.",
        "sources": ["paulgraham.com", "@paulg"],
        "chapters": book_chapters,
    }
    (OUT / "data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    (OUT / "data.js").write_text(
        "window.BOOK = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    )
    nq = sum(len(c["quotes"]) for c in book_chapters)
    print(f"Wrote {len(book_chapters)} chapters, {nq} quotes → {OUT}")


if __name__ == "__main__":
    main()
