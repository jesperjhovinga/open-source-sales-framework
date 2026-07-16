# Governed Autonomy: Approval Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make "autonomy is earned by sustained approval metrics" real — ship the first Draft→Approve workflow (roadmap C4) instrumented from birth, an append-only approval ledger, Decision 1's graduation rule computed and reported, and a local review surface.

**Architecture:** Four new modules in the existing `bdcore` package: `specs.py` (parse spec headers for id/version/zone), `ledger.py` (append-only JSONL read/write + edit-rate maths), `graduation.py` (Decision 1's rule), `review.py` (stdlib localhost dashboard). Each is consumed by `cli.py`. Plus a markdown skill (`skills/outreach-drafting/SKILL.md`) that calls the CLI at the approval moment, retiring four colliding skills.

**Tech Stack:** Python 3.12, uv, typer, ruff (line-length 120), ty, pytest (fixtures, no TestCase classes), stdlib `http.server`/`difflib` — no new dependencies.

Design doc: `docs/superpowers/specs/2026-07-16-approval-ledger-design.md`

## Global Constraints

- **No new dependencies.** stdlib + typer (already present) only.
- **Fail loud, never guess.** A missing spec, unknown spec-id, or malformed ledger line is a blocking error (cross-cutting principle 5). Library code raises; `cli.py` is the only layer that prints and sets an exit code.
- **The seam is law.** New content in `skills/`, `specs/`, `core/` carries no org-specific data. The new skill must pass `bd check seam` with **no baseline entry**.
- **Docs must not lie.** Any doc claim about a path must be true when the commit lands, or the doc must be roadmap/audit/design (exempt).
- **The tool stamps `spec_version` and `zone`** from the spec header — never accepted from the caller.
- **Graduation reports; it never flips a zone.**
- **Ledger is append-only.** Never rewritten. Path: `contexts/<org>/ledger/approvals.jsonl` (gitignored via `contexts/*`).
- **`outcome ∈ {approved, rejected}`** only. "Edited" is derived (`edit_rate > 0`).
- Run `just ci` before every commit; it must pass (ruff + ty + pytest + seam + docs).
- Commit messages: conventional commits. **No AI attribution, no Co-Authored-By lines.**

---

### Task 1: Parse spec headers (id, version, zone)

Every spec declares `**ID**`, `**Version**`, `**Rep-risk zone**` in a header block. This makes the spec the registry — the ledger reads the zone from the contract rather than an invented config.

**Files:**
- Create: `src/bdcore/specs.py`
- Test: `tests/test_specs.py`

**Interfaces:**
- Consumes: `bdcore.context.find_root`, `bdcore.context.ContextError`
- Produces:
  - `class SpecError(Exception)`
  - `class Spec(NamedTuple): id: str; version: str; zone: str; path: Path`
  - `DRAFT_APPROVE = "Draft→Approve"` (exact string, note the U+2192 arrow)
  - `def load_spec(spec_id: str, root: Path) -> Spec` — raises `SpecError` if missing/unparseable
  - `def all_specs(root: Path) -> list[Spec]`
  - `def draft_approve_specs(root: Path) -> list[Spec]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_specs.py
import pytest

from bdcore.specs import DRAFT_APPROVE, Spec, SpecError, all_specs, draft_approve_specs, load_spec


@pytest.fixture
def specs_root(tmp_path):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "outreach-drafting.spec.md").write_text(
        "# Spec: Outreach Drafting\n\n"
        "**ID**: `outreach-drafting`\n"
        "**Version**: `v0.1`\n"
        "**Rep-risk zone**: Draft→Approve\n"
        "**Status**: draft\n",
        encoding="utf-8",
    )
    (tmp_path / "specs" / "account-research.spec.md").write_text(
        "# Spec: Account Research\n\n"
        "**ID**: `account-research`\n"
        "**Version**: `v0.2`\n"
        "**Rep-risk zone**: Autonomous\n",
        encoding="utf-8",
    )
    return tmp_path


def test_load_spec_reads_the_header(specs_root):
    spec = load_spec("outreach-drafting", specs_root)
    assert spec == Spec(
        id="outreach-drafting",
        version="v0.1",
        zone=DRAFT_APPROVE,
        path=specs_root / "specs" / "outreach-drafting.spec.md",
    )


def test_load_spec_reads_a_different_zone(specs_root):
    assert load_spec("account-research", specs_root).zone == "Autonomous"


def test_unknown_spec_fails_loud(specs_root):
    with pytest.raises(SpecError, match="no spec"):
        load_spec("does-not-exist", specs_root)


def test_spec_without_a_zone_fails_loud(specs_root):
    (specs_root / "specs" / "broken.spec.md").write_text("**ID**: `broken`\n", encoding="utf-8")
    with pytest.raises(SpecError, match="Rep-risk zone"):
        load_spec("broken", specs_root)


def test_spec_without_a_version_fails_loud(specs_root):
    (specs_root / "specs" / "nover.spec.md").write_text(
        "**ID**: `nover`\n**Rep-risk zone**: Autonomous\n", encoding="utf-8"
    )
    with pytest.raises(SpecError, match="Version"):
        load_spec("nover", specs_root)


def test_all_specs_finds_every_spec(specs_root):
    assert sorted(s.id for s in all_specs(specs_root)) == ["account-research", "outreach-drafting"]


def test_draft_approve_specs_filters_by_zone(specs_root):
    assert [s.id for s in draft_approve_specs(specs_root)] == ["outreach-drafting"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_specs.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bdcore.specs'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/bdcore/specs.py
"""Read a workflow spec's header — the spec is the registry.

Every spec declares its ID, Version and Rep-risk zone in a header block. The
ledger reads the zone from the spec rather than from a config someone has to
keep in sync: the spec is the contract (see docs/architecture.md).
"""

import re
from pathlib import Path
from typing import NamedTuple

# Exact string used in every spec header. The arrow is U+2192, not "->".
DRAFT_APPROVE = "Draft→Approve"

_FIELD = "^\\*\\*{field}\\*\\*:\\s*`?([^`\n]+?)`?\\s*$"


class SpecError(Exception):
    """A spec could not be found or parsed. Always a blocking error."""


class Spec(NamedTuple):
    id: str
    version: str
    zone: str
    path: Path


def _field(text: str, field: str, path: Path) -> str:
    match = re.search(_FIELD.format(field=field), text, re.MULTILINE)
    if not match:
        raise SpecError(f"{path} has no '**{field}**:' header line — cannot read the spec's contract")
    return match.group(1).strip()


def spec_path(spec_id: str, root: Path) -> Path:
    return root / "specs" / f"{spec_id}.spec.md"


def load_spec(spec_id: str, root: Path) -> Spec:
    """Read a spec's header. Missing or unparseable is a blocking error."""
    path = spec_path(spec_id, root)
    if not path.is_file():
        raise SpecError(f"no spec at {path} — unknown spec id '{spec_id}'")
    text = path.read_text(encoding="utf-8")
    return Spec(
        id=_field(text, "ID", path),
        version=_field(text, "Version", path),
        zone=_field(text, "Rep-risk zone", path),
        path=path,
    )


def all_specs(root: Path) -> list[Spec]:
    return [load_spec(p.name.removesuffix(".spec.md"), root) for p in sorted((root / "specs").glob("*.spec.md"))]


def draft_approve_specs(root: Path) -> list[Spec]:
    """Specs whose zone requires a human approval step — the ones worth measuring."""
    return [s for s in all_specs(root) if s.zone == DRAFT_APPROVE]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_specs.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Verify against the real specs**

Run:
```bash
uv run python -c "
from pathlib import Path
from bdcore.specs import all_specs, draft_approve_specs
r = Path('.').resolve()
for s in all_specs(r): print(f'{s.id:22} {s.version:6} {s.zone}')
print('draft-approve:', [s.id for s in draft_approve_specs(r)])
"
```
Expected: 4 specs listed; `draft-approve: ['discovery-call-prep', 'outreach-drafting']`

- [ ] **Step 6: Run full CI and commit**

```bash
just ci
git add src/bdcore/specs.py tests/test_specs.py
git commit -m "feat(specs): read id, version and rep-risk zone from spec headers"
```

---

### Task 2: The ledger — append-only records and edit-rate maths

**Files:**
- Create: `src/bdcore/ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Consumes: `bdcore.context.find_root`, `bdcore.context.active_org`, `bdcore.specs.load_spec`
- Produces:
  - `class LedgerError(Exception)`
  - `APPROVED = "approved"`, `REJECTED = "rejected"`
  - `class Decision(NamedTuple): ts: str; spec: str; spec_version: str; run: str; outcome: str; edit_rate: float | None; reason: str | None; zone: str`
  - `def word_edit_rate(before: str, after: str) -> float`
  - `def ledger_path(root: Path) -> Path`
  - `def append(decision: Decision, root: Path) -> None`
  - `def read_all(root: Path) -> list[Decision]` — raises `LedgerError` on a malformed line
  - `def record(run, spec_id, outcome, root, *, before=None, after=None, edit_rate=None, reason=None, ts=None) -> Decision`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ledger.py
import pytest

from bdcore.ledger import (
    APPROVED,
    REJECTED,
    Decision,
    LedgerError,
    append,
    ledger_path,
    read_all,
    record,
    word_edit_rate,
)
from bdcore.specs import SpecError


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    (tmp_path / "contexts" / "acme").mkdir(parents=True)
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "outreach-drafting.spec.md").write_text(
        "**ID**: `outreach-drafting`\n**Version**: `v0.1`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        ("one two three four", "one two three four", 0.0),      # untouched
        ("one two three four", "one two three FIVE", 0.25),     # one word of four
        ("one two", "", 1.0),                                   # deleted entirely
        ("", "", 0.0),                                          # both empty
        ("one two", "totally different words here", 1.0),       # full rewrite, capped at 1.0
    ],
)
def test_word_edit_rate(before, after, expected):
    assert word_edit_rate(before, after) == pytest.approx(expected)


def test_word_edit_rate_ignores_whitespace_reflow():
    assert word_edit_rate("one two  three", "one\ntwo three") == 0.0


def test_ledger_path_is_behind_the_seam(repo):
    assert ledger_path(repo) == repo / "contexts" / "acme" / "ledger" / "approvals.jsonl"


def test_record_stamps_version_and_zone_from_the_spec(repo):
    d = record("acme-jane-001", "outreach-drafting", APPROVED, repo, edit_rate=0.1)
    assert d.spec_version == "v0.1"
    assert d.zone == "Draft→Approve"


def test_record_computes_edit_rate_from_before_and_after(repo):
    d = record("r1", "outreach-drafting", APPROVED, repo, before="one two three four", after="one two three FIVE")
    assert d.edit_rate == pytest.approx(0.25)


def test_record_rejects_both_edit_rate_and_texts(repo):
    with pytest.raises(LedgerError, match="both"):
        record("r1", "outreach-drafting", APPROVED, repo, before="a", after="b", edit_rate=0.5)


def test_record_requires_a_reason_for_a_reject(repo):
    with pytest.raises(LedgerError, match="reason"):
        record("r1", "outreach-drafting", REJECTED, repo)


def test_record_refuses_an_edit_rate_on_a_reject(repo):
    with pytest.raises(LedgerError, match="edit rate"):
        record("r1", "outreach-drafting", REJECTED, repo, reason="off-tone", edit_rate=0.2)


def test_record_rejects_an_unknown_outcome(repo):
    with pytest.raises(LedgerError, match="outcome"):
        record("r1", "outreach-drafting", "maybe", repo)


def test_record_on_unknown_spec_fails_loud(repo):
    with pytest.raises(SpecError):
        record("r1", "nope", APPROVED, repo, edit_rate=0.0)


def test_append_and_read_round_trip(repo):
    d = record("r1", "outreach-drafting", APPROVED, repo, edit_rate=0.0)
    append(d, repo)
    assert read_all(repo) == [d]


def test_append_is_append_only(repo):
    first = record("r1", "outreach-drafting", APPROVED, repo, edit_rate=0.0)
    second = record("r2", "outreach-drafting", REJECTED, repo, reason="off-tone")
    append(first, repo)
    append(second, repo)
    assert [d.run for d in read_all(repo)] == ["r1", "r2"]


def test_read_all_on_a_missing_ledger_is_empty(repo):
    assert read_all(repo) == []


def test_a_malformed_line_is_a_blocking_error(repo):
    append(record("r1", "outreach-drafting", APPROVED, repo, edit_rate=0.0), repo)
    with ledger_path(repo).open("a", encoding="utf-8") as f:
        f.write("{not json\n")
    # Silently skipping would change a safety metric without saying so (principle 5).
    with pytest.raises(LedgerError, match="line 2"):
        read_all(repo)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ledger.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bdcore.ledger'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/bdcore/ledger.py
"""The approval ledger — the record that makes "earned autonomy" checkable.

Every Draft→Approve decision appends one line here (cross-cutting principle 1).
It is an audit log (principle 6): append-only, never rewritten, so a poor track
record cannot be quietly laundered before a graduation check reads it.

Lives at contexts/<org>/ledger/approvals.jsonl — org-specific operational data,
behind the seam and gitignored, like the artifacts beside it.
"""

import difflib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from bdcore.context import active_org, find_root
from bdcore.specs import load_spec

APPROVED = "approved"
REJECTED = "rejected"
OUTCOMES = (APPROVED, REJECTED)


class LedgerError(Exception):
    """The ledger could not be written or read. Always a blocking error."""


class Decision(NamedTuple):
    ts: str
    spec: str
    spec_version: str
    run: str
    outcome: str
    edit_rate: float | None
    reason: str | None
    zone: str


def word_edit_rate(before: str, after: str) -> float:
    """Fraction of words changed between two drafts, in [0.0, 1.0].

    Whitespace-normalized, so a reflow is not an edit. Measured against the
    original's length: rewriting every word is 1.0 however long the result.
    """
    old, new = before.split(), after.split()
    if not old:
        return 0.0 if not new else 1.0
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    unchanged = sum(block.size for block in matcher.get_matching_blocks())
    return min(1.0, (len(old) - unchanged) / len(old))


def ledger_path(root: Path | None = None) -> Path:
    root = root or find_root()
    return root / "contexts" / active_org(root) / "ledger" / "approvals.jsonl"


def record(
    run: str,
    spec_id: str,
    outcome: str,
    root: Path | None = None,
    *,
    before: str | None = None,
    after: str | None = None,
    edit_rate: float | None = None,
    reason: str | None = None,
    ts: str | None = None,
) -> Decision:
    """Build a Decision, stamping version and zone from the spec's own header.

    The caller says which spec and what happened; the framework decides the rest.
    A metric a caller can self-report is a metric a caller can flatter.
    """
    if outcome not in OUTCOMES:
        raise LedgerError(f"unknown outcome {outcome!r} — expected one of {', '.join(OUTCOMES)}")

    texts_given = before is not None and after is not None
    if texts_given and edit_rate is not None:
        raise LedgerError("both --before/--after and --edit-rate given — one source of the number, not two")

    if outcome == REJECTED:
        if not reason:
            raise LedgerError("a rejected run needs a --reason (cross-cutting principle 1)")
        if edit_rate is not None or texts_given:
            raise LedgerError("a rejected run has no edit rate — the draft was not taken")
        rate = None
    else:
        rate = word_edit_rate(before or "", after or "") if texts_given else edit_rate
        if rate is None:
            raise LedgerError("an approved run needs --before/--after or --edit-rate")
        if not 0.0 <= rate <= 1.0:
            raise LedgerError(f"edit rate {rate} is outside [0.0, 1.0]")

    spec = load_spec(spec_id, root or find_root())
    return Decision(
        ts=ts or datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        spec=spec.id,
        spec_version=spec.version,
        run=run,
        outcome=outcome,
        edit_rate=rate,
        reason=reason,
        zone=spec.zone,
    )


def append(decision: Decision, root: Path | None = None) -> None:
    """Append one decision. Never rewrites — this is an audit log."""
    path = ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(decision._asdict()) + "\n")


def read_all(root: Path | None = None) -> list[Decision]:
    """Every decision, oldest first. A malformed line is a blocking error.

    Skipping a corrupt row would change the graduation metric without telling
    anyone — the silent fallback principle 5 forbids.
    """
    path = ledger_path(root)
    if not path.is_file():
        return []
    decisions: list[Decision] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            decisions.append(Decision(**json.loads(line)))
        except (json.JSONDecodeError, TypeError) as e:
            raise LedgerError(f"{path} line {lineno} is not a valid decision record: {e}") from e
    return decisions
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_ledger.py -v`
Expected: PASS (17 tests)

- [ ] **Step 5: Run full CI and commit**

```bash
just ci
git add src/bdcore/ledger.py tests/test_ledger.py
git commit -m "feat(ledger): append-only approval ledger with word-edit-rate"
```

---

### Task 3: Graduation — Decision 1's rule, computed and reported

**Files:**
- Create: `src/bdcore/graduation.py`
- Test: `tests/test_graduation.py`

**Interfaces:**
- Consumes: `bdcore.ledger.read_all`, `bdcore.ledger.APPROVED`, `bdcore.specs.load_spec`
- Produces:
  - `WINDOW = 30`, `MIN_APPROVAL_RATE = 0.90`, `MAX_EDIT_RATE = 0.10`
  - `ELIGIBLE = "eligible"`, `NOT_YET = "not yet"`, `INSUFFICIENT = "insufficient data"`
  - `class Status(NamedTuple): spec: str; spec_version: str; runs: int; approval_rate: float | None; edit_rate: float | None; verdict: str; detail: str`
  - `def status_for(spec_id: str, root: Path) -> Status`
  - `def all_statuses(root: Path) -> list[Status]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_graduation.py
import pytest

from bdcore.graduation import (
    ELIGIBLE,
    INSUFFICIENT,
    NOT_YET,
    WINDOW,
    status_for,
)
from bdcore.ledger import APPROVED, REJECTED, append, record


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    (tmp_path / "contexts" / "acme").mkdir(parents=True)
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "outreach-drafting.spec.md").write_text(
        "**ID**: `outreach-drafting`\n**Version**: `v0.1`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    return tmp_path


def log(repo, n, outcome=APPROVED, edit_rate=0.0, version="v0.1"):
    """Append n decisions, stamping a chosen spec version."""
    spec = repo / "specs" / "outreach-drafting.spec.md"
    spec.write_text(
        f"**ID**: `outreach-drafting`\n**Version**: `{version}`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    for i in range(n):
        kwargs = {"reason": "no"} if outcome == REJECTED else {"edit_rate": edit_rate}
        append(record(f"r{version}-{outcome}-{i}", "outreach-drafting", outcome, repo, **kwargs), repo)


def test_no_runs_is_insufficient(repo):
    s = status_for("outreach-drafting", repo)
    assert s.verdict == INSUFFICIENT
    assert s.runs == 0


def test_below_the_window_is_insufficient(repo):
    log(repo, WINDOW - 1)
    s = status_for("outreach-drafting", repo)
    assert s.verdict == INSUFFICIENT
    assert f"{WINDOW - 1}/{WINDOW}" in s.detail


def test_clean_full_window_is_eligible(repo):
    log(repo, WINDOW)
    s = status_for("outreach-drafting", repo)
    assert s.verdict == ELIGIBLE
    assert s.approval_rate == pytest.approx(1.0)
    assert s.edit_rate == pytest.approx(0.0)


def test_too_many_rejects_is_not_yet(repo):
    log(repo, WINDOW - 4)
    log(repo, 4, outcome=REJECTED)  # 26/30 approved = 86.7% < 90%
    s = status_for("outreach-drafting", repo)
    assert s.verdict == NOT_YET
    assert "approval rate" in s.detail


def test_three_rejects_still_meets_the_bar(repo):
    log(repo, WINDOW - 3)
    log(repo, 3, outcome=REJECTED)  # 27/30 = 90.0%, exactly the bar
    assert status_for("outreach-drafting", repo).verdict == ELIGIBLE


def test_heavy_editing_is_not_yet(repo):
    log(repo, WINDOW, edit_rate=0.2)
    s = status_for("outreach-drafting", repo)
    assert s.verdict == NOT_YET
    assert "edit rate" in s.detail


def test_edit_rate_at_the_bar_is_not_eligible(repo):
    log(repo, WINDOW, edit_rate=0.10)  # bar is < 0.10, not <=
    assert status_for("outreach-drafting", repo).verdict == NOT_YET


def test_only_the_last_window_counts(repo):
    log(repo, 5, outcome=REJECTED)  # ancient history, outside the window
    log(repo, WINDOW)
    assert status_for("outreach-drafting", repo).verdict == ELIGIBLE


def test_rejects_are_excluded_from_the_edit_rate_mean(repo):
    log(repo, WINDOW - 1, edit_rate=0.0)
    log(repo, 1, outcome=REJECTED)
    s = status_for("outreach-drafting", repo)
    assert s.edit_rate == pytest.approx(0.0)  # not diluted by the reject


def test_a_version_bump_resets_the_window(repo):
    log(repo, WINDOW, version="v0.1")           # a clean v0.1 record
    log(repo, 1, version="v0.2")                # v0.2 has one run
    s = status_for("outreach-drafting", repo)
    assert s.spec_version == "v0.2"
    assert s.runs == 1                          # v0.1's history does not carry over
    assert s.verdict == INSUFFICIENT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_graduation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bdcore.graduation'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/bdcore/graduation.py
"""Decision 1's auto-graduation rule, computed and reported — never enforced.

A workflow graduates from Draft→Approve to Autonomous-with-spot-check when it
sustains >=90% approval and <10% word-edit-rate over 30 consecutive runs.

This module reports eligibility. It never edits a spec or flips a zone: granting
autonomy is a human act, and a tool that promotes a workflow because a number
crossed a line is exactly the silent behaviour the framework exists to prevent.

Aggregation note: Decision 1 does not say how to aggregate the edit rate. This
uses the mean, the plain reading — see the design doc for its known blind spot.
"""

from pathlib import Path
from typing import NamedTuple

from bdcore.context import find_root
from bdcore.ledger import APPROVED, Decision, read_all
from bdcore.specs import all_specs, load_spec

WINDOW = 30
MIN_APPROVAL_RATE = 0.90
MAX_EDIT_RATE = 0.10

ELIGIBLE = "eligible"
NOT_YET = "not yet"
INSUFFICIENT = "insufficient data"


class Status(NamedTuple):
    spec: str
    spec_version: str
    runs: int
    approval_rate: float | None
    edit_rate: float | None
    verdict: str
    detail: str


def _window_for(decisions: list[Decision], spec_id: str, version: str) -> list[Decision]:
    """The last WINDOW runs of this spec *at this version*.

    A version bump makes it a materially different workflow, so its predecessor's
    track record does not carry over (see docs/decisions.md).
    """
    matching = [d for d in decisions if d.spec == spec_id and d.spec_version == version]
    return matching[-WINDOW:]


def status_for(spec_id: str, root: Path | None = None) -> Status:
    root = root or find_root()
    spec = load_spec(spec_id, root)
    window = _window_for(read_all(root), spec_id, spec.version)

    if len(window) < WINDOW:
        return Status(
            spec=spec_id,
            spec_version=spec.version,
            runs=len(window),
            approval_rate=None,
            edit_rate=None,
            verdict=INSUFFICIENT,
            detail=f"{len(window)}/{WINDOW} runs at {spec.version}",
        )

    approved = [d for d in window if d.outcome == APPROVED]
    approval_rate = len(approved) / len(window)
    rates = [d.edit_rate for d in approved if d.edit_rate is not None]
    edit_rate = sum(rates) / len(rates) if rates else 0.0

    failures = []
    if approval_rate < MIN_APPROVAL_RATE:
        failures.append(f"approval rate {approval_rate:.0%} < {MIN_APPROVAL_RATE:.0%}")
    if edit_rate >= MAX_EDIT_RATE:
        failures.append(f"edit rate {edit_rate:.0%} >= {MAX_EDIT_RATE:.0%}")

    return Status(
        spec=spec_id,
        spec_version=spec.version,
        runs=len(window),
        approval_rate=approval_rate,
        edit_rate=edit_rate,
        verdict=NOT_YET if failures else ELIGIBLE,
        detail="; ".join(failures) or f"sustained over {WINDOW} runs — a human may promote the zone",
    )


def all_statuses(root: Path | None = None) -> list[Status]:
    root = root or find_root()
    return [status_for(s.id, root) for s in all_specs(root)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_graduation.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Run full CI and commit**

```bash
just ci
git add src/bdcore/graduation.py tests/test_graduation.py
git commit -m "feat(graduation): compute Decision 1's rule; report, never enforce"
```

---

### Task 4: CLI — `bd log-approval` and `bd graduation-status`

**Files:**
- Modify: `src/bdcore/cli.py` (add two commands; import `graduation`, `ledger`, `specs`)
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `bdcore.ledger.record/append`, `bdcore.graduation.status_for/all_statuses`, `bdcore.specs.SpecError`
- Produces: CLI commands `log-approval`, `graduation-status`. Tested via `typer.testing.CliRunner`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
import pytest
from typer.testing import CliRunner

from bdcore.cli import app
from bdcore.ledger import read_all

runner = CliRunner()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    (tmp_path / "contexts" / "acme").mkdir(parents=True)
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "outreach-drafting.spec.md").write_text(
        "**ID**: `outreach-drafting`\n**Version**: `v0.1`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_log_approval_appends_a_row(repo):
    result = runner.invoke(
        app, ["log-approval", "acme-jane-001", "--spec", "outreach-drafting", "--outcome", "approved", "--edit-rate", "0.05"]
    )
    assert result.exit_code == 0
    rows = read_all(repo)
    assert len(rows) == 1
    assert rows[0].run == "acme-jane-001"
    assert rows[0].spec_version == "v0.1"  # stamped, not supplied


def test_log_approval_computes_the_rate_from_files(repo, tmp_path):
    (tmp_path / "before.md").write_text("one two three four", encoding="utf-8")
    (tmp_path / "after.md").write_text("one two three FIVE", encoding="utf-8")
    result = runner.invoke(
        app,
        ["log-approval", "r1", "--spec", "outreach-drafting", "--outcome", "approved",
         "--before", str(tmp_path / "before.md"), "--after", str(tmp_path / "after.md")],
    )
    assert result.exit_code == 0
    assert read_all(repo)[0].edit_rate == pytest.approx(0.25)


def test_log_approval_reject_without_reason_fails_cleanly(repo):
    result = runner.invoke(app, ["log-approval", "r1", "--spec", "outreach-drafting", "--outcome", "rejected"])
    assert result.exit_code == 1
    assert "reason" in result.output
    assert "Traceback" not in result.output


def test_log_approval_unknown_spec_fails_cleanly(repo):
    result = runner.invoke(app, ["log-approval", "r1", "--spec", "nope", "--outcome", "approved", "--edit-rate", "0"])
    assert result.exit_code == 1
    assert "nope" in result.output
    assert "Traceback" not in result.output


def test_graduation_status_reports_insufficient_data(repo):
    result = runner.invoke(app, ["graduation-status", "outreach-drafting"])
    assert result.exit_code == 0
    assert "insufficient data" in result.output
    assert "0/30" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — no such command `log-approval`

- [ ] **Step 3: Write minimal implementation**

Add to `src/bdcore/cli.py` (imports at top: `from bdcore import cards, doctruth, engagers, graduation, ledger, seam`, `from bdcore.ledger import LedgerError`, `from bdcore.specs import SpecError`):

```python
@app.command("log-approval")
def log_approval(
    run: Annotated[str, typer.Argument(help="Run label, e.g. the draft's seq-id.")],
    spec: Annotated[str, typer.Option("--spec", help="Spec id this run implements.")],
    outcome: Annotated[str, typer.Option("--outcome", help="approved or rejected.")],
    before: Annotated[Path | None, typer.Option("--before", help="Draft as generated.")] = None,
    after: Annotated[Path | None, typer.Option("--after", help="Draft as approved.")] = None,
    edit_rate: Annotated[float | None, typer.Option("--edit-rate", help="Explicit rate, 0.0-1.0.")] = None,
    reason: Annotated[str | None, typer.Option("--reason", help="Required when rejecting.")] = None,
) -> None:
    """Record one Draft→Approve decision in the ledger."""
    root = _root()
    texts = {}
    for name, path in (("before", before), ("after", after)):
        if path is not None:
            if not path.is_file():
                typer.secho(f"ERROR: no {name} file at {path}", fg=typer.colors.RED, err=True)
                raise typer.Exit(1)
            texts[name] = path.read_text(encoding="utf-8")

    try:
        decision = ledger.record(
            run, spec, outcome, root,
            before=texts.get("before"), after=texts.get("after"),
            edit_rate=edit_rate, reason=reason,
        )
        ledger.append(decision, root)
    except (LedgerError, SpecError, ContextError) as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e

    rate = "n/a" if decision.edit_rate is None else f"{decision.edit_rate:.0%}"
    typer.secho(f"Logged {decision.outcome} for {decision.spec} {decision.spec_version} (edit rate {rate}).",
                fg=typer.colors.GREEN)


@app.command("graduation-status")
def graduation_status(
    spec: Annotated[str | None, typer.Argument(help="Spec id; omit for all specs.")] = None,
) -> None:
    """Report whether a workflow has earned a higher autonomy zone."""
    root = _root()
    try:
        statuses = [graduation.status_for(spec, root)] if spec else graduation.all_statuses(root)
    except (LedgerError, SpecError, ContextError) as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e

    for s in statuses:
        colour = {graduation.ELIGIBLE: typer.colors.GREEN, graduation.NOT_YET: typer.colors.YELLOW}.get(s.verdict)
        approval = "—" if s.approval_rate is None else f"{s.approval_rate:.0%}"
        edits = "—" if s.edit_rate is None else f"{s.edit_rate:.0%}"
        typer.secho(f"{s.spec} {s.spec_version}: {s.verdict}", fg=colour)
        typer.echo(f"    runs {s.runs}/{graduation.WINDOW}  approval {approval}  edit {edits}  — {s.detail}")
    typer.echo("\nGraduation is reported, never applied. A human promotes the zone.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Run full CI and commit**

```bash
just ci
git add src/bdcore/cli.py tests/test_cli.py
git commit -m "feat(cli): add bd log-approval and bd graduation-status"
```

---

### Task 5: The review surface — `bd review`

**Files:**
- Create: `src/bdcore/review.py`
- Modify: `src/bdcore/cli.py` (add the `review` command)
- Test: `tests/test_review.py`

**Interfaces:**
- Consumes: `bdcore.specs.draft_approve_specs`, `bdcore.ledger.read_all/record/append`, `bdcore.graduation.all_statuses`
- Produces:
  - `ARTIFACT_DIRS: dict[str, str]` — spec-id → output dir, per `core/path-conventions.md`
  - `class Pending(NamedTuple): spec: str; run: str; path: Path; text: str`
  - `def pending(root: Path) -> list[Pending]`
  - `def render(root: Path) -> str` — the full HTML page
  - `def serve(root: Path, port: int = 8765) -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_review.py
import pytest

from bdcore.ledger import APPROVED, append, record
from bdcore.review import pending, render


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    (tmp_path / "contexts" / "acme" / "outreach").mkdir(parents=True)
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "outreach-drafting.spec.md").write_text(
        "**ID**: `outreach-drafting`\n**Version**: `v0.1`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    (tmp_path / "specs" / "account-research.spec.md").write_text(
        "**ID**: `account-research`\n**Version**: `v0.1`\n**Rep-risk zone**: Autonomous\n",
        encoding="utf-8",
    )
    return tmp_path


def draft(repo, name, body="Hi Jane, saw your post."):
    p = repo / "contexts" / "acme" / "outreach" / f"{name}.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_an_undecided_draft_is_pending(repo):
    draft(repo, "acme-jane-001")
    assert [p.run for p in pending(repo)] == ["acme-jane-001"]


def test_a_decided_draft_is_not_pending(repo):
    draft(repo, "acme-jane-001")
    append(record("acme-jane-001", "outreach-drafting", APPROVED, repo, edit_rate=0.0), repo)
    assert pending(repo) == []


def test_a_redraft_with_a_new_seq_id_is_pending_again(repo):
    draft(repo, "acme-jane-001")
    append(record("acme-jane-001", "outreach-drafting", APPROVED, repo, edit_rate=0.0), repo)
    draft(repo, "acme-jane-002")
    assert [p.run for p in pending(repo)] == ["acme-jane-002"]


def test_pending_carries_the_draft_text(repo):
    draft(repo, "acme-jane-001", body="Hi Jane, specific hook.")
    assert pending(repo)[0].text == "Hi Jane, specific hook."


def test_autonomous_specs_have_no_pending_queue(repo):
    # account-research is Autonomous — it has no approval step to queue.
    (repo / "contexts" / "acme" / "dossiers").mkdir()
    (repo / "contexts" / "acme" / "dossiers" / "acme.md").write_text("dossier", encoding="utf-8")
    assert pending(repo) == []


def test_render_lists_a_pending_draft_and_escapes_it(repo):
    draft(repo, "acme-jane-001", body="<script>alert(1)</script>")
    html = render(repo)
    assert "acme-jane-001" in html
    assert "<script>alert(1)</script>" not in html   # escaped, not executed
    assert "&lt;script&gt;" in html


def test_render_shows_graduation_status(repo):
    assert "insufficient data" in render(repo)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_review.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bdcore.review'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/bdcore/review.py
"""The review surface — one place to approve, edit, or reject pending drafts.

Decision 1 asks for a single approval surface with inline approve /
edit-and-approve / reject. This serves that on loopback: it renders unsent drafts
to real prospects and appends to an audit log, so it binds to 127.0.0.1 only and
is not an authenticated surface meant to be exposed. Notifications are deferred.

"Pending" is derived, not stored: an artifact under a Draft→Approve spec's output
dir with no ledger entry for its run id. Nothing to queue, nothing to sync.
"""

import html
import http.server
import urllib.parse
import webbrowser
from pathlib import Path
from typing import NamedTuple

from bdcore.context import active_org, find_root
from bdcore.graduation import all_statuses
from bdcore.ledger import APPROVED, REJECTED, append, read_all, record
from bdcore.specs import draft_approve_specs

# spec-id -> artifact dir, per the generated-artifact paths in core/path-conventions.md.
ARTIFACT_DIRS = {
    "outreach-drafting": "outreach",
    "discovery-call-prep": "prep",
}


class Pending(NamedTuple):
    spec: str
    run: str
    path: Path
    text: str


def pending(root: Path | None = None) -> list[Pending]:
    """Drafts of Draft→Approve specs with no decision logged against them."""
    root = root or find_root()
    decided = {d.run for d in read_all(root)}
    org_dir = root / "contexts" / active_org(root)

    items: list[Pending] = []
    for spec in draft_approve_specs(root):
        subdir = ARTIFACT_DIRS.get(spec.id)
        if not subdir:
            continue
        for path in sorted((org_dir / subdir).glob("*.md")):
            run = path.stem
            if run not in decided:
                items.append(Pending(spec=spec.id, run=run, path=path, text=path.read_text(encoding="utf-8")))
    return items


def _draft_form(item: Pending) -> str:
    return f"""
    <article>
      <h3>{html.escape(item.run)} <small>{html.escape(item.spec)}</small></h3>
      <form method="post" action="/decide">
        <input type="hidden" name="run" value="{html.escape(item.run)}">
        <input type="hidden" name="spec" value="{html.escape(item.spec)}">
        <textarea name="after" rows="12">{html.escape(item.text)}</textarea>
        <p>Edit the text above before approving and the diff becomes the edit rate.</p>
        <button name="outcome" value="approved">Approve</button>
        <input name="reason" placeholder="Reason (required to reject)">
        <button name="outcome" value="rejected">Reject</button>
      </form>
    </article>
    """


def render(root: Path | None = None) -> str:
    """The full dashboard page: pending drafts, then graduation status."""
    root = root or find_root()
    items = pending(root)
    drafts = "".join(_draft_form(i) for i in items) or "<p>Nothing pending.</p>"
    rows = "".join(
        f"<tr><td>{html.escape(s.spec)}</td><td>{html.escape(s.spec_version)}</td>"
        f"<td>{s.runs}</td><td>{html.escape(s.verdict)}</td><td>{html.escape(s.detail)}</td></tr>"
        for s in all_statuses(root)
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>BD review</title>
<style>
 body {{ font: 15px/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 52rem; }}
 article {{ border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
 textarea {{ width: 100%; font: 13px/1.5 ui-monospace, monospace; }}
 table {{ border-collapse: collapse; width: 100%; }}
 td, th {{ border-bottom: 1px solid #ddd; padding: .4rem; text-align: left; }}
 button {{ padding: .4rem .8rem; margin-right: .5rem; }}
</style></head><body>
<h1>Pending drafts</h1>
{drafts}
<h2>Graduation status</h2>
<table><tr><th>Spec</th><th>Version</th><th>Runs</th><th>Verdict</th><th>Detail</th></tr>{rows}</table>
<p><em>Graduation is reported, never applied. A human promotes the zone.</em></p>
</body></html>"""


def _handler(root: Path) -> type[http.server.BaseHTTPRequestHandler]:
    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, body: str, status: int = 200) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802 - stdlib's required name
            self._send(render(root))

        def do_POST(self) -> None:  # noqa: N802 - stdlib's required name
            length = int(self.headers.get("Content-Length", 0))
            form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
            field = {k: v[0] for k, v in form.items()}
            item = next((p for p in pending(root) if p.run == field.get("run")), None)
            if item is None:
                self._send("<p>Unknown or already-decided draft.</p>", status=404)
                return
            try:
                outcome = field["outcome"]
                decision = record(
                    item.run, item.spec, outcome, root,
                    before=item.text if outcome == APPROVED else None,
                    after=field.get("after") if outcome == APPROVED else None,
                    reason=field.get("reason") or None if outcome == REJECTED else None,
                )
                append(decision, root)
            except Exception as e:  # surfaced in the page; the ledger stays clean
                self._send(f"<p>Not logged: {html.escape(str(e))}</p><p><a href='/'>Back</a></p>", status=400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass  # keep the terminal readable

    return Handler


def serve(root: Path | None = None, port: int = 8765) -> None:
    """Serve the dashboard on loopback and open a browser at it."""
    root = root or find_root()
    server = http.server.HTTPServer(("127.0.0.1", port), _handler(root))
    url = f"http://127.0.0.1:{port}/"
    print(f"Review surface on {url} — Ctrl-C to stop.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
```

Add to `src/bdcore/cli.py` (import `review` in the `from bdcore import ...` line):

```python
@app.command("review")
def review_cmd(
    port: Annotated[int, typer.Option("--port", help="Loopback port to serve on.")] = 8765,
) -> None:
    """Open the review surface for pending drafts."""
    review.serve(_root(), port)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_review.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Run full CI and commit**

```bash
just ci
git add src/bdcore/review.py src/bdcore/cli.py tests/test_review.py
git commit -m "feat(review): loopback approve/edit/reject surface for pending drafts"
```

---

### Task 6: The outreach skill (roadmap C4) and retiring the four

The first Draft→Approve workflow that actually exists — contract-native from birth, and it logs its own outcome.

**Files:**
- Create: `skills/outreach-drafting/SKILL.md`
- Delete: `skills/bd-email/`, `skills/cold-email/`, `skills/email-sequence/`, `skills/event-invite/`
- Modify: `src/bdcore/seam.py` (drop the `skills/event-invite/SKILL.md` baseline entry)

**Interfaces:**
- Consumes: the `bd log-approval` CLI from Task 4.
- Produces: drafts at `contexts/<org>/outreach/<account>-<contact>-<seq>.md` — the input Task 5's `pending()` reads.

- [ ] **Step 1: Write the skill**

Create `skills/outreach-drafting/SKILL.md`. It MUST carry no org-specific content — no company name, no language default, no pitch prose, no geography (it has to pass `bd check seam` with no baseline entry).

```markdown
---
name: outreach-drafting
description: Drafts a first-touch or follow-up message to a named Contact at an Account, for a stated purpose (cold, warm, re-engage, event). Trigger when the user asks to write outreach, an intro message, a follow-up, a cold email, a LinkedIn DM, or an event invitation to a specific person. Implements specs/outreach-drafting.spec.md.
---

# Outreach drafting

Implements `specs/outreach-drafting.spec.md`. Rep-risk zone: **Draft→Approve** —
you draft, the BDOwner approves and sends. Never send anything yourself.

## Inputs

1. **Account** and **Contact** (required). Ask if not given.
2. **Purpose** — one of `cold`, `warm`, `re-engage`, `event`. Ask if unclear.
   Purpose changes the opening and the ask, not the machinery.
3. **Channel** — e.g. `linkedin_dm`, `email_cold`, `email_followup`.
4. **Context surfaces** — resolve every `context.*` surface per
   `core/path-conventions.md` against the org named in `ACTIVE_CONTEXT.md`. A
   missing surface, or one marked `STATUS: UNFILLED`, is a blocking error: stop
   and tell the BDOwner. Never guess org content.
   - `context.positioning(proposition_id)` — the proposition to lead with.
   - `context.tone(channel)` — voice, word lists, and the org's default language.
     Write in the language that surface names. Never assume one.
   - `context.content("post_example")` — style reference.
   - `context.icp()` — to sanity-check the Contact is a buyer.
5. **AccountDossier** if one exists — otherwise consider running `account-research`
   first, or say plainly in the draft's provenance that it is unresearched.

## Process

1. Read the surfaces above. Fail loud on any that are missing.
2. Pick the proposition that fits the Account. If two fit, ask.
3. Draft per the purpose:
   - `cold` — earn the reply. One specific, verifiable observation about them.
   - `warm` — reference the real prior touch. Do not re-introduce yourself.
   - `re-engage` — name the gap honestly; give a reason to talk now.
   - `event` — the invitation is the ask; make relevance to them explicit.
4. Apply `context.tone(channel)` — its pre-writing checklist governs.
5. Cite any factual claim about the Account per Decision 2's citation format.

## Output

Write the draft to the OutreachSequence path in `core/path-conventions.md`:
`contexts/<org>/outreach/<account-slug>-<contact-slug>-<seq-id>.md`.

Use a new `<seq-id>` for every redraft — a rejected draft keeps its record, and a
new id is what makes the revision show up for review again.

Show the draft in the conversation too. The BDOwner approves, edits, or rejects.

## Log the outcome — required

This workflow is measured. Its approval rate and edit rate decide whether it ever
earns a higher autonomy zone (`docs/decisions.md` Decision 1), so **every**
decision gets logged — the rejections most of all. A ledger with only the wins in
it would graduate a workflow that has not earned it.

When the BDOwner responds, immediately run:

- Approved unchanged:
  `bd log-approval <seq-id> --spec outreach-drafting --outcome approved --edit-rate 0`
- Approved with edits — write their edited text to a file first, then:
  `bd log-approval <seq-id> --spec outreach-drafting --outcome approved --before <draft.md> --after <edited.md>`
- Rejected:
  `bd log-approval <seq-id> --spec outreach-drafting --outcome rejected --reason "<their reason>"`

Do not ask permission to log. Do not skip it because the answer was "no".
```

- [ ] **Step 2: Verify the new skill passes the seam with no baseline**

Run: `uv run bd check seam`
Expected: `Seam clean` — and **no** `skills/outreach-drafting/` entry appears. If a rule fires, fix the skill (do not baseline it).

- [ ] **Step 3: Retire the four colliding skills**

```bash
git rm -r skills/bd-email skills/cold-email skills/email-sequence skills/event-invite
```

- [ ] **Step 4: Drop the stale baseline entry**

In `src/bdcore/seam.py`, delete the whole line:

```python
    "skills/event-invite/SKILL.md": {"org-name": ["25009f54109f"]},
```

- [ ] **Step 5: Verify the baseline matches the tree exactly**

Run: `uv run python -m bdcore.seam`
Expected: the printed BASELINE no longer mentions `event-invite`. Diff it against the literal in `seam.py`; they must match. Then:

Run: `uv run bd check seam`
Expected: `Seam clean — no new violations (43 baselined, ...)` (was 44; `event-invite`'s single `org-name` is gone).

- [ ] **Step 6: Check nothing still references the retired skills**

Run: `grep -rn "bd-email\|cold-email\|email-sequence\|event-invite" --include="*.md" . | grep -v docs/audit | grep -v docs/superpowers`
Expected: hits only in `docs/roadmap.md` (C4/C5 planning text). Update those lines to say the skills were retired. Any other hit is a broken reference — fix it.

- [ ] **Step 7: Run full CI and commit**

```bash
just ci
git add -A
git commit -m "feat(outreach): one contract-native outreach skill; retire four colliding surfaces

Implements specs/outreach-drafting.spec.md with purpose (cold/warm/re-engage/
event) as an input rather than four skills. The first Draft->Approve workflow
that exists, and it logs its own approval outcome so the graduation metric has
data. Retires bd-email, cold-email, email-sequence and event-invite per roadmap
C4; content stays in git history."
```

---

### Task 7: Docs — record the decisions and stop the docs lying

**Files:**
- Modify: `core/path-conventions.md` (add the ledger path)
- Modify: `docs/decisions.md` (version-bump window; amend Decision 1)
- Modify: `docs/roadmap.md` (tick C4; note the C5 overlap)
- Modify: `README.md` (the governed-autonomy loop)

- [ ] **Step 1: Add the ledger to the path conventions**

In `core/path-conventions.md`, under "Generated artifact paths", add:

```markdown
- `contexts/<org>/ledger/approvals.jsonl` — the approval ledger. Append-only; one
  JSON record per Draft→Approve decision. Consumed by `bd graduation-status`.
```

- [ ] **Step 2: Record the version-bump window decision**

Append to `docs/decisions.md`:

```markdown
---

## Decision 11 — Graduation window and a spec version bump

**Q**: When a spec's version bumps, do its previous runs still count toward the
Decision 1 graduation bar?

**Decision**: No. The 30-run window is per `(spec, spec_version)`. A version bump
resets it.

**Why**: A new spec version is a materially different workflow. Counting v0.1's
approvals toward graduating v0.2 would grant autonomy on evidence produced by
something else — precisely the unearned autonomy the bar exists to prevent. The
cost is a slower clock after every spec edit; that is the right trade when the
output is a decision to stop reviewing a prospect-facing message.

**Revisit when**: trivial spec edits (a typo, a reworded heading) are observed
resetting a nearly-graduated workflow. The fix then is a version scheme that
distinguishes editorial from behavioural change, not counting across behaviours.
```

- [ ] **Step 3: Amend Decision 1**

In `docs/decisions.md`, under Decision 1's "Revisit when" line, add:

```markdown
**Amendment (v0.2)**: the review surface ships as `bd review` — a dashboard served
on loopback by the CLI, not a hosted app. Same page, same three actions, and the
structured feedback still lands in the ledger. Mobile and email notifications are
**not** built: they need hosting infrastructure and are a separate concern from the
metric. The auto-graduation rule is computed and **reported** by
`bd graduation-status`; it never flips a zone. Promotion stays a human act.
```

- [ ] **Step 4: Update the roadmap**

In `docs/roadmap.md`, mark C4 done and correct the C5 overlap:

```markdown
## C4 — One deep outreach skill  ✅ shipped
- [x] Single `outreach-drafting` skill implementing outreach-drafting.spec with
      purpose (cold / warm / re-engage / event) as an input. Contract-native from
      birth, no seam baseline. The four colliding trigger surfaces (bd-email,
      cold-email, email-sequence, event-invite) are retired.
- [x] It is instrumented: every approval decision lands in the ledger, so
      Decision 1's graduation rule has data to read.
```

And in C5, note that `email-sequence` and `cold-email` were retired by C4 rather than moved to `skills/library/`.

- [ ] **Step 5: Document the loop in the README**

In `README.md`, after the "Working on the framework" section, add:

```markdown
## Governed autonomy

Autonomy is earned, not assumed. Every Draft→Approve run is logged, and the
record decides when a workflow may be trusted further.

```bash
bd review                      # approve / edit / reject pending drafts
bd graduation-status           # has a workflow earned a higher zone yet?
```

The ledger is append-only at `contexts/<org>/ledger/approvals.jsonl` (org data —
gitignored, never committed). `bd graduation-status` applies Decision 1's bar:
≥90% approval and <10% word-edit-rate over 30 consecutive runs at the same spec
version. It **reports**; a human promotes the zone.
```

- [ ] **Step 6: Verify the docs do not lie**

Run: `uv run bd check docs`
Expected: `Docs tell the truth — every claimed path exists.` Every path named above now exists (the skill from Task 6, the modules from Tasks 1-5). If a claim fails, the doc is wrong — fix the doc, do not exempt it.

- [ ] **Step 7: Run full CI and commit**

```bash
just ci
git add -A
git commit -m "docs: record the graduation window rule and the governed-autonomy loop"
```

---

### Task 8: End-to-end verification against the real repo

Tests pass in fixtures. This proves the loop works in the actual tree — the "verify before claiming" rule.

**Files:** none (verification only)

- [ ] **Step 1: Drive the whole loop by hand**

```bash
cd "$(git rev-parse --show-toplevel)"
uv run bd context                      # expect: example-corp
mkdir -p contexts/example-corp/outreach
printf 'Hi Jane, I saw your talk on field service scheduling.\n' > contexts/example-corp/outreach/acme-jane-001.md

uv run bd graduation-status outreach-drafting     # expect: insufficient data, 0/30
uv run python -c "from bdcore.review import pending; from pathlib import Path; print([p.run for p in pending(Path('.').resolve())])"
# expect: ['acme-jane-001']

printf 'Hi Jane, I really enjoyed your talk on field service scheduling.\n' > /tmp/edited.md
uv run bd log-approval acme-jane-001 --spec outreach-drafting --outcome approved \
  --before contexts/example-corp/outreach/acme-jane-001.md --after /tmp/edited.md
# expect: "Logged approved for outreach-drafting v0.1 (edit rate 20%)."

uv run bd graduation-status outreach-drafting     # expect: insufficient data, 1/30
cat contexts/example-corp/ledger/approvals.jsonl  # expect: exactly one JSON line
uv run python -c "from bdcore.review import pending; from pathlib import Path; print(pending(Path('.').resolve()))"
# expect: [] — the decided draft is no longer pending
```

- [ ] **Step 2: Confirm a reject is refused without a reason**

```bash
uv run bd log-approval acme-jane-002 --spec outreach-drafting --outcome rejected; echo "exit=$?"
```
Expected: a one-line red `ERROR: a rejected run needs a --reason ...`, `exit=1`, **no traceback**.

- [ ] **Step 3: Confirm the ledger is not committable**

```bash
git check-ignore -v contexts/example-corp/ledger/approvals.jsonl
git status --short contexts/    # expect: no ledger file listed
```
Expected: the ledger matches the `contexts/*` ignore rule. **If it is not ignored, stop** — org data must never be committable.

- [ ] **Step 4: Clean up the scratch data**

```bash
rm -rf contexts/example-corp/ledger contexts/example-corp/outreach /tmp/edited.md
git status --short   # expect: clean
```

- [ ] **Step 5: Full CI, then push and open the PR**

```bash
just ci
git push -u origin approval-ledger
gh pr create --repo jesperjhovinga/open-source-sales-framework \
  --base worktree-python-tooling-spine --head approval-ledger \
  --title "feat: governed autonomy — the approval ledger, the outreach skill, and the review surface" \
  --body-file <(cat docs/superpowers/specs/2026-07-16-approval-ledger-design.md)
```

Then watch CI: `gh run watch`. It must pass before the PR is called done.

---

## Self-Review

**Spec coverage** — every design section maps to a task:

| Design section | Task |
|---|---|
| §1 outreach skill (C4) + retire four | 6 |
| §2 ledger (record, append-only, fail-loud on malformed) | 2 |
| §3 capture wired into the skill | 6 (Step 1, "Log the outcome") |
| §3b CLI surface | 4 |
| §4 metrics (edit rate, approval rate, mean) | 2 (rate maths), 3 (aggregation) |
| §5 graduation + version-bump reset | 3, 7 (Decision 11) |
| §6 review surface (pending, actions, loopback) | 5 |
| §7 zone discovery from spec headers | 1 |
| Docs to update | 7 |
| Testing | every task's Steps 1-4; Task 8 end-to-end |

**Type consistency** — `Spec(id, version, zone, path)` from Task 1 is used as `spec.id`/`spec.version`/`spec.zone` in Tasks 2, 3, 5. `Decision(ts, spec, spec_version, run, outcome, edit_rate, reason, zone)` from Task 2 is read as `d.run`/`d.spec`/`d.spec_version`/`d.outcome`/`d.edit_rate` in Tasks 3 and 5. `Status(...)` from Task 3 is read as `s.spec`/`s.spec_version`/`s.runs`/`s.approval_rate`/`s.edit_rate`/`s.verdict`/`s.detail` in Tasks 4 and 5. `Pending(spec, run, path, text)` from Task 5 is used in its own render/handler only. `record(...)` keyword-only args (`before`, `after`, `edit_rate`, `reason`, `ts`) match every call site.

**Known gap, deliberate:** `discovery-call-prep` is Draft→Approve with no skill, so its `ARTIFACT_DIRS` entry (`prep`) will find nothing until that skill exists. That is correct behaviour, not a bug — the entry is there so the surface works the day the skill lands.
