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
  reports, platform launches, geopolitical shifts). Agent-drafted, human-merged.
- `predictions/` — one file per prediction. Each carries a date, a pattern, a
  substrate, a leading indicator, a predicted window, a falsifier, and a
  status.
- `retrospectives/` — quarterly reviews. What predictions hit, what missed,
  what the framework needs to revise.

## Cadence

- **Weekly** (Monday): signal digest drafted by agent, opened as PR for review.
- **Monthly** (1st): one new prediction written by hand. Predictions reaching
  their evaluation window opened as issues for retrospective scoring.
- **Quarterly** (Apr/Jul/Oct/Jan 1): framework revision. Patterns that fail
  twice get rewritten or retired.

## Commitment

- 12-month minimum run. Re-evaluate at month 12.
- All predictions versioned in git. Edits to past predictions disallowed —
  only addenda permitted (`### Addendum YYYY-MM-DD`).
- Retrospective scoring is human-only. No agent grades the practice's track
  record.

## License

- Code (`scripts/`, `.github/`): `MIT OR Apache-2.0`. See `LICENSE-MIT` and
  `LICENSE-APACHE`.
- Predictions, patterns, signals, retrospectives, and all prose: `CC BY 4.0`.
  See `LICENSE-CONTENT`.

## Status

Pre-v0. Scaffold only. No predictions written yet.

## Author's note

The first 5 predictions will be written by hand, with no automation, to test
whether the practice itself is worth automating. If the manual version feels
empty after 5 weeks, this repo gets archived. Tooling is not a substitute for intention.
