"""The approval ledger — the record that makes "earned autonomy" checkable.

Every Draft→Approve decision appends one line here (cross-cutting principle 1).
It is an audit log (principle 6): append-only, never rewritten. That alone
guarantees the file's history, not the graduation check's reading of it — a
duplicate row on one run id still has to be resolved somehow. `graduation.py`
resolves it by keeping the EARLIEST decision per run (first-wins), so a later
row can never supersede an earlier verdict. Together, append-only-ness and
first-wins mean a poor track record cannot be quietly laundered before a
graduation check reads it.

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

# Unicode blocks for scripts conventionally written without spaces between
# words. A word-edit-rate that tokenizes these on whitespace collapses an
# entire sentence into one token, so any edit at all scores 100% — see
# word_edit_rate's docstring. Deliberately narrow: Hangul is excluded because
# Korean *does* delimit words with spaces (whitespace-splitting already gives
# the right unit there), and scripts outside this list simply fall back to
# whitespace splitting, same as before this fix.
_UNSPACED_SCRIPT_RANGES = (
    (0x3040, 0x309F),  # Hiragana
    (0x30A0, 0x30FF),  # Katakana
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
    (0x0E00, 0x0E7F),  # Thai
    (0x0E80, 0x0EFF),  # Lao
    (0x0F00, 0x0FFF),  # Tibetan
    (0x1000, 0x109F),  # Myanmar (Burmese)
    (0x1780, 0x17FF),  # Khmer
)


def _is_unspaced_script(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _UNSPACED_SCRIPT_RANGES)


def _tokenize(text: str) -> list[str]:
    """Split into comparison units: whitespace-delimited words for
    space-delimited scripts, one token per character for scripts that don't
    use spaces (CJK, Thai) — so the unit of change matches the writing
    system. A run of non-CJK characters (e.g. an embedded English product
    name or URL inside Japanese text) is still whitespace-split, so it stays
    one token unless it contains internal whitespace.
    """
    tokens: list[str] = []
    buf: list[str] = []
    for ch in text:
        if _is_unspaced_script(ch):
            if buf:
                tokens.extend("".join(buf).split())
                buf = []
            tokens.append(ch)
        else:
            buf.append(ch)
    if buf:
        tokens.extend("".join(buf).split())
    return tokens


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

    Tokenizes per script (see `_tokenize`), not just on whitespace: a
    language written without spaces (Japanese, Chinese, Thai) would otherwise
    collapse to a single token, so any edit at all — even one character —
    would score 100%, making Decision 1's <10% graduation bar unreachable by
    construction for those languages.
    """
    old, new = _tokenize(before), _tokenize(after)
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
