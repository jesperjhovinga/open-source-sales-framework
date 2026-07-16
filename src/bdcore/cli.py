"""`bd` — the framework's command line.

Library code raises ContextError; this layer is the only place that turns a
failure into a message and an exit code.
"""

from pathlib import Path
from typing import Annotated

import typer

from bdcore import cards, doctruth, engagers, seam
from bdcore.context import ContextError, active_org, find_root

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
    try:
        rows = engagers.run(input_json, output_csv, seed_url, root)
    except ContextError as e:
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
        f"\nSeam clean — no new violations ({known} baselined, see docs/roadmap.md C1+C3).", fg=typer.colors.GREEN
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
    typer.secho("Docs tell the truth — every claimed path exists.", fg=typer.colors.GREEN)
