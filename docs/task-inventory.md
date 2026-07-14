# Task Inventory — v0.1

Source: the BDOwner's AI-generated inventory 2026-04-22, refined 2026-04-22.

## Rep-risk zones

- **Autonomous** — agent executes without pre-send review.
- **Draft→Approve** — agent produces; human reviews and sends / publishes.
- **Agent supports** — human is primary; agent accelerates.
- **Human only** — not a candidate for automation.

## Inventory

| # | Activity | Cadence | Rep risk (1–5) | Zone | Notes |
|---|---|---|---|---|---|
| 1 | ICP / prospect research | weekly | 2 | Autonomous |  |
| 2 | Competitor / market monitoring | weekly | 1 | Autonomous |  |
| 3 | CRM update / opportunity hygiene | daily | 2 | Autonomous | Assumes agent write access |
| 4 | Discovery call debrief / notes capture | per-opp | 3 | Autonomous | Internal only; externally-facing summary is Draft→Approve |
| 5 | Post-deal retrospective | per-deal | 1 | Autonomous |  |
| 6 | LinkedIn outreach — first-touch | weekly | 4 | Draft→Approve |  |
| 7 | Follow-up sequences (cold) | weekly | 3 | Draft→Approve |  |
| 8 | Follow-up after proposal sent | per-deal | 4 | Draft→Approve |  |
| 9 | Contract / SoW chase | per-deal | 3 | Draft→Approve |  |
| 10 | Workshop participant outreach + follow-up | ad hoc | 4 | Draft→Approve |  |
| 11 | Referral / intro requests | ad hoc | 4 | Draft→Approve |  |
| 12 | Content / thought leadership (LinkedIn posts) | weekly | 3 | Draft→Approve |  |
| 13a | Proposal — structure, boilerplate, first pass | per-deal | 3 | Draft→Approve | Split from #13 |
| 13b | Proposal — commercial framing, pricing, scope | per-deal | 5 | Agent supports | Split from #13; too load-bearing for autonomous drafting |
| 14 | Discovery call prep (dossier, agenda, SPICED questions) | per-opp | 3 | Draft→Approve | Moved from Agent supports — it's a deliverable, not live support |
| 15 | Demo / case study prep | per-opp | 5 | Agent supports |  |
| 16 | Pipeline review | weekly | 2 | Agent supports |  |
| 17 | Inbound lead qualification | ad hoc | 4 | Agent supports |  |
| 18 | Workshop / group session prep | ad hoc | 5 | Agent supports |  |
| 19 | Internal alignment (mgmt, delivery) | weekly | 3 | Human only |  |
| 20a | Account expansion — opening message | per-opp | 3 | Draft→Approve | Split from #20 |
| 20b | Account expansion — relationship management | weekly | 2 | Human only | Split from #20 |
| 21 | Internal comms re: open deals | daily | 1 | Human only |  |
| 22 | Meeting scheduling / calendar coordination | ad hoc | 2 | Autonomous | **Added** — big time sink |
| 23 | Inbound reply triage | ad hoc | 4 | Draft→Approve | **Added** |
| 24 | LinkedIn social engagement (Deep Sales "give") | daily | 3 | Draft→Approve | **Added** |
| 25 | Event / conference follow-up | ad hoc | 4 | Draft→Approve | **Added** — drop if no events |
| 26 | Win/loss analysis per deal | per-deal | 2 | Autonomous | **Added** — feeds retrospective + ICP refinement |

## Split summary

- Autonomous: 8
- Draft→Approve: 12
- Agent supports: 5
- Human only: 3

## Workflows selected for v0.1 specs

1. Account research (Autonomous, Researcher).
2. Outreach drafting (Draft→Approve, Drafter).
3. Discovery call prep (Draft→Approve, Researcher + Drafter).

These sit at the front of the funnel and each feeds the next — Researcher output seeds Drafter, Drafter output seeds prep. Clean upstream-downstream dependency.
