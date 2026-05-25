# Signal digest YYYY-Www

- **Week:** YYYY-Www (Mon YYYY-MM-DD through Sun YYYY-MM-DD)
- **Sources scanned:** <count>
- **Raw signals collected:** <count>
- **Signals after dedup:** <count>

## Candidate pattern activations

For each candidate, the agent provides:
- The pattern name
- The signals that triggered the cluster
- A confidence note (low/med/high) on whether this looks like real activation
  vs. noise
- An explicit "no, this is not yet a prediction" disclaimer

### <pattern-name> — <substrate-hint>

- Signals: <links>
- Why this might be activating: <one paragraph>
- Why this might be noise: <one paragraph>
- Suggested next step: <"watch for N more weeks" | "could justify a prediction now" | "discard">

## Discarded clusters

Brief notes on clusters the agent considered and rejected, for transparency.

## Notes for review

- Anything ambiguous the agent could not classify
- Sources that returned errors or were unreachable
- Suggestions for source list revision

---

*This digest was drafted by an automated agent. As of framework v1.0.0
(2026-05-26), the agent may also draft, review, and score predictions derived
from these signals — see `CLAUDE.md` and `ARCHITECTURE.md` §6. The schema and
the immutability rule bind agents and humans equally.*
