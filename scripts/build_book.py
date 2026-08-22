#!/usr/bin/env python3
"""Build a lesson book from local essays.jsonl + tweets.jsonl.

Essay quotes are a curated canon taken from reading the core essays.
Tweets are only short standalone aphorisms that match a chapter.
"""

from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "book"
OUT.mkdir(exist_ok=True)

CHAPTERS = [
    {"id": "start", "section": "STARTUPS", "title": "How to Start"},
    {"id": "want", "section": "STARTUPS", "title": "Something People Want"},
    {"id": "scale", "section": "STARTUPS", "title": "Do Things That Don't Scale"},
    {"id": "growth", "section": "STARTUPS", "title": "Growth"},
    {"id": "fundraising", "section": "STARTUPS", "title": "Fundraising"},
    {"id": "schlep", "section": "STARTUPS", "title": "Schlep Blindness"},
    {"id": "founders", "section": "STARTUPS", "title": "Founders"},
    {"id": "maker", "section": "WORK", "title": "Maker's Schedule"},
    {"id": "great-work", "section": "WORK", "title": "Great Work"},
    {"id": "taste", "section": "WORK", "title": "Taste"},
    {"id": "writing", "section": "MIND", "title": "Writing"},
    {"id": "ideas", "section": "MIND", "title": "Ideas"},
    {"id": "identity", "section": "MIND", "title": "Keep Your Identity Small"},
    {"id": "wealth", "section": "LIFE", "title": "How to Make Wealth"},
    {"id": "cities", "section": "LIFE", "title": "Cities and Ambition"},
    {"id": "young", "section": "LIFE", "title": "What You'll Wish You'd Known"},
    {"id": "nerds", "section": "LIFE", "title": "Nerds"},
]

# (chapter, slug, lesson) — each lesson must appear in that essay's body.
CANON: list[tuple[str, str, str]] = [
    # start
    ("start", "start", "You need three things to create a successful startup: to start with good people, to make something customers actually want, and to spend as little money as possible."),
    ("start", "start", "There is no magically difficult step that requires brilliance to solve."),
    ("start", "start", "In particular, you don't need a brilliant idea to start a startup around."),
    ("start", "before", "Startups are very counterintuitive."),
    ("start", "before", "The way to succeed in a startup is not to be an expert on startups, but to be an expert on your users and the problem you're solving for them."),
    ("start", "notnot", "Even the founders who fail don't seem to have such a bad time."),
    # want
    ("want", "startupideas", "The way to get startup ideas is not to try to think of startup ideas."),
    ("want", "startupideas", "It's to look for problems, preferably problems you have yourself."),
    ("want", "startupideas", "The very best startup ideas tend to have three things in common: they're something the founders themselves want, that they themselves can build, and that few others realize are worth doing."),
    ("want", "startupideas", "by far the most common mistake startups make is to solve problems no one has."),
    ("want", "organic", "The best way to come up with startup ideas is to ask yourself the question: what do you wish someone would make for you?"),
    ("want", "users", "the best advice I could give for getting in, per word, was Explain what you've learned from users."),
    # scale
    ("scale", "ds", "One of the most common types of advice we give at Y Combinator is to do things that don't scale."),
    ("scale", "ds", "Actually startups take off because the founders make them take off."),
    ("scale", "ds", "The most common unscalable thing founders have to do at the start is to recruit users manually."),
    ("scale", "ds", "You can't wait for users to come to you. You have to go out and get them."),
    ("scale", "ds", "When you're operating on the maker's schedule, meetings are a disaster."),  # wait this is maker - REMOVE
    # growth
    ("growth", "growth", "A startup is a company designed to grow fast."),
    ("growth", "growth", "The only essential thing is growth."),
    ("growth", "growth", "if you get growth, everything else tends to fall into place."),
    ("growth", "growth", "You can use growth like a compass to make almost every decision you face."),
    ("growth", "aord", "Half the founders I talk to don't know whether they're default alive or default dead."),
    ("growth", "aord", "instead of starting to ask too late whether you're default alive or default dead, start asking too early."),
    # fundraising
    ("fundraising", "fundraising", "Raising money is the second hardest part of starting a startup."),
    ("fundraising", "fundraising", "The hardest part is making something people want: most startups that die, die because they didn't do that."),
    ("fundraising", "fundraising", "Investors evaluate startups the way customers evaluate products, not the way bosses evaluate employees."),
    ("fundraising", "fundraising", "Don't take rejection personally."),
    ("fundraising", "fundraising", "Avoid inexperienced investors."),
    ("fundraising", "hiresfund", "The reason startups have been using more convertible notes in angel rounds is that they make deals close faster."),
    ("fundraising", "hiresfund", "By far the biggest influence on investors' opinions of a startup is the opinion of other investors."),
    # schlep
    ("schlep", "schlep", "There are great startup ideas lying around unexploited right under our noses."),
    ("schlep", "schlep", "One reason we don't see them is a phenomenon I call schlep blindness."),
    ("schlep", "schlep", "A company is defined by the schleps it will undertake."),
    ("schlep", "schlep", "schleps should be dealt with the same way you'd deal with a cold swimming pool: just jump in."),
    ("schlep", "schlep", "you should never shrink from it if it's on the path to something great."),
    ("schlep", "13sentences", "it's better to make a few people really happy than to make a lot of people semi-happy."),
    ("schlep", "13sentences", "Pick good cofounders."),
    ("schlep", "13sentences", "Launch fast."),
    ("schlep", "13sentences", "Let your idea evolve."),
    ("schlep", "13sentences", "Understand your users."),
    ("schlep", "13sentences", "Better to make a few users love you than a lot ambivalent."),
    ("schlep", "13sentences", "You make what you measure."),
    ("schlep", "13sentences", "Spend little."),
    ("schlep", "13sentences", "Get ramen profitable."),
    ("schlep", "startuplessons", "get a version 1 out fast, then improve it based on users' reactions."),
    ("schlep", "startupmistakes", "There's just one mistake that kills startups: not making something users want."),
    # founders
    ("founders", "founders", "as long as you're over a certain threshold of intelligence, what matters most is determination."),
    ("founders", "founders", "The world of startups is so unpredictable that you need to be able to modify your dreams on the fly."),
    ("founders", "relres", "A couple days ago I finally got being a good startup founder down to two words: relentlessly resourceful."),
    ("founders", "relres", "To be hapless is to be battered by circumstances — to let the world have its way with you, instead of having your way with the world."),
    ("founders", "foundermode", "in effect there are two different ways to run a company: founder mode and manager mode."),
    ("founders", "foundermode", "There are things founders can do that managers can't, and not doing them feels wrong to founders, because it is."),
    # maker
    ("maker", "makersschedule", "There are two types of schedule, which I'll call the manager's schedule and the maker's schedule."),
    ("maker", "makersschedule", "You can't write or program well in units of an hour."),
    ("maker", "makersschedule", "When you're operating on the maker's schedule, meetings are a disaster."),
    ("maker", "makersschedule", "A single meeting can blow a whole afternoon, by breaking it into two pieces each too small to do anything hard in."),
    ("maker", "makersschedule", "For someone on the maker's schedule, having a meeting is like throwing an exception."),
    # great-work
    ("great-work", "greatwork", "The first step is to decide what to work on."),
    ("great-work", "greatwork", "it has to be something you have a natural aptitude for, that you have a deep interest in, and that offers scope to do great work."),
    ("great-work", "greatwork", "The way to figure out what to work on is by working."),
    ("great-work", "greatwork", "If you're not sure what to work on, guess. But pick something and get going."),
    ("great-work", "greatwork", "Don't let \"work\" mean something other people tell you to do."),
    ("great-work", "love", "To do something well you have to like it."),
    ("great-work", "love", "We've got it down to four words: \"Do what you love.\""),
    ("great-work", "when", "Don't wait till the end of college to figure out what to work on."),
    # taste
    ("taste", "taste", "We need good taste to make good things."),
    ("taste", "goodtaste", "If there's no such thing as good taste, then there's no such thing as good art."),
    # writing
    ("writing", "simply", "I try to write using ordinary words and simple sentences."),
    ("writing", "simply", "The less energy they expend on your prose, the more they'll have left for your ideas."),
    ("writing", "simply", "writing simply keeps you honest."),
    ("writing", "useful", "an essay should be useful."),
    ("writing", "useful", "Useful writing tells people something true and important that they didn't already know, and tells them as unequivocally as possible."),
    ("writing", "writes", "To write well you have to think clearly, and thinking clearly is hard."),
    ("writing", "writes", "The result will be a world divided into writes and write-nots."),
    # ideas
    ("ideas", "getideas", "The way to get new ideas is to notice anomalies: what seems strange, or missing, or broken?"),
    ("ideas", "getideas", "the best place to look for them is at the frontiers of knowledge."),
    ("ideas", "ideas", "startup ideas are not million dollar ideas"),
    ("ideas", "ideas", "They overvalue ideas."),
    # identity
    ("identity", "identity", "people can never have a fruitful argument about something that's part of their identity."),
    ("identity", "identity", "The more labels you have for yourself, the dumber they make you."),
    ("identity", "say", "What scares me is that there are moral fashions too."),
    ("identity", "say", "In every period, people believed things that were just ridiculous, and believed them so strongly that you would have gotten in terrible trouble for saying otherwise."),
    ("identity", "mean", "being mean makes you stupid."),
    ("identity", "mean", "how consistently successful startup founders turn out to be good people, and how consistently bad people fail as startup founders."),
    # wealth
    ("wealth", "wealth", "If you wanted to get rich, how would you do it? I think your best bet would be to start or join a startup."),
    ("wealth", "wealth", "A startup is a small company that takes on a hard technical problem."),
    ("wealth", "wealth", "you can think of a startup as a way to compress your whole working life into a few years."),
    # cities
    ("cities", "cities", "Great cities attract ambitious people."),
    ("cities", "cities", "the city sends you a message: you could do more; you should try harder."),
    ("cities", "cities", "New York tells you, above all: you should make more money."),
    ("cities", "cities", "the message there is: you should be smarter."),
    ("cities", "cities", "the message the Valley sends is: you should be more powerful."),
    ("cities", "hubs", "death is the default for startups, and most towns don't save them."),
    # young
    ("young", "hs", "You don't need to be in a rush to choose your life's work."),
    ("young", "hs", "What you need to do is discover what you like."),
    ("young", "hs", "You have to work on stuff you like if you want to be good at what you do."),
    ("young", "hs", "In such a world it's not a good idea to have fixed plans."),
    # nerds
    ("nerds", "nerds", "there is a strong correlation between being smart and being a nerd, and an even stronger inverse correlation between being a nerd and being popular."),
    ("nerds", "nerds", "Being smart seems to make you unpopular."),
    ("nerds", "fn", "In fact some nerds are quite fierce."),
    ("nerds", "fn", "Not all nerds are smart, but the fierce ones are always at least moderately so."),
]

# Remove the mistaken maker line I accidentally put in scale — handled below in CANON cleanup

TWEET_KEYWORDS = {
    "start": ("start a startup", "starting a startup", "just start"),
    "want": ("people want", "startup idea", "live in the future"),
    "scale": ("don't scale", "doesn't scale", "recruit users"),
    "growth": ("growth rate", "default alive", "default dead", "grow fast"),
    "fundraising": ("fundraising", "raise money", "raising money"),
    "schlep": ("schlep", "unglamorous"),
    "founders": ("relentlessly resourceful", "founder mode", "good cofounder", "cofounder"),
    "maker": ("maker's schedule", "manager's schedule", "meetings are a disaster"),
    "great-work": ("great work", "do what you love", "what to work on"),
    "taste": ("good taste", "good design"),
    "writing": ("write simply", "good writing", "writing is thinking"),
    "ideas": ("new ideas", "good ideas", "notice anomalies"),
    "identity": ("identity small", "keep your identity", "labels you have"),
    "wealth": ("make wealth", "create wealth", "get rich"),
    "cities": ("startup hub", "great cities", "you should be smarter"),
    "young": ("when you're young", "wish you'd known", "what you like"),
    "nerds": ("nerds are", "fierce nerds"),
}

MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

SKIP_TWEET = re.compile(
    r"(?i)("
    r"just posted|new essay|someone asked|office hours|"
    r"yc (is now|batch|cycle|alumni)|"
    r"my son|my kids|\d+ yo|took \d|"
    r"thanks @|walking |ran into|"
    r"#|covid|yahoo|republicans|legalizing|venue|"
    r"i'm trying|i read recently|i hope |i love |"
    r"wow,|email from|in the uk"
    r")"
)


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


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def essay_date(body: str) -> str:
    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        body[:300],
    )
    if not m:
        return ""
    return f"{m.group(2)}-{MONTHS[m.group(1).lower()]}"


def month_label(iso: str | None) -> str:
    return (iso or "")[:7]


def tweet_is_lesson(text: str) -> bool:
    t = html.unescape(text).strip()
    if not (50 <= len(t) <= 200):
        return False
    if re.search(r"https?://|t\.co/|www\.|@", t):
        return False
    if SKIP_TWEET.search(t):
        return False
    if t.startswith(("And ", "But ", "So ", "Which ", "Plus ")):
        return False
    if not re.search(r"[.!?]$", t):
        return False
    if t.count("I ") + t.count("I'm ") > 1:
        return False
    return True


def best_chapter(text: str) -> str | None:
    low = text.lower()
    hits = []
    for cid, keys in TWEET_KEYWORDS.items():
        score = sum(len(k) for k in keys if k in low)
        if score:
            hits.append((score, cid))
    if not hits:
        return None
    hits.sort(reverse=True)
    return hits[0][1]


def quote(headline: str, source: str, href: str, kind: str, date: str) -> dict:
    text = html.unescape(headline).strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return {
        "headline": text,
        "source": source,
        "href": href,
        "kind": kind,
        "date": date,
    }


def main() -> None:
    essays = {e["slug"]: e for e in load_jsonl(DATA / "essays.jsonl")}
    tweets = load_jsonl(DATA / "tweets.jsonl")
    buckets: dict[str, list[dict]] = defaultdict(list)
    used: set[str] = set()
    missing = 0

    for chapter, slug, lesson in CANON:
        # skip the mistaken scale/maker mixup if still present
        if chapter == "scale" and "maker's schedule" in lesson:
            continue
        essay = essays.get(slug)
        if not essay:
            print(f"missing essay slug: {slug}")
            missing += 1
            continue
        if norm(lesson).lower() not in norm(essay["body"]).lower():
            print(f"NOT IN {slug}: {lesson[:90]}")
            missing += 1
            continue
        key = lesson.lower()
        if key in used:
            continue
        used.add(key)
        buckets[chapter].append(
            quote(lesson, essay["title"], essay["url"], "essay", essay_date(essay["body"]))
        )

    tweet_counts: dict[str, int] = defaultdict(int)
    for tweet in tweets:
        if tweet.get("type") != "original":
            continue
        text = html.unescape(tweet.get("text") or "").strip()
        if not tweet_is_lesson(text):
            continue
        dest = best_chapter(text)
        if not dest or tweet_counts[dest] >= 6:
            continue
        key = text.lower()
        if key in used:
            continue
        used.add(key)
        tweet_counts[dest] += 1
        buckets[dest].append(
            quote(
                text,
                "@paulg",
                tweet.get("url") or f"https://x.com/paulg/status/{tweet['id']}",
                "tweet",
                month_label(tweet.get("created_at")),
            )
        )

    book_chapters = []
    for i, ch in enumerate(CHAPTERS, 1):
        essays_q = [q for q in buckets[ch["id"]] if q["kind"] == "essay"]
        tweets_q = [q for q in buckets[ch["id"]] if q["kind"] == "tweet"]
        book_chapters.append(
            {
                "num": f"{i:02d}",
                "id": ch["id"],
                "section": ch["section"],
                "title": ch["title"],
                "quotes": essays_q + tweets_q,
            }
        )

    nq = sum(len(c["quotes"]) for c in book_chapters)
    payload = {
        "title": "PAUL GRAHAM",
        "subtitle": "LESSONS & NOTES",
        "dek": f"{len(essays)} essays. {nq} lessons. In his own words.",
        "disclaimer": "Personal reader. Not affiliated with Paul Graham or Y Combinator.",
        "sources": ["paulgraham.com", "@paulg"],
        "chapters": book_chapters,
    }
    (OUT / "data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    (OUT / "data.js").write_text("window.BOOK = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    ne = sum(1 for c in book_chapters for q in c["quotes"] if q["kind"] == "essay")
    nt = sum(1 for c in book_chapters for q in c["quotes"] if q["kind"] == "tweet")
    print(f"Wrote {len(book_chapters)} chapters, {nq} lessons ({ne} essay, {nt} tweet), {missing} canon misses")
    for c in book_chapters:
        e = sum(1 for q in c["quotes"] if q["kind"] == "essay")
        t = sum(1 for q in c["quotes"] if q["kind"] == "tweet")
        print(f"  {c['num']} {c['id']:12} {len(c['quotes']):3}  essay={e:2} tweet={t:2}")


if __name__ == "__main__":
    main()
