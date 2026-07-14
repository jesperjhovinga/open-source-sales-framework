# BD Automation Framework

An open, portable framework for automating 80–90% of a Business Development workflow with AI agents — under explicit human control rules.

Built on DDD + SDD principles: a shared written vocabulary (ubiquitous language) that humans and agents both use, and versioned workflow specs that act as the contract between them.

## Why

BD is pattern-heavy. Research accounts, write outreach, prep calls, summarize conversations, chase commitments, update records. The *process* shape is the same across companies. The *content* (positioning, ICP, tone of voice) is not. This framework separates the two: drop it into any organization and only the org-context layer changes — the machinery doesn't.

## Core ideas

- **Two bounded contexts.** BD Core (portable: language, methodology, specs, skills, agent archetypes) and Org Context (swappable: positioning, ICP, tone, competitors, content, pricing, connectors). Core never hardcodes org data; it reads it through a thin, versioned contract (`core/context-contract.md`).
- **Rep-risk zoning.** Every workflow is classified Autonomous / Draft→Approve / Agent-supports / Human-only. Anything a prospect sees requires human approval; autonomy is *earned* by sustained approval metrics, never assumed.
- **Spec-Driven Development.** A spec defines *what* a workflow must do (inputs, process, outputs, acceptance criteria, risk zone); a skill implements *how*. Specs live in `specs/`, skills in `skills/`.
- **Domain-Driven Design.** No term enters a spec without entering the glossary (`core/language/glossary.md`) first.
- **Governance built in.** Cited claims with timestamps, fail-loud on missing context, explicit write allowlists, agent actions attributed to the human owner.

## Repo map

- `core/` — ubiquitous language, context contract, path conventions. Portable.
- `contexts/_template/` — blank org-context adapter: copy, fill, go. `contexts/example-corp/` — fully filled fictional demo adapter. Real org contexts are gitignored and never committed.
- `ACTIVE_CONTEXT.md` — names the active org slug; all context reads resolve against it.
- `specs/` — workflow specs, one per automated workflow.
- `skills/` — skill implementations (account research, prospect sourcing, outreach, call prep, call notes → CRM, governance and meta-skills).
- `docs/` — architecture, decisions with rationale, task inventory, and a full self-audit.

## Methodology

**Winning by Design** is the backbone: SPICED for discovery, the Bowtie funnel for stages.

## Getting started

1. Try it as-is: `ACTIVE_CONTEXT.md` points at `example-corp`, a fictional demo org — run the account-research skill against any public company to see the flow.
2. Make it yours: copy `contexts/_template/` to `contexts/<your-org>/`, fill every surface (positioning, ICP, tone of voice, competitors, content, pricing, connectors), set `ACTIVE_CONTEXT.md` to your slug.
3. Start with three workflows: account research (Autonomous), outreach drafting and call prep (Draft→Approve).
4. Log approval/edit rates from day one — they drive autonomy graduation. See `docs/roadmap.md` for where the framework is heading.

## License

MIT — see `LICENSE`.

## Author

Jesper Hovinga. End responsibility stays human. Agent execution where the zoning permits.
