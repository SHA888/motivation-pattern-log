"""Publish a prediction file to Dev.to as a draft article.

Reads a predictions/PREDICTION-*.md file, builds a Dev.to article payload,
and POSTs it as an unpublished draft. Prints the draft URL to stdout.

Usage:
    cd scripts
    uv run --env-file ../.env publish_dev.py --file ../predictions/PREDICTION-20260518-0006.md

Environment:
    DEV_TO_API_KEY  required
"""

import argparse
import os
import re
import sys
from pathlib import Path

import httpx

DEV_TO_API = "https://dev.to/api/articles"

PATTERN_TAGS = {
    "status-in-transgressive-subculture": "infosec",
    "grievance-and-humiliation-reversal": "infosec",
    "curiosity-past-the-fence": "infosec",
    "boredom-with-asymmetric-leverage": "infosec",
    "craft-and-peer-recognition": "infosec",
    "ideology-faith-nation": "infosec",
    "coercion-and-desperation": "infosec",
}

PREAMBLE_TEMPLATE = """\
> **Originally written: {created}** — this article was backdated to match the \
prediction log. Dev.to does not support custom publication dates; the original \
date is preserved here for the record.
>
> From the [motivation-pattern-log](https://github.com/SHA888/motivation-pattern-log) — \
a public, dated, falsifiable prediction log for AI-era cybersecurity attack patterns \
grounded in motivation analysis. Predictions are scored quarterly against stated falsifiers.

---

"""


def extract_field(text: str, field: str) -> str:
    m = re.search(rf"^-\s+\*\*{re.escape(field)}:\*\*\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def build_title(pred_id: str, pattern: str, window: str) -> str:
    return f"{pred_id}: {pattern} [{window}]"


def build_tags(pattern: str) -> list[str]:
    tags = ["cybersecurity", "security", "prediction"]
    extra = PATTERN_TAGS.get(pattern)
    if extra and extra not in tags:
        tags.append(extra)
    return tags[:4]


def publish(file: Path, api_key: str, dry_run: bool) -> str:
    text = file.read_text(encoding="utf-8")
    pred_id = file.stem  # e.g. PREDICTION-20260518-0006

    pattern = extract_field(text, "Pattern")
    window = extract_field(text, "Predicted window")
    confidence = extract_field(text, "Confidence")
    created = extract_field(text, "Created")

    if not pattern:
        print(f"ERROR: could not extract Pattern from {file.name}", file=sys.stderr)
        sys.exit(1)

    title = build_title(pred_id, pattern, window)
    tags = build_tags(pattern)
    preamble = PREAMBLE_TEMPLATE.format(created=created or pred_id)
    body = preamble + text

    if confidence:
        body += (
            f"\n\n---\n\n*Confidence: {confidence} | Status: open | "
            f"Scored quarterly. See repo for addenda and scoring rationale.*\n"
        )

    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "published": False,
            "tags": tags,
            "series": "motivation-pattern-log",
        }
    }

    if dry_run:
        import json

        print(json.dumps(payload, indent=2))
        return "(dry-run)"

    resp = httpx.post(
        DEV_TO_API,
        json=payload,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        print(
            f"ERROR: Dev.to returned {resp.status_code}: {resp.text[:400]}",
            file=sys.stderr,
        )
        sys.exit(1)

    data = resp.json()
    url = data.get("url") or f"https://dev.to/dashboard (id={data.get('id')})"
    return url


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", type=Path, required=True, help="Prediction markdown file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print payload to stdout instead of posting",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("DEV_TO_API_KEY", "")
    if not api_key and not args.dry_run:
        print("ERROR: DEV_TO_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    url = publish(args.file, api_key, args.dry_run)
    print(url)


if __name__ == "__main__":
    main()
