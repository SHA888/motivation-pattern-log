"""Validate prediction files against the schema defined in ARCHITECTURE.md §4."""

import re
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "Created",
    "Pattern",
    "Substrate",
    "Leading indicator observed",
    "Predicted window",
    "Predicted shape",
    "Falsifier",
    "Confidence",
    "Status",
]

VALID_PATTERNS = {
    "status-in-transgressive-subculture",
    "grievance-and-humiliation-reversal",
    "curiosity-past-the-fence",
    "boredom-with-asymmetric-leverage",
    "craft-and-peer-recognition",
    "ideology-faith-nation",
    "coercion-and-desperation",
}

VALID_CONFIDENCE = {"low", "medium", "high"}
VALID_STATUS = {"open", "confirmed", "failed", "ambiguous", "withdrawn"}

FILENAME_RE = re.compile(r"^PREDICTION-\d{8}-\d{4}\.md$")
WINDOW_RE = re.compile(r"^\d{4}-Q[1-4] through \d{4}-Q[1-4]$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_SECTIONS = ["## Reasoning", "## Sources", "## Addenda"]


def parse_fields(text: str) -> dict[str, str]:
    fields = {}
    for field in REQUIRED_FIELDS:
        pattern = re.compile(rf"^-\s+\*\*{re.escape(field)}:\*\*\s*(.+)$", re.MULTILINE)
        m = pattern.search(text)
        if m:
            fields[field] = m.group(1).strip()
    return fields


def validate_file(path: Path) -> list[str]:
    errors = []

    if not FILENAME_RE.match(path.name):
        errors.append(f"Filename '{path.name}' does not match PREDICTION-YYYYMMDD-NNNN.md")

    text = path.read_text()

    if not text.startswith(f"# {path.stem}"):
        errors.append(f"H1 heading must be '# {path.stem}'")

    fields = parse_fields(text)

    for field in REQUIRED_FIELDS:
        if field not in fields:
            errors.append(f"Missing required field: '{field}'")

    if "Created" in fields and not DATE_RE.match(fields["Created"]):
        errors.append(f"'Created' must be YYYY-MM-DD, got: '{fields['Created']}'")

    if "Pattern" in fields and fields["Pattern"] not in VALID_PATTERNS:
        errors.append(f"'Pattern' value '{fields['Pattern']}' not in allowed vocabulary")

    if "Predicted window" in fields and not WINDOW_RE.match(fields["Predicted window"]):
        got = fields["Predicted window"]
        errors.append(f"'Predicted window' must match 'YYYY-Qn through YYYY-Qn', got: '{got}'")

    if "Confidence" in fields and fields["Confidence"] not in VALID_CONFIDENCE:
        errors.append(f"'Confidence' must be low|medium|high, got: '{fields['Confidence']}'")

    if "Status" in fields and fields["Status"] not in VALID_STATUS:
        errors.append(f"'Status' must be one of {VALID_STATUS}, got: '{fields['Status']}'")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"Missing required section: '{section}'")

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_predictions.py <predictions-dir>", file=sys.stderr)
        sys.exit(1)

    predictions_dir = Path(sys.argv[1])
    if not predictions_dir.is_dir():
        print(f"Not a directory: {predictions_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(f for f in predictions_dir.glob("*.md") if f.name != "TEMPLATE.md")

    if not files:
        print("No prediction files found (TEMPLATE.md excluded). OK.")
        sys.exit(0)

    all_errors: dict[str, list[str]] = {}
    for f in files:
        errs = validate_file(f)
        if errs:
            all_errors[f.name] = errs

    if all_errors:
        for filename, errs in all_errors.items():
            for err in errs:
                print(f"ERROR [{filename}]: {err}", file=sys.stderr)
        sys.exit(1)

    print(f"All {len(files)} prediction(s) valid.")


if __name__ == "__main__":
    main()
