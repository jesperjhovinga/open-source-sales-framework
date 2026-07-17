import json

import pytest

from bdcore.graduation import (
    ELIGIBLE,
    INSUFFICIENT,
    NOT_APPLICABLE,
    NOT_YET,
    WINDOW,
    major,
    status_for,
)
from bdcore.ledger import APPROVED, REJECTED, append, ledger_path, record
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


def log(repo, n, outcome=APPROVED, edit_rate=0.0, version="v0.1"):
    """Append n decisions, stamping a chosen spec version."""
    spec = repo / "specs" / "outreach-drafting.spec.md"
    spec.write_text(
        f"**ID**: `outreach-drafting`\n**Version**: `{version}`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    for i in range(n):
        run_id = f"r{version}-{outcome}-{i}"
        if outcome == REJECTED:
            append(record(run_id, "outreach-drafting", outcome, repo, reason="no"), repo)
        else:
            append(record(run_id, "outreach-drafting", outcome, repo, edit_rate=edit_rate), repo)


def raw_append(repo, decision):
    """Write a decision straight to the ledger file, bypassing append()'s duplicate guard.

    Simulates a hand-edited or legacy ledger that predates that guard — the
    scenario `_distinct_runs` (the read-time half of the Defect 1 fix) defends
    against.
    """
    path = ledger_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(decision._asdict()) + "\n")


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
    # A non-zero rate is load-bearing: with edit_rate=0.0 this test would pass
    # even if a reject's None were diluted in as a zero. At 0.05, exclusion gives
    # 0.05 and dilution would give 29*0.05/30 = 0.0483 — so the bug cannot hide.
    log(repo, WINDOW - 1, edit_rate=0.05)
    log(repo, 1, outcome=REJECTED)
    s = status_for("outreach-drafting", repo)
    assert s.edit_rate == pytest.approx(0.05)  # the reject is excluded, not counted as zero


def test_a_spec_above_draft_approve_is_not_applicable(repo):
    # account-research is already Autonomous — there is no higher zone to
    # promote it to, so "eligible" would be misleading even with a perfect
    # 30-run record. Graduation simply does not apply here.
    (repo / "specs" / "account-research.spec.md").write_text(
        "**ID**: `account-research`\n**Version**: `v0.1`\n**Rep-risk zone**: Autonomous\n",
        encoding="utf-8",
    )
    for i in range(WINDOW):
        append(record(f"ar{i}", "account-research", APPROVED, repo, edit_rate=0.0), repo)
    s = status_for("account-research", repo)
    assert s.verdict == NOT_APPLICABLE
    assert "Autonomous" in s.detail


def test_a_major_version_bump_resets_the_window(repo):
    log(repo, WINDOW, version="v0.9")  # a clean v0.9 record
    log(repo, 1, version="v1.0")  # v1.0 is a behavioural change — one run so far
    s = status_for("outreach-drafting", repo)
    assert s.spec_version == "v1.0"
    assert s.runs == 1  # v0.9's history does not carry over
    assert s.verdict == INSUFFICIENT


def test_a_minor_version_bump_carries_the_window(repo):
    log(repo, WINDOW - 5, version="v0.1")  # a clean v0.1 record, partway there
    log(repo, 5, version="v0.2")  # editorial bump — same MAJOR, evidence carries
    s = status_for("outreach-drafting", repo)
    assert s.spec_version == "v0.2"
    assert s.runs == WINDOW  # v0.1's 25 runs still count
    assert s.verdict == ELIGIBLE


def test_an_unparseable_spec_version_is_a_blocking_error(repo):
    (repo / "specs" / "outreach-drafting.spec.md").write_text(
        "**ID**: `outreach-drafting`\n**Version**: `not-a-version`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="not a parseable"):
        status_for("outreach-drafting", repo)


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("v0.1", "v0"),
        ("v1.0", "v1"),
        ("v0.1.2", "v0"),
        ("v1", "v1"),
    ],
)
def test_major_parses_the_major_component(version, expected):
    assert major(version) == expected


@pytest.mark.parametrize("version", ["0.1", "v", "vX.1", "1.0", ""])
def test_major_on_an_unparseable_version_is_a_blocking_error(version):
    with pytest.raises(SpecError, match="not a parseable"):
        major(version)


def test_i3_first_wins_a_racing_approval_cannot_launder_a_rejection(repo):
    # ledger.append's duplicate guard is check-then-act with no lock: two
    # concurrent `bd log-approval` calls on one run can still both land
    # (reproduced). With last-wins dedupe, an approval appended moments after a
    # rejection would silently REPLACE it in the graduation window, even though
    # the rejection is still physically in the ledger file. First-wins makes
    # the race benign: whichever row landed first is the one that counts.
    #
    # 26 clean approvals + 3 clean rejections + 1 raced run = 30 (the window).
    # If the raced run counts as rejected (first-wins, correct): 26/30 = 86.7%
    # approval rate -> NOT_YET. If it counted as approved (last-wins, the bug):
    # 27/30 = 90.0% exactly -> ELIGIBLE. The two dedupe strategies produce
    # different verdicts, so this test cannot pass by accident either way.
    log(repo, 26, outcome=APPROVED, edit_rate=0.0)
    log(repo, 3, outcome=REJECTED)
    raw_append(repo, record("raced-run", "outreach-drafting", REJECTED, repo, reason="off-tone"))
    raw_append(repo, record("raced-run", "outreach-drafting", APPROVED, repo, edit_rate=0.0))

    s = status_for("outreach-drafting", repo)

    assert s.runs == WINDOW  # 26 + 3 + 1 raced-but-distinct run
    assert s.approval_rate == pytest.approx(26 / 30)  # the raced run counts as REJECTED
    assert s.verdict == NOT_YET  # would be ELIGIBLE (27/30) if the approval had won the race
    assert "approval rate" in s.detail


def test_thirty_rows_sharing_one_run_id_is_insufficient_not_eligible(repo):
    # The exact gaming scenario Defect 1 exists to prevent: 30 decisions on a
    # single draft must not count as 30 runs. ledger.append blocks this at
    # write time (see test_ledger.py); this proves the read-time defence
    # (_distinct_runs) holds even against a ledger that predates that guard.
    for _ in range(WINDOW):
        raw_append(repo, record("same-run", "outreach-drafting", APPROVED, repo, edit_rate=0.0))
    s = status_for("outreach-drafting", repo)
    assert s.runs == 1
    assert s.verdict == INSUFFICIENT
