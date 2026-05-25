"""Draft a weekly signal digest from fetched signals JSON.

Reads signals from --signals-file or stdin (output of fetch_signals.py).
Loads ARCHITECTURE.md and patterns/*.md as context (prompt-cached).
Calls the Claude API once and writes a markdown digest to stdout.

Usage:
    uv run scripts/fetch_signals.py | uv run scripts/draft_digest.py
    uv run scripts/draft_digest.py --signals-file signals/2026-W21-raw.json
    uv run scripts/draft_digest.py --signals-file signals/2026-W21-raw.json > signals/2026-W21.md

Environment:
    ANTHROPIC_API_KEY  required
    ANTHROPIC_MODEL    optional, overrides --model default
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_SIGNALS = 100  # trim before sending; prioritise order from fetcher (source-grouped)


SYSTEM_PROMPT = """\
You are a signal-clustering assistant for a cybersecurity motivation-pattern research log.

Your task: read a batch of raw security signals (news, papers, advisories) and produce a
structured weekly digest that clusters them by the motivation pattern they may indicate.
Each signal carries a `candidate_patterns` hint from the source list; treat these as starting
points, not conclusions — use the signal content to confirm or reassign.

## HARD CONSTRAINTS

1. Do NOT write predictions in the digest output. Do not write "I predict", "this will",
   "expect X to happen", or any forward-looking claim about attacker behaviour here.
   Predictions are produced by `draft_prediction.py` in a separate step that operates on
   the digest you produce — keeping the steps separate prevents single-prompt drift.
2. Do NOT attribute attacks to specific named companies, individuals, or groups unless that
   attribution is stated explicitly in the signal text you received.
3. Do NOT generate offensive techniques, exploit code, or attack recipes.
4. Do NOT pre-grade the practice's calibration in this digest. Retrospective scoring lives
   in its own quarterly artifact (`retrospectives/YYYY-Qn.md`), not in the weekly digest.
5. Each candidate-activation section must include an explicit disclaimer:
   "This is not yet a prediction."
6. Honest uncertainty is required. If you are unsure whether something is real activation
   or noise, say so. Confident-sounding noise is worse than an admission of uncertainty.

## OUTPUT FORMAT

Produce markdown that exactly follows this structure. Fill placeholders from the signals data.

---

# Signal digest {WEEK}

- **Week:** {WEEK} ({DATE_RANGE})
- **Sources scanned:** {SOURCES_SCANNED}
- **Raw signals collected:** {TOTAL_FETCHED}
- **Signals after dedup:** {NEW_SIGNALS}

## Candidate pattern activations

For each pattern where 2 or more signals plausibly indicate activation this week, write one
subsection below. Omit patterns with fewer than 2 signals — do not pad with weak evidence.

### {pattern-slug} — {brief substrate hint}

- **Signals:** [title](url), [title](url), ...
- **Confidence:** low | med | high — one word, then one sentence explaining why
- **Why this might be activating:** one paragraph grounded specifically in the signals listed
- **Why this might be noise:** one paragraph of honest skepticism
- **Suggested next step:** exactly one of:
  "Watch N more weeks" | "Could justify a prediction now" | "Discard"
- **Disclaimer:** This is not yet a prediction.

## Discarded clusters

One bullet per signal or small cluster you considered and rejected. One-sentence reason each.

## Notes for review

- Flag signals that are ambiguous or unclassifiable
- Note any sources that were unreachable or returned low-quality content this week
- Flag any signal that looks like a useful leading indicator even if it does not yet support
  a full activation cluster

---

*This digest was drafted by an automated agent. Predictions derived from this
digest are written by `draft_prediction.py` in a separate step; the agent may
also review those drafts and score predictions at retrospective time. See
`ARCHITECTURE.md` §6 for the boundary.*

---

Keep the total digest under 1500 words. Prefer specific signal citations over general commentary.\
"""


def load_static_context(repo_root: Path) -> str:
    """Load ARCHITECTURE.md and all active pattern files as a single string."""
    parts: list[str] = []

    arch_path = repo_root / "ARCHITECTURE.md"
    parts.append(f"# Framework reference: ARCHITECTURE.md\n\n{arch_path.read_text()}")

    for pat_file in sorted((repo_root / "patterns").glob("*.md")):
        if pat_file.name == "TEMPLATE.md":
            continue
        parts.append(pat_file.read_text())

    return "\n\n---\n\n".join(parts)


def week_date_range(week_str: str) -> str:
    """Return 'Mon YYYY-MM-DD through Sun YYYY-MM-DD' for an ISO week string."""
    year_s, week_s = week_str.split("-W")
    monday = date.fromisocalendar(int(year_s), int(week_s), 1)
    sunday = monday + timedelta(days=6)
    return f"Mon {monday} through Sun {sunday}"


def build_signals_block(signals_data: dict) -> str:
    signals = signals_data.get("signals", [])[:MAX_SIGNALS]
    week = signals_data.get("week", "unknown")
    try:
        date_range = week_date_range(week)
    except (ValueError, AttributeError):
        date_range = "unknown"
    meta = (
        f"Week: {week}\n"
        f"Date range: {date_range}\n"
        f"Sources scanned: {signals_data.get('sources_scanned', 0)}\n"
        f"Total fetched: {signals_data.get('total_fetched', 0)}\n"
        f"New signals: {signals_data.get('new_signals', 0)}\n\n"
        f"Signals ({len(signals)} items):\n"
    )
    return meta + json.dumps(signals, indent=2, ensure_ascii=False)


def call_api(
    client: anthropic.Anthropic,
    model: str,
    context: str,
    signals_block: str,
) -> tuple[str, dict]:
    """One API call with prompt caching on static context. Returns (text, usage)."""
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Framework context (ARCHITECTURE.md + all pattern files):\n\n" + context
                        ),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": "Raw signals for this week:\n\n" + signals_block,
                    },
                ],
            }
        ],
    )
    content = response.content[0].text if response.content else ""
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
        "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
    }
    return content, usage


def log_cost(model: str, usage: dict) -> None:
    """Print a rough cost estimate to stderr for the completed API call."""
    # Pricing reference (claude-sonnet-4-6, 2026):
    #   input $3.00/MTok, output $15.00/MTok
    #   cache write $3.75/MTok, cache read $0.30/MTok
    rates = {
        "claude-sonnet-4-6": (3.00, 15.00, 3.75, 0.30),
        "claude-haiku-4-5": (0.80, 4.00, 1.00, 0.08),
    }
    r = rates.get(model, rates["claude-sonnet-4-6"])
    cost = (
        usage["input_tokens"] * r[0]
        + usage["output_tokens"] * r[1]
        + usage["cache_creation_input_tokens"] * r[2]
        + usage["cache_read_input_tokens"] * r[3]
    ) / 1_000_000
    print(
        f"INFO: tokens — in: {usage['input_tokens']}, out: {usage['output_tokens']}, "
        f"cache_write: {usage['cache_creation_input_tokens']}, "
        f"cache_read: {usage['cache_read_input_tokens']} — "
        f"estimated cost: ${cost:.4f}",
        file=sys.stderr,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--signals-file",
        type=Path,
        default=None,
        help="Signals JSON file (default: read from stdin)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Repo root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        help=f"Claude model (default: {DEFAULT_MODEL} or $ANTHROPIC_MODEL)",
    )
    args = parser.parse_args()

    # Load signals JSON
    raw = args.signals_file.read_text(encoding="utf-8") if args.signals_file else sys.stdin.read()
    try:
        signals_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid signals JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if not signals_data.get("signals"):
        print("INFO: no new signals this week — skipping API call", file=sys.stderr)
        sys.exit(0)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    context = load_static_context(args.repo_root)
    signals_block = build_signals_block(signals_data)

    n_signals = len(signals_data["signals"])
    print(f"INFO: calling {args.model} ({n_signals} signals)...", file=sys.stderr)

    client = anthropic.Anthropic(api_key=api_key)
    content, usage = call_api(client, args.model, context, signals_block)
    log_cost(args.model, usage)

    sys.stdout.write(content)
    if not content.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
