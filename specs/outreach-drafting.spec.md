# Spec: Outreach Drafting

**ID**: `outreach-drafting`
**Version**: `v0.1`
**Rep-risk zone**: Draft→Approve
**Primary archetype**: Drafter (+ Reviewer)
**Status**: draft

## Intent

Eliminate the blank-page problem for LinkedIn first-touches and cold follow-ups. Produce drafts that match the BDOwner's tone, reference the right Org Context positioning, and are specific enough to an Account that edit-and-send works. This is the largest recurring weekly time drain on the inventory.

## Trigger

- Manual: BDOwner requests outreach for a named Account + Contact + purpose.
- Event-based: `AccountIdentified` + qualifying Contact → propose a first-touch.

## Inputs

### From BD Core
- `Account`, `Contact` (required).
- `AccountDossier` (strongly preferred). If absent, Drafter calls `account-research` first or degrades to a weaker output, flagged as such.

### From Org Context
- `context.positioning(proposition_id)` — proposition to lead with.
- `context.tone("linkedin_dm")` or `context.tone("email_cold")`.
- `context.content("post_example")` — recent BDOwner posts as style reference.

### From external systems
- LinkedIn (Contact profile + recent activity, for personalization).

## Process

Drafter takes Account + Contact + purpose + dossier, selects the most relevant angle (from positioning + dossier signals), and drafts:
- First-touch message.
- Follow-up 1 (after X days without reply).
- Follow-up 2 (after Y days without reply).

Each draft is specific — references a signal from the dossier or a recent Contact activity, not a generic hook.

Reviewer archetype checks each message: tone match, no fabricated claims, no banned words / fillers, SPICED-aware where relevant. Failures surface as annotations on the draft rather than silent rewrites.

## Outputs

### Artifacts produced
- `OutreachSequence` — markdown with 1 first-touch + 2 follow-ups, channel-tagged.

### Events emitted
- `OutreachDrafted`.
- On BDOwner approval: `OutreachSent` (emitted by the sending action, not the draft itself).

### Writes to external systems
- None from the draft step. Sending happens separately after approval.

## Acceptance criteria

- Every message references at least one Account-specific or Contact-specific signal (not just "I saw you're in X industry").
- Tone matches `context.tone` — no banned words, sentence-length patterns consistent with example posts.
- No fabricated claims (no invented mutual connections, no made-up numbers).
- Drafts produced in under 3 minutes.
- Edit rate tracked — goal <25% of words changed on approve.

## Human-in-the-loop gate

BDOwner reviews the sequence. Three actions: approve (sends first-touch, schedules follow-ups), edit + approve, reject. Reject is optionally captured as feedback for Reviewer archetype.

## Dependencies

- Consumes: `AccountDossier`, `context.positioning`, `context.tone`, `context.content`.
- Produces input for: follow-up logic, CRM activity logging.

## Open questions

- LinkedIn send mechanism — hand-send vs. semi-automated connector. Separate decision.
- Multi-contact sequencing within one Account (multithreading) in v0.1, or single-threaded?
- Feedback capture mechanism for Reviewer improvement — inline comment, thumbs, diff?
- Where does the BDOwner review the draft — in-chat, in a dashboard, in email?
