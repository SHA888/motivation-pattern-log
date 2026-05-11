# TODO

Atomic, ordered. Each leaf task is independently completable.
Milestones map to SemVer.

---

## Milestone v0.1.0 — Scaffold (this commit)

- [x] **Define practice charter**
  - [x] Write README.md with cadence, commitment, license summary
  - [x] Write ARCHITECTURE.md with framework, patterns, tests, schema
- [x] **Decide licenses before any code**
  - [x] Code: MIT OR Apache-2.0
  - [x] Content: CC BY 4.0
  - [x] Add LICENSE-MIT, LICENSE-APACHE, LICENSE-CONTENT files
- [x] **Lock prediction schema**
  - [x] Schema documented in ARCHITECTURE.md §4
  - [x] Schema versioning policy in §8
- [x] **Lock cadence**
  - [x] Weekly digest (Mon)
  - [x] Monthly prediction + due-list (1st)
  - [x] Quarterly retrospective (Apr/Jul/Oct/Jan 1)

---

## Milestone v0.2.0 — Manual practice viability gate

**Block on automation until this milestone passes.**

- [ ] **Hand-write 5 predictions over 5 weeks**
  - [x] Week 1: prediction-001
  - [x] Week 2: prediction-002
  - [x] Week 3: prediction-003
  - [x] Week 4: prediction-004
  - [ ] Week 5: prediction-005
- [ ] **Honesty gate**
  - [ ] After week 5, decide: does the practice feel valuable enough to automate?
  - [ ] If no: archive repo, document why in `RETROSPECTIVE-PRE-V1.md`
  - [ ] If yes: proceed to v0.3.0

---

## Milestone v0.3.0 — Pattern files

- [ ] **One file per seed pattern in `patterns/`**
  - [ ] patterns/01-status-in-transgressive-subculture.md
  - [ ] patterns/02-grievance-and-humiliation-reversal.md
  - [ ] patterns/03-curiosity-past-the-fence.md
  - [ ] patterns/04-boredom-with-asymmetric-leverage.md
  - [ ] patterns/05-craft-and-peer-recognition.md
  - [ ] patterns/06-ideology-faith-nation.md
  - [ ] patterns/07-coercion-and-desperation.md
- [ ] **Each pattern documents**
  - [ ] Operational definition (1 paragraph)
  - [ ] Three historical instantiations across different eras
  - [ ] Leading indicators (bulleted, observable)
  - [ ] Known failure modes
  - [ ] Cultural variants (note SEA/Indonesian texture where applicable)

---

## Milestone v0.4.0 — Signal ingestion (serverless)

- [ ] **Curated signal source list**
  - [ ] Draft `signals/SOURCES.md` with 8 sources max
  - [ ] Each source: rationale, format (RSS/Atom/scrape), update cadence
- [ ] **Python signal fetcher (`scripts/fetch_signals.py`)**
  - [ ] uv-managed, pyproject.toml with feedparser, httpx
  - [ ] Outputs deduplicated JSON to stdout
  - [ ] Idempotent: dedup against last week's signals via git history
- [ ] **Test locally before workflow**
  - [ ] `uv run scripts/fetch_signals.py` produces sane output
  - [ ] Manually inspect for noise

---

## Milestone v0.5.0 — Agent-drafted weekly digest

- [ ] **Digest drafter (`scripts/draft_digest.py`)**
  - [ ] Loads ARCHITECTURE.md and patterns/\*.md as context
  - [ ] Loads week's signals from fetch_signals.py
  - [ ] Calls Claude API with system prompt encoding motivation-pattern vocabulary
  - [ ] Produces markdown digest: signals clustered by candidate pattern activation
  - [ ] Hard guard: agent must not write predictions, only cluster and surface
- [ ] **Output format locked in `signals/TEMPLATE.md`**
- [ ] **Cost ceiling**
  - [ ] One Claude call per week, max
  - [ ] Document expected monthly token cost in README

---

## Milestone v0.6.0 — GitHub Actions wiring

- [ ] **Weekly workflow (`.github/workflows/weekly-digest.yml`)**
  - [ ] Trigger: Mon 06:00 UTC + workflow_dispatch
  - [ ] Steps: checkout, setup-python with uv, fetch signals, draft digest, open PR
  - [ ] PR title: "Signal digest YYYY-Www"
  - [ ] PR body: summary stats, patterns flagged
- [ ] **Monthly workflow (`.github/workflows/monthly-due.yml`)**
  - [ ] Trigger: 1st of month 06:00 UTC + workflow_dispatch
  - [ ] Steps: scan predictions/, find any with predicted_window ending this month
  - [ ] Open issue: "Predictions due for retrospective scoring — YYYY-MM"
  - [ ] Issue body: checklist with links to each due prediction
- [ ] **CI workflow (`.github/workflows/ci.yml`)**
  - [ ] Lint Python with ruff
  - [ ] Validate prediction frontmatter against schema
  - [ ] Validate one pattern file per active pattern in framework
- [ ] **Secrets**
  - [ ] ANTHROPIC_API_KEY as repo secret
  - [ ] No other secrets — all sources are public

---

## Milestone v0.7.0 — First automated cycle

- [ ] **Two consecutive weeks of clean automated digests**
  - [ ] No malformed PRs
  - [ ] No false-positive pattern activations from agent
  - [ ] Manual review time per PR < 10 minutes
- [ ] **One automated monthly due-list**
- [ ] **Document any v0.5/v0.6 issues in `retrospectives/2026-Qn.md`**

---

## Milestone v1.0.0 — Calibration baseline

**Reached only after 6 months of practice.**

- [ ] **Minimum 6 predictions reaching final status (confirmed/failed/ambiguous)**
- [ ] **First Brier-style calibration analysis**
- [ ] **First framework revision based on observed pattern performance**
- [ ] **Public charter for next 12 months**
- [ ] **Honest decision: continue, refactor, or sunset**

---

## Anti-goals (tasks explicitly not on this list)

- Web UI / dashboard / search interface
- Database (SQLite, Postgres, DuckDB) — git is the database
- Newsletter, RSS feed for predictions, social media automation
- Subscriber list, email collection
- Any agent capability to write or score predictions
- Any private signal source
- Any feature whose only justification is "it would be cool"

If a task feels like it belongs here but is not on the list, it goes in
`docs/maybe-someday.md`, not in TODO.
