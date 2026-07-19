---
name: grill-with-docs
description: Grilling session that challenges a plan against the existing domain model, sharpens terminology, and updates CONTEXT.md and ADRs inline as decisions crystallise. Use when stress-testing a plan against an existing project's language and documented decisions — ideal for BD Automation Framework development sessions.
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one by one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback before continuing.

If a question can be answered by reading existing files in the project, read them instead of asking.

## Domain awareness

Look for existing documentation in the project:

- `core/language/glossary.md` — the ubiquitous language (not a spec, not implementation notes — just terms)
- `docs/decisions.md` — settled decisions, with the rationale, for hard-to-reverse choices

Create these files lazily — only when you have something to write.

## During the session

**Challenge against the glossary.** When I use a term that conflicts with an existing entry in `core/language/glossary.md`, call it out. "Your glossary defines X as Y, but you seem to mean Z — which is it?"

**Sharpen fuzzy language.** When I use vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

**Discuss concrete scenarios.** When domain relationships are being discussed, stress-test them with specific examples that probe edge cases.

**Update the glossary inline.** When a term is resolved, update `core/language/glossary.md` right there — don't batch these up.

**Offer ADRs sparingly.** Only offer to create an ADR when all three are true:
1. Hard to reverse — changing your mind later has real cost
2. Surprising without context — a future reader would wonder "why did they do it this way?"
3. The result of a real trade-off — genuine alternatives existed and one was chosen for specific reasons
