"""Every skill's frontmatter must actually parse as YAML.

Claude loads a skill by reading this block. When it fails to parse, the skill
loads with *empty metadata* — no name, no description — so it is silently never
triggered. Nothing else in the repo catches that: the file looks fine, the
markdown renders, and the skill simply never runs.

`bd-user-rules` shipped broken this way. Its description contained
"any BD task: prospecting" — a colon-space inside an unquoted scalar, which YAML
reads as a mapping. The house rules every other BD skill inherits were loading as
nothing at all, and only `claude plugin validate` surfaced it.
"""

import re
from pathlib import Path

import pytest
import yaml

SKILLS = sorted(Path(__file__).resolve().parents[1].glob("skills/*/SKILL.md"))
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def ids(paths: list[Path]) -> list[str]:
    return [p.parent.name for p in paths]


def frontmatter_of(skill: Path) -> str:
    """The raw frontmatter block, or fail naming the skill — never an AttributeError."""
    match = FRONTMATTER.match(skill.read_text(encoding="utf-8"))
    if not match:
        pytest.fail(f"{skill} has no --- frontmatter block")
    return match.group(1)


def test_the_repo_has_skills_to_check():
    # Guards the glob itself: a broken path would make every test below vacuous.
    assert len(SKILLS) > 10


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_frontmatter_parses_as_yaml(skill: Path):
    try:
        parsed = yaml.safe_load(frontmatter_of(skill))
    except yaml.YAMLError as e:
        pytest.fail(f"{skill} frontmatter is not valid YAML — the skill would load with no metadata: {e}")
    assert isinstance(parsed, dict), f"{skill} frontmatter is not a mapping"


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_frontmatter_carries_name_and_description(skill: Path):
    parsed = yaml.safe_load(frontmatter_of(skill))
    assert parsed.get("name"), f"{skill} declares no name — it cannot be invoked"
    assert parsed.get("description"), f"{skill} declares no description — it will never be triggered"


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_name_matches_its_directory(skill: Path):
    # Claude resolves a skill by directory; a mismatched name is a silent misfire.
    parsed = yaml.safe_load(frontmatter_of(skill))
    assert parsed["name"] == skill.parent.name
