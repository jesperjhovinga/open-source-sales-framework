# CLAUDE.md — Open Source Sales Framework

You are working on a markdown-based BD automation framework. "Module" here means
a skill, spec, or context surface — not code.

## Read first, in order
1. `README.md`, then `docs/architecture.md`
2. `core/language/glossary.md` — the ubiquitous language. No new term enters a
   spec or skill without entering the glossary first.
3. `core/context-contract.md` + `core/path-conventions.md` — the seam.
4. `docs/decisions.md` — settled decisions. Do not re-litigate without flagging.
5. `docs/roadmap.md` — current build priorities.

## Hard rules
- **The seam is law.** BD Core (`core/`, `specs/`, `skills/`) never contains
  org-specific content: no company names, no language defaults, no geography
  rules, no pitch prose. Those live in `contexts/<org>/` and are read via the
  contract surfaces. If you find residue, extracting it IS the task.
- **Active org** is whatever slug `ACTIVE_CONTEXT.md` names. Missing or
  unfilled surface (STATUS: UNFILLED) = blocking error. Fail loud, never guess.
- **Never commit a real org context.** Only `contexts/_template/` and
  `contexts/example-corp/` belong in git (enforced by .gitignore — don't weaken it).
- **Docs must not lie.** If you change behavior, update README/STATE/specs in
  the same commit. Claims about files that don't exist are bugs.
- **Verify before claiming.** Re-read the file / run the script before stating
  a count, a fix, or a finding. This repo once shipped a false audit finding.

## How to work (orchestrator + subagents)
Run as orchestrator; delegate breadth work. Suggested split:
- **Explore subagent** — repo sweeps: trigger-overlap checks, residue grep,
  consistency audits. Cheap, read-only, use liberally before any refactor.
- **General-purpose subagents** — one per roadmap candidate; they draft the
  refactor in place, you review the diff against the seam rules above.
- **Review pass** — before any commit claiming a candidate is done, spawn a
  fresh subagent to verify acceptance criteria with no context from the build
  agent (avoid self-grading).
Commit in small reviewable steps, one candidate at a time, referencing the
roadmap item in the commit message.
