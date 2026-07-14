#!/usr/bin/env python3
"""Validate a BD skill card before it's considered done.

Checks *shape*, not truth: every required section is present and no
unresolved markers (HUMAN-REQUIRED, {{placeholder}}) remain. A human still
certifies correctness — see skills/bd-skill-card/SKILL.md.

Usage:
    python3 validate_card.py path/to/skill-card.md
Exit code 0 = pass, 1 = problems found (printed to stdout).
"""
import re
import sys

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


def validate(text: str) -> list[str]:
    problems: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            problems.append(f"missing required section: {section}")

    if "HUMAN-REQUIRED" in text:
        n = text.count("HUMAN-REQUIRED")
        problems.append(
            f"{n} unresolved HUMAN-REQUIRED marker(s) — source the value or confirm with the BDOwner"
        )

    placeholders = re.findall(r"\{\{.*?\}\}", text)
    if placeholders:
        sample = ", ".join(sorted(set(placeholders))[:5])
        problems.append(
            f"{len(placeholders)} unfilled template placeholder(s) remain, e.g. {sample}"
        )

    if "Status: DRAFT" in text or "Status:** DRAFT" in text:
        # Not a hard failure — just a reminder the card is unreviewed.
        problems.append(
            "note: card still marked DRAFT — flip to reviewed only after the BDOwner confirms"
        )

    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 validate_card.py path/to/skill-card.md")
        return 1
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"could not read card: {e}")
        return 1

    problems = validate(text)
    hard = [p for p in problems if not p.startswith("note:")]
    for p in problems:
        print(("  - " if p.startswith("note:") else "FAIL: ") + p)
    if hard:
        print(f"\n{len(hard)} problem(s) to fix.")
        return 1
    print("OK — card shape valid (human review still required).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
