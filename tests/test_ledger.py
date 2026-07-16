import pytest

from bdcore.ledger import (
    APPROVED,
    REJECTED,
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
        ("one two three four", "one two three four", 0.0),  # untouched
        ("one two three four", "one two three FIVE", 0.25),  # one word of four
        ("one two", "", 1.0),  # deleted entirely
        ("", "", 0.0),  # both empty
        ("one two", "totally different words here", 1.0),  # full rewrite, capped at 1.0
        ("a b c d", "a b", 0.5),  # deletion
        ("one two three", "one two three four five six seven", 4 / 7),  # 4 inserted of 7
        ("one two three four five", "one two THREE-POINT-FIVE three four five", 1 / 6),  # 1 inserted of 6
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


def test_record_rejects_before_alone(repo):
    with pytest.raises(LedgerError, match="only one of"):
        record("r1", "outreach-drafting", APPROVED, repo, before="some draft text")


def test_record_rejects_after_alone(repo):
    with pytest.raises(LedgerError, match="only one of"):
        record("r1", "outreach-drafting", APPROVED, repo, after="some draft text")


def test_record_rejects_before_alone_with_edit_rate(repo):
    with pytest.raises(LedgerError, match="only one of"):
        record("r1", "outreach-drafting", APPROVED, repo, before="some draft text", edit_rate=0.5)


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


def test_append_rejects_a_duplicate_run_for_the_same_spec(repo):
    # "One row = one decision" (design doc): a redraft needs a new seq-id, not
    # a second decision on the same run — this is the write-time half of the
    # defence against a duplicated run id filling the graduation window.
    append(record("r1", "outreach-drafting", APPROVED, repo, edit_rate=0.0), repo)
    second = record("r1", "outreach-drafting", REJECTED, repo, reason="no")
    with pytest.raises(LedgerError, match="already decided") as exc_info:
        append(second, repo)
    assert "new seq-id" in str(exc_info.value)


def test_append_allows_the_same_run_id_under_a_different_spec(repo):
    # Two different workflows sharing a run id are two different runs.
    (repo / "specs" / "discovery-call-prep.spec.md").write_text(
        "**ID**: `discovery-call-prep`\n**Version**: `v0.1`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    append(record("r1", "outreach-drafting", APPROVED, repo, edit_rate=0.0), repo)
    append(record("r1", "discovery-call-prep", APPROVED, repo, edit_rate=0.0), repo)
    assert [(d.spec, d.run) for d in read_all(repo)] == [
        ("outreach-drafting", "r1"),
        ("discovery-call-prep", "r1"),
    ]


def test_read_all_on_a_missing_ledger_is_empty(repo):
    assert read_all(repo) == []


def test_a_malformed_line_is_a_blocking_error(repo):
    append(record("r1", "outreach-drafting", APPROVED, repo, edit_rate=0.0), repo)
    with ledger_path(repo).open("a", encoding="utf-8") as f:
        f.write("{not json\n")
    # Silently skipping would change a safety metric without saying so (principle 5).
    with pytest.raises(LedgerError, match="line 2"):
        read_all(repo)
