import pytest

from bdcore.graduation import (
    ELIGIBLE,
    INSUFFICIENT,
    NOT_APPLICABLE,
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
        run_id = f"r{version}-{outcome}-{i}"
        if outcome == REJECTED:
            append(record(run_id, "outreach-drafting", outcome, repo, reason="no"), repo)
        else:
            append(record(run_id, "outreach-drafting", outcome, repo, edit_rate=edit_rate), repo)


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


def test_a_version_bump_resets_the_window(repo):
    log(repo, WINDOW, version="v0.1")  # a clean v0.1 record
    log(repo, 1, version="v0.2")  # v0.2 has one run
    s = status_for("outreach-drafting", repo)
    assert s.spec_version == "v0.2"
    assert s.runs == 1  # v0.1's history does not carry over
    assert s.verdict == INSUFFICIENT
