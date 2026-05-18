"""Draft a prediction from a signal digest.

Reads the most-recent signals/YYYY-Www.md (or --digest-file) and calls the
Claude API to produce one prediction file in the repo schema. Output goes to
stdout by default; redirect or use --out to write directly.

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


def call_api(
    client: anthropic.Anthropic,
    model: str,
    context: str,
    digest_text: str,
    existing_preds: str,
    activation_hint: str,
    seq: int,
    today: str,
) -> tuple[str, dict]:
    user_content = (
        f"Framework context (ARCHITECTURE.md + all pattern files):\n\n{context}\n\n"
        f"---\n\n{existing_preds}\n\n"
        f"---\n\n"
        f"Signal digest to base the prediction on:\n\n{digest_text}\n\n"
        f"---\n\n"
        f"Task: Draft one prediction based on the activation cluster: **{activation_hint}**\n\n"
        f"Use filename PREDICTION-{today.replace('-', '')}-{seq:04d}.md "
        f"and Created date {today}.\n"
        f"Sequence number: {seq:04d}.\n"
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
        help="Signals digest .md file (default: latest signals/YYYY-Www.md)",
    )
    parser.add_argument(
        "--activation",
        type=int,
        default=1,
        help="Which activation cluster to use, 1-indexed (default: 1 = first listed)",
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

    digest_path = args.digest_file or find_latest_digest(signals_dir)
    digest_text = digest_path.read_text(encoding="utf-8")
    print(f"INFO: using digest {digest_path.name}", file=sys.stderr)

    activations = parse_activations(digest_text)
    if not activations:
        print("ERROR: no activation clusters found in digest", file=sys.stderr)
        sys.exit(1)

    idx = args.activation - 1
    if idx >= len(activations):
        print(
            f"ERROR: --activation {args.activation} out of range "
            f"(digest has {len(activations)} activation(s))",
            file=sys.stderr,
        )
        sys.exit(1)

    activation_hint = activations[idx]
    print(f"INFO: targeting activation: {activation_hint}", file=sys.stderr)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    context = load_static_context(args.repo_root)
    existing_preds = load_existing_predictions(predictions_dir)
    seq = next_sequence(predictions_dir)
    today = date.today().isoformat()

    print(f"INFO: calling {args.model} (seq {seq:04d}, date {today})...", file=sys.stderr)

    client = anthropic.Anthropic(api_key=api_key)
    content, usage = call_api(
        client, args.model, context, digest_text, existing_preds, activation_hint, seq, today
    )
    log_cost(args.model, usage)

    if not content.strip():
        print("ERROR: empty response from API", file=sys.stderr)
        sys.exit(1)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        filename = f"PREDICTION-{today.replace('-', '')}-{seq:04d}.md"
        out_path = args.out / filename
        out_path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        print(f"INFO: written to {out_path}", file=sys.stderr)
    else:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()
