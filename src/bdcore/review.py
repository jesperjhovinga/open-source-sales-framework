"""The review surface — one place to approve, edit, or reject pending drafts.

Decision 1 asks for a single approval surface with inline approve /
edit-and-approve / reject. This serves that on loopback: it renders unsent drafts
to real prospects and appends to an audit log, so it binds to 127.0.0.1 only and
is not an authenticated surface meant to be exposed. Notifications are deferred.

"Pending" is derived, not stored: an artifact under a Draft→Approve spec's output
dir with no ledger entry for its run id. Nothing to queue, nothing to sync.
"""

import html
import http.server
import urllib.parse
import webbrowser
from pathlib import Path
from typing import NamedTuple

from bdcore.context import active_org, find_root
from bdcore.graduation import all_statuses
from bdcore.ledger import APPROVED, REJECTED, append, read_all, record
from bdcore.specs import DRAFT_APPROVE, draft_approve_specs

# spec-id -> artifact dir, per the generated-artifact paths in core/path-conventions.md.
ARTIFACT_DIRS = {
    "outreach-drafting": "outreach",
    "discovery-call-prep": "prep",
}


class ReviewError(Exception):
    """A Draft→Approve spec cannot be reviewed as configured. Always a blocking error."""


class Pending(NamedTuple):
    spec: str
    run: str
    path: Path
    text: str


def pending(root: Path | None = None) -> list[Pending]:
    """Drafts of Draft→Approve specs with no decision logged against them."""
    root = root or find_root()
    decided = {(d.spec, d.run) for d in read_all(root)}
    org_dir = root / "contexts" / active_org(root)

    items: list[Pending] = []
    for spec in draft_approve_specs(root):
        subdir = ARTIFACT_DIRS.get(spec.id)
        if subdir is None:
            raise ReviewError(
                f"spec '{spec.id}' is zoned {DRAFT_APPROVE} but has no ARTIFACT_DIRS entry — "
                f"its drafts would never reach review. Add its output dir (see core/path-conventions.md)."
            )
        for path in sorted((org_dir / subdir).glob("*.md")):
            run = path.stem
            if (spec.id, run) not in decided:
                items.append(Pending(spec=spec.id, run=run, path=path, text=path.read_text(encoding="utf-8")))
    return items


def _draft_form(item: Pending) -> str:
    return f"""
    <article>
      <h3>{html.escape(item.run)} <small>{html.escape(item.spec)}</small></h3>
      <form method="post" action="/decide">
        <input type="hidden" name="run" value="{html.escape(item.run)}">
        <input type="hidden" name="spec" value="{html.escape(item.spec)}">
        <textarea name="after" rows="12">{html.escape(item.text)}</textarea>
        <p>Edit the text above before approving and the diff becomes the edit rate.</p>
        <button name="outcome" value="{APPROVED}">Approve</button>
        <input name="reason" placeholder="Reason (required to reject)">
        <button name="outcome" value="{REJECTED}">Reject</button>
      </form>
    </article>
    """


def render(root: Path | None = None) -> str:
    """The full dashboard page: pending drafts, then graduation status."""
    root = root or find_root()
    items = pending(root)
    drafts = "".join(_draft_form(i) for i in items) or "<p>Nothing pending.</p>"
    rows = "".join(
        f"<tr><td>{html.escape(s.spec)}</td><td>{html.escape(s.spec_version)}</td>"
        f"<td>{s.runs}</td><td>{html.escape(s.verdict)}</td><td>{html.escape(s.detail)}</td></tr>"
        for s in all_statuses(root)
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>BD review</title>
<style>
 body {{ font: 15px/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 52rem; }}
 article {{ border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
 textarea {{ width: 100%; font: 13px/1.5 ui-monospace, monospace; }}
 table {{ border-collapse: collapse; width: 100%; }}
 td, th {{ border-bottom: 1px solid #ddd; padding: .4rem; text-align: left; }}
 button {{ padding: .4rem .8rem; margin-right: .5rem; }}
</style></head><body>
<h1>Pending drafts</h1>
{drafts}
<h2>Graduation status</h2>
<table><tr><th>Spec</th><th>Version</th><th>Runs</th><th>Verdict</th><th>Detail</th></tr>{rows}</table>
<p><em>Graduation is reported, never applied. A human promotes the zone.</em></p>
</body></html>"""


def _handler(root: Path) -> type[http.server.BaseHTTPRequestHandler]:
    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, body: str, status: int = 200) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802 - stdlib's required name
            self._send(render(root))

        def do_POST(self) -> None:  # noqa: N802 - stdlib's required name
            length = int(self.headers.get("Content-Length", 0))
            form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
            field = {k: v[0] for k, v in form.items()}
            item = next((p for p in pending(root) if p.spec == field.get("spec") and p.run == field.get("run")), None)
            if item is None:
                self._send("<p>Unknown or already-decided draft.</p>", status=404)
                return
            try:
                outcome = field["outcome"]
                decision = record(
                    item.run,
                    item.spec,
                    outcome,
                    root,
                    before=item.text if outcome == APPROVED else None,
                    after=field.get("after") if outcome == APPROVED else None,
                    reason=field.get("reason") or None if outcome == REJECTED else None,
                )
                # record() succeeded — the decision is valid. Append the ledger row
                # BEFORE touching the artifact: if the ledger write then fails (e.g. an
                # unwritable ledger file), the decision — computed here from item.text,
                # the draft as it stood before this edit — never got recorded, so the
                # draft must stay pending and unedited for the next attempt. Only once
                # the row is safely on disk does the artifact get overwritten with what
                # was actually approved. A rejected draft keeps its original text, and a
                # validation failure (caught below) never touches either.
                append(decision, root)
                if outcome == APPROVED:
                    item.path.write_text(field["after"], encoding="utf-8")
            except Exception as e:  # surfaced in the page; the ledger stays clean
                self._send(f"<p>Not logged: {html.escape(str(e))}</p><p><a href='/'>Back</a></p>", status=400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass  # keep the terminal readable — signature matches the base class

    return Handler


def serve(root: Path | None = None, port: int = 8765) -> None:
    """Serve the dashboard on loopback and open a browser at it."""
    root = root or find_root()
    server = http.server.HTTPServer(("127.0.0.1", port), _handler(root))
    url = f"http://127.0.0.1:{port}/"
    print(f"Review surface on {url} — Ctrl-C to stop.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
