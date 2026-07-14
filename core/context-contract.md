# Context Contract — v0.1

BD Core consumes org-specific data only through this contract. No direct file paths, no hardcoded values, no leakage.

## Surfaces

### `context.positioning(proposition_id)`
Positioning narrative for a named proposition.
- **Input**: `proposition_id` (string). At ExampleOrg: `"example_prop_a"` or `"example_prop_b"`.
- **Returns**: narrative arc, key messages, objection reframes.

### `context.icp(segment?)`
ICP definition.
- **Input**: optional `segment` to scope.
- **Returns**: filters (industry, size, tech stack), persona definitions, qualification criteria.

### `context.tone(channel)`
Tone-of-voice rules for a channel.
- **Input**: `channel` — `linkedin_dm`, `linkedin_post`, `email_cold`, `email_followup`, `proposal`, `discovery_call`.
- **Returns**: voice patterns, word lists, pre-writing checklist.

### `context.content(type, topic?)`
Matching ContentAsset.
- **Input**: `type` (`case_study`, `one_pager`, `deck`, `post_example`). Optional `topic`.
- **Returns**: asset reference + relevant excerpts.

### `context.competitors(proposition_id?)`
Competitor list + battlecards.
- **Returns**: competitors with positioning, weaknesses, our angle.

### `context.connector(name)`
Configured connector handle.
- **Input**: `name` — `crm`, `email`, `drive`, `sharepoint`, `linkedin`, `calendar`.
- **Returns**: scoped connector the agent can use.

### `context.pricing(proposition_id)`
Commercial terms.
- **Returns**: price ranges, engagement shapes, boilerplate terms.

## Rules

1. BD Core never imports from `contexts/<org>/` directly. Always via the contract.
2. New surfaces are added to the contract, not bypassed.
3. A missing surface implementation in a given Org Context is a blocking error for any spec that calls it — fail loud, don't silently degrade.
4. The contract is versioned. Breaking changes require bumping the version and updating every Org Context instance.

## v0.1 implementation

Contract defined. First concrete implementation: `contexts/<org>/` provides these surfaces as markdown files read by the agent. A lightweight Python or Node wrapper may formalize the surface calls later; for now, the agent reads the files directly using paths documented in `contexts/<org>/README.md`.

## Rule 5 — Active org (v0.2)

The active Org Context is named by `ACTIVE_CONTEXT.md` at repo root. Surfaces
resolve only against the active org. A surface file containing
`STATUS: UNFILLED` is treated as missing (Rule 3 applies: fail loud).
