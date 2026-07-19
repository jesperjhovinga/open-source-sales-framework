"""Resolve Org Context surfaces for BD Core.

Implements the resolver specified in `core/path-conventions.md` against the
contract in `core/context-contract.md` (v0.2): find the repo root, read the
active org slug from ACTIVE_CONTEXT.md, read the surface's markdown.

Contract Rule 3 and Rule 5 are the whole point of this module: a missing
surface, or one still marked `STATUS: UNFILLED`, is a blocking error. Fail
loud, never silently degrade. Library code raises ContextError; the CLI turns
that into an exit code.
"""

import json
import re
from pathlib import Path

UNFILLED_MARKER = "STATUS: UNFILLED"
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*")

# Contract surface name -> filename, per the table in core/path-conventions.md.
SURFACES = {
    "positioning": "positioning.md",
    "icp": "icp.md",
    "value-props": "value-props.md",
    "competitors": "competitors.md",
    "content": "content-library.md",
    "tone": "tone-of-voice.md",
    "pricing": "pricing.md",
    "connector": "connectors.md",
}


class ContextError(Exception):
    """A context surface could not be resolved. Always a blocking error."""


def find_root(start: Path | None = None) -> Path:
    """Walk up from `start` to the directory holding ACTIVE_CONTEXT.md."""
    here = (start or Path(__file__)).resolve()
    candidates = [here, *here.parents] if here.is_dir() else list(here.parents)
    for parent in candidates:
        if (parent / "ACTIVE_CONTEXT.md").is_file():
            return parent
    raise ContextError(f"no ACTIVE_CONTEXT.md in any parent of {here} — cannot resolve the active org")


def active_org(root: Path | None = None) -> str:
    """Return the active org slug named by ACTIVE_CONTEXT.md."""
    root = root or find_root()
    path = root / "ACTIVE_CONTEXT.md"
    if not path.is_file():
        raise ContextError(f"{path} does not exist — cannot resolve the active org")

    slug = ""
    in_comment = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if in_comment:
            in_comment = "-->" not in stripped
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("<!--"):
            in_comment = "-->" not in stripped  # stays open across lines until closed
            continue
        slug = stripped
        break

    if not slug:
        raise ContextError(f"{path} has no non-comment slug line — cannot resolve the active org")
    if not SLUG_RE.fullmatch(slug):
        raise ContextError(f"{path} slug line {slug!r} is not a valid slug (expected {SLUG_RE.pattern})")
    if slug == "_template":
        raise ContextError(f"{path} names '_template' as the active org — set it to a real org slug")
    if not (root / "contexts" / slug).is_dir():
        raise ContextError(f"{path} names '{slug}' but contexts/{slug}/ does not exist")
    return slug


def surface_path(name: str, root: Path | None = None) -> Path:
    """Path to a contract surface for the active org."""
    if name not in SURFACES:
        known = ", ".join(sorted(SURFACES))
        raise ContextError(f"unknown contract surface '{name}' — known surfaces: {known}")
    root = root or find_root()
    return root / "contexts" / active_org(root) / SURFACES[name]


def read_surface(name: str, root: Path | None = None) -> str:
    """Read a contract surface's markdown. Missing or UNFILLED is a blocking error."""
    path = surface_path(name, root)
    if not path.is_file():
        raise ContextError(f"context.{name} surface not found at {path} — the active org has not filled it in")
    content = path.read_text(encoding="utf-8")
    if UNFILLED_MARKER in content:
        raise ContextError(f"{path} is marked {UNFILLED_MARKER} — the {name} surface is not filled in for this org")
    return content


def config_block(name: str, key: str, root: Path | None = None) -> dict:
    """Extract a machine-readable config block from a surface.

    Surfaces may carry fenced ```json blocks for scripts to consume — see the
    `context.icp` entry in core/context-contract.md. Returns the object at `key`
    from the first block that defines it; callers still validate its fields (see
    engagers.load_prefilter). Only used for object-valued keys today.
    """
    content = read_surface(name, root)
    path = surface_path(name, root)

    for block in re.findall(r"```json\s*(.*?)```", content, re.DOTALL):
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and key in parsed:
            return parsed[key]

    raise ContextError(f"no ```json block in {path} defines '{key}' — cannot load config for context.{name}")
