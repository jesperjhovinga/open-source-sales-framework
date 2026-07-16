import os

import pytest
from typer.testing import CliRunner

from bdcore.cli import app
from bdcore.ledger import append, ledger_path, read_all, record

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
        app,
        [
            "log-approval",
            "acme-jane-001",
            "--spec",
            "outreach-drafting",
            "--outcome",
            "approved",
            "--edit-rate",
            "0.05",
        ],
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
        [
            "log-approval",
            "r1",
            "--spec",
            "outreach-drafting",
            "--outcome",
            "approved",
            "--before",
            str(tmp_path / "before.md"),
            "--after",
            str(tmp_path / "after.md"),
        ],
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


def test_graduation_status_eligible_shows_disclaimer(repo):
    for i in range(30):
        append(record(f"r{i}", "outreach-drafting", "approved", repo, edit_rate=0.0), repo)
    result = runner.invoke(app, ["graduation-status", "outreach-drafting"])
    assert result.exit_code == 0
    assert "eligible" in result.output
    assert "Graduation is reported, never applied. A human promotes the zone." in result.output


def test_graduation_status_not_yet_shows_disclaimer(repo):
    for i in range(30):
        append(record(f"r{i}", "outreach-drafting", "approved", repo, edit_rate=0.2), repo)
    result = runner.invoke(app, ["graduation-status", "outreach-drafting"])
    assert result.exit_code == 0
    assert "not yet" in result.output
    assert "Graduation is reported, never applied. A human promotes the zone." in result.output


def test_graduation_status_not_applicable_for_a_higher_zone(repo):
    (repo / "specs" / "account-research.spec.md").write_text(
        "**ID**: `account-research`\n**Version**: `v0.1`\n**Rep-risk zone**: Autonomous\n",
        encoding="utf-8",
    )
    for i in range(30):
        append(record(f"ar{i}", "account-research", "approved", repo, edit_rate=0.0), repo)
    result = runner.invoke(app, ["graduation-status", "account-research"])
    assert result.exit_code == 0
    assert "not applicable" in result.output
    assert "Autonomous" in result.output
    assert "Graduation is reported, never applied. A human promotes the zone." in result.output


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions; chmod 000 would not block reads")
def test_log_approval_unreadable_ledger_fails_cleanly(repo):
    path = ledger_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    path.chmod(0o000)
    try:
        result = runner.invoke(
            app,
            ["log-approval", "r1", "--spec", "outreach-drafting", "--outcome", "approved", "--edit-rate", "0.1"],
        )
    finally:
        path.chmod(0o644)
    assert result.exit_code == 1
    assert "ERROR" in result.output
    assert "Traceback" not in result.output


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions; chmod 000 would not block reads")
def test_graduation_status_unreadable_ledger_fails_cleanly(repo):
    path = ledger_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    path.chmod(0o000)
    try:
        result = runner.invoke(app, ["graduation-status", "outreach-drafting"])
    finally:
        path.chmod(0o644)
    assert result.exit_code == 1
    assert "ERROR" in result.output
    assert "Traceback" not in result.output
