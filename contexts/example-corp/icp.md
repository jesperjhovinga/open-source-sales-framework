# ICP — Example-Corp

## Overarching ICP
Commercial field-service contractor (HVAC, plumbing, electrical, fire safety),
**US-based**, **50–500 field technicians**, running dispatch on spreadsheets or
a legacy tool. Buyer has budget authority and operational pain TODAY.

## Buyer personas
- **Primary:** VP Operations / Ops Director — owns dispatch efficiency, feels
  the pain daily, controls the tooling budget.
- **Secondary:** Owner/CEO (companies <100 techs), CFO (invoice-lag angle).

## Segments
- `segment_a` — growth contractors (50–150 techs), often PE-backed, tool
  consolidation trigger.
- `segment_b` — established regionals (150–500 techs), legacy-system
  replacement trigger.

## Disqualifiers
- Residential-only one-truck shops (<20 techs) → no budget, founder-led buying.
- Government / municipal fleets → procurement cycle mismatch for outbound.
- Enterprise (>1,000 techs) → inbound/landed only, not cold.
- Already on a modern competitor (see competitors.md) with <2 years on contract.

## Geography & reachability
- US and Canada only. Decision-maker must be reachable via LinkedIn or direct
  line. Filter location before enrichment spend.

## Winnability layer
Fit is not enough — deprioritize when: over-hyped darling every vendor chases;
locked into an ecosystem partner we can't displace; no reachable champion.

## Headline pre-filter config
Machine-readable config for `skills/prospect-sourcing/scripts/process_engagers.py`
(headline-based pre-scoring of LinkedIn engagers). Keyword matching is
case-insensitive substring.

```json
{
  "headline_prefilter": {
    "disqualify_keywords": [
      "government", "municipal", "city of", "county", "federal",
      "school district", "university", "public works", "non-profit", "nonprofit"
    ],
    "buyer_title_keywords": [
      "owner", "ceo", "president", "vp operations", "vp of operations",
      "ops director", "director of operations", "general manager", "coo",
      "cfo", "managing partner", "founder"
    ],
    "specialist_keywords": [
      "hvac", "plumbing", "electrical", "fire safety", "fire protection",
      "mechanical contractor", "field service", "service manager",
      "dispatch", "facilities", "refrigeration", "controls"
    ]
  }
}
```
