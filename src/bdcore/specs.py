"""Read a workflow spec's header — the spec is the registry.

Every spec declares its ID, Version and Rep-risk zone in a header block. The
ledger reads the zone from the spec rather than from a config someone has to
keep in sync: the spec is the contract (see docs/architecture.md).
"""

import re
from pathlib import Path
from typing import NamedTuple

# Exact string used in every spec header. The arrow is U+2192, not "->".
DRAFT_APPROVE = "Draft→Approve"

_FIELD = "^\\*\\*{field}\\*\\*:\\s*`?([^`\n]+?)`?\\s*$"


class SpecError(Exception):
    """A spec could not be found or parsed. Always a blocking error."""


class Spec(NamedTuple):
    id: str
    version: str
    zone: str
    path: Path


def _field(text: str, field: str, path: Path) -> str:
    match = re.search(_FIELD.format(field=field), text, re.MULTILINE)
    if not match:
        raise SpecError(f"{path} has no '**{field}**:' header line — cannot read the spec's contract")
    return match.group(1).strip()


def spec_path(spec_id: str, root: Path) -> Path:
    return root / "specs" / f"{spec_id}.spec.md"


def load_spec(spec_id: str, root: Path) -> Spec:
    """Read a spec's header. Missing or unparseable is a blocking error."""
    path = spec_path(spec_id, root)
    if not path.is_file():
        raise SpecError(f"no spec at {path} — unknown spec id '{spec_id}'")
    text = path.read_text(encoding="utf-8")
    return Spec(
        id=_field(text, "ID", path),
        version=_field(text, "Version", path),
        zone=_field(text, "Rep-risk zone", path),
        path=path,
    )


def all_specs(root: Path) -> list[Spec]:
    return [load_spec(p.name.removesuffix(".spec.md"), root) for p in sorted((root / "specs").glob("*.spec.md"))]


def draft_approve_specs(root: Path) -> list[Spec]:
    """Specs whose zone requires a human approval step — the ones worth measuring."""
    return [s for s in all_specs(root) if s.zone == DRAFT_APPROVE]
