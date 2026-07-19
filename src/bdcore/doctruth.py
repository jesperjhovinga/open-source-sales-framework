"""Enforce "docs must not lie" — every repo path a doc claims exists, exists.

Scans markdown for backticked repo-relative paths and checks them against the
filesystem. Paths containing template placeholders (`<org>`, `{{name}}`) are
unverifiable by definition and are skipped, not guessed at.

Only *normative* docs are checked. A roadmap names paths it intends to create, a
design doc names the paths its implementation will add, and an audit names paths
it found missing; none of them is lying, so all are exempt. Everything else —
README, architecture, core/, specs/, skills/, contexts/ — describes the repo as
it is now and must be true.

Two claim shapes are recognized. A directory-prefixed path
(`core/language/glossary.md`) says exactly where the file is, so it's checked
at that literal location. A bare backticked filename (`STATE.md`) says nothing
about where it lives — prose legitimately refers to `icp.md` or `SKILL.md`
without spelling out which org's context or which skill — so it's checked by
basename anywhere in the tree instead. That still catches a name that exists
nowhere (a real lie, e.g. `STATE.md`) without demanding every mention spell out
a full path. It is not a location check: a doc could still misdirect a reader
to the wrong copy of a same-named file and this would not catch it — see the
CLI success message.
"""

import re
from pathlib import Path
from typing import NamedTuple

TOP_LEVEL_DIRS = ("core", "contexts", "specs", "skills", "docs", "tests", "src")

# Backticked token starting at a known top-level dir: `core/language/glossary.md`
PATH_PATTERN = re.compile(r"`(" + "|".join(TOP_LEVEL_DIRS) + r")/([^`\s]*)`")

# Backticked bare filename that looks like a repo doc: `STATE.md`, `icp.md`.
# Restricted to `.md` (this module's own subject) and to a plain-filename
# character class — no "/", no "<", "{", "*" — so it can never match a
# directory-prefixed path (those are PATH_PATTERN's job) or a template
# placeholder (those characters simply aren't in the class, so e.g.
# `{{name}}.md` or `<org>.md` never matches at all; no separate placeholder
# check is needed for this pattern).
BARE_FILENAME_PATTERN = re.compile(r"`([A-Za-z0-9_.-]+\.md)`")

PLACEHOLDER_PATTERN = re.compile(r"<[^>]+>|\{\{[^}]*\}\}|\*")


class Claim(NamedTuple):
    source: Path
    line: int
    path: str

    def __str__(self) -> str:
        return f"{self.source}:{self.line}: claims `{self.path}` exists — it does not"


# Tooling scratch, not repo docs: agent worktrees, virtualenvs, and the
# .superpowers/ working directory (untracked briefs full of not-yet-real paths).
EXCLUDED_DIRS = {".git", ".claude", ".venv", ".superpowers", "node_modules"}

# Docs whose job is to name paths that do not exist: the roadmap plans them, a
# design doc specifies what its implementation will add, an audit reports them
# missing. Checking these produces exactly backwards findings — see
# docs/audit-2026-06-25.md, which reports the missing core/methodology/ and
# would otherwise be flagged for claiming it exists.
EXEMPT_DOCS = ("docs/roadmap.md",)
# Anchored to the repo-root docs/ dir. Path.match matches from the right, so a
# bare "docs/audit-*.md" would also exempt skills/x/docs/audit-y.md — a nested
# doc could then lie freely. Match the full relative path instead.
EXEMPT_PATTERNS = (
    re.compile(r"^docs/audit-[^/]*\.md$"),
    # A design doc specifies what an implementation will add; a plan tells an
    # engineer which files to create. Both name future paths by definition.
    re.compile(r"^docs/superpowers/(specs|plans)/[^/]*\.md$"),
)


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
    """Extract (line_number, path) for every verifiable path claim in `text`.

    A directory-prefixed claim (from PATH_PATTERN) always contains a "/"; a
    bare-filename claim (from BARE_FILENAME_PATTERN) never does — `check()`
    uses that to tell the two apart without a separate marker.
    """
    found = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in PATH_PATTERN.finditer(line):
            claimed = f"{match.group(1)}/{match.group(2)}"
            claimed = claimed.split("#", 1)[0].split("?", 1)[0]  # drop link fragment/query
            if not claimed or PLACEHOLDER_PATTERN.search(claimed):
                continue  # template path or bare fragment — nothing concrete to verify
            found.append((lineno, claimed))
        for match in BARE_FILENAME_PATTERN.finditer(line):
            claimed = match.group(1)
            if PLACEHOLDER_PATTERN.search(claimed):
                continue  # can't happen given the pattern's character class, but stay defensive
            found.append((lineno, claimed))
    return found


def _basename_exists(root: Path, name: str) -> bool:
    """True if a file named exactly `name` exists anywhere under root.

    Used for bare-filename claims, which name no directory. Excludes the same
    tooling-scratch directories `markdown_files` skips, so a name that only
    "exists" inside a worktree, venv, or `.superpowers/` brief still counts as
    missing.
    """
    return any(p.is_file() and not EXCLUDED_DIRS.intersection(p.relative_to(root).parts) for p in root.rglob(name))


def check(root: Path) -> list[Claim]:
    """Return every doc claim about a repo path that the filesystem contradicts."""
    broken: list[Claim] = []
    for md in markdown_files(root):
        text = md.read_text(encoding="utf-8")
        for lineno, claimed in claims_in(text):
            exists = _basename_exists(root, claimed) if "/" not in claimed else (root / claimed.rstrip("/")).exists()
            if not exists:
                broken.append(Claim(md.relative_to(root), lineno, claimed))
    return broken
