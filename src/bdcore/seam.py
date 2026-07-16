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
baselined fails.

Each baselined violation is grandfathered by a fingerprint of its offending
line, not by a count — so swapping one residue line for a different one in the
same file fails the build (a count would mask it). Editing a baselined line
changes its fingerprint and re-flags it: touching residue means dealing with
it. Regenerate the fingerprints after extracting residue with:

    uv run python -m bdcore.seam

Delete entries as files get cleaned; the ratchet only tightens.
"""

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import NamedTuple

from bdcore.context import SURFACES

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
# Surface names come from the contract itself so the two never drift apart.
_SURFACE_NAMES = "|".join(re.escape(name.replace("-", "_")) for name in SURFACES)
CONTRACT_CALL = re.compile(rf"context\.({_SURFACE_NAMES})\([^)]*\)")

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
# Keyed file -> rule -> [line fingerprints]. A violation is grandfathered only if
# its offending line's fingerprint is listed. Fingerprints (not counts) mean a
# swapped-in residue line fails even when the tally is unchanged. Regenerate with
# `uv run python -m bdcore.seam` after extracting residue.
BASELINE: dict[str, dict[str, list[str]]] = {
    "core/context-contract.md": {"org-name": ["2d556eea8788"]},
    "core/language/glossary.md": {"org-name": ["62c285514136"]},
    "skills/account-research/SKILL.md": {
        "geography": ["af1119226bc6", "4623fdf9bfbf"],
        "language-token": ["7db484e1b02d"],
        "org-name": ["ea99c2da0ca1", "efe2e0306421", "02f4c37c67ec", "17e493f92f69"],
        "proposition": ["6e9724a08ba4", "02f4c37c67ec"],
    },
    "skills/bd-skill-card/assets/skill-card-template.md": {"named-language": ["3b95a674f8c0"]},
    "skills/bd-skill-evolution/SKILL.md": {"language-token": ["aa0e60207de7"]},
    "skills/bd-user-rules/SKILL.md": {
        "language-token": ["ee7579d9ebd0", "84fefe8a8ae4"],
        "org-name": ["ee7579d9ebd0"],
        "proposition": ["a90dcc09e33a"],
    },
    "skills/call-notes-to-crm/SKILL.md": {
        "account-name": ["4b954fb228e8", "b0da59ef0070"],
        "language-token": ["6848a773cf83"],
        "named-language": ["d101eb9085d3"],
        "org-name": ["bb1c1da81bb1", "0e5a6b82c291", "ef06f5a345a7"],
    },
    "skills/call-notes-to-crm/references/callnote-template.md": {
        "account-name": [
            "1ab80d06f754",
            "ab79936cb6d4",
            "6a577d042300",
            "b12192711752",
            "854c92786843",
            "8ba43d1f2aec",
        ],
        "geography": ["d72d9c91abe6"],
        "org-name": ["fcf36b5c3be2", "1d1843b2d0bd", "fe4621c3575d", "6a577d042300", "e327fb982baa"],
    },
    "specs/account-research.spec.md": {"proposition": ["717d2691339e"]},
    "specs/discovery-call-prep.spec.md": {"proposition": ["f4b05fc2b2e9"]},
    "specs/prospect-sourcing.spec.md": {
        "geography": ["e433fc32a7e1", "102a2af039d7", "60d6413a21db", "3c9ad9849044", "cec7029995ee"],
    },
}


def fingerprint(text: str) -> str:
    """Stable short fingerprint of an offending line, whitespace-normalized."""
    normalized = " ".join(text.split())
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


class Violation(NamedTuple):
    path: str
    line: int
    rule: Rule
    text: str
    known: bool = False  # set by check(): line fingerprint is in the baseline

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.text)

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
    """Every seam violation, each marked `known` if its line is grandfathered.

    A violation is known when its line fingerprint appears in the baseline for
    its (file, rule). Exact-duplicate residue lines are matched as a multiset, so
    two identical baselined lines grandfather exactly two occurrences, no more.
    """
    remaining = {(f, r): Counter(fps) for f, rules in BASELINE.items() for r, fps in rules.items()}
    result: list[Violation] = []
    for v in _scan(root):
        budget = remaining.get((v.path, v.rule.name))
        known = bool(budget and budget[v.fingerprint] > 0)
        if known:
            budget[v.fingerprint] -= 1
        result.append(v._replace(known=known))
    return result


def new_violations(root: Path) -> list[Violation]:
    """Violations whose line is not grandfathered — these fail the build."""
    return [v for v in check(root) if not v.known]


def _render_baseline(root: Path) -> str:
    """Render the current tree's violations as a BASELINE literal, for regeneration."""
    grouped: dict[str, dict[str, list[str]]] = {}
    for v in _scan(root):
        if allowed(v.path, v.rule.name):
            continue
        grouped.setdefault(v.path, {}).setdefault(v.rule.name, []).append(v.fingerprint)
    lines = ["BASELINE: dict[str, dict[str, list[str]]] = {"]
    for path in sorted(grouped):
        rules = ", ".join(f'"{r}": {grouped[path][r]}' for r in sorted(grouped[path]))
        lines.append(f'    "{path}": {{{rules}}},')
    lines.append("}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Reprints BASELINE from the current tree so it can be pasted back after
    # residue is extracted. Run from the repo root: `uv run python -m bdcore.seam`.
    print(_render_baseline(Path.cwd()))
