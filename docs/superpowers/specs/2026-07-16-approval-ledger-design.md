# Design — Governed autonomy: the approval ledger, the outreach skill, and the review surface

Date: 2026-07-16
Status: approved, not yet implemented
Branch: `approval-ledger` (merge base: the Python spine PR)

## The problem

The framework's pitch is *governed* autonomy: "autonomy is **earned** by sustained
approval metrics, never assumed." `docs/decisions.md` specifies the mechanism
precisely — Decision 1's auto-graduation rule (≥90% approval and <10% word-edit-rate
over 30 consecutive runs) and cross-cutting principle 1 ("every Draft→Approve run
logs: approved? edited? edit-distance? rejection reason?").

None of it exists. There is no approval log, no edit-rate capture, no graduation
computation. The single claim that separates this framework from a prompt pack is
entirely on paper.

### Why the ledger alone is not enough

An audit of the tree found the meter would have nothing to measure:

| Spec | Rep-risk zone | Skill exists? |
|---|---|---|
| account-research | Autonomous | yes |
| prospect-sourcing | Autonomous | yes |
| outreach-drafting | **Draft→Approve** | **no** |
| discovery-call-prep | **Draft→Approve** | **no** |

The two workflows that need approval logging have no skills; the two that have
skills do not need it. No skill writes to the `contexts/<org>/outreach/` or
`/prep/` artifact paths. A ledger shipped today would log nothing, and a review
dashboard would list a permanently empty queue.

Therefore this design builds the **workflow and its meter together**: roadmap C4
(the one deep outreach skill) is the first real Draft→Approve workflow, and it is
instrumented from birth.

## Goals

1. A Draft→Approve workflow that actually exists (roadmap C4).
2. Every approval decision on it is captured — automatically, where the decision happens.
3. Decision 1's graduation rule is computed from that data and reported.
4. A single review surface for pending drafts.

## Non-goals

- **Mobile / email notifications** (named in Decision 1). Needs hosting infrastructure;
  a separate concern from the metric.
- **Auto-graduation.** The tool reports eligibility. A human flips a rep-risk zone.
  Granting autonomy from a metric, silently, is the exact failure the framework exists
  to prevent.
- Instrumenting the Autonomous workflows (account-research, prospect-sourcing). They
  have no approval step. Spot-check sampling is a follow-up.

## Design

### 1. The outreach skill (roadmap C4)

New `skills/outreach-drafting/SKILL.md`, implementing the existing
`specs/outreach-drafting.spec.md` (path per `core/path-conventions.md`:
`skills/<spec-id>/SKILL.md`).

- **Inputs**: Account, Contact, `purpose ∈ {cold, warm, re-engage, event}`, channel.
  Warmth/purpose is an input, not four separate skills.
- **Contract-native from birth**: reads `context.positioning`, `context.tone(channel)`,
  `context.content`, `context.icp`. No raw context paths, no hardcoded language,
  no pitch prose — it must pass `bd check seam` with no baseline entry.
- **Output**: an OutreachSequence draft at
  `contexts/<org>/outreach/<account-slug>-<contact-slug>-<seq-id>.md`, the path already
  declared in path-conventions and, until now, written by nothing.
- **Zone**: Draft→Approve, as the spec declares.

**Retires the four colliding trigger surfaces** — `bd-email`, `cold-email`,
`email-sequence`, `event-invite` — per roadmap C4. Deleted; content preserved in git
history. Of the four, only `event-invite` carries a seam-baseline entry (`org-name`);
it is removed in the same change and the baseline regenerated.

### 2. The ledger

Append-only JSONL at `contexts/<org>/ledger/approvals.jsonl`. It is org-specific
operational data, so it lives behind the seam and is already gitignored by the
`contexts/*` rule — the same treatment as the generated artifacts alongside it.

One line per decision:

```json
{"ts": "2026-07-16T10:22:01Z", "spec": "outreach-drafting", "spec_version": "v0.1",
 "run": "acme-jane-001", "outcome": "approved", "edit_rate": 0.08,
 "reason": null, "zone": "Draft→Approve"}
```

- **Append-only.** It is an audit log (cross-cutting principle 6). Never rewritten,
  so a bad track record cannot be quietly laundered.
- `outcome ∈ {approved, rejected}`. "Edited" is **derived** (`edit_rate > 0`), not a
  third state — one less thing to keep consistent.
- `run` is a label, not a file path. The approval moment is conversational; the draft
  may never be a file.
- `spec_version` and `zone` are **stamped by the tool** from the spec's header
  (`specs/<spec-id>.spec.md`), never supplied by the caller. The caller passes
  `--spec`; the framework's own contract decides the rest. A metric a caller can
  self-report is a metric a caller can flatter.

**What a run is.** One row = one decision. A draft only becomes a run when a decision
is made, so abandoned drafts are not runs (and cannot dilute an approval rate). A
redraft after a rejection is a **new** run with a new seq-id, not an amendment of the
old one — so the rejection stays on the record.

**Two decisions on one run id are guarded twice, not left to "both count."**
`ledger.append` is a **write-time duplicate guard**: it refuses to log a second
decision against a run that already has one, so under normal operation one run
produces exactly one row. That guard is check-then-act with no lock, so two
concurrent `bd log-approval` calls on the same run can still both land (reproduced).
For that race, and for a hand-edited or legacy ledger that predates the guard, the
*read* side — `graduation._distinct_runs` — is a **first-wins distinct-run window**:
it dedupes by run id, keeping the earliest decision. A later row can never supersede
an earlier verdict on the same run, so an approval appended after a rejection cannot
launder it out of the graduation window, even though the rejection is still
physically in the file.

**A malformed ledger line is a blocking error, not a skipped line.** Silently ignoring
an unparseable row would change a safety metric without telling anyone — the exact
"silent fallback" cross-cutting principle 5 forbids. `graduation-status` refuses to
compute over a corrupt ledger rather than quietly computing over part of one.

### 3. Capture — the part that makes it real

A metric that depends on a human remembering a CLI command will not be collected, and
partial data is worse than none: wins get logged, rejects get forgotten, and
graduation is then granted on biased evidence. That would be a safety regression
wearing a safety feature's clothes.

So capture is a **step in the skill**, not a chore for the operator. The outreach
skill's final step calls `bd log-approval` at the moment the BDOwner approves, edits,
or rejects. The runtime is Claude; Claude is already present at that moment and does
the logging.

### 3b. CLI surface

```
bd log-approval <run> --spec <spec-id> --outcome approved|rejected
                      [--before FILE --after FILE | --edit-rate FLOAT]
                      [--reason TEXT]
bd graduation-status [spec-id]
bd review [--port N]
```

- `--spec` is required; `spec_version` and `zone` are read from that spec's header.
- `--before/--after` computes the edit rate (the default path); `--edit-rate` supplies
  it directly. Both given is an error — two sources of one number.
- `--reason` is **required for `rejected`** (principle 1 asks for a rejection reason)
  and rejected with `--edit-rate`, which is meaningless for a reject.
- Unknown spec, or a spec whose file is missing, is a blocking error — never a guess.

### 4. Metrics

Over the last N runs of a spec:

- **Approval rate** = (approved) / (approved + rejected). An edited-and-sent draft is
  approved; heavy editing is caught by the separate edit-rate gate, not by this one.
- **Edit rate** = mean `edit_rate` over approved runs. Rejected runs have no meaningful
  edit distance and are excluded.
- **Word-edit-rate** is computed by the tool from the before/after texts when both are
  available (the default), or supplied explicitly via `--edit-rate` when the edit
  happened elsewhere. One definition, in one place.

**`mean` is an interpretation, and it has a known blind spot.** Decision 1 says
"<10% word-edit-rate" without saying how to aggregate. Mean is the plain reading and
what this design implements — but it can mask an outlier: 29 untouched drafts and one
total rewrite average to ~3% and pass the gate. Recorded here so the choice is visible;
if it bites, a percentile gate is the fix, and the raw per-run rates are in the ledger
to recompute against.

**Two different edit-rate thresholds exist and must not be confused:**

| Threshold | Source | Meaning |
|---|---|---|
| **<10%** | Decision 1 | the *graduation bar* — sustained, over 30 runs |
| **<25%** | `specs/outreach-drafting.spec.md` | the *per-draft quality goal* for a single draft |

They are not in conflict. The ledger names which is which so no one wires the wrong one.

### 5. Graduation

`bd graduation-status [spec]` evaluates Decision 1's bar — ≥90% approval **and**
<10% edit rate over the **last 30 consecutive runs** — per spec, and reports one of:

- `eligible` — the bar is met; a human may promote the zone.
- `not yet` — with the failing metric named.
- `insufficient data (n/30)`.

It **reports only**. It never edits a spec or flips a zone.

**New decision required — the version-bump window.** A spec version bump makes it a
materially different workflow; counting v0.1 runs toward graduating v0.2 would grant
autonomy on evidence from something else. **The 30-run window resets on a spec version
bump.** This is recorded in `docs/decisions.md`, not buried in code.

### 6. The review surface

`bd review` serves a dashboard bound explicitly to `127.0.0.1` (stdlib `http.server`,
no new dependency) and opens a browser. It renders unsent drafts to real prospects and
appends to an audit log, so it binds to loopback only — never `0.0.0.0` — and is not
an authenticated surface meant to be exposed.

- **Pending** = an artifact under a Draft→Approve spec's output dir with no ledger
  entry for its run id. Derived — no queue to maintain, no state to sync. This only
  works because §1 ships a skill that actually writes those artifacts. A redraft is a
  new seq-id (see "What a run is"), so it reappears as pending; a decided draft never
  does.
- Each pending draft renders its content with three actions: **Approve**,
  **Edit-and-approve** (a textarea; the diff against the original *is* the edit rate),
  **Reject** (reason required).
- Posting a decision appends to the ledger.
- A panel per workflow shows graduation status.

A local server is the only honest way to deliver Decision 1's "inline approve /
edit-and-approve / reject" write-back without a hosted backend. **Decision 1 is
amended** to record that the v0.2 surface is a local server rather than a hosted
dashboard, and that notifications are deferred.

### 7. Zone discovery

Every spec already declares `**ID**`, `**Version**` and `**Rep-risk zone**` in a
consistent header block. The specs are parsed for these — the spec is the contract,
and the ledger reads the zone from it rather than from an invented registry. This is
the SDD claim doing real work.

## Testing

pytest with fixtures, no TestCase classes, per the existing suite.

Load-bearing cases:
- word-edit-rate arithmetic, including the empty/identical/total-rewrite edges
- approval-rate arithmetic; rejects excluded from the edit-rate mean
- the 30-run window boundary (29 vs 30 vs 31 runs; only the *last* 30 count)
- eligible / not-yet / insufficient-data verdicts, each triggered by one failing metric
- window reset on a spec version bump
- ledger append-only-ness; a malformed line does not destroy the log
- pending = artifact minus ledger entry
- zone parsed from a spec header
- dashboard POST round-trip appends exactly one correct row

## Risks

- **The ledger's shape becomes a de-facto contract before any real data exists.** It is
  cheap to change while the JSONL is empty and expensive afterwards. Mitigation: keep
  the record thin; let real usage add fields.
- **The graduation rule is unproven.** ≥90%/<10%/30 runs was set as a v0.1 working
  assumption with no data behind it. Reporting (not enforcing) keeps the cost of a
  wrong threshold low.
- **Deleting four skills is destructive** and sanctioned by roadmap C4. Content remains
  in git history.

## Docs to update in the same change

- `core/path-conventions.md` — add the ledger path.
- `docs/decisions.md` — the version-bump window rule; amend Decision 1 (local server,
  notifications deferred).
- `docs/roadmap.md` — tick C4; note the C5 overlap (`email-sequence`, `cold-email` were
  on C5's list and are now retired).
- `README.md` — the governed-autonomy loop, and how to run it.
