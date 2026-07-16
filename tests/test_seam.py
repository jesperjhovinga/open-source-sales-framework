"""The seam check guards the repo's first hard rule, so its own edges are tested.

Two properties matter most: contract-call form is never a violation, and the
allowlist actually reaches nested files — Path.match("dir/**") silently does
not, which is how the first version of this module let residue through.
"""

import pytest

from bdcore import seam


@pytest.fixture
def core(tmp_path):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    for d in seam.BD_CORE_DIRS:
        (tmp_path / d).mkdir()
    return tmp_path


@pytest.fixture(autouse=True)
def no_baseline(monkeypatch):
    """Test the rules, not the baselined history of this particular repo."""
    monkeypatch.setattr(seam, "BASELINE", {})


def test_flags_an_org_name_in_core(core):
    (core / "core" / "glossary.md").write_text(
        "- WorkshopParticipant attends an ExampleOrg Workshop.\n", encoding="utf-8"
    )
    violations = seam.check(core)
    assert [v.rule.name for v in violations] == ["org-name"]
    assert violations[0].line == 1


def test_contract_call_arguments_are_not_flagged_as_residue(core):
    # `context.positioning("example_prop_a")` — the quoted proposition ID is a
    # contract-call argument, not residue. Would fire the `proposition` rule if
    # the call weren't blanked first.
    (core / "skills" / "SKILL.md").write_text(
        'Load `context.positioning("example_prop_a")` before drafting.\n', encoding="utf-8"
    )
    assert seam.check(core) == []


def test_residue_on_a_contract_call_line_is_still_caught(core):
    # The F1 regression: a real instruction that references the contract AND
    # names the org default in one sentence. Blanking the whole line would miss both.
    (core / "skills" / "SKILL.md").write_text(
        'Draft via `context.tone("email")`; for ExampleOrg default to Dutch.\n', encoding="utf-8"
    )
    assert sorted(v.rule.name for v in seam.check(core)) == ["named-language", "org-name"]


def test_allowlist_reaches_nested_files(core):
    nested = core / "skills" / "improve-framework-architecture" / "references"
    nested.mkdir(parents=True)
    (nested / "architecture-language.md").write_text("`contexts/<org>/` is the ExampleOrg adapter.\n", encoding="utf-8")
    assert seam.check(core) == []


def test_allowlist_is_scoped_to_its_rule(core):
    # path-conventions may name contexts/ paths, but not carry an org name.
    (core / "core" / "path-conventions.md").write_text(
        "`contexts/example-corp/icp.md` at ExampleOrg\n", encoding="utf-8"
    )
    assert [v.rule.name for v in seam.check(core)] == ["org-name"]


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        ("Read `contexts/example-corp/icp.md` directly.", "raw-context-path"),
        ("Write the samenvatting first.", "language-token"),
        ("Default to Dutch unless told otherwise.", "named-language"),
        ("Filter for NL-based companies.", "geography"),
        ("Pitch Prop A to the founder.", "proposition"),
        ("e.g. 'GreenTech follow-up'", "account-name"),
        ("ready for the CRM (example: a mid-market CRM) import", "mangled-scrub"),
    ],
)
def test_each_rule_catches_its_residue(core, text, rule):
    (core / "skills" / "SKILL.md").write_text(text + "\n", encoding="utf-8")
    assert [v.rule.name for v in seam.check(core)] == [rule]


@pytest.mark.parametrize("placeholder", ["contexts/<org>/icp.md", "contexts/_template/icp.md"])
def test_placeholder_and_template_paths_are_not_raw_paths(core, placeholder):
    (core / "skills" / "SKILL.md").write_text(f"Copy `{placeholder}`.\n", encoding="utf-8")
    assert seam.check(core) == []


def test_violations_within_budget_are_reported_but_not_build_failing(core, monkeypatch):
    monkeypatch.setattr(seam, "BASELINE", {"core/glossary.md": {"org-name": 2}})
    (core / "core" / "glossary.md").write_text("ExampleOrg here\nExampleOrg again\n", encoding="utf-8")

    assert len(seam.check(core)) == 2
    assert all(v.known for v in seam.check(core))
    assert seam.new_violations(core) == []


def test_one_more_than_the_budget_fails(core, monkeypatch):
    # The F2 ratchet: baseline allows 1 org-name, the file now has 2. The extra one fails.
    monkeypatch.setattr(seam, "BASELINE", {"core/glossary.md": {"org-name": 1}})
    (core / "core" / "glossary.md").write_text("ExampleOrg here\nExampleOrg again\n", encoding="utf-8")

    new = seam.new_violations(core)
    assert [v.rule.name for v in new] == ["org-name"]
    assert new[0].line == 2  # the first is within budget, the second overflows


def test_a_new_rule_in_a_baselined_file_still_fails(core, monkeypatch):
    monkeypatch.setattr(seam, "BASELINE", {"core/glossary.md": {"org-name": 1}})
    (core / "core" / "glossary.md").write_text("ExampleOrg\nDefault to Dutch.\n", encoding="utf-8")

    assert [v.rule.name for v in seam.new_violations(core)] == ["named-language"]
