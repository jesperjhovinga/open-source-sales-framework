# Roadmap — toward v1.0

Source: architecture review 2026-07-14 (six candidates, verified findings).
Order chosen for adoption impact: **C1+C3 → C2 → C5 → C4 → C6.**

## C1+C3 — Make the seam real  ✅ shipped
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
      (bd-email and event-invite are since retired — see C4.)
- [x] Secondary residue (found in the extraction audit, out of that scope):
      account-research dossier template (inline ICP table, Prop A/B pitch,
      offer-format names) → `context.icp`/`context.positioning`, done;
      bd-user-rules hardcoded subject convention → `context.tone`, done
      (now "any subject-line convention defined in `context.tone`", no
      hardcoded shape); prospect-sourcing.spec.md "Netherlands filter" step
      → renamed "Geography filter", resolved from `context.icp()`
      (the deeper spec↔skill reconciliation is still C2's job); reviewed
      `src/bdcore/engagers.py`'s multilingual headline separators
      (" at ", " bij ", …) — judged input-parsing heuristics, not ICP policy:
      they recognize how *any* LinkedIn headline (in whatever language the
      commenter wrote it) delimits title from company, which is independent
      of the org's own `context.tone` language default. Left as-is; no code
      change (out of scope for this pass — only `seam.py`'s `BASELINE`
      changed in `src/bdcore/`). Seam baseline driven from 43 to 0 across
      `core/`, `specs/`, `skills/`, including the callnote-template.md worked
      example, which was rewritten in place with generic bracket placeholders
      rather than moved to `contexts/example-corp/`.
- [ ] **Known limitation, not yet fixed**: `bd check seam` is a keyword scan for
      denylisted org proper nouns (`RULES` in `src/bdcore/seam.py`), now run
      over `core/`, `specs/`, `skills/`, and `src/bdcore/` itself. It cannot and
      does not detect *structural* residue — prose that encodes one org's sales
      motion (an ICP, a buyer shape, a channel mix) without using a denylisted
      word. A live example: `skills/account-research/SKILL.md:90-96` hardcodes
      an ICP table (`Specialist firm`, `15–150 people`, `Founder/CEO buyer`,
      `Commercial revenue`) describing one specific consultancy, contradicting
      the demo org's own `contexts/example-corp/icp.md` (50–500 technicians,
      VP Operations) — `RULES` matches none of those strings, so the check
      reports clean. `specs/prospect-sourcing.spec.md:47` has the same shape
      (`Founder/MD/CEO is likely buyer` stated as prose next to the
      `context.icp()` call meant to fetch it). Fixing those ICPs is a separate
      change; this bullet only records that the checker cannot see them.

## C2 — One source of truth per workflow
- [ ] Reconcile prospect-sourcing spec↔skill (dedup key, enrichment call, ICP
      criteria, output schema — skill is battle-tested; update spec to match,
      keep spec as interface + acceptance criteria).
- [ ] Reconcile account-research spec↔skill (inputs, proposition naming).
- [ ] Decide fate of orphaned specs (outreach-drafting → C4; discovery-call-prep
      → needs core/methodology first, see C6).

## C5 — Quarantine the generic island
- [ ] Move marketing-psychology, revops, sales-enablement to `skills/library/`
      (optional, no framework integration) or cut. (email-sequence and
      cold-email are already retired — see C4.)
- [ ] Merge grill-me into grill-with-docs as no-docs mode.
- [ ] Fix grill-with-docs doc conventions (CONTEXT.md/adr → glossary.md/decisions.md).

## C4 — One deep outreach skill  ✅ shipped
- [x] Design single `outreach-drafting` skill implementing outreach-drafting.spec
      with purpose as an input (cold / warm / re-engage / event). Contract-native
      from birth, logs its own approval outcome. Retired the four colliding
      trigger surfaces (bd-email, cold-email, email-sequence, event-invite) —
      content stays in git history.
- [x] It is instrumented: every approval decision lands in the ledger, so
      Decision 1's graduation rule has data to read.

## C6 — Packaging & truth
- [x] `.claude-plugin/plugin.json` (Decision 8). Turned out `plugin.json` alone
      doesn't make the repo installable from GitHub — `.claude-plugin/marketplace.json`
      is also required (one entry, `source: "./"`). Both now ship; see Decision 8's
      v0.2 amendment. `claude plugin validate . --strict` passes.
- [ ] `tests/<spec>.cases.md` per implemented spec (Decision 4).
- [ ] `core/methodology/` SPICED + Bowtie summaries (unblocks discovery-call-prep).
- [ ] Decide `core/archetypes/`: build it, or accept that the glossary's archetype
      list is the whole story and drop the path from the convention for good.
      (Removed from path-conventions in the tooling PR — it never existed.)
- [ ] One frontmatter version scheme; canonical proposition IDs (`example_prop_a/b`).
- [ ] Fresh `STATE.md`; CONTRIBUTING.md; fix all doc claims to match reality.
