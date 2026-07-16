# Skill Card — {{skill_name}}

**Version:** {{version}}
**Card last reviewed:** {{YYYY-MM-DD}} (by the BDOwner)
**Status:** DRAFT — requires human review

## Identity
- **Name:** {{skill_name}}
- **One-line purpose:** {{what it does, in one sentence}}
- **Implements spec:** {{specs/<id>.spec.md, or "none"}}

## Trigger
{{When this skill should fire — the phrases/contexts from its description.}}

## Rep-risk zone
{{One of: Autonomous | Draft→Approve | Agent-supports | Human-only. Justify in one line.}}

## Inputs
- **Context surfaces:** {{e.g. context.tone(email_followup), context.icp — or "none"}}
- **Entities read:** {{Account, Contact, CallNote, AccountDossier… — or "none"}}
- **External sources:** {{web, LinkedIn, pasted notes… — or "none"}}

## Outputs
- **Artifacts produced:** {{name + path, e.g. CallNote → path per `core/path-conventions.md` — or "none"}}
- **Events emitted:** {{e.g. OutreachDrafted — or "none"}}
- **Writes to external systems:** {{e.g. CRM note via connector — or "none"}}

## Connectors & permissions
- **May read:** {{connectors/files — or "none"}}
- **May write:** {{connectors/files, with confirmation requirement — or "none"}}
- **May send / post:** {{usually "none — Draft→Approve; human sends"}}
- **Must NOT do without explicit approval:** {{send email, post publicly, write CRM, run installs…}}

## Guardrails
{{The skill's hard rules — e.g. never fabricate claims, never auto-send, honour tov, flag rough figures.}}

## Limitations
{{Honest limits — e.g. "no CRM connector bound yet, so output is paste-text"; "single-language output only (per context.tone)". Delete any canned line that doesn't apply.}}

## Provenance
- **Origin:** {{authored | adapted from <source> | bd-skill-evolution}}
- **Source files carded:** {{SKILL.md + references/assets/scripts read to build this card}}
