# scripts/

Python scripts that drive the automation. All managed with `uv`.

**Status: not yet implemented.** This directory holds only the
`pyproject.toml` skeleton and this README at v0.1.0.

Implementation begins at milestone v0.4.0 (signal ingestion) and v0.5.0
(agent-drafted digest), per `../TODO.md`.

## Planned scripts

- `fetch_signals.py` — RSS/Atom aggregator. Reads `../signals/SOURCES.md`,
  fetches new entries since last run (deduplicated against git history),
  outputs JSON to stdout.
- `draft_digest.py` — Loads the framework (`../ARCHITECTURE.md` and
  `../patterns/*.md`) plus the week's signals, calls Claude API to cluster
  signals by candidate pattern activation, writes the digest markdown.
- `notify_due.py` — Scans `../predictions/` for entries whose predicted
  window ends in the given month, formats a checklist for the monthly issue.
- `validate_predictions.py` — Schema validator for prediction files. Used in
  CI.
- `validate_patterns.py` — Schema validator for pattern files. Used in CI.

## Conventions

- Latest stable Python (3.13+).
- Dependencies pinned via `uv.lock`.
- Single-purpose scripts, no shared framework. If shared logic emerges,
  refactor into a small local module — do not introduce a package.
- All scripts must be runnable locally with `uv run <script>` for debugging
  outside Actions.

## Anti-conventions (explicitly avoided)

- No async unless a script genuinely needs concurrent network I/O.
- No web framework. No FastAPI, no Flask.
- No database driver.
- No LLM-orchestration framework (LangChain, LlamaIndex, etc.). Direct
  `anthropic` SDK calls only.
