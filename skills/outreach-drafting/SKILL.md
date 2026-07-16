---
name: outreach-drafting
description: Drafts a first-touch or follow-up message to a named Contact at an Account, for a stated purpose (cold, warm, re-engage, event). Trigger when the user asks to write outreach, an intro message, a follow-up, a cold email, a LinkedIn DM, or an event invitation to a specific person. Implements specs/outreach-drafting.spec.md.
---

# Outreach drafting

Implements `specs/outreach-drafting.spec.md`. Rep-risk zone: **Draft→Approve** —
you draft, the BDOwner approves and sends. Never send anything yourself.

## Inputs

1. **Account** and **Contact** (required). Ask if not given.
2. **Purpose** — one of `cold`, `warm`, `re-engage`, `event`. Ask if unclear.
   Purpose changes the opening and the ask, not the machinery.
3. **Channel** — e.g. `linkedin_dm`, `email_cold`, `email_followup`.
4. **Context surfaces** — resolve every `context.*` surface per
   `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A
   missing surface, or one marked `STATUS: UNFILLED`, is a blocking error: stop
   and tell the BDOwner. Never guess org content.
   - `context.positioning(proposition_id)` — the proposition to lead with.
   - `context.tone(channel)` — voice, word lists, and the org's default language.
     Write in the language that surface names. Never assume one.
   - `context.content("post_example")` — style reference.
   - `context.icp()` — to sanity-check the Contact is a buyer.
5. **AccountDossier** if one exists — otherwise consider running `account-research`
   first, or say plainly in the draft's provenance that it is unresearched.

## Process

1. Read the surfaces above. Fail loud on any that are missing.
2. Pick the proposition that fits the Account. If two fit, ask.
3. Draft per the purpose:
   - `cold` — earn the reply. One specific, verifiable observation about them.
   - `warm` — reference the real prior touch. Do not re-introduce yourself.
   - `re-engage` — name the gap honestly; give a reason to talk now.
   - `event` — the invitation is the ask; make relevance to them explicit.
4. Apply `context.tone(channel)` — its pre-writing checklist governs.
5. Cite any factual claim about the Account per Decision 2's citation format.

## Output

Write the draft to the OutreachSequence path in `core/path-conventions.md`:
`contexts/<org>/outreach/<account-slug>-<contact-slug>-<seq-id>.md`.

Use a new `<seq-id>` for every redraft — a rejected draft keeps its record, and a
new id is what makes the revision show up for review again.

Show the draft in the conversation too. The BDOwner approves, edits, or rejects.

## Log the outcome — required

This workflow is measured. Its approval rate and edit rate decide whether it ever
earns a higher autonomy zone (`docs/decisions.md` Decision 1), so **every**
decision gets logged — the rejections most of all. A ledger with only the wins in
it would graduate a workflow that has not earned it.

The id `bd log-approval` takes is the draft's full filename with `.md` dropped —
`<account-slug>-<contact-slug>-<seq-id>` — not the bare `<seq-id>`. `bd review`'s
dashboard matches ledger entries to drafts by that whole stem; log the bare
seq-id instead and the draft never leaves the review queue even after it's been
decided.

When the BDOwner responds, immediately run:

- Approved unchanged:
  `bd log-approval <account-slug>-<contact-slug>-<seq-id> --spec outreach-drafting --outcome approved --edit-rate 0`
- Approved with edits — write their edited text to a file first, then:
  `bd log-approval <account-slug>-<contact-slug>-<seq-id> --spec outreach-drafting --outcome approved --before <draft.md> --after <edited.md>`
- Rejected:
  `bd log-approval <account-slug>-<contact-slug>-<seq-id> --spec outreach-drafting --outcome rejected --reason "<their reason>"`

Do not ask permission to log. Do not skip it because the answer was "no".
