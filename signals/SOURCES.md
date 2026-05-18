# Signal Sources

Eight curated feeds for weekly signal ingestion. Hard limit: eight sources maximum.
Each source is justified by the motivation patterns it surfaces most reliably.
The script `scripts/fetch_signals.py` mirrors this list programmatically.

Verify each URL on first run — feed URLs change occasionally. The script
logs a WARN per unreachable source and continues; no source failure is fatal.

---

## 1. Krebs on Security

- **URL:** `https://krebsonsecurity.com/feed/`
- **Format:** RSS 2.0
- **Cadence:** Several times per week
- **Primary patterns:** grievance-and-humiliation-reversal, coercion-and-desperation, ideology-faith-nation
- **Rationale:** Investigative cybercrime reporting with named actors, court documents,
  and motivation attribution. Best single source for distinguishing grievance-motivated
  insiders from financially-motivated ones, and for tracking coercion schemes (DPRK
  workers, money mule networks). Regularly covers state-directed operations with primary
  source citations.

## 2. CISA Cybersecurity Advisories

- **URL:** `https://www.cisa.gov/cybersecurity-advisories/all.xml`
- **Format:** RSS 2.0
- **Cadence:** Several times per week
- **Primary patterns:** ideology-faith-nation, boredom-with-asymmetric-leverage
- **Rationale:** Official US government advisories on active threats. State-actor
  attribution (PRC, DPRK, Russian SVR/GRU, Iranian APTs) is present in many
  advisories, making this the most reliable source for ideology-faith-nation
  activation signals. Also surfaces commodity campaigns (boredom-with-leverage)
  when volume triggers a government response.

## 3. Schneier on Security

- **URL:** `https://www.schneier.com/feed/atom/`
- **Format:** Atom
- **Cadence:** Several times per week
- **Primary patterns:** curiosity-past-the-fence, craft-and-peer-recognition
- **Rationale:** Long-running security analysis blog with consistent focus on
  research findings, novel techniques, and systemic analysis. Good leading-indicator
  source: when Schneier covers a new class of attack, it typically signals that the
  technique has reached peer-reviewed or publication-grade attention — the
  craft-and-peer-recognition and curiosity-past-the-fence patterns in their
  early stages.

## 4. arXiv cs.CR — Cryptography and Security

- **URL:** `https://export.arxiv.org/rss/cs.CR`
- **Format:** RSS 2.0
- **Cadence:** Daily (weekdays)
- **Primary patterns:** curiosity-past-the-fence, craft-and-peer-recognition
- **Rationale:** Direct feed of preprints in computer security. Novel adversarial
  technique papers appear here before conference acceptance. This is where
  curiosity-past-the-fence output lands first (researchers documenting what they
  found) and where craft-and-peer-recognition is most visible (institutional
  affiliations, citation networks). High volume — capped at 50 entries per fetch.

## 5. The Hacker News

- **URL:** `https://feeds.feedburner.com/TheHackersNews`
- **Format:** RSS 2.0 via Feedburner
- **Cadence:** Daily
- **Primary patterns:** status-in-transgressive-subculture, boredom-with-asymmetric-leverage, ideology-faith-nation
- **Rationale:** Broad-coverage security news site that quickly covers breaking
  incidents across all motivation categories. Useful as a breadth signal: if an
  attack class appears here, it has crossed the threshold of general security
  awareness, which is a lagging indicator useful for calibration. Also picks up
  commodity campaign reports (boredom-with-leverage) early.

## 6. SANS Internet Storm Center

- **URL:** `https://isc.sans.edu/rssfeed_full.xml`
- **Format:** RSS 2.0
- **Cadence:** Daily
- **Primary patterns:** boredom-with-asymmetric-leverage, status-in-transgressive-subculture
- **Rationale:** Practitioner-written daily threat analysis with a focus on
  scanning, exploit campaigns, and emerging commodity attack tooling. Good
  leading indicator for the boredom-with-leverage pattern: ISC diary entries
  often identify new commodity tooling before it appears in mainstream security
  media, and document volume increases that signal the skill-floor collapse
  the pattern predicts.

## 7. OpenSSF Blog

- **URL:** `https://openssf.org/feed/`
- **Format:** RSS 2.0
- **Cadence:** Weekly
- **Primary patterns:** boredom-with-asymmetric-leverage
- **Rationale:** Open Source Security Foundation blog covering supply chain security,
  package registry security, SLSA framework adoption, and open source ecosystem threats.
  Most directly relevant source for PREDICTION-20260512-0004. Covers both defensive
  developments (sigstore, SLSA, OpenSSF Scorecard) and incident reports affecting the
  package ecosystem — defensive investment is itself a leading indicator that the
  attack pattern is activating. Replaced Phylum Research Blog (Phylum acquired by
  Veracode 2025; blog inactive).

## 8. Seriously Risky Business

- **URL:** `https://srslyriskybiz.substack.com/feed`
- **Format:** Atom (Substack)
- **Cadence:** Weekly
- **Primary patterns:** ideology-faith-nation, coercion-and-desperation, craft-and-peer-recognition
- **Rationale:** Weekly analysis newsletter by Tom Uren and Patrick Gray, with consistent
  coverage of state-actor operations, geopolitical context for cybercrime, and
  practitioner-community developments. Good for ideology-faith-nation leading
  indicators (diplomatic context, sanctions developments) and coercion-and-desperation
  (DPRK IT worker scheme, sanctioned-state cybercrime labor). Higher signal-to-noise
  than the podcast feed; each issue contains substantive analysis with primary citations.

---

## Source selection criteria

A source earns a slot only if it:
1. Has a stable, machine-fetchable RSS or Atom feed
2. Updates at least monthly (no dead blogs)
3. Covers at least one motivation pattern not already well-served by existing sources
4. Has a public-source-only policy consistent with this repo's boundaries

Sources explicitly excluded:
- Commercial threat intelligence feeds requiring authentication
- Dark-web forums (no stable RSS; violates public-source constraint)
- Social media firehoses (rate limits, ToS complexity)
- Vendor marketing blogs (low signal-to-noise, structural bias toward novelty)
