"""`bd` — the framework's command line.

Library code raises ContextError; this layer is the only place that turns a
failure into a message and an exit code.
"""

import json
from pathlib import Path
from typing import Annotated

import typer

from bdcore import cards, doctruth, engagers, graduation, ledger, review, seam
from bdcore.context import ContextError, active_org, find_root
from bdcore.ledger import LedgerError
from bdcore.review import ReviewError
from bdcore.specs import SpecError

app = typer.Typer(no_args_is_help=True, help="BD Core — validate, source, and enforce the seam.")
check_app = typer.Typer(no_args_is_help=True, help="Enforce the framework's own rules.")
app.add_typer(check_app, name="check")


def _root() -> Path:
    try:
        return find_root(Path.cwd())
    except ContextError as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e


@app.command("validate-card")
def validate_card(path: Annotated[Path, typer.Argument(help="Path to a skill card.")]) -> None:
    """Check a skill card's shape. Human review is still required."""
    if not path.is_file():
        typer.secho(f"ERROR: no card at {path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    problems = cards.validate(path.read_text(encoding="utf-8"))
    failures = cards.failures(problems)
    for p in problems:
        note = p.startswith(cards.NOTE_PREFIX)
        typer.secho(("  - " if note else "FAIL: ") + p, fg=None if note else typer.colors.RED)

    if failures:
        typer.secho(f"\n{len(failures)} problem(s) to fix.", fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.secho("OK — card shape valid (human review still required).", fg=typer.colors.GREEN)


@app.command("source")
def source(
    input_json: Annotated[Path, typer.Argument(help="Apify engagement export.")],
    output_csv: Annotated[Path, typer.Argument(help="CSV to write.")],
    seed_url: Annotated[str, typer.Option("--seed-url", help="Profile the engagement came from.")] = "",
) -> None:
    """Turn an Apify engagement export into a pre-filtered prospect CSV."""
    root = _root()
    if not input_json.is_file():
        typer.secho(f"ERROR: no input file at {input_json}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    try:
        rows = engagers.run(input_json, output_csv, seed_url, root)
    except (ContextError, json.JSONDecodeError) as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e

    soft = sum(1 for r in rows if r["icp_score"] == "soft_pass")
    typer.echo(f"Total unique engagers: {len(rows)}")
    typer.echo(f"  soft_pass (needs research): {soft}")
    typer.echo(f"  fail (excluded): {len(rows) - soft}")
    typer.echo(f"Saved to: {output_csv}")


@app.command("context")
def context() -> None:
    """Show the active org context."""
    root = _root()
    try:
        typer.echo(f"{active_org(root)}  (from {root / 'ACTIVE_CONTEXT.md'})")
    except ContextError as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e


@app.command("log-approval")
def log_approval(
    run: Annotated[str, typer.Argument(help="Run id — the draft's filename without .md, not the bare seq-id.")],
    spec: Annotated[str, typer.Option("--spec", help="Spec id this run implements.")],
    outcome: Annotated[str, typer.Option("--outcome", help="approved or rejected.")],
    before: Annotated[Path | None, typer.Option("--before", help="Draft as generated.")] = None,
    after: Annotated[Path | None, typer.Option("--after", help="Draft as approved.")] = None,
    edit_rate: Annotated[float | None, typer.Option("--edit-rate", help="Explicit rate, 0.0-1.0.")] = None,
    reason: Annotated[str | None, typer.Option("--reason", help="Required when rejecting.")] = None,
) -> None:
    """Record one Draft→Approve decision in the ledger."""
    root = _root()
    texts: dict[str, str] = {}
    for name, path in (("before", before), ("after", after)):
        if path is not None:
            if not path.is_file():
                typer.secho(f"ERROR: no {name} file at {path}", fg=typer.colors.RED, err=True)
                raise typer.Exit(1)
            texts[name] = path.read_text(encoding="utf-8")

    try:
        decision = ledger.record(
            run,
            spec,
            outcome,
            root,
            before=texts.get("before"),
            after=texts.get("after"),
            edit_rate=edit_rate,
            reason=reason,
        )
        ledger.append(decision, root)
    except (LedgerError, SpecError, ContextError, OSError) as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e

    rate = "n/a" if decision.edit_rate is None else f"{decision.edit_rate:.0%}"
    typer.secho(
        f"Logged {decision.outcome} for {decision.spec} {decision.spec_version} (edit rate {rate}).",
        fg=typer.colors.GREEN,
    )


@app.command("graduation-status")
def graduation_status(
    spec: Annotated[str | None, typer.Argument(help="Spec id; omit for all specs.")] = None,
) -> None:
    """Report whether a workflow has earned a higher autonomy zone."""
    root = _root()
    try:
        statuses = [graduation.status_for(spec, root)] if spec else graduation.all_statuses(root)
    except (LedgerError, SpecError, ContextError, OSError) as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e

    for s in statuses:
        colour = {graduation.ELIGIBLE: typer.colors.GREEN, graduation.NOT_YET: typer.colors.YELLOW}.get(s.verdict)
        approval = "—" if s.approval_rate is None else f"{s.approval_rate:.0%}"
        edits = "—" if s.edit_rate is None else f"{s.edit_rate:.0%}"
        typer.secho(f"{s.spec} {s.spec_version}: {s.verdict}", fg=colour)
        typer.echo(f"    runs {s.runs}/{graduation.WINDOW}  approval {approval}  edit {edits}  — {s.detail}")
    typer.echo("\nGraduation is reported, never applied. A human promotes the zone.")


@app.command("review")
def review_cmd(
    port: Annotated[int, typer.Option("--port", help="Loopback port to serve on.")] = 8765,
) -> None:
    """Open the review surface for pending drafts."""
    root = _root()
    try:
        review.serve(root, port)
    except (ReviewError, ContextError, SpecError, LedgerError, OSError) as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e


@check_app.command("seam")
def check_seam() -> None:
    """Fail if BD Core carries org-specific content that isn't already baselined."""
    root = _root()
    violations = seam.check(root)
    new = [v for v in violations if not v.known]

    for v in violations:
        typer.secho(str(v), fg=typer.colors.RED if not v.known else None)

    known = len(violations) - len(new)
    if new:
        typer.secho(f"\n{len(new)} new seam violation(s). BD Core stays portable.", fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.secho(
        f"\nNo denylisted org nouns found in {', '.join(seam.BD_CORE_DIRS)} ({known} baselined, see "
        "docs/roadmap.md C1+C3). This is a keyword scan, not proof of portability — prose that encodes "
        "one org's motion (an ICP, a buyer shape, a channel mix) passes unseen.",
        fg=typer.colors.GREEN,
    )


@check_app.command("docs")
def check_docs() -> None:
    """Fail if a normative doc claims a repo path that does not exist."""
    root = _root()
    broken = doctruth.check(root)
    for claim in broken:
        typer.secho(str(claim), fg=typer.colors.RED)

    if broken:
        typer.secho(f"\n{len(broken)} doc(s) lying about the repo.", fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.secho(
        "Docs tell the truth — every backticked path and bare `.md` filename this checker "
        "recognizes points at something real. This is not proof against every doc claim: a "
        "path mentioned without backticks, a bare filename with any other extension, or a bare "
        "filename that resolves to the wrong same-named file all pass unseen.",
        fg=typer.colors.GREEN,
    )
