"""Verify claim-level source accuracy for prediction files.

validate_predictions.py checks schema shape and that cited signals/ filenames
are well-formed — it does not check that the *content* attributed to a cited
digest actually appears in it. This script closes that gap: for each cited
signals/ digest, it asks Claude to check every claim in the prediction's
"Leading indicator observed" field and "Reasoning" section against that
digest's real text, and reports whether each claim is supported, misattributed
to the wrong week, or presented with the wrong framing (e.g. citing a digest's
own "discarded" item as confirmed evidence).

Usage (from scripts/):
    uv run verify_prediction_sources.py ../predictions/PREDICTION-20260701-0009.md
    uv run verify_prediction_sources.py ../predictions          # all prediction files

Environment:
    ANTHROPIC_API_KEY  required
    ANTHROPIC_MODEL    optional, overrides --model default
"""

import argparse
import os
import re
import sys
from pathlib import Path

import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"

LEADING_INDICATOR_RE = re.compile(r"^-\s+\*\*Leading indicator observed:\*\*\s*(.+)$", re.MULTILINE)
REASONING_RE = re.compile(r"^## Reasoning\s*$(.*?)^## ", re.MULTILINE | re.DOTALL)
SOURCES_RE = re.compile(r"^## Sources\s*$(.*?)^## ", re.MULTILINE | re.DOTALL)
SOURCE_FILE_RE = re.compile(r"signals/[\w.\-]+\.md")

VALID_VERDICTS = {"SUPPORTED", "UNSUPPORTED", "MISATTRIBUTED", "MISCHARACTERIZED"}
BLOCKING_VERDICTS = {"UNSUPPORTED", "MISATTRIBUTED", "MISCHARACTERIZED"}

SYSTEM_PROMPT = """\
You are a claim-level fact-checker for a falsifiable cybersecurity prediction \
log. You will be given one prediction's "Leading indicator observed" field and \
"Reasoning" section, plus the full text of every signals/ digest it cites in \
its Sources section.

Your job: extract every discrete factual claim in the prediction that is \
attributed to a specific cited digest (explicit tags like "(W24)", or clear \
contextual attribution), then check each claim against that digest's actual \
text. For each claim, decide exactly one verdict:

- SUPPORTED — the claim's facts, numbers, and week attribution match the \
  cited digest, AND the digest's own framing (confidence level, "why this \
  might be noise", discarded-vs-activated status) is not misrepresented.
- UNSUPPORTED — the claim's facts are not present anywhere in the cited digest.
- MISATTRIBUTED — the facts exist in one of the supplied digests, but under a \
  *different* week than the one the prediction attributes them to (e.g. an \
  event actually reported in W27 is tagged (W24) instead).
- MISCHARACTERIZED — the underlying fact is present in the cited digest, but \
  the digest itself frames it with a caveat, discard, or hedge (e.g. listed \
  under "Discarded clusters", or a "why this might be noise" paragraph) that \
  the prediction drops or contradicts when presenting it as confirming \
  evidence.

Only report a claim if you can quote the digest text that proves your \
verdict. Do not flag stylistic paraphrasing, reasonable summarization, or \
inference the prediction is explicit about drawing itself (e.g. "For this \
prediction to fail..." reasoning is not a claim about digest content). Be \
conservative: if a claim is a fair reading of what a digest says, mark it \
SUPPORTED.

Call the `report_verdicts` tool exactly once with every claim you extracted, \
including the SUPPORTED ones. Never respond with plain text.
"""

REPORT_TOOL = {
    "name": "report_verdicts",
    "description": "Report claim-level source verification verdicts.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {
                            "type": "string",
                            "description": (
                                "The claim as stated in the prediction, quoted or "
                                "closely paraphrased."
                            ),
                        },
                        "cited_source": {
                            "type": "string",
                            "description": (
                                "The signals/*.md filename the prediction attributes this claim to."
                            ),
                        },
                        "verdict": {
                            "type": "string",
                            "enum": sorted(VALID_VERDICTS),
                        },
                        "evidence": {
                            "type": "string",
                            "description": (
                                "Quoted text from the cited digest (or the correct digest, "
                                "for MISATTRIBUTED) proving the verdict."
                            ),
                        },
                    },
                    "required": ["claim", "cited_source", "verdict", "evidence"],
                },
            }
        },
        "required": ["verdicts"],
    },
}


def extract_section(pattern: re.Pattern, text: str) -> str:
    m = pattern.search(text + "\n## ")  # sentinel so the lookahead-free regex terminates
    return m.group(1).strip() if m else ""


def parse_claim_material(text: str) -> tuple[str, str, list[str]]:
    """Return (leading_indicator, reasoning, cited_source_filenames)."""
    m = LEADING_INDICATOR_RE.search(text)
    leading_indicator = m.group(1).strip() if m else ""
    reasoning = extract_section(REASONING_RE, text)
    sources_block = extract_section(SOURCES_RE, text)
    cited = SOURCE_FILE_RE.findall(sources_block)
    return leading_indicator, reasoning, cited


def load_digest_texts(signals_dir: Path, filenames: list[str]) -> dict[str, str]:
    texts: dict[str, str] = {}
    for name in filenames:
        path = signals_dir / Path(name).name
        if path.is_file():
            texts[name] = path.read_text(encoding="utf-8")
        else:
            texts[name] = f"[MISSING FILE: {name} does not exist in {signals_dir}]"
    return texts


def build_user_content(
    prediction_name: str, leading_indicator: str, reasoning: str, digests: dict[str, str]
) -> str:
    digest_blocks = "\n\n---\n\n".join(
        f"### {name}\n\n{content}" for name, content in digests.items()
    )
    return (
        f"Prediction file: {prediction_name}\n\n"
        f"Leading indicator observed:\n{leading_indicator}\n\n"
        f"Reasoning section:\n{reasoning}\n\n"
        f"---\n\nCited digests (full text):\n\n{digest_blocks}"
    )


def call_api(client: anthropic.Anthropic, model: str, user_content: str) -> tuple[list[dict], dict]:
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[REPORT_TOOL],
        tool_choice={"type": "tool", "name": "report_verdicts"},
        messages=[{"role": "user", "content": user_content}],
    )
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
    }
    for block in response.content:
        if block.type == "tool_use" and block.name == "report_verdicts":
            return block.input.get("verdicts", []), usage
    return [], usage


def verify_file(
    client: anthropic.Anthropic, model: str, path: Path, signals_dir: Path
) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    leading_indicator, reasoning, cited = parse_claim_material(text)

    if not cited:
        print(f"INFO [{path.name}]: no signals/ sources cited, skipping.", file=sys.stderr)
        return []

    digests = load_digest_texts(signals_dir, cited)
    user_content = build_user_content(path.name, leading_indicator, reasoning, digests)

    print(f"INFO [{path.name}]: verifying {len(cited)} cited source(s)...", file=sys.stderr)
    verdicts, usage = call_api(client, model, user_content)
    print(
        f"INFO [{path.name}]: tokens in={usage['input_tokens']} out={usage['output_tokens']} "
        f"cache_read={usage['cache_read_input_tokens']}",
        file=sys.stderr,
    )
    for v in verdicts:
        v["file"] = path.name
    return verdicts


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target", type=Path, help="A prediction file, or a directory of them")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Repo root, used to resolve signals/ (default: parent of scripts/)",
    )
    parser.add_argument(
        "--model", default=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL), help="Claude model"
    )
    args = parser.parse_args()

    if args.target.is_dir():
        files = sorted(f for f in args.target.glob("PREDICTION-*.md"))
    elif args.target.is_file():
        files = [args.target]
    else:
        print(f"ERROR: not a file or directory: {args.target}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("No prediction files to verify. OK.")
        sys.exit(0)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    signals_dir = args.repo_root / "signals"
    client = anthropic.Anthropic(api_key=api_key)

    all_verdicts: list[dict] = []
    for f in files:
        all_verdicts.extend(verify_file(client, args.model, f, signals_dir))

    blocking = [v for v in all_verdicts if v.get("verdict") in BLOCKING_VERDICTS]
    supported = [v for v in all_verdicts if v.get("verdict") == "SUPPORTED"]

    for v in all_verdicts:
        tag = v.get("verdict", "UNKNOWN")
        marker = "ERROR" if tag in BLOCKING_VERDICTS else "OK"
        print(f"{marker} [{v.get('file')}] {tag} — {v.get('claim')}", file=sys.stderr)
        if tag in BLOCKING_VERDICTS:
            print(f"       cited: {v.get('cited_source')}", file=sys.stderr)
            print(f"       evidence: {v.get('evidence')}", file=sys.stderr)

    print(
        f"\n{len(supported)} supported, {len(blocking)} flagged, "
        f"{len(all_verdicts)} claim(s) checked across {len(files)} file(s).",
    )

    if blocking:
        sys.exit(1)


if __name__ == "__main__":
    main()
