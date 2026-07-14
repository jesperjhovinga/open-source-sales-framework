# Spec: Prospect Sourcing via LinkedIn Engagement

**ID**: `prospect-sourcing`
**Version**: `v0.1`
**Rep-risk zone**: Autonomous
**Primary archetype**: Researcher
**Status**: draft

---

## Intent

Surface net-new prospect Contacts and Accounts by mining engagement on LinkedIn posts from a known ICP persona. People who engage with a target persona's content have demonstrated interest in the same topic space — they are warm, unsolicited leads.

This workflow produces a deduplicated, ICP-filtered, enriched contact list ready for import into the CRM (example: a mid-market CRM) and for seeding the `account-research` spec.

---

## Trigger

- Manual: BDOwner drops one or more LinkedIn profile URLs (a seed persona matching the ICP).

---

## Inputs

### From BDOwner
- One LinkedIn profile URL of a target ICP persona (e.g. a founder at a specialist NL firm).
- Number of posts to mine: default 5, minimum 3.

### From BD Core / Org Context
- `context.icp()` — ICP filters + qualification criteria + disqualifiers.

### From external systems
- **Apify** (LinkedIn Post Commenters/Reactors actor) — raw engagement data per post.
- **Apollo** — contact and organization enrichment (email, phone, company size, location).

---

## Process

1. **Scrape** — BDOwner runs the Apify LinkedIn Post Commenters actor on the seed profile and drops the output (JSON or CSV) into the session. Agent receives the raw engager list.

2. **Deduplicate** — Remove duplicate Contacts across posts. A person who engaged on 3 posts appears once. Dedup key: LinkedIn profile URL. Retain all engagement events in a `posts_engaged` column (comma-separated post URLs or titles).

3. **ICP filter** — Score each Contact's organization against `context.icp()`:
   - **Pass**: specialist firm, NL-based, 15–150 people, commercial revenue, Founder/MD/CEO is likely buyer.
   - **Soft pass**: matches most criteria, one signal missing or unverifiable — flag for manual review.
   - **Fail**: disqualifiers present (government-funded, public sector clients, no decision authority, outside NL) — exclude.
   - Add column `icp_score`: `pass` / `soft_pass` / `fail`.

4. **Netherlands filter** — Apply before enrichment to avoid burning Apollo credits on out-of-scope contacts. Exclude contacts where location is clearly non-NL and org is non-NL.

5. **Enrich** — For contacts that pass or soft-pass ICP filter, call Apollo `apollo_enrich_person` to retrieve:
   - Work email
   - Direct phone (if available)
   - Job title (verify/correct)
   - Company name, size, industry, website
   - LinkedIn URL (confirm)

6. **Assemble output** — Produce a CSV with the columns defined below. Sort by `icp_score` (pass first), then by `engagement_type` weight (comment > react > share).

---

## Output

### CSV columns (the CRM (example: a mid-market CRM)-ready)

| Column | Source |
|--------|--------|
| `first_name` | Apify / Apollo |
| `last_name` | Apify / Apollo |
| `linkedin_url` | Apify |
| `job_title` | Apollo |
| `company_name` | Apollo |
| `company_size` | Apollo |
| `company_website` | Apollo |
| `company_industry` | Apollo |
| `email` | Apollo |
| `phone` | Apollo |
| `location` | Apollo |
| `icp_score` | Agent (pass / soft_pass / fail) |
| `icp_notes` | Agent (brief reason — e.g. "no NL signal", "public sector risk") |
| `engagement_type` | Apify (comment / react / share) |
| `posts_engaged` | Apify (list of post URLs or titles) |
| `source_profile` | BDOwner input (seed LinkedIn URL) |
| `sourced_date` | Auto (ISO date) |

### Events emitted
- `AccountIdentified` — for each Account (org) that passes ICP filter, if not already on TargetAccountList.
- `LeadQualified` — for each Contact that passes ICP filter and has a valid email.

---

## Acceptance criteria

- No duplicate Contacts in output (dedup by LinkedIn URL).
- Every Contact has `icp_score` populated with a non-empty `icp_notes` justification.
- Enrichment attempted for all pass + soft_pass contacts.
- `fail` contacts excluded from CSV (or optionally kept in a separate tab/file if BDOwner wants to review).
- CSV opens cleanly in Excel and maps to the CRM (example: a mid-market CRM) import template without manual column renames.
- Workflow completes in under 15 minutes from data drop to CSV delivery.

---

## Human-in-the-loop gate

- **Autonomous** for scrape → dedup → filter → enrich → CSV.
- BDOwner reviews `soft_pass` rows before deciding to import them into the CRM (example: a mid-market CRM).
- BDOwner triggers `account-research` spec manually on high-priority Accounts from the output.

---

## Dependencies

- **Upstream**: BDOwner manual trigger + Apify scrape output.
- **Downstream**: feeds `account-research`, `outreach-drafting`.
- **Connectors**: Apify (manual output drop in v0.1), Apollo MCP.

---

## Open questions / v0.2 considerations

- Automate Apify trigger via API (eliminate manual scrape step).
- Add Sales Navigator scope for richer engagement data.
- Cross-reference output against existing the CRM (example: a mid-market CRM) contacts via the CRM (example: a mid-market CRM) MCP to flag known contacts.
- Weighted ICP scoring (numeric score 0–100) instead of pass/soft_pass/fail.
- Auto-trigger `account-research` for all `pass` accounts.
