"""Validate pattern files against the schema defined in ARCHITECTURE.md §2."""

import re
import sys
from pathlib import Path

VALID_STATUS = {"active", "retired", "provisional"}

FILENAME_RE = re.compile(r"^\d{2}-[\w-]+\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_FIELDS = ["Status", "Added", "Last revised", "Framework version"]

REQUIRED_SECTIONS = [
    "## Operational definition",
    "## Historical instantiations",
    "## Leading indicators",
    "## Known failure modes",
    "## Cultural variants",
    "## Disconfirmability test",
    "## Predictions deriving from this pattern",
]


def parse_fields(text: str) -> dict[str, str]:
    fields = {}
    for field in REQUIRED_FIELDS:
        pattern = re.compile(rf"^\*\*{re.escape(field)}:\*\*\s*(.+)$", re.MULTILINE)
        m = pattern.search(text)
        if m:
            fields[field] = m.group(1).strip()
    return fields


def validate_file(path: Path) -> list[str]:
    errors = []

    if not FILENAME_RE.match(path.name):
        errors.append(f"Filename '{path.name}' does not match NN-pattern-name.md")

    text = path.read_text()

    if not text.startswith("# Pattern:"):
        errors.append("H1 heading must start with '# Pattern:'")

    fields = parse_fields(text)

    for field in REQUIRED_FIELDS:
        if field not in fields:
            errors.append(f"Missing required field: '{field}'")

    if "Status" in fields:
        status_val = fields["Status"].split("|")[0].strip()
        if status_val not in VALID_STATUS:
            errors.append(f"'Status' must be active|retired|provisional, got: '{fields['Status']}'")

    for date_field in ("Added", "Last revised"):
        if date_field in fields and not DATE_RE.match(fields[date_field]):
            errors.append(f"'{date_field}' must be YYYY-MM-DD, got: '{fields[date_field]}'")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"Missing required section: '{section}'")

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_patterns.py <patterns-dir>", file=sys.stderr)
        sys.exit(1)

    patterns_dir = Path(sys.argv[1])
    if not patterns_dir.is_dir():
        print(f"Not a directory: {patterns_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(f for f in patterns_dir.glob("*.md") if f.name != "TEMPLATE.md")

    if not files:
        print("No pattern files found (TEMPLATE.md excluded). OK.")
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

    print(f"All {len(files)} pattern file(s) valid.")


if __name__ == "__main__":
    main()
