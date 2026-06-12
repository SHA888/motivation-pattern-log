"""Draft a prediction from a month of signal digests.

Reads every signals/YYYY-Www.md digest whose ISO-week Monday falls in the prior
calendar month (or a single --digest-file), ranks candidate patterns by how many
of those weeks activated them, and calls the Claude API to produce one prediction
file in the repo schema. Output goes to stdout by default; redirect or use --out
to write directly.

Usage:
    cd scripts
    uv run --env-file ../.env draft_prediction.py
    uv run --env-file ../.env draft_prediction.py --digest-file ../signals/2026-W21.md
    uv run --env-file ../.env draft_prediction.py --activation 2 --out ../predictions/

Environment:
    ANTHROPIC_API_KEY  required
    ANTHROPIC_MODEL    optional, overrides --model default
"""

import argparse
import os
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"

VALID_PATTERNS = {
    "status-in-transgressive-subculture",
    "grievance-and-humiliation-reversal",
    "curiosity-past-the-fence",
    "boredom-with-asymmetric-leverage",
    "craft-and-peer-recognition",
    "ideology-faith-nation",
    "coercion-and-desperation",
}

SYSTEM_PROMPT = """\
You are a prediction-drafting assistant for a cybersecurity motivation-pattern research log.

Your task: given a signal digest and the framework context, write ONE complete, falsifiable
prediction file in the exact schema required by the repository.

## SCHEMA (reproduce exactly, including all fields and section headers)

# PREDICTION-{DATE}-{NNNN}

- **Created:** {YYYY-MM-DD}
- **Pattern:** {slug}
- **Substrate:** {specific named system/network/industry — not generic terms like "AI agents"}
- **Leading indicator observed:** {what was actually seen, with reference to the digest signals}
- **Predicted window:** {YYYY-Qn through YYYY-Qn}
- **Predicted shape:** {one concrete paragraph, specific enough to score later}
- **Falsifier:** {one specific observable that, if it occurred, would make this prediction wrong}
- **Confidence:** {low | medium | high}
- **Status:** open

## Reasoning

{One to three paragraphs. State the inference chain: why this pattern, why this substrate,
why this window. Acknowledge what would have to be true for the prediction to fail.
No marketing language.}

## Sources

- {link or signals/ reference from the digest}

## Addenda

## HARD CONSTRAINTS

1. Output ONLY the raw markdown. No commentary, no preamble, no explanation — just the file.
2. The Pattern field must be exactly one of the 7 valid slugs (listed below).
3. Substrate must be specific: name the actual system, platform, or industry vertical.
   Bad: "AI security tools". Good: "LLM-integrated IDE plugins (GitHub Copilot, Cursor, Continue)".
4. Falsifier must be a single, checkable observable — not a vague absence of events.
5. Predicted window must span at least 2 quarters and at most 6 quarters from today.
6. Confidence must reflect genuine uncertainty. Low = plausible but thin evidence.
   Medium = multiple independent signals, pattern-consistent.
   High = reserved for strong convergence.
7. Do NOT score or reference the track record of previous predictions.
8. The Addenda section must exist but be empty (no content after the header).
9. In the Sources section, any reference to a local signals/ file MUST use exactly the
   filename provided in the task prompt (e.g. "signals/2026-W21.md"). Do NOT invent
   variant filenames such as "signals/2026-W21-digest.md" or "signals/2026-W21-raw.md".

## VALID PATTERN SLUGS

- status-in-transgressive-subculture
- grievance-and-humiliation-reversal
- curiosity-past-the-fence
- boredom-with-asymmetric-leverage
- craft-and-peer-recognition
- ideology-faith-nation
- coercion-and-desperation
"""


def find_latest_digest(signals_dir: Path) -> Path:
    digests = sorted(
        f for f in signals_dir.glob("????-W??.md") if not f.name.startswith("TEMPLATE")
    )
    if not digests:
        raise FileNotFoundError(f"No digest files found in {signals_dir}")
    return digests[-1]


def prior_month(today: date) -> tuple[int, int]:
    """Return (year, month) of the calendar month preceding `today`."""
    year, month = today.year, today.month - 1
    if month == 0:
        year, month = year - 1, 12
    return year, month


def find_month_digests(signals_dir: Path, year: int, month: int) -> list[Path]:
    """Return digests whose ISO-week Monday falls in the given calendar month.

    Filenames are ISO year-week (YYYY-Www). A week is assigned to the month
    containing its Monday, so a week straddling a month boundary counts toward
    whichever month its Monday lands in. Returned chronologically.
    """
    dated: list[tuple[date, Path]] = []
    for f in signals_dir.glob("????-W??.md"):
        if f.name.startswith("TEMPLATE"):
            continue
        m = re.match(r"(\d{4})-W(\d{2})\.md$", f.name)
        if not m:
            continue
        monday = date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)
        if monday.year == year and monday.month == month:
            dated.append((monday, f))
    dated.sort()
    return [f for _, f in dated]


def rank_patterns(digest_paths: list[Path]) -> tuple[list[str], Counter]:
    """Rank valid pattern slugs by how many digests activated them.

    A pattern counts at most once per digest (so the score is the number of
    weeks it activated). Ties break by first appearance, chronologically.
    """
    counts: Counter = Counter()
    order: list[str] = []
    for p in digest_paths:
        text = p.read_text(encoding="utf-8")
        seen_in_digest: set[str] = set()
        for heading in parse_activations(text):
            m = re.match(r"\s*([a-z][a-z-]+)", heading)
            slug = m.group(1) if m else ""
            if slug not in VALID_PATTERNS:
                continue
            if slug not in order:
                order.append(slug)
            if slug not in seen_in_digest:
                counts[slug] += 1
                seen_in_digest.add(slug)
    ranked = sorted(order, key=lambda s: (-counts[s], order.index(s)))
    return ranked, counts


def load_static_context(repo_root: Path) -> str:
    parts: list[str] = []
    arch_path = repo_root / "ARCHITECTURE.md"
    parts.append(f"# Framework reference: ARCHITECTURE.md\n\n{arch_path.read_text()}")
    for pat_file in sorted((repo_root / "patterns").glob("*.md")):
        if pat_file.name == "TEMPLATE.md":
            continue
        parts.append(pat_file.read_text())
    return "\n\n---\n\n".join(parts)


def load_existing_predictions(predictions_dir: Path) -> str:
    files = sorted(predictions_dir.glob("PREDICTION-*.md"))
    if not files:
        return "No predictions written yet."
    summaries: list[str] = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        # Extract pattern, substrate, window, status lines for brief summary
        lines = []
        for field in ("Pattern", "Substrate", "Predicted window", "Status"):
            m = re.search(rf"^\*\*{field}:\*\*\s*(.+)$", text, re.MULTILINE)
            if m:
                lines.append(f"  {field}: {m.group(1).strip()}")
        summaries.append(f"- {f.name}\n" + "\n".join(lines))
    return "Existing predictions (to avoid duplication):\n\n" + "\n\n".join(summaries)


def next_sequence(predictions_dir: Path) -> int:
    files = list(predictions_dir.glob("PREDICTION-*.md"))
    if not files:
        return 1
    nums = []
    for f in files:
        m = re.search(r"-(\d{4})\.md$", f.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def parse_activations(digest_text: str) -> list[str]:
    """Return list of activation subsection headings from the digest."""
    return re.findall(r"^### (.+)$", digest_text, re.MULTILINE)


def fix_signal_sources(content: str, digest_filename: str, signals_dir: Path) -> str:
    """Replace hallucinated signals/ paths with the actual digest filename.

    The model occasionally invents variant names like '2026-W21-digest.md' or
    '2026-W21-raw.md'. We correct any signals/*.md reference that does not
    correspond to a real file on disk.
    """
    real_files = {f.name for f in signals_dir.glob("*.md") if f.name != "TEMPLATE.md"}

    def replace(m: re.Match) -> str:
        fname = m.group(1)
        if fname in real_files:
            return m.group(0)  # already correct
        print(
            f"INFO: corrected hallucinated source path 'signals/{fname}' "
            f"→ 'signals/{digest_filename}'",
            file=sys.stderr,
        )
        return f"signals/{digest_filename}"

    return re.sub(r"signals/([\w.\-]+\.md)", replace, content)


def call_api(
    client: anthropic.Anthropic,
    model: str,
    context: str,
    digest_text: str,
    existing_preds: str,
    activation_hint: str,
    seq: int,
    today: str,
    digest_filenames: list[str],
    real_signal_files: list[str],
) -> tuple[str, dict]:
    signal_files_note = (
        "Real signals/ files you may cite (exact filenames — do not invent others):\n"
        + "\n".join(f"  signals/{f}" for f in sorted(real_signal_files))
    )
    digest_cite_note = ", ".join(f"signals/{n}" for n in digest_filenames)
    user_content = (
        f"Framework context (ARCHITECTURE.md + all pattern files):\n\n{context}\n\n"
        f"---\n\n{existing_preds}\n\n"
        f"---\n\n"
        f"{signal_files_note}\n\n"
        f"---\n\n"
        f"Signal digests to base the prediction on "
        f"(this month's weekly digests: {digest_cite_note}):\n\n"
        f"{digest_text}\n\n"
        f"---\n\n"
        f"Task: Draft one prediction synthesizing this month's evidence for the "
        f"recurring activation: **{activation_hint}**\n\n"
        f"Use filename PREDICTION-{today.replace('-', '')}-{seq:04d}.md "
        f"and Created date {today}.\n"
        f"Sequence number: {seq:04d}.\n"
        f"When citing digests in Sources, use one or more of exactly: {digest_cite_note}\n"
        f"Output only the raw markdown file."
    )
    response = client.messages.create(
        model=model,
        max_tokens=2048,
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
                        "text": user_content,
                        "cache_control": {"type": "ephemeral"},
                    }
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
        "--digest-file",
        type=Path,
        default=None,
        help="Single signals digest .md file (overrides the prior-month window)",
    )
    parser.add_argument(
        "--activation",
        type=int,
        default=1,
        help="Pattern rank across the month's digests, 1-indexed (default: 1 = most recurring)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Directory to write the prediction file (default: stdout)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent.parent,
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
    )
    args = parser.parse_args()

    signals_dir = args.repo_root / "signals"
    predictions_dir = args.repo_root / "predictions"

    today = date.today()

    if args.digest_file:
        digest_paths = [args.digest_file]
    else:
        year, month = prior_month(today)
        digest_paths = find_month_digests(signals_dir, year, month)
        if not digest_paths:
            fallback = find_latest_digest(signals_dir)
            print(
                f"INFO: no digests with an ISO-week Monday in {year}-{month:02d}; "
                f"falling back to latest digest {fallback.name}",
                file=sys.stderr,
            )
            digest_paths = [fallback]

    digest_filenames = [p.name for p in digest_paths]
    digest_text = "\n\n---\n\n".join(
        f"## Digest: {p.name}\n\n{p.read_text(encoding='utf-8')}" for p in digest_paths
    )
    print(
        f"INFO: using {len(digest_paths)} digest(s): {', '.join(digest_filenames)}",
        file=sys.stderr,
    )

    real_signal_files = [f.name for f in signals_dir.glob("*.md") if f.name != "TEMPLATE.md"]

    ranked, counts = rank_patterns(digest_paths)
    if not ranked:
        print("ERROR: no valid pattern activations found in digest(s)", file=sys.stderr)
        sys.exit(1)

    idx = args.activation - 1
    if idx < 0 or idx >= len(ranked):
        print(
            f"ERROR: --activation {args.activation} out of range "
            f"({len(ranked)} distinct pattern(s) activated this month)",
            file=sys.stderr,
        )
        sys.exit(1)

    chosen = ranked[idx]
    activation_hint = (
        f"{chosen} (activated in {counts[chosen]} of {len(digest_paths)} "
        f"weekly digest(s) this month)"
    )
    print(f"INFO: targeting pattern: {activation_hint}", file=sys.stderr)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    context = load_static_context(args.repo_root)
    existing_preds = load_existing_predictions(predictions_dir)
    seq = next_sequence(predictions_dir)
    today_str = today.isoformat()

    print(f"INFO: calling {args.model} (seq {seq:04d}, date {today_str})...", file=sys.stderr)

    client = anthropic.Anthropic(api_key=api_key)
    content, usage = call_api(
        client,
        args.model,
        context,
        digest_text,
        existing_preds,
        activation_hint,
        seq,
        today_str,
        digest_filenames,
        real_signal_files,
    )
    log_cost(args.model, usage)

    if not content.strip():
        print("ERROR: empty response from API", file=sys.stderr)
        sys.exit(1)

    content = fix_signal_sources(content, digest_filenames[-1], signals_dir)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        filename = f"PREDICTION-{today_str.replace('-', '')}-{seq:04d}.md"
        out_path = args.out / filename
        out_path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        print(f"INFO: written to {out_path}", file=sys.stderr)
    else:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()
