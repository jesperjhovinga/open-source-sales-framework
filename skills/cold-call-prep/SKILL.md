---
name: cold-call-prep
description: Generates a flat Dutch cold call script for CRM prep from an AccountDossier. Use whenever the BDOwner needs to prepare for a cold outreach call — trigger when the user mentions "cold call", "bel script", "CRM prep", "call prep", "uitschrijven", "outreach", or asks to prepare a call for a specific account. Also trigger when an AccountDossier is available and the user wants to reach out by phone. Always produce flat plain text output — no markdown, no headers, no bullet points — ready to paste directly into a CRM note.
---

# Cold Call Prep

You produce a flat Dutch cold call script for the BDOwner at ExampleOrg. The output goes directly into a CRM note — no formatting, no headers, just plain text the BDOwner can read off the screen while on the phone.

## Who the BDOwner is and how he speaks

the BDOwner is BD at ExampleOrg, a Dutch digital product agency. ExampleOrg derisk and accelerates — from product idea to working software, faster and with less risk than going alone. Custom work every time, no fixed products.

His voice is defined once via `context.tone(channel)` — read it; don't restate its rules here. Resolve `context.*` surfaces per `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A missing surface file or one marked `STATUS: UNFILLED` is a blocking error — stop and tell the BDOwner; never guess. For a cold call specifically: practitioner-to-practitioner, short sentences, no agency speak, and he never pitches.

The goal of the call is one thing: **book a meeting**. Not to diagnose pain, not to qualify in depth, not to pitch. Just get a yes to a short, low-friction conversation.

The ask should be easy to say yes to. Frame it from the prospect's perspective — a 20-minute conversation between two people in the same world, not a sales meeting.

Words to avoid: the anti-hype list lives in the `context.tone` surface; for a cold call also avoid "oplossing", "propositie", "pitch", "demo" (too salesy for this format).

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
Reference a relevant organisation ExampleOrg has worked with — one the prospect might know ("misschien ken je ze"). This is the credibility signal. Then state clearly: I'm not calling you for nothing. This combination — a shared reference + transparent intent — does the trust work without pitching.

**Step 3 — Intellectual humility:**
State that he doesn't know their organisation. This is important — it positions the BDOwner as curious and respectful, not assuming. It sets up the questions naturally.

**Step 4 — Permission to continue:**
Ask two questions to understand if it makes sense to continue this conversation. The framing "om te begrijpen of het zinvol is om dit gesprek voort te zetten" is key — it's low stakes (just this call, not a commitment) and puts the prospect in control.

**Step 5 — Questions (natural flow):**
Ask 1–3 questions based on what you know from the dossier. Situation, what they're working on, what's on their plate. These should feel like genuine curiosity, not qualification. Let the conversation breathe — this is not a rigid checklist.

**Step 6 — The close (earned by the conversation):**
If there's signal in their answers, close naturally: propose a proper follow-up call. Don't ask permission — assume the yes. "Op basis van wat je zegt, lijkt het me zinvol om hier verder over te praten. Zullen we iets inplannen?"

**Objection handler (for "niet nu" or "we zijn goed bezig"):**
Don't push back. Ask when a better moment would be. Leave it warm and open. Two sentences maximum.

## Important: what NOT to say
- Never say "geen pitch" — it's overused and signals the opposite
- Never use hedging phrases like "zou het wat zijn", "de moeite waard om bij te praten", "even kennismaken"
- Never manufacture urgency or pain you haven't heard from them
- Don't ask for a fixed time slot (30 min, 20 min) — just "iets inplannen"

## Output rules

- Plain text only. No asterisks, no dashes, no headers, no markdown of any kind.
- Dutch throughout.
- Written as spoken words — contractions, natural rhythm, the way the BDOwner actually talks.
- The full script should be readable in under 60 seconds.
- Label the objection handler clearly in plain text so the BDOwner knows when to use it: start that section with "Als hij zegt dat het geen goed moment is:"

## Example output shape

Hey [naam], met the BDOwner. Wij kennen elkaar niet — geen zorgen. Ik bel je niet voor niets: wij hebben goed werk gedaan voor [referentie], misschien ken je ze. Dat triggerde mij om je te bellen. Ik ken jullie organisatie verder niet, dus mag ik je twee vragen stellen om te begrijpen of het zinvol is om dit gesprek voort te zetten?

[Vraag 1 — situatie bevestiging, klopt dat?]

[Vraag 2 — wat houdt ze bezig / wat gaat langzaam]

Op basis van wat je zegt, lijkt het me zinvol om hier verder over te praten. Zullen we iets inplannen?

Als hij zegt dat het geen goed moment is: Helemaal begrijpelijk. Wanneer zou een beter moment zijn?
