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
    if not old and not new:
        return 0.0
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    unchanged = sum(block.size for block in matcher.get_matching_blocks())
    # Count whichever side changed more: words that vanished from the draft, or
    # words injected into it. Taking the max (not the sum) keeps a replacement as
    # one change rather than two, and normalising by the longer text keeps a large
    # insertion from exceeding 1.0.
    changed = max(len(old) - unchanged, len(new) - unchanged)
    return changed / max(len(old), len(new))


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

    if (before is not None) != (after is not None):
        raise LedgerError("only one of --before/--after was given — both texts are needed to compute a rate")

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
    """Append one decision. Never rewrites — this is an audit log.

    One row = one decision (see the design doc): a run that already has a
    decision logged against it cannot get a second one. Validated by reading
    the existing ledger first — the write itself still only ever appends.
    """
    for existing in read_all(root):
        if existing.spec == decision.spec and existing.run == decision.run:
            raise LedgerError(
                f"run {decision.run!r} of spec {decision.spec!r} was already decided — "
                "a redraft needs a new seq-id, not a second decision on the same run"
            )

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
