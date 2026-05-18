"""Fetch and deduplicate signals from curated RSS/Atom sources.

Source list mirrors signals/SOURCES.md. Outputs a JSON object to stdout
containing only signals not already present in committed *.json files
under the signals/ directory.

Usage (from repo root):
    uv run scripts/fetch_signals.py [--signals-dir PATH]

The CI workflow pipes stdout to signals/YYYY-Www-raw.json and commits it.
That committed file is what makes subsequent runs idempotent: any signal
whose ID appears in a committed *.json file is silently skipped.
"""

import argparse
import hashlib
import html as html_mod
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import feedparser
import httpx

MAX_ENTRIES_PER_SOURCE = 50
MAX_SUMMARY_CHARS = 600

# Mirrors signals/SOURCES.md. Update both files when the source list changes.
SOURCES: list[dict] = [
    {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "candidate_patterns": [
            "grievance-and-humiliation-reversal",
            "coercion-and-desperation",
            "ideology-faith-nation",
        ],
    },
    {
        "name": "CISA Cybersecurity Advisories",
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "candidate_patterns": [
            "ideology-faith-nation",
            "boredom-with-asymmetric-leverage",
        ],
    },
    {
        "name": "Schneier on Security",
        "url": "https://www.schneier.com/feed/atom/",
        "candidate_patterns": [
            "curiosity-past-the-fence",
            "craft-and-peer-recognition",
        ],
    },
    {
        "name": "arXiv cs.CR",
        "url": "https://export.arxiv.org/rss/cs.CR",
        "candidate_patterns": [
            "curiosity-past-the-fence",
            "craft-and-peer-recognition",
        ],
    },
    {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "candidate_patterns": [
            "status-in-transgressive-subculture",
            "boredom-with-asymmetric-leverage",
            "ideology-faith-nation",
        ],
    },
    {
        "name": "SANS Internet Storm Center",
        "url": "https://isc.sans.edu/rssfeed_full.xml",
        "candidate_patterns": [
            "boredom-with-asymmetric-leverage",
            "status-in-transgressive-subculture",
        ],
    },
    {
        "name": "OpenSSF Blog",
        "url": "https://openssf.org/feed/",
        "candidate_patterns": [
            "boredom-with-asymmetric-leverage",
        ],
    },
    {
        "name": "Seriously Risky Business",
        "url": "https://srslyriskybiz.substack.com/feed",
        "candidate_patterns": [
            "ideology-faith-nation",
            "coercion-and-desperation",
            "craft-and-peer-recognition",
        ],
    },
]

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    return html_mod.unescape(_HTML_TAG_RE.sub(" ", text))


def collapse_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def clean(text: str) -> str:
    return collapse_whitespace(strip_html(text))


def entry_id(entry: feedparser.util.FeedParserDict, source_url: str) -> str:
    """Return a stable unique ID for a feed entry."""
    if guid := getattr(entry, "id", None):
        return guid
    if link := getattr(entry, "link", None):
        return link
    raw = f"{source_url}|{getattr(entry, 'title', '')}"
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()[:20]


def parse_published(entry: feedparser.util.FeedParserDict) -> str | None:
    """Return ISO 8601 UTC string for the entry's publication time, or None."""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, attr, None)
        if t is not None:
            try:
                return datetime(*t[:6], tzinfo=UTC).isoformat()
            except (TypeError, ValueError):
                continue
    return None


def fetch_source(source: dict, client: httpx.Client) -> list[dict]:
    """Fetch and parse one RSS/Atom source. Returns list of signal dicts."""
    try:
        resp = client.get(source["url"], timeout=20.0)
        resp.raise_for_status()
    except Exception as exc:
        print(f"WARN [{source['name']}]: {exc}", file=sys.stderr)
        return []

    try:
        feed = feedparser.parse(
            resp.text,
            response_headers={"content-type": resp.headers.get("content-type", "")},
        )
    except Exception as exc:
        print(f"WARN [{source['name']}]: parse error: {exc}", file=sys.stderr)
        return []

    signals = []
    for entry in feed.entries[:MAX_ENTRIES_PER_SOURCE]:
        title = clean(getattr(entry, "title", "") or "")
        url = getattr(entry, "link", "") or ""
        raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        summary = clean(raw_summary)[:MAX_SUMMARY_CHARS]

        signals.append(
            {
                "id": entry_id(entry, source["url"]),
                "title": title,
                "url": url,
                "published": parse_published(entry),
                "source": source["name"],
                "summary": summary,
                "candidate_patterns": source["candidate_patterns"],
            }
        )

    return signals


def load_seen_ids(signals_dir: Path) -> set[str]:
    """Return all signal IDs from committed *.json files in signals_dir."""
    seen: set[str] = set()
    if not signals_dir.is_dir():
        return seen
    for json_path in sorted(signals_dir.glob("*.json")):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            for sig in data.get("signals", []):
                if sid := sig.get("id"):
                    seen.add(sid)
        except Exception as exc:
            print(f"WARN: could not read {json_path.name}: {exc}", file=sys.stderr)
    return seen


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--signals-dir",
        type=Path,
        default=Path(__file__).parent.parent / "signals",
        help="Path to signals/ directory (default: ../signals relative to this script)",
    )
    args = parser.parse_args()

    signals_dir: Path = args.signals_dir
    seen_ids = load_seen_ids(signals_dir)
    print(f"INFO: {len(seen_ids)} previously seen IDs loaded from {signals_dir}", file=sys.stderr)

    now = datetime.now(UTC)
    week = now.strftime("%G-W%V")

    all_signals: list[dict] = []
    sources_ok = 0

    with httpx.Client(
        headers={
            "User-Agent": (
                "motivation-pattern-log/0.4.0 "
                "(signal fetcher; https://github.com/SHA888/motivation-pattern-log)"
            )
        },
        follow_redirects=True,
    ) as client:
        for source in SOURCES:
            signals = fetch_source(source, client)
            print(f"INFO: [{source['name']}] {len(signals)} entries", file=sys.stderr)
            if signals:
                sources_ok += 1
            all_signals.extend(signals)

    # Deduplicate: skip IDs already committed, and skip within-run duplicates.
    seen_this_run: set[str] = set()
    new_signals: list[dict] = []
    for sig in all_signals:
        sid = sig["id"]
        if sid not in seen_ids and sid not in seen_this_run:
            new_signals.append(sig)
            seen_this_run.add(sid)

    output = {
        "fetched_at": now.isoformat(),
        "week": week,
        "sources_scanned": sources_ok,
        "total_fetched": len(all_signals),
        "new_signals": len(new_signals),
        "signals": new_signals,
    }

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    print(
        f"INFO: {sources_ok}/{len(SOURCES)} sources OK — "
        f"{len(all_signals)} fetched, {len(new_signals)} new",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
