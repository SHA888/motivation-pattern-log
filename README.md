# motivation-pattern-log

A public, dated, falsifiable prediction log for AI-era cybersecurity attack
patterns, grounded in motivation reading rather than technique cataloging.

## Why this exists

Every prior framework (kill chains, ATT&CK, agent-attack taxonomies) catalogs
*what attackers do*. The vocabulary of *why* — motivation patterns that persist
across decades while techniques churn quarterly — has not been organized into a
disciplined, publicly-calibrated prediction practice.

This repo is one person's attempt at that practice. It is small on purpose.

## What this is not

- Not threat intelligence. Not a product. Not a service.
- Not attribution. Predictions describe *classes* of attack, not specific
  actors or incidents.
- Not deep theory. Patterns are calibrated forecasts, not causal models.
- Not always right. The point is to be *publicly wrong on schedule* so the
  framework can improve.

## How to read the log

- `patterns/` — the motivation-pattern vocabulary. Slow-moving. Revised
  quarterly at most.
- `signals/` — weekly digests of observed signals (subculture chatter, threat
  reports, platform launches, geopolitical shifts). Agent-drafted.
- `predictions/` — one file per prediction. Each carries a date, a pattern, a
  substrate, a leading indicator, a predicted window, a falsifier, and a
  status.
- `retrospectives/` — quarterly reviews. What predictions hit, what missed,
  what the framework needs to revise.

## Cadence

- **Weekly** (Monday): signal digest drafted by agent, opened as PR for review.
- **Monthly** (1st): prediction drafted by agent from the latest digest,
  opened as PR for review. Predictions reaching their evaluation window are
  opened as issues for retrospective scoring.
- **Quarterly** (Apr/Jul/Oct/Jan 1): framework revision and retrospective
  scoring (by agent or author). Patterns that fail twice get rewritten or
  retired.

## Commitment

- 12-month minimum run. Re-evaluate at month 12.
- All predictions versioned in git. Edits to past predictions disallowed —
  only addenda permitted (`### Addendum YYYY-MM-DD`). This rule binds agents
  and humans equally.
- The falsifier and predicted shape, frozen at creation, are the operative
  test. Retrospective scoring records the scorer (`human` | `agent` | `mixed`)
  but is bound by what the prediction said, not by who is grading it.

## License

- Code (`scripts/`, `.github/`): `MIT OR Apache-2.0`. See `LICENSE-MIT` and
  `LICENSE-APACHE`.
- Predictions, patterns, signals, retrospectives, and all prose: `CC BY 4.0`.
  See `LICENSE-CONTENT`.

## Automation costs

The weekly digest agent (`scripts/draft_digest.py`) makes one Claude API call per week.
Expected cost at default model (`claude-sonnet-4-6`):

| Item | Tokens | Cost/week |
|---|---|---|
| Context (ARCHITECTURE + 7 patterns) | ~12 000 | — |
| Signals (up to 100 entries) | ~24 000 | — |
| Output (digest markdown) | ~2 000 | — |
| **Total per call** | **~38 000** | **~$0.15** |
| **Monthly (4 calls)** | | **~$0.60** |

Switch to `claude-haiku-4-5` via `ANTHROPIC_MODEL=claude-haiku-4-5` for ~$0.05/month
at lower output quality. Prompt caching is enabled on the static context; cache hits
reduce cost on repeated runs within the 5-minute TTL (relevant mainly during testing).

## Status

Repo milestone v0.5.0. Framework v1.0.0 (as of 2026-05-26 — agents may now
write, review, and score predictions under the schema and §7 boundaries).
Five predictions open, all 7 pattern files written, weekly signal fetcher
and digest drafter operational. See `TODO.md` for remaining milestones.

## Author's note

The first 5 predictions were written by hand to test whether the practice
itself is worth automating. It is. Weekly digests are agent-drafted,
predictions are now agent-drafted from those digests, and retrospective
scoring may be done by agent or by author. The discipline is preserved by the
schema and by immutability after commit, not by which keyboard the words came
from. Tooling is not a substitute for intention, but intention without
tooling doesn't scale.
