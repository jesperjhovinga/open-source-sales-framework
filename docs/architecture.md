# Architecture

## Two bounded contexts

### BD Core (portable)
Contains everything that does *not* change from org to org:
- Ubiquitous language (entities, events, actors, stages).
- Winning by Design methodology (SPICED, Bowtie, blueprints).
- Agent archetypes (Researcher, Drafter, Summarizer, Reviewer, Coach).
- Workflow templates and spec scaffolds.
- Rep-risk zoning logic.

### Org Context (swappable)
Contains everything that *does* change from org to org:
- Positioning, value props, propositions.
- ICP definitions, target account lists.
- Competitors and competitive angles.
- Content library (case studies, one-pagers, decks).
- Tone of voice per channel.
- Pricing and commercial terms.
- Connector bindings (CRM, email, SharePoint/Drive, LinkedIn).

## Contract between them

BD Core never hardcodes org-specific data. It queries Org Context through a thin, versioned contract. See `/core/context-contract.md`.

Rule of thumb: Org Context holds no process. BD Core holds no positioning. If either side violates this, fix it.

## Adding a new org

Create `contexts/<org-slug>/` with the required surfaces (see `contexts/<org>/` for shape). Nothing in BD Core changes. That's the portability test.

## Spec / skill / agent relationship

- A **spec** (`specs/`) defines *what* a workflow must do — intent, inputs, process, outputs, acceptance criteria, rep-risk zone.
- A **skill** (`skills/`) implements *how* — prompt, tools, logic. Multiple skills may implement one spec (e.g., quick draft vs. deep research variant).
- An **agent** is an archetype applied to a spec/skill bundle at runtime.

## Versioning

Specs and language are versioned. Breaking changes to the contract require bumping a version and updating every Org Context. Internal improvements inside a skill don't.

## What this repo is not

- Not org-specific. ExampleOrg is one Org Context inside it.
- Not a CRM. It consumes the CRM through a connector, it does not replace it.
- Not a final answer — it's v0.1, designed to evolve.
