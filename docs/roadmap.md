# Roadmap — toward v1.0

Source: architecture review 2026-07-14 (six candidates, verified findings).
Order chosen for adoption impact: **C1+C3 → C2 → C5 → C4 → C6.**

## C1+C3 — Make the seam real  ✅ partially shipped / 🔨 in progress
Shipped: `contexts/_template/` (blank adapter), `contexts/example-corp/` (demo
adapter), `ACTIVE_CONTEXT.md` resolution rule, .gitignore guard.
Remaining:
- [ ] Convert all 22 raw-path references in 11 skills to contract-call form
      (`context.tone(channel)` style) resolved via path-conventions.
- [ ] Extract org residue: Dutch defaults in bd-email/event-invite/cold-call-prep
      → `context.tone` language field; NL disqualifier lists in
      prospect-sourcing skill + `process_engagers.py` → `context.icp` config;
      pitch prose in bd-email/cold-call-prep → `context.positioning`.

## C2 — One source of truth per workflow
- [ ] Reconcile prospect-sourcing spec↔skill (dedup key, enrichment call, ICP
      criteria, output schema — skill is battle-tested; update spec to match,
      keep spec as interface + acceptance criteria).
- [ ] Reconcile account-research spec↔skill (inputs, proposition naming).
- [ ] Decide fate of orphaned specs (outreach-drafting → C4; discovery-call-prep
      → needs core/methodology first, see C6).

## C5 — Quarantine the generic island
- [ ] Move marketing-psychology, revops, sales-enablement, email-sequence,
      cold-email to `skills/library/` (optional, no framework integration) or cut.
- [ ] Merge grill-me into grill-with-docs as no-docs mode.
- [ ] Fix grill-with-docs doc conventions (CONTEXT.md/adr → glossary.md/decisions.md).

## C4 — One deep outreach skill
- [ ] Design single `outreach` skill implementing outreach-drafting.spec with
      warmth/purpose as inputs (cold / warm / re-engage / event). Contract-native
      from birth. Retire the four colliding trigger surfaces.

## C6 — Packaging & truth
- [ ] `.claude-plugin/plugin.json` (Decision 8).
- [ ] `tests/<spec>.cases.md` per implemented spec (Decision 4).
- [ ] `core/methodology/` SPICED + Bowtie summaries (unblocks discovery-call-prep).
- [ ] One frontmatter version scheme; canonical proposition IDs (`example_prop_a/b`).
- [ ] Fresh `STATE.md`; CONTRIBUTING.md; fix all doc claims to match reality.
