# Ubiquitous Language — v0.1

The canonical vocabulary shared by the BDOwner and every agent. If a concept isn't here, it doesn't belong in specs. If a spec uses a term, it must be defined here.

## Entities

Persistent things with identity.

- **Account** — prospect or customer organization. Has: name, industry, size, segment, status.
- **Contact** — person at an Account. Has: name, role, seniority, persona, account.
- **Lead** — Contact + intent signal (not yet an Opportunity). Has: source, intent strength, owner.
- **Opportunity** — a sales motion toward a specific transaction. Has: account, stage, value, close date, owner.
- **Message** — a single outreach touch (LinkedIn DM, email). Has: channel, direction, timestamp, sequence.
- **Sequence** — ordered set of Messages. Has: purpose, cadence, exit conditions.
- **Meeting** — synchronous interaction. Has: participants, purpose, transcript, outcomes.
- **CallNote** — structured record of a Meeting. Has: SPICED fields, action items, next step.
- **Proposal** — formal offer. Has: scope, pricing, terms, version.
- **Contract / SoW** — signed commitment. Has: party, value, effective date.
- **Workshop** — org-specific engagement (workshop-led motion). Has: participants, proposition, outcome.
- **ICPDefinition** — ideal customer profile for a proposition. Has: filters, qualification criteria.
- **TargetAccountList** — Accounts selected from ICP. Has: proposition, accounts, prioritization.
- **Competitor** — alternative the prospect considers. Has: positioning, known weaknesses, our angle.
- **ContentAsset** — reusable artifact (case study, post, deck). Has: type, topic, audience.
- **PipelineSnapshot** — point-in-time state of all Opportunities. Has: timestamp, coverage, gaps.
- **AccountDossier** — researched profile of an Account. Output of `account-research` spec.
- **OutreachSequence** — first-touch + planned follow-ups. Output of `outreach-drafting` spec.
- **DiscoveryPrepDoc** — pre-call briefing. Output of `discovery-call-prep` spec.

## Events

Things that happened. Past tense.

- **AccountIdentified** — surfaced as a fit candidate.
- **LeadQualified** — intent + fit threshold met.
- **OutreachDrafted** — draft ready for BDOwner approval.
- **OutreachSent** — a Message went out after approval.
- **OutreachReplied** — a prospect responded.
- **MeetingScheduled** — a Meeting is on the calendar.
- **DiscoveryCallHeld** — a discovery Meeting happened.
- **DiagnosisCaptured** — SPICED fields filled for an Opportunity.
- **ProposalSent** — a Proposal went out.
- **ObjectionRaised** — a prospect voiced a blocker.
- **ContractSigned** — a Contract was executed.
- **DealWon / DealLost** — Opportunity closed.
- **RetrospectiveCompleted** — post-deal analysis written.
- **ExpansionSignalDetected** — account behavior suggests upsell / cross-sell.

## Actors

- **BDOwner** — the human (the human owner at the org). Owns the Opportunity through the BD phase.
- **Prospect** — external person not yet qualified into a role.
- **Champion** — internal advocate at the Account.
- **DecisionMaker** — has authority to sign.
- **InternalSME** — colleague who provides domain expertise.
- **DeliveryTeam** — takes over at Onboarding handoff.
- **WorkshopParticipant** — attends an ExampleOrg Workshop.

## Stages (Winning by Design Bowtie)

1. **Awareness** — Account aware of the problem / category.
2. **Education** — Account learning about solutions.
3. **Selection** — Account comparing options.
4. **Commitment** — Contract signed.
5. **Onboarding** — Delivery kickoff.
6. **Impact** — Customer realizing value.
7. **Expansion** — Additional scope, referrals, cross-sell.

BD owns Awareness → Commitment. Handoff to DeliveryTeam at Onboarding.

## Agent archetypes

- **Researcher** — gathers, structures, and synthesizes information. Low-write, high-read.
- **Drafter** — produces first-pass output in a defined format. Human approves before send.
- **Summarizer** — distills long-form inputs (transcripts, threads) into structured records.
- **Reviewer** — evaluates drafts against rules (tone, factuality, SPICED coverage).
- **Coach** — asks the BDOwner targeted questions before, during, or after an activity.

## Rep-risk zones

- **Autonomous** — executes without pre-send review.
- **Draft→Approve** — agent drafts, human reviews + sends.
- **Agent supports** — human is primary, agent accelerates.
- **Human only** — not a candidate for automation.

## SPICED (Winning by Design)

Discovery framework. Every discovery call and prep spec uses these dimensions.

- **S**ituation — current state, context, environment.
- **P**ain — what's broken or costly about the current state.
- **I**mpact — what the pain costs in money, time, risk, morale.
- **C**ritical event — forcing function, deadline, or trigger event that drives urgency.
- **D**ecision criteria — how the prospect will choose a solution.

## Conventions

- Glossary terms are capitalized when referenced in specs (`Account`, `OutreachSequence`).
- New terms are added here before being used in a spec.
- Deprecated terms are struck through and kept for one version before removal.
