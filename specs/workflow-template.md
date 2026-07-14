# Workflow Spec Template — v0.1

Every workflow spec in this repo follows this shape. Copy this file to `specs/<name>.spec.md` and fill it in.

---

# Spec: [Workflow Name]

**ID**: `[unique-slug]`
**Version**: `v0.1`
**Rep-risk zone**: `Autonomous | Draft→Approve | Agent supports | Human only`
**Primary archetype**: `Researcher | Drafter | Summarizer | Reviewer | Coach`
**Status**: `draft | approved | implemented | verified`

## Intent

One paragraph. What problem does this workflow solve for the BDOwner? What does it replace or accelerate?

## Trigger

When does this run? Manual / scheduled / event-based. If event-based, name the event from the glossary.

## Inputs

### From BD Core
Domain entities the workflow reads (e.g., `Account`, `Opportunity`).

### From Org Context
Every call through the context contract, explicit. Example:
- `context.positioning("example_prop_a")`
- `context.icp()`
- `context.tone("linkedin_dm")`

### From external systems
Connectors required (and what's read from them).

## Process

Narrative, in terms of the ubiquitous language. Not code. Describe the shape — *what* happens, not *how*.

## Outputs

### Artifacts produced
Named outputs (e.g., `AccountDossier` — markdown doc at a path).

### Events emitted
Glossary events (e.g., `AccountIdentified`).

### Writes to external systems
Any CRM / Drive / LinkedIn writes, with scope.

## Acceptance criteria

Testable statements. Each phrased as a scenario the output must pass. Examples:
- Given an Account with no public data, output states "insufficient public information" rather than fabricating.
- Every non-obvious claim cites a source URL or internal doc path.

## Human-in-the-loop gate

If zone is Draft→Approve: where does the human review, and what does approval mean in practice?

## Dependencies

- Other specs consumed or produced (upstream / downstream).
- Context surfaces required.

## Open questions

Explicit gaps. Anything unresolved goes here. A spec with open questions is still shippable — it just means those questions must be answered before implementation.
