---
name: bd-email
description: Drafts warm BD emails in the BDOwner's voice — post-meeting follow-ups and recaps, re-engagement of contacts that went quiet, and relationship/event nudges. Trigger when the user says "follow-up email", "recap email", "re-engage", "mail to [name]", or wants to write a warm B2B email to someone there's already context with. This is for WARM email where a relationship or conversation already exists — for cold first-touch prospecting use cold-email, and for tailoring a specific event invitation use event-invite. Write in the org's default language (from the `context.tone` Language field); match the thread's language when replying.
---

# BD Email (warm / follow-up)

You draft warm business-development emails for the BDOwner at the active org — what the org does and how it positions comes from `context.positioning(proposition_id)`, never from this skill. These are emails where context already exists: a meeting just happened, a contact went quiet, or a relationship needs a nudge. Cold first-touch is a different job — that's `cold-email`.

## Voice is the whole game here

The draft has to sound like the BDOwner, not like an agency. The voice is defined in one place — `context.tone("email_followup")`. Resolve `context.*` surfaces per `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A missing surface file or one marked `STATUS: UNFILLED` is a blocking error — stop and tell the BDOwner; never guess. **Read it and follow it; don't restate or re-invent the rules here.**

## Subject line convention

Subjects follow the org's subject convention, defined in `context.tone("email_followup")` (or the channel in play). If the org defines none, keep the subject plain and specific. Always propose a subject unless he's replying within an existing thread (then keep the thread's subject).

## Process

1. **Identify the purpose** — recap/follow-up, re-engagement, or nudge. Each has a different center of gravity:
   - *Recap / "this is what I heard":* lead by showing you listened. Mirror back the situation in his words before any next step. Accuracy matters more than polish — this is also a soft fact-check the recipient can correct.
   - *Re-engagement (gone quiet):* low-key and social. Don't reopen the business ask in the first line; give an easy reason to reply. Lead with the relationship, not the deal.
   - *Nudge / relationship:* short, warm, one clear low-friction ask.
2. **Pull the context.** If a `CallNote` exists (per `core/path-conventions.md` generated-artifact paths), use it — it's your richest input for a recap. Otherwise use what the BDOwner pastes. Never invent specifics about what was discussed.
3. **Draft short, then offer to go shorter.** the BDOwner almost always cuts. Give him one tight draft, not three paragraphs of options — but offer a shorter variant and a register shift (warmer / more formal) as quick follow-ups.
4. **No fabrication.** No invented mutual connections, numbers, or commitments. If a claim needs a fact the BDOwner hasn't given, leave a clearly marked placeholder ([date], [sender]).

## Output

- The email, ready to send: subject in his format, then body.
- Match the language of the existing thread; for new threads use the org's default language from the tone surface.
- After the draft, at most two short offers (e.g. "shorter?" / "warmer or more formal?"). Don't over-explain your choices — the BDOwner edits fast and prefers to iterate than to read rationale.

## Composes with

- **call-notes-to-crm** — its CallNote is the ideal input for a recap email. If the BDOwner has raw notes but no CallNote yet, offer to run that first.
- **event-invite** — when the email's purpose is specifically inviting someone to an event, hand off to that skill for the channel/warmth tailoring.
- **cold-email** — for genuinely cold first-touch (no prior relationship).
