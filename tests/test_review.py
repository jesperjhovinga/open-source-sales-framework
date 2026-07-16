import pytest

from bdcore.ledger import APPROVED, append, record
from bdcore.review import ARTIFACT_DIRS, ReviewError, pending, render


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


def test_autonomous_specs_have_no_pending_queue(repo, monkeypatch):
    # account-research is Autonomous — it has no approval step to queue, even
    # when it's mapped in ARTIFACT_DIRS and has a draft sitting on disk. If this
    # only passed because the spec was unmapped, mapping it would break the test.
    monkeypatch.setitem(ARTIFACT_DIRS, "account-research", "dossiers")
    (repo / "contexts" / "acme" / "dossiers").mkdir()
    (repo / "contexts" / "acme" / "dossiers" / "acme.md").write_text("dossier", encoding="utf-8")
    assert pending(repo) == []


def test_render_lists_a_pending_draft_and_escapes_it(repo):
    draft(repo, "acme-jane-001", body="<script>alert(1)</script>")
    html = render(repo)
    assert "acme-jane-001" in html
    assert "<script>alert(1)</script>" not in html  # escaped, not executed
    assert "&lt;script&gt;" in html


def test_render_shows_graduation_status(repo):
    assert "insufficient data" in render(repo)


def test_unmapped_draft_approve_spec_raises(repo):
    # A Draft→Approve spec with no ARTIFACT_DIRS entry must fail loud, not be
    # silently skipped — its drafts would otherwise never reach review.
    (repo / "specs" / "new-thing.spec.md").write_text(
        "**ID**: `new-thing`\n**Version**: `v0.1`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    with pytest.raises(ReviewError, match="new-thing"):
        pending(repo)


def test_render_escapes_the_run_and_spec_ids(repo):
    draft(repo, 'x" onmouseover="alert(1)')
    html = render(repo)
    assert 'x" onmouseover="alert(1)' not in html
    assert "x&quot; onmouseover=&quot;alert(1)" in html
