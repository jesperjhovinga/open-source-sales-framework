# Path Conventions — v0.1

How the agent finds files in BD Core and Org Context. v0.1 uses direct file reads. A wrapper layer may formalize this later — see `docs/decisions.md` Decision 9.

## BD Core paths

- `core/language/glossary.md` — ubiquitous language.
- `core/context-contract.md` — Core ↔ Context API contract.
- `core/path-conventions.md` — this file.
Agent archetypes (Researcher, Drafter, Summarizer, Reviewer, Coach) live in
`core/language/glossary.md`.

This list documents paths that exist. Paths the framework intends to add are
tracked in `docs/roadmap.md` (C6) until they do — a convention is not a plan.

## Org Context paths

For each Org Context at `contexts/<org-slug>/`:

| Path | Maps to contract surface |
|---|---|
| `contexts/<org>/positioning.md` | `context.positioning` |
| `contexts/<org>/icp.md` | `context.icp` |
| `contexts/<org>/value-props.md` | (referenced by positioning) |
| `contexts/<org>/competitors.md` | `context.competitors` |
| `contexts/<org>/content-library.md` | `context.content` |
| `contexts/<org>/tone-of-voice.md` | `context.tone` |
| `contexts/<org>/pricing.md` | `context.pricing` |
| `contexts/<org>/connectors.md` | `context.connector` |

## Generated artifact paths

- `contexts/<org>/dossiers/<account-slug>.md` — AccountDossier.
- `contexts/<org>/prep/<account-slug>-<meeting-date>.md` — DiscoveryPrepDoc.
- `contexts/<org>/outreach/<account-slug>-<contact-slug>-<seq-id>.md` — OutreachSequence draft.
- `contexts/<org>/outreach/originals/<account-slug>-<contact-slug>-<seq-id>.md` — frozen
  copy of that draft as first generated, written once and never edited again. It is what
  `bd log-approval --before` names; `bd review`'s pending queue does not look inside this
  subdirectory, so it never appears as a draft awaiting review.
- `contexts/<org>/call-notes/<account-slug>-<meeting-date>.md` — CallNote.
- `contexts/<org>/retrospectives/<deal-slug>.md` — Post-deal retrospective.
- `contexts/<org>/ledger/approvals.jsonl` — the approval ledger. Append-only; one
  JSON record per Draft→Approve decision. Consumed by `bd graduation-status`.

## Spec & skill paths

- `specs/<spec-id>.spec.md` — workflow specs.
- `skills/<spec-id>/SKILL.md` — Claude skill implementing a spec.
- `tests/cases/<spec-id>.cases.md` — eval harness cases (Decision 4; not yet built, roadmap C6).
- `tests/test_*.py` — the Python suite for `src/bdcore/`.

## Resolver behavior

When the agent asks for a contract surface, the resolver:
1. Looks up the path in this convention.
2. Reads the markdown file.
3. Returns the file content (and metadata: timestamp, version if present).
4. If file is missing, fails loud — see `docs/decisions.md` cross-cutting principle 5.

## Active org resolution (v0.2)

`ACTIVE_CONTEXT.md` at the repo root contains exactly one org slug (e.g.
`example-corp`). All `contexts/<org>/` references resolve against that slug.
Missing file, empty file, or slug `_template` = blocking error — fail loud.
One clone can hold multiple org contexts; switching orgs is editing one line.
