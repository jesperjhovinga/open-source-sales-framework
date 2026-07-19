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
`contexts/<org>/outreach/<account-slug>-<contact-slug>-<seq-id>.md`. Call this
filename, minus `.md`, **the stem** — it is also the run id (see below).

The first time you generate a draft for a stem, also copy it — byte-for-byte,
unchanged — to `contexts/<org>/outreach/originals/<account-slug>-<contact-slug>-<seq-id>.md`.
That copy is the frozen baseline: never write to it again. (`bd review`'s
pending queue only looks directly inside `contexts/<org>/outreach/`, not its
subdirectories, so this copy never itself shows up as a second pending draft.)

If the BDOwner asks for changes before approving ("make it shorter", "different
hook"), **overwrite the same stem file** — do not give the revision a new
seq-id. The stem is the run id, and it must stay the same file through every
pre-approval revision, or the draft forks into two pending items for one
conceptual draft. Only `originals/<stem>.md` is frozen; `<stem>.md` itself is
expected to change up until approval.

Use a **new** `<seq-id>` only when drafting again **after a rejection** — a
rejected run keeps its own record (see below), and giving the redraft a new id
is what makes that next attempt show up for review as its own run. Never reuse
a seq-id that already has a decision logged against it.

Show the draft in the conversation too. The BDOwner approves, edits, or rejects.

## Log the outcome — required

This workflow is measured. Its approval rate and edit rate decide whether it ever
earns a higher autonomy zone (`docs/decisions.md` Decision 1), so **every**
decision gets logged — the rejections most of all. A ledger with only the wins in
it would graduate a workflow that has not earned it.

**A self-reported edit rate flatters the gate that decides whether this workflow
stops being reviewed.** `--before`/`--after` compute the rate from the actual
text; `--edit-rate` is a number you assert. Prefer the computed form whenever
both texts exist.

- `--before` is `contexts/<org>/outreach/originals/<stem>.md` — the frozen,
  first-generated copy from the Output step, whatever pre-approval iteration
  happened after it was written.
- `--after` is `contexts/<org>/outreach/<stem>.md` — the same stem file the
  BDOwner actually approved, however many times it was revised before that.

The id `bd log-approval` takes is the stem — the draft's full filename with
`.md` dropped (`<account-slug>-<contact-slug>-<seq-id>`), not the bare
`<seq-id>`. `bd review`'s dashboard matches ledger entries to drafts by that
whole stem; log the bare seq-id instead and the draft never leaves the review
queue even after it's been decided.

When the BDOwner responds, immediately run:

- Approved (unchanged or after pre-approval revisions) — `--before` is always
  `originals/<stem>.md`, `--after` is always the live `<stem>.md`, so the rate
  is computed across every pre-approval iteration, not just whatever changed at
  the moment of approval:
  `bd log-approval <stem> --spec outreach-drafting --outcome approved --before contexts/<org>/outreach/originals/<stem>.md --after contexts/<org>/outreach/<stem>.md`
- Rejected:
  `bd log-approval <stem> --spec outreach-drafting --outcome rejected --reason "<their reason>"`
- `--edit-rate <n>` is for the rare case where the edit happened outside this
  loop and neither `originals/<stem>.md` nor the live `<stem>.md` is available
  as a file to diff — not a shortcut for "nothing changed that I noticed."

Do not ask permission to log. Do not skip it because the answer was "no".
