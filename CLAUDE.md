# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## What this repo is

A public, dated, falsifiable prediction log for AI-era cybersecurity attack patterns, grounded in motivation analysis rather than technique cataloging. The primary artifact is a disciplined writing practice; code is minimal scaffolding.

The framework is documented in `ARCHITECTURE.md`. Read it before touching any content files — it defines the vocabulary (7 motivation patterns), the prediction schema, and the four tests a pattern must pass to remain in the framework.

## Commands

All scripts use `uv` with Python ≥ 3.13. Run from the `scripts/` directory:

```bash
# Install dependencies
cd scripts && uv sync --locked

# Validate all prediction files against schema
cd scripts && uv run validate_predictions.py ../predictions

# Validate all pattern files against schema
cd scripts && uv run validate_patterns.py ../patterns

# Lint Python
cd scripts && uv run ruff check .
cd scripts && uv run ruff format --check .
```

CI runs both validators and ruff on every push/PR (`.github/workflows/ci.yml`).

Pre-commit hooks: trailing whitespace, YAML/JSON check, ruff lint+format. Run `pre-commit install` to activate locally.

## Content schemas (enforced by validators)

**Prediction files** (`predictions/PREDICTION-YYYYMMDD-NNNN.md`):
- Required frontmatter fields: `Created`, `Pattern`, `Substrate`, `Leading indicator observed`, `Predicted window`, `Predicted shape`, `Falsifier`, `Confidence`, `Status`
- `Pattern` must be a slug from the 7 valid patterns (see `validate_predictions.py:VALID_PATTERNS`)
- `Predicted window` format: `YYYY-Qn through YYYY-Qn`
- `Confidence`: `low | medium | high`
- `Status`: `open | confirmed | failed | ambiguous | withdrawn`
- Required sections: `## Reasoning`, `## Sources`, `## Addenda`
- **After commit, the prediction body is frozen.** Append-only via `### Addendum YYYY-MM-DD` under `## Addenda`. Never edit above the addenda section.
- Sequence number `NNNN` is monotonically increasing across the whole repo, never reset per day.

**Pattern files** (`patterns/NN-<slug>.md`):
- Required frontmatter: `Status`, `Added`, `Last revised`, `Framework version`
- `Status`: `active | retired | provisional`
- Required sections: `## Operational definition`, `## Historical instantiations`, `## Leading indicators`, `## Known failure modes`, `## Cultural variants`, `## Disconfirmability test`, `## Predictions deriving from this pattern`
- Filename: `NN-pattern-name.md` (two-digit prefix)

Use `patterns/TEMPLATE.md`, `predictions/TEMPLATE.md`, `signals/TEMPLATE.md`, `retrospectives/TEMPLATE.md` as canonical starting points.

## Architecture and content rules

**Content the agent must never write:**
- Retrospective scores (human-only, quarterly)
- Status updates on existing predictions

**Agent-permitted automation:**
- Weekly signal digests: cluster signals by candidate pattern activation, surface for human review.
- Prediction drafts: agent may draft a prediction from a signal digest; human reviews and commits.

**Framework versioning** (SemVer, in `ARCHITECTURE.md §8`):
- Patch: prose/link fixes
- Minor: pattern added, retired, or leading-indicator refined
- Major: schema change, test change, or boundary change

**Immutability rule:** Past prediction files may only receive addenda. Any edit to the prediction body (title, frontmatter, Reasoning, Sources) is a protocol violation.

## Scripts

- `scripts/fetch_signals.py` — fetch and deduplicate signals from curated RSS/Atom sources → JSON to stdout
- `scripts/draft_digest.py` — call Claude API with ARCHITECTURE.md + patterns context + signals; output a `signals/YYYY-Www.md` digest file
- `scripts/draft_prediction.py` — call Claude API with digest + framework context; draft one prediction file for human review
