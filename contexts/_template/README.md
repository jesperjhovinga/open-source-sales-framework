# Org Context Template

Copy this folder to `contexts/<your-org-slug>/`, fill every surface file, then set
`ACTIVE_CONTEXT.md` (repo root) to your slug. Every file here is REQUIRED — a
missing surface is a blocking error for any spec that calls it (fail loud, per
`docs/decisions.md` principle 5).

| File | Contract surface | What goes in it |
|---|---|---|
| `positioning.md` | `context.positioning(proposition_id)` | Narrative per proposition: arc, key messages, objection reframes, boundaries (what you DON'T do) |
| `icp.md` | `context.icp(segment?)` | Fit criteria, size bands, buyer personas, disqualifiers, geography/reachability rules, winnability. Also requires a `## Headline pre-filter config` section with a ` ```json ` fence containing `headline_prefilter` → `disqualify_keywords` / `buyer_title_keywords` / `specialist_keywords` (required by the prospect-sourcing script; the script fails loud without it) |
| `value-props.md` | (referenced by positioning) | Value propositions per proposition/segment |
| `competitors.md` | `context.competitors(proposition_id?)` | Competitor list, their positioning, weaknesses, your angle |
| `content-library.md` | `context.content(type, topic?)` | Index of case studies, one-pagers, decks, post examples |
| `tone-of-voice.md` | `context.tone(channel)` | Voice patterns, banned/preferred words, language/locale per channel, pre-write checklist. Also requires a `## Language` section stating the default language per org |
| `pricing.md` | `context.pricing(proposition_id)` | Price ranges, engagement shapes, boilerplate terms |
| `connectors.md` | `context.connector(name)` | Provider bindings + auth model + read/write scope allowlists per Decision 7 |

**Never commit a real org context to a public repo.** The repo `.gitignore`
excludes everything under `contexts/` except this template and `example-corp/`.
