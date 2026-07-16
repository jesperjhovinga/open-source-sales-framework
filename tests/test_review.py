import io
import urllib.parse
from typing import NamedTuple

import pytest

from bdcore.ledger import APPROVED, REJECTED, append, read_all, record, word_edit_rate
from bdcore.review import ARTIFACT_DIRS, ReviewError, _handler, pending, render


class Sent(NamedTuple):
    status: int
    body: str


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


def post(repo, fields: dict[str, str]) -> Sent:
    """Drive do_POST directly, with no socket and no server() loop.

    Builds the handler class the same way `serve()` does, then instantiates it
    without running BaseHTTPRequestHandler.__init__ (which wants a real
    connection) — rfile/wfile/headers are set by hand and the response methods
    are stubbed to just record what was sent.
    """
    handler_cls = _handler(repo)
    handler = handler_cls.__new__(handler_cls)
    body = urllib.parse.urlencode(fields).encode("utf-8")
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    handler.headers = {"Content-Length": str(len(body))}
    status_holder: list[int] = []
    handler.send_response = lambda code, message=None: status_holder.append(code)
    handler.send_header = lambda k, v: None
    handler.end_headers = lambda: None
    handler.do_POST()
    return Sent(status=status_holder[0], body=handler.wfile.getvalue().decode("utf-8"))


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


def test_approve_with_edit_writes_the_edited_text_and_logs_one_row(repo):
    path = draft(repo, "acme-jane-001", body="Hi Jane, original draft.")
    edited = "Hi Jane, a much shorter pitch."

    sent = post(repo, {"run": "acme-jane-001", "spec": "outreach-drafting", "outcome": APPROVED, "after": edited})

    assert sent.status == 303  # redirect back to the dashboard
    assert path.read_text(encoding="utf-8") == edited  # the artifact now holds what was approved

    rows = read_all(repo)
    assert len(rows) == 1
    assert rows[0].run == "acme-jane-001"
    assert rows[0].outcome == APPROVED
    assert rows[0].edit_rate == pytest.approx(word_edit_rate("Hi Jane, original draft.", edited))


def test_reject_does_not_overwrite_the_file(repo):
    original = "Hi Jane, original draft."
    path = draft(repo, "acme-jane-001", body=original)

    sent = post(
        repo,
        {"run": "acme-jane-001", "spec": "outreach-drafting", "outcome": REJECTED, "reason": "wrong angle"},
    )

    assert sent.status == 303
    assert path.read_text(encoding="utf-8") == original  # untouched

    rows = read_all(repo)
    assert len(rows) == 1
    assert rows[0].outcome == REJECTED
    assert rows[0].edit_rate is None


def test_reject_without_reason_writes_no_row_and_does_not_touch_the_file(repo):
    original = "Hi Jane, original draft."
    path = draft(repo, "acme-jane-001", body=original)

    sent = post(repo, {"run": "acme-jane-001", "spec": "outreach-drafting", "outcome": REJECTED})

    assert sent.status == 400
    assert "Not logged" in sent.body
    assert path.read_text(encoding="utf-8") == original  # untouched
    assert read_all(repo) == []  # no ledger row for a decision that never validated


def test_pending_does_not_cross_specs_with_the_same_run_id(repo):
    # outreach/acme-2026-07-16.md and prep/acme-2026-07-16.md would collide on a
    # flat run-id key: deciding one would silence both. Keying on (spec, run)
    # keeps them independent.
    (repo / "specs" / "discovery-call-prep.spec.md").write_text(
        "**ID**: `discovery-call-prep`\n**Version**: `v0.1`\n**Rep-risk zone**: Draft→Approve\n",
        encoding="utf-8",
    )
    (repo / "contexts" / "acme" / "prep").mkdir()
    draft(repo, "acme-2026-07-16")
    (repo / "contexts" / "acme" / "prep" / "acme-2026-07-16.md").write_text("prep notes", encoding="utf-8")

    append(record("acme-2026-07-16", "outreach-drafting", APPROVED, repo, edit_rate=0.0), repo)

    remaining = pending(repo)
    assert [(p.spec, p.run) for p in remaining] == [("discovery-call-prep", "acme-2026-07-16")]
