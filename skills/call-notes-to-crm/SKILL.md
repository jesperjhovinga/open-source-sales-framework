---
name: call-notes-to-crm
description: Turns raw notes from a meeting or call that already happened into a flat, paste-ready CRM CallNote in the BDOwner's BD style. Trigger whenever the user says "summarise my call notes", "samenvatting van het gesprek", "CRM note", "maak er een CRM-notitie van", "log this meeting", "verwerk mijn aantekeningen", or pastes rough notes from a discovery/follow-up meeting and wants them structured. This is the POST-meeting counterpart to cold-call-prep (which preps a call BEFORE it happens) — if the call hasn't happened yet, use cold-call-prep instead. Also trigger after a discovery call when the user wants the account logged before drafting a follow-up.
---

# Call Notes → CRM CallNote

You turn the BDOwner's rough notes from a meeting that already happened into a clean `CallNote` — a structured BD record he can paste straight into the CRM. The reader is the BDOwner (the BDOwner) and, later, anyone on the team who opens the account. Output is plain text, ready to paste, no formatting to strip out.

## The one rule that matters most

**Never claim more than the notes support.** This is the single correction the BDOwner makes most often. Raw notes are fragmentary and you will be tempted to smooth them into confident prose — resist it.

- When you merge two fragments into one sentence, you often invent specificity that neither fragment had. Don't. If note A says "support via India" and note B says "we do second-line for ClientCaseB", do **not** write "second-line for ClientCaseB via India" unless a note actually says that. Keep them as the two separate facts they are.
- Flag every figure you didn't get from the person directly as rough: "~150 employees (third-party, treat as rough)", "est. revenue ~$25M (rough)".
- If something is your inference rather than something said, mark it ("Realistic read:", "Likely:") so the BDOwner can see the seam.
- When the notes genuinely don't cover a section, write the gap ("Opportunity scope: unclear, qualify after next meeting") rather than padding it.

When you're unsure whether a phrasing overstates, surface it to the BDOwner as a question at the end rather than silently committing to it. He would much rather be asked than have to catch a fabrication.

## What to extract before writing

Read the notes once and pull:

1. **Account** — the company, and the Contact(s) in the room.
2. **Where this sits** — was it a first discovery, a follow-up, an event conversation? Warm or cold?
3. **The entry point** — the specific reason there's a conversation at all (a felt pain, a trigger, a mutual connection, a case that resonated).
4. **SPICED signal** — map what you heard onto Situation, Pain, Impact, Critical event, Decision criteria. Don't force empty dimensions; name the ones you have.
5. **The ExampleOrg angle** — where ExampleOrg plausibly helps, in the BDOwner's framing, and explicitly where it does *not* (the honest boundary is part of the credibility — see tone of voice).
6. **Next steps & open questions** — concrete actions, owners, and what's still unknown.

## CallNote structure

Follow this order. Use plain-text section labels (no markdown headers, no bullets — the CRM strips them). See `references/callnote-template.md` for the full annotated template and a worked example.

```
ACCOUNT: [Company] — [context tag, e.g. "GreenTech follow-up"]

Account overview (rough): [1 paragraph. Flag every third-party figure as rough.]

Entry point: [Why there's a conversation. The specific hook.]

Read from the meeting: [Your honest assessment — warmth, fit, where it could go. Mark inferences.]

Opportunity / ExampleOrg angle: [Where ExampleOrg helps and where it deliberately doesn't.]

Next actions: [Numbered, concrete, with owner where known.]

Open questions: [What's still unknown — don't fabricate answers.]
```

Add a `Business model:` or `Competitive landscape:` line only when the notes contain it. Don't create empty sections.

## Context to pull when the project is connected

This skill is portable — it works from pasted notes alone. But when the BDOwner's BD project folder is connected, it gets sharper:

- Read the `context.tone` surface (`contexts/<org>/tone-of-voice.md`) so the "Read" and "ExampleOrg angle" sections sound like him — it's the single source for voice; don't restate its rules here.
- If an `AccountDossier` exists at `contexts/<org>/dossiers/<account>.md`, reconcile your overview against it rather than re-deriving — and note any contradiction.
- Save the finished CallNote to `contexts/<org>/call-notes/<account-slug>-<YYYY-MM-DD>.md` so it's versioned and so `bd-email` and future `discovery-call-prep` runs can consume it. Confirm the path with the BDOwner if the org slug is ambiguous.

## Delivery — port to a CRM, don't assume copy-paste

The CallNote should travel to wherever the BDOwner's CRM lives. The destination is **pluggable, not hardcoded** — this is the `context.connector("crm")` surface in `core/context-contract.md`. Pick the delivery path in this order:

1. **A bound CRM connector** — if a CRM connector is configured/connected (Apollo, the CRM (example: a mid-market CRM), HubSpot, or whatever is wired to `context.connector("crm")`), port the CallNote into it: create/update the Account + Contact and log the note (or task) directly. Confirm the target account with the BDOwner before writing.
2. **The project folder** — also save to `contexts/<org>/call-notes/<account-slug>-<YYYY-MM-DD>.md` for version history, regardless of connector.
3. **Paste text (universal fallback)** — if no CRM connector is bound, output the flat note for manual paste. This is the floor, not the goal.

Do not assume copy-paste when a connector is available, and do not hardcode a specific CRM — read what's bound and use it. The flat-text format below is what gets pasted *or* written into the note field either way.

## Output rules

- Plain text only. No markdown, no headers, no bullets — the note goes into a CRM note field (pasted or written via connector).
- Match the language of the notes (Dutch notes → Dutch note; English → English).
- Tight and scannable. A CallNote is a record, not an essay.
- End with: the paste-ready note, then a short line offering the obvious next step (usually "Want me to draft the follow-up?" → hands off to `bd-email`).

## Composes with

- **account-research** — if there's no dossier yet and the account looks real, offer to build one.
- **bd-email** — the natural next step; the CallNote is its richest input for a follow-up.
- **discovery-call-prep** — a prior CallNote sharpens prep for the next meeting on the same account.
