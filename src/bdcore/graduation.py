"""Decision 1's auto-graduation rule, computed and reported — never enforced.

A workflow graduates from Draft→Approve to Autonomous-with-spot-check when it
sustains >=90% approval and <10% word-edit-rate over 30 consecutive runs.

This module reports eligibility. It never edits a spec or flips a zone: granting
autonomy is a human act, and a tool that promotes a workflow because a number
crossed a line is exactly the silent behaviour the framework exists to prevent.

Aggregation note: Decision 1 does not say how to aggregate the edit rate. This
uses the mean, the plain reading — see the design doc for its known blind spot.
"""

import re
from pathlib import Path
from typing import NamedTuple

from bdcore.context import find_root
from bdcore.ledger import APPROVED, Decision, read_all
from bdcore.specs import DRAFT_APPROVE, SpecError, all_specs, load_spec

WINDOW = 30
MIN_APPROVAL_RATE = 0.90
MAX_EDIT_RATE = 0.10

ELIGIBLE = "eligible"
NOT_YET = "not yet"
INSUFFICIENT = "insufficient data"
NOT_APPLICABLE = "not applicable"

_VERSION = re.compile(r"^v(\d+)(?:\.\d+){0,2}$")


def major(version: str) -> str:
    """The MAJOR component of a `vMAJOR[.MINOR[.PATCH]]` spec version.

    Decision 10 (v0.2 amendment): MAJOR bumps are behavioural — process,
    acceptance criteria, or output shape changed — and reset a workflow's
    graduation track record. MINOR bumps are editorial only, so evidence
    carries over. A version this cannot parse is a blocking error, never a
    silent pass (cross-cutting principle 5).
    """
    match = _VERSION.match(version)
    if not match:
        raise SpecError(f"spec version {version!r} is not a parseable vMAJOR[.MINOR[.PATCH]] version")
    return f"v{match.group(1)}"


class Status(NamedTuple):
    spec: str
    spec_version: str
    runs: int
    approval_rate: float | None
    edit_rate: float | None
    verdict: str
    detail: str


def _distinct_runs(decisions: list[Decision]) -> list[Decision]:
    """Dedupe by run id, keeping the FIRST decision for each, in first-decided order.

    A window of "30 runs" that is really "30 rows" can be filled by 30 duplicate
    decisions on one run id — the exact gaming scenario Decision 1 exists to
    prevent (this is belt-and-braces: `ledger.append` blocks new duplicates at
    write time; this is the read-time defence for a hand-edited or legacy
    ledger that predates that check).

    First-wins, not last-wins: `ledger.append`'s duplicate guard is
    check-then-act with no lock, so two concurrent `bd log-approval` calls on
    one run can still both land (reproduced). If the LAST decision won, an
    approval appended moments after a rejection would silently replace it in
    the graduation window — laundering a verdict the operator already
    recorded, even though it is still physically in the ledger file. Keeping
    the FIRST decision makes the race benign: whichever row landed first is
    the one that counts, and no later row can ever supersede an earlier
    verdict on the same run.
    """
    by_run: dict[str, Decision] = {}
    for d in decisions:
        if d.run not in by_run:  # first decision for this run wins; later ones are ignored
            by_run[d.run] = d
    return list(by_run.values())


def _window_for(decisions: list[Decision], spec_id: str, version_major: str) -> list[Decision]:
    """The last WINDOW *distinct runs* of this spec at this MAJOR version.

    A MAJOR version bump makes it a materially different workflow, so its
    predecessor's track record does not carry over. A MINOR bump is editorial
    only and does not reset the window (see docs/decisions.md, Decision 10 and
    Decision 11, v0.2 amendments).
    """
    matching = [d for d in decisions if d.spec == spec_id and major(d.spec_version) == version_major]
    return _distinct_runs(matching)[-WINDOW:]


def status_for(spec_id: str, root: Path | None = None) -> Status:
    root = root or find_root()
    spec = load_spec(spec_id, root)

    if spec.zone != DRAFT_APPROVE:
        # Graduation only makes sense for a spec still under Draft→Approve — a
        # spec already in a higher zone has no zone left to be promoted to.
        # Logging against it stays allowed (ledger.record does not gate on
        # zone, for future spot-check sampling); only this verdict changes.
        return Status(
            spec=spec_id,
            spec_version=spec.version,
            runs=0,
            approval_rate=None,
            edit_rate=None,
            verdict=NOT_APPLICABLE,
            detail=f"zone is {spec.zone}, not {DRAFT_APPROVE} — graduation does not apply",
        )

    window = _window_for(read_all(root), spec_id, major(spec.version))

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
