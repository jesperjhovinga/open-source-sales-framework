"""Enforce "docs must not lie" — every repo path a doc claims exists, exists.

Scans markdown for backticked repo-relative paths and checks them against the
filesystem. Paths containing template placeholders (`<org>`, `{{name}}`) are
unverifiable by definition and are skipped, not guessed at.

Only *normative* docs are checked. A roadmap names paths it intends to create
and an audit names paths it found missing; neither is lying, so both are exempt.
Everything else — README, architecture, core/, specs/, skills/, contexts/ —
describes the repo as it is now and must be true.
"""

import re
from pathlib import Path
from typing import NamedTuple

TOP_LEVEL_DIRS = ("core", "contexts", "specs", "skills", "docs", "tests", "src")

# Backticked token starting at a known top-level dir: `core/language/glossary.md`
PATH_PATTERN = re.compile(r"`(" + "|".join(TOP_LEVEL_DIRS) + r")/([^`\s]*)`")

PLACEHOLDER_PATTERN = re.compile(r"<[^>]+>|\{\{[^}]*\}\}|\*")


class Claim(NamedTuple):
    source: Path
    line: int
    path: str

    def __str__(self) -> str:
        return f"{self.source}:{self.line}: claims `{self.path}` exists — it does not"


EXCLUDED_DIRS = {".git", ".claude", ".venv", "node_modules"}

# Docs whose job is to name paths that do not exist: the roadmap plans them,
# an audit reports them missing. Checking these produces exactly backwards
# findings — see docs/audit-2026-06-25.md, which reports the missing
# core/methodology/ and would otherwise be flagged for claiming it exists.
EXEMPT_DOCS = ("docs/roadmap.md",)
# Anchored to the repo-root docs/ dir. Path.match matches from the right, so a
# bare "docs/audit-*.md" would also exempt skills/x/docs/audit-y.md — a nested
# doc could then lie freely. Match the full relative path instead.
EXEMPT_PATTERNS = (re.compile(r"^docs/audit-[^/]*\.md$"),)


def is_normative(relative: Path) -> bool:
    """True if `relative` describes the repo as it is, and so must be accurate."""
    as_posix = relative.as_posix()
    if as_posix in EXEMPT_DOCS:
        return False
    return not any(pattern.match(as_posix) for pattern in EXEMPT_PATTERNS)


def markdown_files(root: Path) -> list[Path]:
    """Every normative markdown file under `root`, skipping tooling directories.

    Exclusions match on the path *relative to root* — the repo itself may sit
    inside a directory named `.claude` (a git worktree does exactly that).
    """
    return sorted(
        p
        for p in root.rglob("*.md")
        if not EXCLUDED_DIRS.intersection(p.relative_to(root).parts) and is_normative(p.relative_to(root))
    )


def claims_in(text: str) -> list[tuple[int, str]]:
    """Extract (line_number, path) for every verifiable path claim in `text`."""
    found = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in PATH_PATTERN.finditer(line):
            claimed = f"{match.group(1)}/{match.group(2)}"
            claimed = claimed.split("#", 1)[0].split("?", 1)[0]  # drop link fragment/query
            if not claimed or PLACEHOLDER_PATTERN.search(claimed):
                continue  # template path or bare fragment — nothing concrete to verify
            found.append((lineno, claimed))
    return found


def check(root: Path) -> list[Claim]:
    """Return every doc claim about a repo path that the filesystem contradicts."""
    broken: list[Claim] = []
    for md in markdown_files(root):
        text = md.read_text(encoding="utf-8")
        for lineno, claimed in claims_in(text):
            if not (root / claimed.rstrip("/")).exists():
                broken.append(Claim(md.relative_to(root), lineno, claimed))
    return broken
