---
name: cold-call-prep
description: Generates a flat cold call script in the org's language for CRM prep from an AccountDossier. Use whenever the BDOwner needs to prepare for a cold outreach call — trigger when the user mentions "cold call", "CRM prep", "call prep", "outreach", or asks to prepare a call for a specific account. Also trigger when an AccountDossier is available and the user wants to reach out by phone. Always produce flat plain text output — no markdown, no headers, no bullet points — ready to paste directly into a CRM note.
---

# Cold Call Prep

You produce a flat cold call script for the BDOwner, in the org's default language (from the `context.tone` Language field). The output goes directly into a CRM note — no formatting, no headers, just plain text the BDOwner can read off the screen while on the phone.

## Who the BDOwner is and how he speaks

Who the org is and what it offers comes from `context.positioning(proposition_id)`; read it before writing — the credibility and framing must match it, but the call never pitches it.

His voice is defined once via `context.tone(channel)` — read it; don't restate its rules here. Resolve `context.*` surfaces per `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A missing surface file or one marked `STATUS: UNFILLED` is a blocking error — stop and tell the BDOwner; never guess. For a cold call specifically: practitioner-to-practitioner, short sentences, no agency speak, and he never pitches.

The goal of the call is one thing: **book a meeting**. Not to diagnose pain, not to qualify in depth, not to pitch. Just get a yes to a short, low-friction conversation.

The ask should be easy to say yes to. Frame it from the prospect's perspective — a 20-minute conversation between two people in the same world, not a sales meeting.

Words to avoid: the anti-hype list lives in the `context.tone` surface; for a cold call also avoid sales-format words — the org-language equivalents of "solution", "proposition", "pitch", "demo" (too salesy for this format).

## What you need from the AccountDossier

Extract these three things before writing anything:

1. **Contact name and role** — who the BDOwner is calling
2. **Best trigger** — the single most specific, recent, true thing to reference in the opener (from the dossier's "Best trigger" field, or the warm signal if no trigger is available)
3. **Situation in one sentence** — what is happening at this company right now

If the dossier has a "Best trigger" field, use that. If not, fall back to the LinkedIn engagement signal.

## The script structure

Write the script in this exact order. No section labels. No formatting. Just the spoken words.

**Step 1 — We don't know each other:**
First name only, no company. Acknowledge they don't know him. Short, matter-of-fact.

**Step 2 — Credibility + reason for calling:**
Reference a relevant client the org has worked with — one the prospect might recognize. Take it from `context.content("case_study")` or ask the BDOwner; never invent one. This is the credibility signal. Then state clearly: I'm not calling you for nothing. This combination — a shared reference + transparent intent — does the trust work without pitching.

**Step 3 — Intellectual humility:**
State that he doesn't know their organisation. This is important — it positions the BDOwner as curious and respectful, not assuming. It sets up the questions naturally.

**Step 4 — Permission to continue:**
Ask two questions to understand if it makes sense to continue this conversation. The framing "to understand whether it makes sense to continue this conversation" is key — it's low stakes (just this call, not a commitment) and puts the prospect in control. Note it renders in the org's language.

**Step 5 — Questions (natural flow):**
Ask 1–3 questions based on what you know from the dossier. Situation, what they're working on, what's on their plate. These should feel like genuine curiosity, not qualification. Let the conversation breathe — this is not a rigid checklist.

**Step 6 — The close (earned by the conversation):**
If there's signal in their answers, close naturally: propose a proper follow-up and assume the yes — don't ask permission. E.g. "based on what you're saying it seems worth a longer conversation — shall we put something in the calendar?", rendered in the org's language.

**Objection handler (for "not now" or "we're doing fine"):**
Don't push back. Ask when a better moment would be. Leave it warm and open. Two sentences maximum.

## Important: what NOT to say
- Never say "no pitch" — it's overused and signals the opposite
- Never use hedging phrases — the org-language equivalents of "would it be worth...", "worth catching up", "just to get acquainted"
- Never manufacture urgency or pain you haven't heard from them
- Don't ask for a fixed time slot (30 min, 20 min) — just "put something in the calendar"

## Output rules

- Plain text only. No asterisks, no dashes, no headers, no markdown of any kind.
- Write in the org's default language (from the `context.tone` Language field) unless the BDOwner says otherwise.
- Written as spoken words — contractions, natural rhythm, the way the BDOwner actually talks.
- The full script should be readable in under 60 seconds.
- Label the objection handler clearly in plain text, in the org's language, so the BDOwner knows when to use it (e.g. "If they say it's not a good moment:").

## Example output shape

Illustrative shape only — always render in the org's language.

Hey [name], it's the BDOwner. We don't know each other — no worries. I'm not calling you for nothing: we've done good work for [reference client], maybe you know them. That's what got me to call. I don't know your organization beyond that, so can I ask you two questions to understand if it makes sense to continue this conversation?

[Question 1 — situation check, does that sound right?]

[Question 2 — what keeps them busy / what's moving slowly]

Based on what you're saying, it seems worth talking further. Shall we put something in the calendar?

If they say it's not a good moment: Totally understandable. When would be a better time?
