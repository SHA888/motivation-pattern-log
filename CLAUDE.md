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

# Verify a prediction's cited claims actually match its cited signals/ digests
cd scripts && uv run verify_prediction_sources.py ../predictions/PREDICTION-YYYYMMDD-NNNN.md

# Lint Python
cd scripts && uv run ruff check .
cd scripts && uv run ruff format --check .
```

CI runs both validators and ruff on every push/PR (`.github/workflows/ci.yml`).

`verify_prediction_sources.py` is a separate, narrower check from `validate_predictions.py`:
the schema validator confirms cited `signals/` filenames are well-formed and exist; it does
**not** confirm that the claims attributed to a cited digest are actually supported by that
digest's text. `verify_prediction_sources.py` calls the Claude API to check every claim in a
prediction's `Leading indicator observed` field and `Reasoning` section against the real text
of each digest it cites, and flags `UNSUPPORTED` (fact not in the digest), `MISATTRIBUTED`
(fact is real but under a different week), or `MISCHARACTERIZED` (fact is real but the digest
itself caveats or discards it and the prediction drops that caveat). It runs automatically and
blocks the PR check on any `predictions/PREDICTION-*.md` change
(`.github/workflows/verify-prediction-sources.yml`) — closing the gap where a prediction could
cite a real digest filename while still misrepresenting what that digest said, previously
catchable only by a manual `@claude review`.

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

**Agent-permitted automation** (framework v1.0.0, 2026-05-26):

- Weekly signal digests: cluster signals by candidate pattern activation.
- Prediction drafts: agent may draft predictions from a signal digest.
- Prediction review: agent may review drafted predictions against schema and framework before merge.
- Retrospective scoring: agent may close predictions as `confirmed | failed | ambiguous`, append the scoring addendum, and produce Brier-style calibration analyses on the same terms as the author.

**Constraints that still hold for every writer (agent or human):**

- Predictions, patterns, and retrospectives must conform to the schemas validated by `scripts/validate_*.py`.
- §7 boundaries from `ARCHITECTURE.md` apply universally: no specific-incident prediction, no actor attribution, no offensive tooling, no private signals, no monetization.
- Scoring is bound by what the prediction said at creation — the frozen falsifier and predicted shape — not by the scorer's narrative judgement.

**Framework versioning** (SemVer, in `ARCHITECTURE.md §8`):

- Patch: prose/link fixes
- Minor: pattern added, retired, or leading-indicator refined
- Major: schema change, test change, or boundary change

**Immutability rule:** Past prediction files may only receive addenda. Any edit to the prediction body (title, frontmatter, Reasoning, Sources) is a protocol violation. This rule binds agents and humans equally — the agent's expanded scope to write and score does not extend to revising committed predictions.

## Scripts

- `scripts/fetch_signals.py` — fetch and deduplicate signals from curated RSS/Atom sources → JSON to stdout
- `scripts/draft_digest.py` — call Claude API with ARCHITECTURE.md + patterns context + signals; output a `signals/YYYY-Www.md` digest file
- `scripts/draft_prediction.py` — call Claude API with digest + framework context; draft one prediction file (reviewed by agent or author before merge)

**Do not include `Co-Authored-By:` trailers in commit messages.** This applies to all assistant-generated commits, including those produced by Claude Code or any other AI tool. Commit attribution stays with the human author. Boilerplate trailers add noise to the history without conveying meaningful authorship and have been retroactively stripped from past commits.
