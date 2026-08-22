"""Semantic labels for book quotes via OpenRouter (cached).

There is no dedicated “is this a lesson” MCP. Hugging Face has a
zero-shot classification HTTP API, but this repo already talks to
OpenRouter. We send each sentence with the chapter’s topic list and
store {is_lesson, topic, confidence}.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "lesson_labels.json"
ENV = ROOT / ".env.local"

CHAPTER_TOPICS: dict[str, list[str]] = {
    "start": ["People", "Ideas", "Users", "Starting", "Failure", "Money"],
    "want": ["Ideas", "Problems", "Users"],
    "scale": ["Unscalable", "Users"],
    "growth": ["Definition", "Compass", "Default alive", "Ramen"],
    "fundraising": ["Priority", "Investors", "Deals", "Money"],
    "schlep": ["Blindness", "Hard work", "Users", "Cofounders", "Launch", "Money"],
    "founders": ["Determination", "Resourcefulness", "Founder mode", "Earnestness", "Cofounders"],
    "maker": ["Schedule", "Meetings", "Attention", "Work"],
    "great-work": ["Choosing", "Doing", "Love", "Effort", "Projects"],
    "taste": ["Taste", "Design", "Art"],
    "writing": ["Simplicity", "Thinking", "Essays"],
    "ideas": ["Anomalies", "Ideas"],
    "identity": ["Identity", "Fashion", "Character"],
    "wealth": ["Getting rich", "Compression"],
    "cities": ["Ambition", "Messages", "Hubs"],
    "young": ["Plans", "Taste", "Time", "School"],
    "nerds": ["Popularity", "Fierce", "Learning"],
}

CHAPTER_DEFAULT = {
    "start": "Starting",
    "want": "Ideas",
    "scale": "Unscalable",
    "growth": "Compass",
    "fundraising": "Investors",
    "schlep": "Hard work",
    "founders": "Determination",
    "maker": "Work",
    "great-work": "Doing",
    "taste": "Taste",
    "writing": "Essays",
    "ideas": "Ideas",
    "identity": "Identity",
    "wealth": "Getting rich",
    "cities": "Ambition",
    "young": "Plans",
    "nerds": "Popularity",
}

SYSTEM = """You label Paul Graham sentences for a book of lessons.

A lesson is a standalone general claim or piece of advice that still makes sense out of context.
Not a lesson: anecdote about a named person or company, news, navigation leftover, a mid-thought fragment, or a process detail that needs the surrounding essay.

Return JSON only: {"items":[{"id":1,"is_lesson":true,"topic":"Users","confidence":0.86}]}
topic MUST be one of the allowed topics for that chapter.
"""


def load_dotenv() -> None:
    if not ENV.exists():
        return
    for line in ENV.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def cache_key(chapter: str, text: str) -> str:
    blob = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha1(f"{chapter}\n{blob}".encode()).hexdigest()


def load_cache() -> dict[str, dict]:
    if not CACHE.exists():
        return {}
    try:
        data = json.loads(CACHE.read_text())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(cache: dict[str, dict]) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n")


def lookup(cache: dict[str, dict], chapter: str, text: str) -> dict | None:
    return cache.get(cache_key(chapter, text))


def labeled_topic(cache: dict[str, dict], chapter: str, text: str, fallback: str = "") -> str:
    allowed = CHAPTER_TOPICS.get(chapter, [])
    hit = lookup(cache, chapter, text)
    if hit and hit.get("topic") in allowed:
        return hit["topic"]
    if fallback in allowed:
        return fallback
    return CHAPTER_DEFAULT.get(chapter) or (allowed[0] if allowed else "Ideas")


def _chat(messages: list[dict]) -> dict:
    load_dotenv()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")
    model = os.environ.get("OPENROUTER_MODEL") or "openai/gpt-4o-mini"
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": messages,
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/mollaosmanoglu/paul-graham",
            "X-Title": "Paul Graham lessons",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:400]
        raise RuntimeError(f"OpenRouter {exc.code}: {body}") from exc
    content = payload["choices"][0]["message"]["content"]
    return json.loads(content)


def classify_batch(chapter: str, chapter_title: str, items: list[tuple[int, str]]) -> list[dict]:
    allowed = CHAPTER_TOPICS[chapter]
    lines = "\n".join(f"{i}. {text}" for i, text in items)
    user = (
        f"Chapter: {chapter_title}\n"
        f"Allowed topics: {', '.join(allowed)}\n\n"
        f"{lines}"
    )
    data = _chat(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ]
    )
    by_id = {int(row["id"]): row for row in data.get("items", []) if "id" in row}
    out = []
    for i, text in items:
        row = by_id.get(i) or {}
        topic = row.get("topic")
        if topic not in allowed:
            topic = CHAPTER_DEFAULT[chapter]
        out.append(
            {
                "is_lesson": bool(row.get("is_lesson", True)),
                "topic": topic,
                "confidence": float(row.get("confidence") or 0),
            }
        )
    return out


def classify_missing(
    jobs: list[tuple[str, str, str]],
    cache: dict[str, dict] | None = None,
    batch_size: int = 10,
) -> dict[str, dict]:
    """jobs: (chapter_id, chapter_title, text). Updates and returns cache."""
    cache = load_cache() if cache is None else cache
    pending: dict[str, list[tuple[str, str]]] = {}
    for chapter, title, text in jobs:
        key = cache_key(chapter, text)
        if key in cache:
            continue
        pending.setdefault(chapter, []).append((title, text))

    for chapter, rows in pending.items():
        title = rows[0][0]
        texts = [text for _, text in rows]
        for start in range(0, len(texts), batch_size):
            chunk = texts[start : start + batch_size]
            numbered = list(enumerate(chunk, start=1))
            labels = classify_batch(chapter, title, numbered)
            for text, label in zip(chunk, labels):
                cache[cache_key(chapter, text)] = label
            save_cache(cache)
            time.sleep(0.25)
    return cache
