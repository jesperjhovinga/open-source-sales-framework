---
name: prospect-sourcing
description: Runs the full prospect sourcing pipeline from LinkedIn engagement data to a research-scored, CRM-ready prospect CSV. Trigger when the user uploads or mentions an Apify JSON file from LinkedIn engagement scraping, says "run the pipeline", "score these engagers", "process the LinkedIn data", or wants to turn a list of LinkedIn engagers into qualified prospects. Also trigger when the user drops a engagers.json or similar Apify export into the session.
---

# Prospect Sourcing Pipeline

Turns raw LinkedIn engagement data (from Apify) into a scored, enriched prospect list ready for CRM import and account research.

## What you need before starting

1. **Apify JSON file** — exported from `harvestapi/linkedin-profile-posts`. If not yet uploaded, ask the user to drop it into the session.
2. **Seed profile URL** — the LinkedIn profile that was scraped (e.g. `https://www.linkedin.com/in/<seed-profile>/`). Ask if not provided.
3. **Context surfaces** — `context.icp()` to load the ICP criteria before scoring. Resolve `context.*` surfaces per `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A missing surface file or one marked `STATUS: UNFILLED` is a blocking error — stop and tell the BDOwner; never guess.

## Step 1 — Parse and deduplicate

Run the `bd` CLI to parse the Apify JSON, deduplicate by actor ID, and apply the headline-based ICP pre-filter:

```bash
bd source <input.json> <output_prefiltered.csv> --seed-url "<seed_url>"
```

This outputs a CSV with all unique engagers, scored as `soft_pass` (needs research) or `fail`.

It loads its headline pre-filter keywords from the active org's `context.icp` surface (the `headline_prefilter` JSON block in `icp.md`) and fails loud if the surface or block is missing.

The command prints a summary — share it with the user before proceeding.

## Step 2 — Web research and ICP scoring

For every `soft_pass` contact where a company name is visible in the `company_name` column or can be inferred from `job_title`, do a web search to verify the account against the ICP criteria from `context.icp()` — geography/reachability, size band, revenue model, and buyer authority per its persona definitions.

**Scoring rules:**
- `pass` — all ICP criteria confirmed
- `soft_pass` — all but one confirmed, or a buyer-authority title without confirmed company size
- `fail` — any hard disqualifier from `context.icp()` confirmed

**Hard disqualifiers (immediate fail):** defined in `context.icp()` — any confirmed match is an immediate fail.

Update the `icp_score` and `icp_notes` columns with your findings. Also fill in `company_size_est` where found.

For contacts where no company can be identified from public sources, leave as `soft_pass` with note "no company identified — needs manual check".

## Step 3 — Apollo enrichment (requires Professional plan)

For all `pass` and `soft_pass` contacts, enrich with Apollo to get email, phone, company size, and location.

Use `apollo_people_bulk_match` with batches of max 10 contacts. Pass `linkedin_url` and `name` for each contact.

If Apollo API returns an error about plan access, skip this step and note it in the output — the user will enrich manually via Apollo web app.

Update `email`, `phone`, `location`, and `company_size_est` columns with Apollo results.

## Step 4 — Assemble final output

Produce two files:

**1. Full scored CSV** (all pass + soft_pass, fails excluded):
- Sort: `pass` first, then `soft_pass`; within each group, `comment` engagements before `reaction`
- Save as: `prospect-sourcing-<seed-name>-<date>.csv`

**2. Summary for user** — print in chat:
```
Seed profile: <url>
Total unique engagers: X
  ✅ pass:      N (ready for account research)
  🔶 soft_pass: N (needs manual check or enrichment)
  ❌ fail:      N (excluded)

Pass contacts:
  - [Name] | [Company] | [Why]
  ...
```

Save the CSV to the user's workspace folder.

## Apollo notes

- LinkedIn URLs from Apify are ID-based format (`https://www.linkedin.com/in/ACoAAA...`) — Apollo can match on these
- Bulk match endpoint (`apollo_people_bulk_match`) requires Professional plan
- Single match (`apollo_people_match`) also requires Professional plan
- Free plan only gives credits for the Apollo web app — not the API
- If API is unavailable, output the CSV with empty email/phone fields and tell the user to import into Apollo web app for enrichment

## Output columns

`first_name`, `last_name`, `linkedin_url`, `job_title`, `company_name`, `company_size_est`, `email`, `phone`, `location`, `icp_score`, `icp_notes`, `engagement_type`, `posts_engaged`, `source_profile`, `sourced_date`
