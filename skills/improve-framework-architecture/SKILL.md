---
name: improve-framework-architecture
version: "0.1.0"
description: Surface architectural friction in the BD Automation Framework and propose deepening opportunities — refactors that turn shallow skills/context-surfaces into deep ones, sharpen the Core/Org-Context seam, and reduce duplication. Use when the user wants an architectural review, wants to improve or refactor the framework, find overlap between skills, make the framework more portable, or decide what to consolidate before a rewrite. Adapted from mattpocock/skills improve-codebase-architecture for a skill/spec/context framework rather than a codebase.
origin: improve-codebase-architecture (mattpocock/skills), adapted for the BD framework
---

# Improve Framework Architecture

Surface architectural friction and propose **deepening opportunities** — changes that turn shallow skills and context-surfaces into deep ones. The aim is portability, commercial flexibility, and an agent that can navigate the framework without thrashing. This framework is markdown (skills, specs, context files), not code — so "module" means a skill, a context surface, or a spec, never a function or class.

This is the engine for the architectural-review layer. It is *informed* by the framework's own documents: the domain glossary (`core/language/glossary.md`) names the good seams; the decisions (`docs/decisions.md`) record choices the review should not re-litigate.

## Vocabulary

Use these terms exactly — consistent language is the point. Full definitions and the mapping from the code-world originals are in `references/architecture-language.md`.

- **Module** — anything with an interface and an implementation. Here: a **skill**, a **context surface**, or a **spec**.
- **Interface** — everything a caller must know to use the module. For a skill, that's its `description` (the trigger) plus the inputs it expects; for a surface, its contract signature (`context.tone(channel)`).
- **Implementation** — the SKILL.md body, the context file content, the spec process.
- **Depth** — a lot of BD capability behind a small, clear interface. **Deep** = high leverage. **Shallow** = the trigger/description is nearly as complex as what the skill actually does, or the skill is a thin pass-through.
- **Seam** — where an interface lives and behaviour can be swapped without editing in place. The **context contract** is this framework's defining seam: swap the Org Context, get a new company. (Use "seam", not "boundary".)
- **Adapter** — a concrete thing satisfying a surface at the seam. An **Org Context instance** (`contexts/<org>/`) is an adapter for every surface.

Key principles (see the reference for the rest):

- **Deletion test** — imagine deleting the module. If complexity vanishes, it was a pass-through (e.g. an email skill that overlaps two others). If complexity reappears across many invocations or callers, it was earning its keep.
- **The interface is the trigger surface.** If two skills compete at trigger time, their interfaces overlap — that's shallowness at the seam.
- **One adapter = hypothetical seam. Two adapters = real seam.** The framework claims portability but has one Org Context (ExampleOrg). The seam isn't proven real until a second adapter exists — which is why a blank `contexts/_template/` matters.

## Process

### 1. Explore

Read `core/language/glossary.md` and the relevant `docs/decisions.md` entries first, so you use the framework's own names and don't re-open settled decisions.

Then walk the framework — use the `Explore` subagent for breadth. Don't follow rigid heuristics; note where you feel friction:

- Where does one BD task require bouncing between several skills (no **locality**)?
- Which skills are **shallow** — the description nearly restates the body, or they're thin pass-throughs?
- Where do skills overlap at trigger time (the same intent triggers two)?
- Where is org-specific content leaking across the Core/Org-Context **seam** (person/company names in portable skills)?
- Where is the same content (voice rules, proposition names) duplicated across modules rather than living behind one surface?

Apply the **deletion test** to anything that smells shallow: would deleting it concentrate complexity, or just move it?

### 2. Present candidates as a report

Write a self-contained report to the OS temp / outputs directory — **never into the repo** — named `architecture-review-<timestamp>.md` (or `.html` if a visual before/after helps; keep any HTML self-contained, no build step). Tell the user the absolute path.

For each candidate:

- **Modules involved** — which skills / surfaces / specs.
- **Friction** — why the current shape causes pain (use glossary vocabulary for the domain, the vocabulary above for the architecture).
- **Deepening** — plain-English description of the change.
- **Benefits** — in terms of **leverage** (what callers/invocations gain), **locality** (what maintainers gain), and **portability/commercial flexibility** (does it sharpen the seam?).
- **Before / after** — a simple sketch of the shallow shape and the deepened one.
- **Strength** — `Strong` / `Worth exploring` / `Speculative`.

If a candidate contradicts a `docs/decisions.md` entry, surface it only when the friction is real enough to reopen the decision, and flag it clearly. Don't list every refactor a decision forbids.

End with a **Top recommendation**: what you'd tackle first and why. Do NOT design the new interfaces yet — ask the user which candidate to explore.

### 3. Grill the chosen candidate

Once the user picks one, drop into a grilling conversation — use the existing `grill-with-docs` skill, which already challenges a plan against this framework's language and decisions and updates `glossary.md` / `docs/decisions.md` inline. Walk the design tree: constraints, what sits behind the seam, which skills collapse or deepen, what the new interface looks like.

Side effects happen inline as decisions crystallise (same discipline as `grill-with-docs`):
- Naming a deepened module after a concept not in `glossary.md`? Add the term (new terms enter the glossary before use — the framework's own rule).
- The user rejects a candidate with a load-bearing reason a future review would need? Offer to record it in `docs/decisions.md` so the next architecture pass doesn't re-suggest it.

## Commercial-flexibility lens

This framework exists to optimise GTM, not to be technically pure. Weigh every deepening against: *does this preserve or increase commercial flexibility* — the ability to re-target a proposition, segment, channel, or org cheaply? Prefer changes that strengthen the Org-Context seam and keep the Core lean. Be skeptical of refactors that add runtime weight or lock in one GTM motion, even if they're technically elegant.

## Composes with

- **grill-with-docs** — the grilling loop in step 3.
- **bd-skill-evolution** — a confirmed architectural learning becomes a proposed update there.
- **verification-before-completion** — verify each finding against the actual files before putting it in the report (this skill's own audit once shipped a false finding for lack of that).
