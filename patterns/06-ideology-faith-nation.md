# Pattern: Ideology, Faith, Nation

**Status:** active
**Added:** 2026-05-18
**Last revised:** 2026-05-18
**Framework version:** v0.3.0

## Operational definition

Actors operating under explicit or implicit authorization from a state, religious movement, or national in-group, targeting entities defined as the out-group by that collective. The defining feature is institutional tasking: the actor answers to a collective whose goals transcend individual incentive. The operation is authorized and resourced above the level of the individual actor — it is a collective act even when executed by a single person. Financial gain may be present as a secondary incentive or as operational cover, but it is subordinate to the collective mission. The target is selected by strategic logic (deny a rival a capability, punish an apostate, degrade an adversary's infrastructure), not by personal grievance or by where the highest-value data happens to sit.

## Historical instantiations

1. **Cold War intelligence collection (1940s–1990s):** State-directed human assets exfiltrated nuclear, military, and technological secrets across decades. Klaus Fuchs passed atomic bomb designs to Soviet handlers from ideological conviction; Aldrich Ames sold CIA assets from a combination of financial need and ideological disillusionment; the Rosenbergs acted from explicit communist commitment. In each case, the act was authorized by an institutional collective (a state intelligence service) and targeted strategic assets selected by that collective, not by individual opportunity.

2. **State-directed semiconductor IP theft (2000s–present):** People's Republic of China-directed collection operations against ASML, Applied Materials, and multiple TSMC-adjacent companies followed a strategic pattern: the target was not the easiest or most lucrative IP but the IP most relevant to closing a specific technological gap. DOJ prosecutions document state-adjacent tasking through front companies and talent-acquisition programs. The actors were not opportunistic financial criminals; they were executing a state industrial strategy.

3. **Jihadist and religiously motivated hacktivism (2010s–present):** Groups targeting media organizations, financial institutions, and government infrastructure of defined ideological out-groups (Israeli tech companies, Charlie Hebdo-adjacent targets, anti-Shia targets in Gulf context) act under collective religious authorization. The target selection is symbolic and strategic — chosen for ideological significance — not for financial return. Individual actors may have no personal grievance against the specific target.

## Leading indicators

- Public government statements framing a technology class, sector, or capability as a strategic national priority requiring acquisition or denial
- Export-control expansion to cover new artifact types — the regulatory signal that a government has formally identified a substrate as national security infrastructure
- Intelligence community advisories naming collection threats against specific sectors (FBI, CISA, allied equivalents)
- Deterioration of bilateral agreements governing technology access, creating a gap between a rival's strategic need and its legal access
- Diplomatic or political events that redefine the in-group/out-group boundary — elections, sanctions escalations, military incidents — which can reactivate the pattern against previously low-priority targets

## Known failure modes

- **Misidentifying state-linked opportunism as state direction:** Actors who are employees of state-adjacent companies and opportunistically exfiltrate valuable IP are not necessarily executing institutionally tasked operations. The pattern requires evidence of strategic target selection and institutional authorization above the individual, not merely state employment. Financially-motivated insiders at state-owned enterprises are a separate category.
- **Misidentifying patriotic hacktivism as institutionally tasked:** Nationalist hacker crews operating on their own initiative — without state tasking, resourcing, or coordination — may share ideological motivation with state actors but do not carry the institutional signature. Predicting state-level operational capability based on volunteer crew activity produces false positives.
- **Overfitting to one ideology or one state:** The pattern is substrate-independent across states, religious movements, and nationalist movements. Applying it only to PRC actors or only to Islamist groups misses instantiations from other collectives and introduces analytical blind spots.

## Cultural variants

- **Indonesia and SEA nationalist hacktivism:** Indonesian hacker crews (Garuda, anonim_ID variants) conduct defacement and DDoS campaigns against Malaysian, Australian, and Israeli government targets during political tensions. The ideological motivation is real and the collective authorization is present (community consensus, shared target lists), but institutional state tasking is typically absent — this is closer to decentralized nationalist activism than state-directed collection. The pattern applies but at a lower institutional intensity.
- **Iran:** Iranian state-directed operations show a distinctive pattern of mixing ideological targeting (Israeli infrastructure, dissident networks) with financial cybercrime (ransomware for revenue generation under sanctions). The ideology-faith-nation motivation is primary in target selection; coercion-and-desperation (sanctions pressure) shapes the operational model. Both patterns may be simultaneously active.
- **Russia:** The line between institutionally tasked operations (GRU, FSB-directed) and state-tolerated but independent criminal groups is deliberately blurred. Attribution of the ideology-faith-nation pattern should require positive evidence of institutional direction, not merely consistency with state interests.

## Disconfirmability test

If incidents in a domain are consistently attributed to financially-motivated actors without public evidence of state direction, or if state-directed operations are systematically limited to other substrates and the predicted substrate shows only opportunistic activity, then the ideology-faith-nation pattern has not activated for that domain. The observable prediction requires the institutional signature: strategic target selection, evidence of resourcing or tasking above the individual actor, and a public record (indictment, attribution statement, testimony) that establishes the collective authorization. Activity that is merely consistent with state interests but lacks those signatures does not confirm the pattern.

## Predictions deriving from this pattern

- [PREDICTION-20260518-0005](../predictions/PREDICTION-20260518-0005.md) — State-directed collection operations targeting AI model weights and training pipelines at US frontier labs
