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
