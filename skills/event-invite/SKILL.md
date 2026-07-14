---
name: event-invite
description: Tailors a standard event invitation to one specific contact and channel in the BDOwner's voice. Trigger when the user says "invite [name] to the event", "uitnodigen voor het event", "Signals invite", "stuur [name] een uitnodiging", "WhatsApp invite", or wants to adapt a generic invite for a particular person. Handles channel (email / LinkedIn DM / WhatsApp), relationship warmth (cold, warm, gone quiet), and subtle audience signaling (e.g. aimed at C-level / strategic decision-makers without saying so bluntly). Use this rather than bd-email whenever the specific job is an event invitation. Default to Dutch unless the contact is addressed in English.
---

# Event Invite

You adapt a standard event invitation into a personal one for a single contact, for the BDOwner (BDOwner) at ExampleOrg. The standard invite is the same for everyone; your job is to make it land for *this* person, on *this* channel, given *how well the BDOwner knows them*. Three dials: channel, warmth, audience signal.

This skill is parametric — it works for any event. The current event's details and the canonical invite text are inputs, not baked in. See `assets/signals-2026-example.md` for a worked example (the Signals 9 July 2026 event) you can pattern-match against.

## Inputs to gather (ask only for what's missing)

1. **The standard invite** — the canonical event text and facts (date, time, location, what's on, who else is coming). If the project is connected, check the active Org Context for the event brief, or ask the BDOwner to paste it.
2. **The contact** — name, role, company, and **relationship history**: never spoken (cold), spoken positively then went quiet, warm/booked, etc. This drives everything.
3. **Channel** — email, LinkedIn DM, or WhatsApp.

## The three dials

### Channel sets the register
- **Email:** can carry the most. Use the subject convention `[functie] onderwerp` (e.g. `[vraag] uitnodigen voor event 9 juli`). Full but still tight.
- **WhatsApp:** short, lowercase, low-key. One personal line, the hook, one ask. No formal sign-off.
- **LinkedIn DM:** between the two — conversational, a couple of lines, no subject.

### Warmth sets the opening move
- **Cold:** open with the genuine reason you're reaching out (a mutual connection, their work that caught your eye). Don't pretend familiarity. For a borderline-fit contact, it's often stronger to offer a quick call to check it's worth their time than to hard-invite.
- **Warm / positive prior contact:** reference it lightly and pick the thread back up.
- **Went quiet:** lead with the relationship, not the business ask. Give an easy, low-pressure reason to reply. The invite itself is the re-entry — don't reopen the deal in the first line.

### Audience signal (when the event is for decision-makers)
When the BDOwner wants to attract C-level / strategic decision-makers and gently filter out, say, junior developers, do it *between the lines* — never "this is for C-level only". Techniques that work:
- The word **"besloten"** (invitation-only) does a lot of quiet status work.
- Signal who else is in the room: "een aantal beslissers en C-level uit jullie sector".
- Frame the level of the conversation: "het gesprek een niveau hoger — wat het betekent voor je organisatie, niet hoe je het in code giet".
- Put it in the ask: "laat weten of jij of een andere strategische besluitvormer erbij wil zijn."

## Voice

Same voice as everything the BDOwner sends — defined once via `context.tone(channel)`. Resolve `context.*` surfaces per `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A missing surface file or one marked `STATUS: UNFILLED` is a blocking error — stop and tell the BDOwner; never guess. Read it; don't restate the rules here. The surface covers the per-channel registers — for WhatsApp/LinkedIn DM that means lowercase, dry, short, deliberately unpolished. Authentic beats glossy.

## Process & output

1. Confirm channel + warmth (infer from what the BDOwner says; ask only if genuinely unclear).
2. Draft one tailored invite in the right register, with the audience signal woven in if relevant.
3. For the personal hook, use only true, known facts about the contact. If a strong warm-up (e.g. a mutual connection attending) depends on a fact you can't confirm, ask before using it — don't assert it.
4. Offer 2-3 quick variants of the line doing the heavy lifting (the hook or the audience-signal line) so the BDOwner can pick the register, rather than rewriting the whole thing.

Output is the ready-to-send message (subject + body for email; just the message for WhatsApp/DM), in the contact's language.

## Composes with

- **bd-email** — for non-event warm emails (recaps, follow-ups, re-engagement).
- **call-notes-to-crm / account-research** — source of the relationship history that sets the warmth dial.
