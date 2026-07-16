"""Enforce "the seam is law" — BD Core carries no org-specific content.

`core/`, `specs/` and `skills/` are portable. Company names, language defaults,
geography rules, pitch prose and ICP criteria belong in `contexts/<org>/` and
are reached through the contract (`core/context-contract.md`). This module
greps BD Core for content that should have stayed behind the seam.

Every rule and every allowlist entry below is grounded in a violation that was
present in the tree when it was written — none are speculative.

The BASELINE records violations that already existed when this check was added.
They are reported but do not fail the build, so the check can land without
blocking on the domain decisions in docs/roadmap.md C1+C3. Anything *not*
baselined fails. Delete entries as files get cleaned; the ratchet only tightens.
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

BD_CORE_DIRS = ("core", "specs", "skills")


class Rule(NamedTuple):
    name: str
    pattern: re.Pattern[str]
    why: str


RULES = [
    Rule(
        "org-name",
        re.compile(r"\bExampleOrg\b"),
        "org proper noun in BD Core — belongs in contexts/<org>/",
    ),
    Rule(
        "raw-context-path",
        re.compile(r"contexts/(?!<org>|<org-slug>|<slug>|_template)[a-z0-9-]+/"),
        "raw org-context path — read the surface via the contract instead",
    ),
    Rule(
        "language-token",
        re.compile(
            r"\b(samenvatting|gesprek|aantekeningen|verwerk|onderwerp|functie|afzender|referentie|Directeur|notitie)\b"
        ),
        "non-English token — language is an org value, see context.tone",
    ),
    Rule(
        "named-language",
        re.compile(r"\b(Dutch|Nederlands|Flemish|Vlaams)\b"),
        "named language default — belongs in the context.tone Language field",
    ),
    Rule(
        "geography",
        re.compile(r"\b(NL|Netherlands|Holland|Benelux|Randstad)\b"),
        "geography rule — belongs in context.icp",
    ),
    Rule(
        "proposition",
        re.compile(r"EXAMPLE PROP [AB]|\bProp [AB]\b|Delivery Scan|Blueprint Session"),
        "proposition ID or offer-format name — belongs in context.positioning",
    ),
    Rule(
        "account-name",
        re.compile(r"GreenControl|GreenTech|helioSENSE|HelioCORE|\bJII\b|ClientCaseB"),
        "real or semi-sanitized account name — belongs in contexts/<org>/",
    ),
    Rule(
        "mangled-scrub",
        re.compile(r"the CRM \(example:"),
        "botched find/replace artifact from scrubbing an org's CRM product name",
    ),
]

# Contract-call form is the correct way to reach org content. A call like
# `context.tone("email_cold")` is blanked from the line before the rules run, so
# its quoted channel/proposition arguments can't be mistaken for residue — but
# residue elsewhere on the same line is still caught. (Skipping the whole line
# instead would let `... context.tone(...); default to Dutch for ExampleOrg` pass.)
CONTRACT_CALL = re.compile(r"context\.(positioning|icp|tone|content|competitors|connector|pricing)\([^)]*\)")

# Exact file path, or a directory prefix ending in "/", -> rules it may match.
# A directory prefix exempts EVERY line under it from the listed rules, including
# files added later — coarse by design, justified only where the whole subtree's
# subject is the seam itself. Keep this list tiny for that reason.
ALLOWLIST: dict[str, set[str]] = {
    # The path table and the contract rules must name contexts/<org>/ — they define it.
    "core/path-conventions.md": {"raw-context-path"},
    "core/context-contract.md": {"raw-context-path"},
    # This skill's whole subject is the seam; it names the parts to describe them.
    "skills/improve-framework-architecture/": {"raw-context-path", "org-name"},
}

# Violations present when this check landed — extracted from the tree, not guessed.
# Reported, but not build-failing: clearing them needs the org-content decisions
# tracked in docs/roadmap.md C1+C3, which are the BDOwner's to make.
#
# Keyed file -> rule -> COUNT, not a bare set: the count is the ratchet. Adding
# one more instance of an already-baselined rule to an already-baselined file
# pushes the count over budget and fails the build. Extract residue and lower the
# number (delete the entry at 0). It only ever tightens.
BASELINE: dict[str, dict[str, int]] = {
    "core/context-contract.md": {"org-name": 1},
    "core/language/glossary.md": {"org-name": 1},
    "skills/account-research/SKILL.md": {"geography": 2, "language-token": 1, "org-name": 4, "proposition": 2},
    "skills/bd-skill-card/assets/skill-card-template.md": {"named-language": 1},
    "skills/bd-skill-evolution/SKILL.md": {"language-token": 1},
    "skills/bd-user-rules/SKILL.md": {"language-token": 2, "org-name": 1, "proposition": 1},
    "skills/call-notes-to-crm/SKILL.md": {"account-name": 2, "language-token": 1, "named-language": 1, "org-name": 3},
    "skills/call-notes-to-crm/references/callnote-template.md": {"account-name": 6, "geography": 1, "org-name": 5},
    "skills/event-invite/SKILL.md": {"org-name": 1},
    "specs/account-research.spec.md": {"proposition": 1},
    "specs/discovery-call-prep.spec.md": {"proposition": 1},
    "specs/prospect-sourcing.spec.md": {"geography": 5},
}


class Violation(NamedTuple):
    path: str
    line: int
    rule: Rule
    text: str
    known: bool = False  # set by check(): within the file+rule's baselined budget

    def __str__(self) -> str:
        marker = "known" if self.known else "SEAM"
        return f"{marker}: {self.path}:{self.line}: [{self.rule.name}] {self.why_line()}"

    def why_line(self) -> str:
        snippet = self.text.strip()
        if len(snippet) > 90:
            snippet = snippet[:87] + "..."
        return f"{self.rule.why}\n        {snippet}"


def core_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for d in BD_CORE_DIRS:
        files.extend(p for p in (root / d).rglob("*") if p.is_file() and p.suffix in (".md", ".py"))
    return sorted(files)


def allowed(relative: str, rule: str) -> bool:
    """True if `relative` is exempt from `rule`.

    Prefix matching is deliberate over Path.match(): its "**" does not recurse,
    which silently un-exempts nested files.
    """
    for pattern, rules in ALLOWLIST.items():
        if rule not in rules:
            continue
        if relative == pattern or (pattern.endswith("/") and relative.startswith(pattern)):
            return True
    return False


def _scan(root: Path) -> list[Violation]:
    """Every seam violation in BD Core, in stable (file, line) order, known unset."""
    violations: list[Violation] = []
    for path in core_files(root):
        relative = path.relative_to(root).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            scanned = CONTRACT_CALL.sub("", line)  # blank contract calls; keep the rest of the line
            for rule in RULES:
                if rule.pattern.search(scanned) and not allowed(relative, rule.name):
                    violations.append(Violation(relative, lineno, rule, line))
    return violations


def check(root: Path) -> list[Violation]:
    """Every seam violation, each marked `known` if it fits its file+rule budget.

    The first N matches of a rule in a file (in line order) are within the
    baselined budget N and marked known; the N+1th onward are new.
    """
    seen: dict[tuple[str, str], int] = defaultdict(int)
    result: list[Violation] = []
    for v in _scan(root):
        key = (v.path, v.rule.name)
        seen[key] += 1
        budget = BASELINE.get(v.path, {}).get(v.rule.name, 0)
        result.append(v._replace(known=seen[key] <= budget))
    return result


def new_violations(root: Path) -> list[Violation]:
    """Violations over their baselined budget — these fail the build."""
    return [v for v in check(root) if not v.known]
