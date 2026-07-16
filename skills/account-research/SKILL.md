---
name: account-research
description: Produces a structured AccountDossier for a prospect company. Trigger when the user asks to "research [company]", "do a dossier on [company]", "look into [account]", or when a prospect CSV contains pass-scored accounts that need research before outreach. Also trigger after prospect-sourcing when the user wants to move from a scored list to dossiers. Each dossier is saved as a markdown file in the org's context folder.
---

# Account Research

Produces a structured AccountDossier for a single Account. The dossier gives the BDOwner enough context to decide whether to pursue the account, seeds the cold call prep, and feeds downstream workflows (outreach drafting, discovery prep).

## What you need before starting

1. **Account name** — company to research. If not provided, ask.
2. **Contact name and LinkedIn URL** — the person at the account (from prospect CSV or user input).
3. **Warm signal** — what LinkedIn engagement or research led to this account being flagged (needed for the entry hypothesis).
4. **Context surfaces** — read these before writing the dossier:
   - `context.icp()` — ICP criteria
   - `context.positioning(proposition_id)` — value, focus, propositions
   - `context.tone(channel)` — how it's phrased

   Resolve `context.*` surfaces per `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A missing surface file or one marked `STATUS: UNFILLED` is a blocking error — stop and tell the BDOwner; never guess.

## Research process

Search the web for the following signals. Cite sources or flag as inference — never fabricate.

**Company basics:**
- What do they do (core service or product)?
- How many people (LinkedIn, company site, ZoomInfo, Apollo, KvK)?
- Revenue model — commercial fees, grants, government contracts?
- HQ location — meets the geography criteria in `context.icp()`?
- Website

**Recent signals (last 6–12 months):**
- News, press releases, funding rounds
- New hires or leadership changes
- New products, market expansions, partnerships
- Job postings (signals growth areas and priorities)

**Key people:**
- Decision-maker: Founder/MD/CEO — or the local-language equivalent title, per `context.tone` — with budget authority
- Champion candidate: someone technical or operational who would benefit from the org's work
- Anyone connected to the warm signal (e.g. the person who engaged on LinkedIn)

**Proposition fit:**
- Which proposition from `context.positioning()` fits better, and why?
- What specific problem would the org solve for them?
- Is there a repeatable methodology, internal tool, or operational process that could become a digital product?

**Competitive context:**
- What alternatives would they consider (freelancers, agencies, low-code platforms, hiring in-house)?
- What makes the org's approach different in this specific context?

If public data is thin on any section, write "insufficient public information" — do not invent.

## Dossier format

Save the dossier as markdown to the AccountDossier path per `core/path-conventions.md`.

Use this exact structure:

```markdown
# AccountDossier: [Company Name]

**Generated**: [YYYY-MM-DD]
**Source trigger**: [how this account was identified]
**Status**: ready for outreach-drafting

---

## Company snapshot
[What they do, size, location, revenue model, website]

---

## Recent signals
[News, hires, funding, product launches — dated where possible]

---

## Key people
| Name | Role | Reasoning |
|---|---|---|
| [Name] | [Role] | [Why they matter — decision authority, champion potential] |

---

## ICP fit
| Criterion | Signal | Score |
|---|---|---|
| Specialist firm | [evidence] | ✅ / 🟡 / ❌ |
| Geography fit (per `context.icp()`) | [evidence] | ✅ / 🟡 / ❌ |
| 15–150 people | [evidence] | ✅ / 🟡 / ❌ |
| Commercial revenue | [evidence] | ✅ / 🟡 / ❌ |
| Founder/CEO buyer | [evidence] | ✅ / 🟡 / ❌ |
| Proprietary methodology / tool | [evidence] | ✅ / 🟡 / ❌ |
| Disqualifiers | [any present?] | ✅ / ❌ |

**ICP score: PASS / SOFT_PASS / FAIL**

---

## Proposition fit
[Which proposition from `context.positioning()` fits, and why. What specific problem it solves. Custom framing — never mention specific entry-format names.]

---

## Competitive context
[What alternatives they'd consider. Where the org differentiates in this specific context.]

---

## Entry hypothesis
[The specific angle to open with. What to test in the first conversation. What the entry move is — tied to the warm signal where possible.]

---

## Risks and anti-signals
[Reasons to be cautious. Timing risks. Budget signals. Things to verify.]

---

*Sources: [list URLs and retrieval date]*
```

## After saving

Tell the user:
- The dossier has been saved and is ready for cold-call-prep
- The ICP score
- The entry hypothesis in one sentence
- Any risks worth flagging

If multiple accounts were requested, process them one by one and summarise all results at the end.
