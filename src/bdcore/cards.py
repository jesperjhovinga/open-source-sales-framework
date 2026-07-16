"""Validate a BD skill card before it's considered done.

Checks *shape*, not truth: every required section is present and no unresolved
markers (HUMAN-REQUIRED, {{placeholder}}) remain. A human still certifies
correctness — see skills/bd-skill-card/SKILL.md.
"""

import re

REQUIRED_SECTIONS = [
    "## Identity",
    "## Trigger",
    "## Rep-risk zone",
    "## Inputs",
    "## Outputs",
    "## Connectors & permissions",
    "## Guardrails",
    "## Limitations",
    "## Provenance",
]

NOTE_PREFIX = "note: "


def validate(text: str) -> list[str]:
    """Return problems found in a card. Entries prefixed `note: ` are advisory, not failures."""
    problems: list[str] = []

    problems.extend(f"missing required section: {section}" for section in REQUIRED_SECTIONS if section not in text)

    if "HUMAN-REQUIRED" in text:
        n = text.count("HUMAN-REQUIRED")
        problems.append(f"{n} unresolved HUMAN-REQUIRED marker(s) — source the value or confirm with the BDOwner")

    placeholders = re.findall(r"\{\{.*?\}\}", text)
    if placeholders:
        sample = ", ".join(sorted(set(placeholders))[:5])
        problems.append(f"{len(placeholders)} unfilled template placeholder(s) remain, e.g. {sample}")

    if "Status: DRAFT" in text or "Status:** DRAFT" in text:
        problems.append(f"{NOTE_PREFIX}card still marked DRAFT — flip to reviewed only after the BDOwner confirms")

    return problems


def failures(problems: list[str]) -> list[str]:
    """The subset of `problems` that are hard failures rather than advisory notes."""
    return [p for p in problems if not p.startswith(NOTE_PREFIX)]
