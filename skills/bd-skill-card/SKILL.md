---
name: bd-skill-card
version: "0.1.0"
description: Generate or refresh a governance "skill card" for an existing skill in the BD Automation Framework — a one-page record of what the skill does, its rep-risk zone, the context surfaces and connectors it touches, its inputs/outputs, guardrails, limitations, and provenance. Use when the user says "make a skill card for [skill]", "document [skill] for governance", "audit our skills", or before a rewrite/refactor when you need a clear inventory of what each skill is and may do. Do NOT use to explain or build the skill itself — only to produce its governance card. Adapted from NVIDIA's skill-card-generator for the BD framework.
origin: skill-card-generator (NVIDIA/skills), adapted for BD
compatibility: Reads a skill directory; optional Python 3 for the validator script.
---

# BD Skill Card

Produce a grounded, one-page governance card for an existing BD skill so its behaviour, permissions, and risks are auditable — useful on its own, and essential before a framework rewrite where you need to know exactly what each skill is and is allowed to do. The card is a **draft for the BDOwner to review**, not an approval.

Use when: a skill needs a governance card, a changed skill needs its card refreshed, or you're taking inventory ahead of a refactor.

Do NOT use to: explain, compare, or build skills; generate cards for non-skill assets; or sign/approve anything. The card never replaces the BDOwner's review.

## How a card stays truthful

The whole value is that the card reflects what the skill *actually* does, not what it claims. So **ground every field in the skill's own files** — read its `SKILL.md`, references, and any scripts. Where a field genuinely can't be sourced, write `HUMAN-REQUIRED` rather than guessing. A card full of confident fiction is worse than one honest gap.

This framework already names most of what a card needs — reuse that vocabulary instead of inventing terms:

- **Rep-risk zone** — Autonomous / Draft→Approve / Agent-supports / Human-only (`core/language/glossary.md`).
- **Context surfaces** consumed — `context.tone`, `context.icp`, `context.positioning`, etc. (`core/context-contract.md`).
- **Connectors** touched — crm, email, linkedin, calendar (`context.connector`).
- **Artifacts** produced and their paths (`core/path-conventions.md`).
- **Ubiquitous-language entities** the skill reads or writes (Account, Contact, CallNote, OutreachSequence…).

## Procedure

1. Resolve the target skill directory (from the user; else ask). Read its `SKILL.md` fully, plus any `references/`, `assets/`, and `scripts/`.
2. Fill the card template in `assets/skill-card-template.md`, sourcing each field from those files. Map the skill onto the framework vocabulary above — e.g. if its body says "never send, draft only", its rep-risk zone is Draft→Approve.
3. For anything the files don't support, write `HUMAN-REQUIRED: <what to confirm>` so the BDOwner sees exactly what to check.
4. Save the card next to the skill as `skills/<name>/skill-card.md`.
5. Validate: run `bd validate-card skills/<name>/skill-card.md`. It fails if required sections are missing or any `HUMAN-REQUIRED` / `{{placeholder}}` markers remain — clear them (by sourcing the value or confirming with the BDOwner) before calling the card done.
6. Tell the BDOwner where the card is and list any `HUMAN-REQUIRED` fields he still needs to confirm.

## Card contents (see the template for the exact layout)

Identity (name, version, one-line purpose) · Trigger · Rep-risk zone · Inputs (context surfaces, entities, external sources) · Outputs (artifacts + paths, events, external writes) · Connectors & permissions (what it may read/write/send — and explicitly what it must not) · Guardrails · Limitations · Provenance (origin, version, last reviewed).

## Notes

- Keep cards honest about **permissions**: state plainly what the skill may send or write and, just as importantly, what it must never do without approval (per `bd-user-rules`). The permissions line is the part a reviewer scans first.
- Canned limitation/risk phrasing is a starting point — delete anything that doesn't apply to the specific skill. An inaccurate limitation is noise.
- The validator checks *shape*, not truth. It can't tell you a field is wrong, only that it's filled — the BDOwner's review is what certifies correctness.

## Composes with

- **bd-skill-evolution** — when carding a skill surfaces something stale or wrong, that's a skill-evolution trigger; propose the fix there.
- **bd-user-rules** — the source of truth for the permissions/guardrails section of every card.
