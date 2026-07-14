# Roadmap — toward v1.0

Source: architecture review 2026-07-14 (six candidates, verified findings).
Order chosen for adoption impact: **C1+C3 → C2 → C5 → C4 → C6.**

## C1+C3 — Make the seam real  ✅ partially shipped / 🔨 in progress
Shipped: `contexts/_template/` (blank adapter), `contexts/example-corp/` (demo
adapter), `ACTIVE_CONTEXT.md` resolution rule, .gitignore guard.
Remaining:
- [x] Convert raw-path references in skills to contract-call form
      (`context.tone(channel)` style) resolved via path-conventions.
      (Pre-conversion audit counted 23 raw-path lines across 10 skills, not
      the 22/11 originally claimed. Definitional `contexts/<org>/` mentions
      in improve-framework-architecture stay — they describe the seam itself.)
- [x] Extract org residue: Dutch defaults in bd-email/event-invite/cold-call-prep
      → `context.tone` language field; NL disqualifier lists in
      prospect-sourcing skill + `process_engagers.py` → `context.icp` config
      (`headline_prefilter` JSON block, script fails loud without it);
      pitch prose in bd-email/cold-call-prep → `context.positioning`.
      Removed Dutch content lives in git history (pre-extraction: 0aafb9f);
      a real org context carries it locally, never in git.
- [ ] Secondary residue (found in the extraction audit, out of that scope):
      account-research dossier template (inline ICP table, Prop A/B pitch,
      offer-format names) → `context.icp`/`context.positioning`;
      bd-user-rules hardcoded subject convention → `context.tone`;
      prospect-sourcing.spec.md "Netherlands filter" step → fold into the
      C2 spec↔skill reconciliation; decide whether `process_engagers.py`'s
      multilingual headline separators (" at ", " bij ", …) are input-parsing
      heuristics (fine) or belong in `headline_prefilter` config.

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
