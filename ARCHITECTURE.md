# ARCHITECTURE

This document defines the framework. It is the slowest-moving part of the
repo. Changes require a quarterly retrospective entry justifying the change.

## 1. Core claim

Attack *techniques* change on quarterly timescales. Attack *motivations* change
on decade timescales. Reading motivation gives longer prediction horizons than
reading techniques, at the cost of lower specificity.

Predictions describe **classes** of attacks on **substrates** within **windows**.
Not specific incidents. Not specific actors.

## 2. Motivation patterns (the vocabulary)

Each pattern below is a working hypothesis. Patterns are added, revised, or
retired in quarterly retrospectives. Each pattern lives in its own file under
`patterns/` once active.

Initial seed set (v0):

1. **Status-in-transgressive-subculture** — actors rewarded by peer
   recognition for breaking new systems first. Substrate-independent across
   phreaking, web defacement, zero-day drops, jailbreak culture.
2. **Grievance-and-humiliation-reversal** — actors reclaiming agency after
   perceived systemic wrong. Insider threats, hacktivism, doxing.
3. **Curiosity-past-the-fence** — non-malicious exploration whose writeups
   become recipes downstream. The original Levy hacker ethic.
4. **Boredom-with-asymmetric-leverage** — low motivation × high automation
   multiplier = volume attacks. Script kiddies, spam, LLM-amplified noise.
5. **Craft-and-peer-recognition** — professional identity through mastery.
   Career pentesters, bug bounty hunters, state-aligned operators.
6. **Ideology-faith-nation** — loyalty to in-group defining out-group as
   legitimate target. Espionage, terrorism, state-actor target selection.
7. **Coercion-and-desperation** — survival pressure absent legitimate outlet.
   Insider blackmail, money mules, sanctioned-state IT labor schemes.

Each pattern in `patterns/` documents:
- Operational definition
- Historical instantiations across at least three eras
- Leading indicators (what to watch for *before* the wave)
- Known failure modes (where the pattern has been wrong)
- Cultural variants (regional textures the pattern takes)

## 3. The four tests

A pattern earns and keeps its place in the vocabulary only if it passes all
four tests. A pattern that fails any test in retrospective gets rewritten or
retired.

1. **Substrate independence.** Demonstrable across at least three
   technology eras. If it works only in one era, it is a technique, not a
   motivation.
2. **Leading-indicator identifiability.** A nameable, observable signal that
   precedes the predicted attack wave. If nothing is observable in advance,
   the pattern has no predictive teeth.
3. **Dated retrodiction.** Apply the framework to a frozen historical moment
   using only information available then. Does it predict the subsequent
   landscape better than chance and better than naive technique-extrapolation?
4. **Disconfirmability.** A specific observation that, if it occurred, would
   falsify the predicted shape. If nothing falsifies it, the pattern is
   astrology.

## 4. Prediction schema

Every file in `predictions/` follows this exact schema. Schema changes require
a major version bump and a retrospective entry.

Filename: `PREDICTION-YYYYMMDD-NNNN.md`, where `YYYYMMDD` is the creation date
and `NNNN` is a zero-padded sequence number monotonically increasing across
the entire repository (not reset per day).

```markdown
# PREDICTION-YYYYMMDD-NNNN

- **Created:** YYYY-MM-DD
- **Pattern:** <pattern name from patterns/>
- **Substrate:** <where the attack will land>
- **Leading indicator observed:** <what was seen, with sources>
- **Predicted window:** <YYYY-Qn through YYYY-Qn>
- **Predicted shape:** <one paragraph, concrete>
- **Falsifier:** <one specific observable that would make this wrong>
- **Confidence:** <low | medium | high> (calibration target, not certainty)
- **Status:** open

## Reasoning
<one to three paragraphs, no marketing language>

## Sources
- <links to signals or external references>

## Addenda
<append-only; never edit prediction body after creation>
```

## 5. Status lifecycle

A prediction's `Status` field moves through:

- `open` — created, evaluation window not yet reached
- `confirmed` — predicted shape materialized within window, falsifier did not occur
- `failed` — falsifier occurred, or window passed without predicted shape
- `ambiguous` — partial match, or evidence insufficient to score
- `withdrawn` — author retracts before window closes; counts as failed for calibration

Once a prediction reaches `confirmed`, `failed`, or `ambiguous`, status is
locked. No re-scoring.

## 6. Retrospective scoring

Quarterly. May be performed by the repository author or by an automated agent
following the procedure below. The schema is the source of truth; whoever
scores must produce a retrospective entry matching it, and each entry records
the scorer (`human` | `agent` | `mixed`).

Framework v0.1.0 forbade agent-assisted scoring on the reasoning that
self-grading "launders accountability through the same class of system the
practice studies." That constraint was relaxed in framework v1.0.0
(2026-05-26). The counter-balance is mechanical rather than procedural: the
falsifier and predicted shape, frozen at creation, remain the operative test
of whether a prediction held — not the scorer's narrative judgement, and not
who is grading it.

Each retrospective records:
- Predictions reaching status this quarter (count by outcome)
- Brier-style calibration: do `high`-confidence predictions hit more than
  `medium`, more than `low`?
- Pattern-level performance: which patterns produced reliable predictions,
  which produced noise
- Framework changes applied this quarter, with reasoning

## 7. Boundaries (what this practice will not do)

- Will not predict specific incidents, dates, or victims.
- Will not attribute attacks to specific actors or groups.
- Will not generate offensive tooling or exploit code.
- Will not accept private threat-intel feeds. All sources public.
- Will not monetize. No subscribers, no paywall, no sponsor logos.

These boundaries exist because crossing any of them changes the incentive
structure in ways that corrupt calibration.

## 8. Versioning

The framework follows SemVer:
- **Patch** (0.0.x): typo fixes, link updates, prose clarification
- **Minor** (0.x.0): pattern added, leading-indicator refined, pattern retired
- **Major** (x.0.0): schema change, test change, boundary change

Current version: `1.0.0` (2026-05-26). §6 boundary change — agents are
permitted to write, review, and score predictions under the same schemas and
§7 boundaries as the author. See `retrospectives/2026-Q2.md` for the change
rationale.

## 9. Open questions the framework has not resolved

Stated honestly so future revisions can return to them:

- How to handle multi-pattern attacks (most real attacks combine motivations).
- Whether to track defender-side motivation patterns symmetrically.
- How to weight regional cultural variants without privileging any region.
- Whether agent-driven attackers constitute a new motivation pattern or a
  multiplier on existing ones.
- What constitutes "better than chance" for the third test in a domain
  without natural base rates.
