"""Find open predictions whose evaluation window has ended.

Outputs a markdown checklist to stdout. Exits 0 with empty output if
no predictions are due — the caller (monthly-due.yml) checks for empty
output before opening an issue.

Usage:
    uv run notify_due.py --predictions-dir ../predictions --month 2026-05
"""

import argparse
import re
import sys
from pathlib import Path

WINDOW_RE = re.compile(r"(\d{4})-Q([1-4]) through (\d{4})-Q([1-4])")
WINDOW_FIELD_RE = re.compile(r"^-\s+\*\*Predicted window:\*\*\s+(.+)$", re.MULTILINE)
STATUS_FIELD_RE = re.compile(r"^-\s+\*\*Status:\*\*\s+(\w+)$", re.MULTILINE)

# Last month of each quarter
QUARTER_END_MONTH = {1: 3, 2: 6, 3: 9, 4: 12}


def quarter_of_month(month: int) -> int:
    return (month - 1) // 3 + 1


def parse_prediction(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    window_m = WINDOW_FIELD_RE.search(text)
    status_m = STATUS_FIELD_RE.search(text)
    return {
        "file": path.name,
        "window": window_m.group(1).strip() if window_m else "",
        "status": status_m.group(1).strip() if status_m else "",
    }


def window_end_quarter(window_str: str) -> tuple[int, int] | None:
    """Return (end_year, end_quarter) from a window string, or None."""
    m = WINDOW_RE.search(window_str)
    if not m:
        return None
    return int(m.group(3)), int(m.group(4))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions-dir", type=Path, required=True)
    parser.add_argument("--month", required=True, help="Current month as YYYY-MM")
    args = parser.parse_args()

    year_s, month_s = args.month.split("-")
    current_year = int(year_s)
    current_quarter = quarter_of_month(int(month_s))

    due: list[dict] = []
    for pred_file in sorted(args.predictions_dir.glob("PREDICTION-*.md")):
        p = parse_prediction(pred_file)
        if p["status"] != "open":
            continue
        end = window_end_quarter(p["window"])
        if end is None:
            continue
        end_year, end_quarter = end
        # Due when the end quarter has arrived (window has reached its close)
        if end_year < current_year or (end_year == current_year and end_quarter <= current_quarter):
            due.append(p)

    if not due:
        sys.exit(0)

    print(f"## Predictions due for retrospective scoring — {args.month}")
    print()
    print(
        "The following open predictions have reached or passed their evaluation window. "
        "Score each as `confirmed`, `failed`, or `ambiguous`, update the `Status` field, "
        "and append a `### Addendum YYYY-MM-DD` with scoring rationale."
    )
    print()
    for p in due:
        pred_id = p["file"].replace(".md", "")
        print(f"- [ ] [{pred_id}](predictions/{p['file']}) — window: {p['window']}")
    print()
    print(
        "_Retrospective scoring is human-only. No agent scores predictions. "
        "See ARCHITECTURE.md §6._"
    )


if __name__ == "__main__":
    main()
