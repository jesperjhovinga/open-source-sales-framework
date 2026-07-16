# Spec: Account Research

**ID**: `account-research`
**Version**: `v0.1`
**Rep-risk zone**: Autonomous
**Primary archetype**: Researcher
**Status**: draft

## Intent

Produce a structured AccountDossier that gives the BDOwner enough context to decide whether an Account is worth pursuing, and to seed every downstream workflow (outreach, discovery prep, proposal). Today this research is manual, inconsistent, and under-leveraged once the call is over.

## Trigger

- Manual: BDOwner requests research on a named Account.
- Event-based: `AccountIdentified` — a new Account lands on the TargetAccountList.

## Inputs

### From BD Core
- `Account` (at minimum: name; ideally: domain, segment, stage).
- `ICPDefinition` (for fit scoring).

### From Org Context
- `context.icp()` — ICP filters + qualification criteria.
- `context.positioning(proposition_id)` — positioning for the candidate proposition.
- `context.competitors(proposition_id)` — relevant alternatives.

### From external systems
- Public web (news, website, job postings, leadership changes, earnings, press).
- SharePoint / Drive (internal notes on the Account, if any).
- LinkedIn (decision-maker + champion candidate identification).
- CRM (existing activity, prior touches, prior Opportunities).

## Process

Researcher gathers signals across inputs and structures them into an AccountDossier organized around: what the company does, what's changing, who matters, what their likely priorities are, where our propositions map, what risks / anti-signals exist, and what entry hypothesis to test.

Explicit about evidence gaps: claims are sourced or flagged as inference.

## Outputs

### Artifacts produced
- `AccountDossier` — markdown document stored at `contexts/<org>/dossiers/<account-slug>.md`.

### Events emitted
- `AccountIdentified` (if triggered manually on a net-new Account).
- `DossierProduced`.

### Writes to external systems
- None in v0.1. Optional CRM annotation in a future version.

## Acceptance criteria

- Dossier includes sections: Company snapshot, Recent signals, Key people (with role + reasoning), ICP fit (scored against criteria), Proposition fit (per `context.positioning()`), Competitive context, Entry hypothesis, Risks and anti-signals.
- Every non-obvious claim cites a source URL or internal doc path.
- If public data is thin, the relevant section states "insufficient public information" instead of fabricating.
- Dossier produced in under 10 minutes from trigger.
- Dossier can be consumed by `outreach-drafting` and `discovery-call-prep` without further research.

## Human-in-the-loop gate

None — Autonomous. BDOwner reads the dossier when opening downstream workflows. Optional lightweight thumbs-up/thumbs-down feedback loop for quality calibration.

## Dependencies

- Consumes: `context.icp`, `context.positioning`, `context.competitors`, connectors (web, SharePoint, LinkedIn, CRM).
- Produces input for: `outreach-drafting`, `discovery-call-prep`, `proposal-first-pass`.

## Open questions

- Refresh cadence: schedule-based for active Accounts, or only on retrigger?
- Source citation format — URL only, or short quote + URL?
- SharePoint access: confirm scope and auth model before implementation.
- Which LinkedIn data is in scope — public profile data only, or Sales Navigator if available?
