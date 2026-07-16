# Spec: Discovery Call Prep

**ID**: `discovery-call-prep`
**Version**: `v0.1`
**Rep-risk zone**: Draft→Approve
**Primary archetype**: Researcher + Drafter
**Status**: draft

## Intent

Produce a pre-call briefing the BDOwner reads in the 15 minutes before a discovery call. Goal: walk in with a working hypothesis, a SPICED-aligned agenda, specific questions per stakeholder, and anticipated objections. Replaces ad hoc prep that today ranges from "quick LinkedIn scan" to "nothing."

## Trigger

- Event-based: `MeetingScheduled` with purpose=`discovery` → generate 24h before meeting start.
- Manual: BDOwner requests prep for a named Meeting.

## Inputs

### From BD Core
- `Meeting` (participants, time, purpose).
- `Account`, all `Contact`s on the Meeting.
- `AccountDossier` (required — if absent, run `account-research` first).
- `Opportunity` (if one exists).

### From Org Context
- `context.positioning(proposition_id)` — likely proposition for this call.
- `context.icp()` — for fit verification.
- `context.content("case_study")` — relevant proof points.
- `context.tone("discovery_call")` — conversational tone cues.

### From external systems
- Prior meeting notes on this Account (CallNote entities).
- Prior outreach thread (Messages).

## Process

Researcher pulls dossier + prior context. Drafter produces a DiscoveryPrepDoc with:

1. Call objective (one sentence — what decision we're trying to drive).
2. Participant mini-profiles (role, persona, likely lens).
3. Working hypothesis — the problem we believe they have + our entry angle.
4. SPICED-aligned agenda — Situation, Pain, Impact, Critical event, Decision criteria, exit question.
5. Questions to ask (5–10, each mapped to a SPICED dimension).
6. Likely objections + reframes (from `project_sales_enablement.md` + positioning).
7. Proof points to keep handy (case studies, workshop examples).
8. Explicit unknowns — what we don't know and want to find out.

Reviewer: no fabricated claims, SPICED coverage complete, tone match.

## Outputs

### Artifacts produced
- `DiscoveryPrepDoc` — markdown, stored at `contexts/<org>/prep/<account-slug>-<meeting-date>.md`.

### Events emitted
- `PrepDocProduced`.

### Writes to external systems
- None.

## Acceptance criteria

- Doc fits on one screen (~500–700 words). No padding.
- SPICED coverage: every dimension has at least one planned question.
- Every named objection has a reframe.
- Working hypothesis is specific to the Account — not "they probably want efficiency."
- If data is missing for a section, the section states the gap rather than fabricating.
- BDOwner read-time under 5 minutes.

## Human-in-the-loop gate

BDOwner reads and optionally edits. No "approve" action because nothing is sent — the doc is for internal use. Post-call feedback: did the prep predict the call accurately? Captured into Reviewer calibration.

## Dependencies

- Consumes: `AccountDossier`, prior `CallNote`s, prior `Message`s, `context.positioning`, `context.icp`, `context.content`, `context.tone`.
- Produces input for: future `call-summary` spec (post-call).

## Open questions

- Delivery channel — where does the BDOwner actually read the doc (Drive, Notion, email, chat)?
- Auto-detection of the proposition (per `context.positioning()`) per call, or BDOwner-tagged?
- Calendar connector choice (Google Calendar, Outlook) — confirm before implementation.
- If the Meeting has multiple purposes (e.g., discovery + workshop pitch), which template applies?
