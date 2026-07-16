# Decisions & Defaults — v0.1

Resolved 2026-04-28 with AI-first, autonomy-leaning best-practice defaults. Each decision is a working assumption with explicit "When to revisit" triggers. Surface a contradiction in implementation? Bring it back here, don't quietly drift.

---

## Decision 1 — Review surface for Draft→Approve

**Q**: Where does the BDOwner review drafts?

**Decision**: Single approval surface — an interactive dashboard (HTML artifact) listing all pending drafts. Inline approve / edit-and-approve / reject. Mobile + email notifications when items land. No reviewing in chat, email threads, or scattered tools.

**Why**: One scan place. Structured feedback (diff + reason) becomes Reviewer training data. Scales as workflows multiply. Same surface displays auto-approved items for spot-check as autonomy grows — no UX rebuild needed.

**Auto-graduation rule**: when a workflow type sustains ≥90% approval and <10% word-edit-rate over 30 consecutive runs, it graduates from Draft→Approve to Autonomous-with-spot-check (10% sample).

**Revisit when**: dashboard ships and meets ≥3 weeks usage. Reconsider Slack/Teams notifications if email feels too slow.

**Amendment (v0.2)**: the review surface ships as `bd review` — a dashboard served
on loopback by the CLI, not a hosted app. Same page, same three actions, and the
structured feedback still lands in the ledger. Mobile and email notifications are
**not** built: they need hosting infrastructure and are a separate concern from the
metric. The auto-graduation rule is computed and **reported** by
`bd graduation-status`; it never flips a zone. Promotion stays a human act.

---

## Decision 2 — Source citation format

**Q**: URL only, or quote + URL?

**Decision**: Structured citation = short quote (≤25 words) + URL + retrieval timestamp. Format: `(cite: "quote" — URL, retrieved YYYY-MM-DD)`.

**Why**: Auditability (verify any claim). Auto-staleness via timestamp. Faster human read — quote tells you what the source said before clicking.

**Revisit when**: dossier output gets noisy. Consolidate to one citation block per paragraph if so.

---

## Decision 3 — AccountDossier refresh cadence

**Q**: Schedule, or manual?

**Decision**: Hybrid, signal-driven.
- Active Accounts (open Opportunity or touch in last 30 days) → full re-research weekly.
- Watching list (target accounts not yet engaged) → light delta-check weekly.
- Signal triggers (news, leadership change, funding round, buying-signal job posting) → immediate refresh, regardless of schedule.
- Manual retrigger always available.

**Why**: Pure schedule wastes runs on dormant accounts. Pure manual misses signals. Signal-driven matches the AI-first instinct: agent does the watching, not the human.

**Revisit when**: after first month of running. If signal triggers fire too often (noise) or too rarely (missed events), tune.

---

## Decision 4 — LinkedIn send mechanism

**Q**: Hand-send vs. semi-automated.

**Decision**: Hand-send in v0.1. Agent prepares the message and opens a one-click deeplink to the Contact's DM. BDOwner action: paste + send. No ToS-violating automation.

**Why**: ToS compliance is non-negotiable. One-click design preserves the autonomy trajectory: when policy/tooling allows compliant automation, the spec doesn't change — only the connector.

**Revisit when**: a compliant LinkedIn connector lands (Sales Nav API, MCP, etc.).

---

## Decision 5 — Multithreading

**Q**: Multi-contact sequences in v0.1, or single-threaded?

**Decision**: Single-threaded in v0.1. Multithreading lands in v0.2.

**However**: model the data structures for multi-threading from day one. Account has many Contacts, each Contact has independent OutreachSequence state, agent's planning view sees the Account as a stakeholder graph.

**Why**: Faster v0.1 ship and easier to evaluate quality. Multi-thread adds cross-message-consistency complexity — Reviewer needs to evolve before that works. WbD/Bowtie strongly favors multi-thread, so v0.2 is mandatory not optional.

**Revisit when**: v0.1 outreach quality is proven on single-thread (≥70% approval rate sustained 4 weeks).

---

## Decision 6 — Calendar connector

**Q**: Google or Outlook?

**Decision**: Abstract behind `context.connector("calendar")`. Each Org Context binds its own provider. ExampleOrg instance: Microsoft 365 (assumed — confirm if different).

**Why**: BD Core stays portable. Each Org binds to whatever its BDOwner uses.

**Revisit when**: never at Core level. Org-level binding is trivially swappable.

---

## Decision 7 — Connector access scope and auth

**Q**: How are connectors scoped per Org Context?

**Decision**: Per Org Context, declared in `contexts/<org>/connectors.md`. Each entry specifies:
- Provider (e.g., `microsoft-365`, `hubspot`, `linkedin-sales-nav`).
- Auth model (OAuth2 with named scopes preferred; PAT for one-off cases).
- Read scopes (default).
- Write scopes (explicit allowlist — no implicit writes).
- Rate limits / quotas if relevant.
- Fallback / failure mode (skip, retry, notify).

**Why**: Write scopes are the autonomy gate. Explicit allowlisting means no surprises. Per-Org scoping = no shared connectors across orgs (data isolation).

**Revisit when**: first write-capable connector ships (e.g., CRM activity logging). That's when discipline matters most.

---

## Decision 8 — Spec implementation runtime

**Q**: Claude skills, wrapper library, or both?

**Decision**: Claude skills, packaged as a Claude Code plugin. Skill files in `skills/<spec-id>/SKILL.md`, agent personas as markdown, the whole bundle installable in any Claude Code session. No wrapper library in v0.1.

**Why**: Lowest friction. Native to the BDOwner's environment. Trivially version-controlled (already in Git). Same plugin loads in any Org Context — only `contexts/<org>/` swaps. AI-first by definition: the runtime *is* Claude.

**Plugin shape**:
- `.claude-plugin/plugin.json` at repo root.
- `skills/<spec-id>/SKILL.md` for each implemented spec.
- Agent personas (Researcher, Drafter, Reviewer, etc.) referenced by skills.

**Revisit when**: a real cross-runtime requirement appears (e.g., embedding agent in a non-Claude product).

**Amendment (v0.2)**: still true — the runtime *is* Claude, and skills remain the
implementation of every spec. `src/bdcore/` is not a second runtime and implements
no workflow: it holds the deterministic work that has an objectively right answer
(parse a JSON export, check a card's shape, grep for seam residue) and that a
language model should not be re-deriving per call. Skills invoke it via the `bd`
CLI. If a thing requires judgement, it belongs in a skill, not in `bdcore`.

---

## Decision 9 — Context surface read mechanism

**Q**: Direct file reads or wrapper?

**Decision**: Direct file reads in v0.1, against a documented path convention captured in `core/path-conventions.md`. Markdown-as-API.

**Why**: Simplest thing that works. A wrapper library is premature.

**Revisit when**: agent needs typed access (e.g., structured ICP filters as objects). At that point, formalize as a Python or Node module wrapping the file reads.

**Amendment (v0.2)**: the revisit trigger fired. The `headline_prefilter` JSON
block in `context.icp` is exactly the "structured ICP filters as objects" case
this decision named, and `bd source` needs typed access to it. The resolver is
now `src/bdcore/context.py`, wrapping the same file reads against the same
convention.

Markdown-as-API is unchanged: surfaces are still markdown, still authored by
hand, still readable by an agent doing a direct file read. The wrapper is for
*code* that needs a surface, and it exists because the resolution rules —
active-org lookup, Rule 3 fail-loud, Rule 5 UNFILLED-is-missing — were being
reimplemented ad hoc inside a sourcing script, where they were untestable and
would have been copy-pasted into the next script that needed them. One
implementation, covered by tests. Agents reading surfaces directly is still
correct and still the common case.

---

## Decision 10 — Versioning

**Q**: Semver, date-based, other?

**Decision**:
- **Context contract**: semver. `v0.1.0` today. Breaking changes bump major.
- **Specs**: `vMAJOR.MINOR` per spec. **MAJOR** bumps for any behavioural change —
  acceptance criteria, process, or output shape — and resets the workflow's Decision 1
  graduation track record; this holds **even at 0.x** — semver's usual convention that
  0.x changes are exempt from breaking-change discipline does not apply here, because
  Decision 1 evidence must never silently carry across a behavioural change. **MINOR**
  bumps only for an editorial change (wording, a typo, an example) where behaviour is
  identical, and evidence carries over.
- **Repo releases**: date-tagged for milestones (`v2026.04.28`).

**Why**: Contract is the load-bearing API; semver makes breaking changes visible and forces every Org Context to update on bumps. Specs are working documents, but MAJOR/MINOR still has to be unambiguous because Decision 1's graduation evidence hangs on it. Date tags = handoff/rollback markers.

**Revisit when**: first breaking contract change ships (forces real semver discipline).

**Amendment (v0.2)**: the original Decision text above has been edited in place —
it originally said specs used a "lightweight version field... bumped when
acceptance criteria or process changes," with no MAJOR/MINOR distinction. That
wording could not tell a wording fix from a behavioural change, so a spec
author had no way to say "nothing behavioural happened here," and — because
every spec in this repo sits at `v0.1` — it invited the unsafe default of
bumping straight to `v0.2` for a real behavioural change, silently carrying
graduation evidence that should have reset. This is why Decision 11 could be
rewritten to stop resetting the graduation window on every bump: MAJOR/MINOR
gives it a real distinction to key on.

---

## Decision 11 — Graduation window and a spec version bump

**Q**: When a spec's version bumps, do its previous runs still count toward the
Decision 1 graduation bar?

**Decision**: Depends on the kind of bump (Decision 10, v0.2 amendment). The
30-run window is keyed on `(spec, MAJOR)`. A **MAJOR** bump resets it — a new
major version is a materially different workflow. A **MINOR** bump does not —
the workflow's behaviour is unchanged, so its evidence carries over.

**Why**: Decision 1's bar exists to earn autonomy on real evidence. Resetting on
every bump (the original v0.1 rule) counted a typo fix as a new workflow and
threw away a nearly-graduated track record for no behavioural reason — the
mirror-image failure of counting v0.1's evidence toward a materially different
v0.2. Keying on MAJOR gets both right: an editorial fix doesn't cost 30 runs,
and a real behaviour change still starts its own clock.

**Revisit when**: an author bumps MAJOR out of caution for a change that was
really editorial (losing evidence they didn't need to lose), or bumps MINOR for
a change that turns out to be behavioural (hiding a change graduation should
have reset on). Either observed in practice means the MAJOR/MINOR line needs
tightening, not just trusting the author's judgement call.

Also note: every spec in this repo currently sits at `v0.1`. The first
behavioural change to any of them must bump to `v1.0`, not `v0.2` — `v0.2` is
reserved for an editorial-only change. Treating `v0.2` as available for a
spec's first behavioural change is exactly the unsafe default Decision 10's
amendment exists to close off.

---

## Cross-cutting principles for autonomy

These aren't decisions about specific questions. They're the guardrails that make AI-first execution safe and trustworthy as autonomy expands.

1. **Approval rate + edit rate are first-class metrics.** Every Draft→Approve run logs: approved? edited? edit-distance? rejection reason? This dataset auto-graduates workflows toward Autonomous.

2. **Reviewer learns continuously.** Every reject and every >25% edit becomes Reviewer training material. The Reviewer archetype's prompt evolves over time on this signal.

3. **Confidence thresholds gate autonomy.** A workflow's rep-risk zone is not static. Track its track record, apply confidence thresholds, escalate to higher autonomy when earned. Demote if quality regresses.

4. **Eval harness ships in v0.1.** Each spec gets a `tests/<spec>.cases.md` with sample inputs and expected acceptance-criteria results. Scheduled task runs the harness. Quality regressions block promotion.

5. **No silent fallbacks.** When a context surface is missing or a connector fails, the agent fails loud — not "best effort." Loud failures preserve trust as autonomy grows.

6. **Audit log per artifact.** Every produced artifact (Dossier, OutreachSequence, PrepDoc) carries metadata: which spec version, which context version, sources cited, decisions made, run timestamp. Auditability is the price of autonomy.

7. **Identity attribution on writes.** Every external write (CRM activity, email, Drive file) is attributed "by AI agent on behalf of <BDOwner>." Governance + future audit.

8. **Token / cost budget per workflow.** Each spec declares an upper-bound token cost. Runs that exceed flag to the BDOwner and pause. Prevents runaway autonomy from being economically harmful.
