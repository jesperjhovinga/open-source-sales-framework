---
name: handoff
description: Compact the current conversation into a handoff document so a fresh session can continue the work without losing context. Use at the end of a long session, or when switching focus. Optionally pass an argument describing what the next session will focus on.
---

Write a handoff document summarising the current conversation so a fresh session can pick up the work.

## What to include

- **Current state**: where things stand right now
- **What was decided**: key decisions made and why
- **What's next**: concrete next steps, in priority order
- **Open questions**: anything unresolved that the next session should address
- **Suggested skills**: which skills the next session should invoke (e.g. `/grill-with-docs`, `/to-prd`)
- **References**: paths or links to relevant files, docs, PRDs — don't duplicate content already captured elsewhere

## What to exclude

- Sensitive information (API keys, passwords, personal data)
- Content already fully captured in other documents — reference those instead

## Tailoring

If the user passed an argument describing what the next session will focus on, tailor the handoff doc to that focus — emphasise what's most relevant, de-emphasise the rest.

Save the handoff document as a `.md` file in the current workspace.
