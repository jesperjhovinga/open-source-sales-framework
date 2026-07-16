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


def _baseline(text: str, rule: str = "org-name") -> dict:
    return {"core/glossary.md": {rule: [seam.fingerprint(text)]}}


def test_grandfathered_lines_are_reported_but_not_build_failing(core, monkeypatch):
    monkeypatch.setattr(
        seam,
        "BASELINE",
        {"core/glossary.md": {"org-name": [seam.fingerprint("ExampleOrg one"), seam.fingerprint("ExampleOrg two")]}},
    )
    (core / "core" / "glossary.md").write_text("ExampleOrg one\nExampleOrg two\n", encoding="utf-8")

    assert len(seam.check(core)) == 2
    assert all(v.known for v in seam.check(core))
    assert seam.new_violations(core) == []


def test_one_more_than_the_baseline_fails(core, monkeypatch):
    monkeypatch.setattr(seam, "BASELINE", _baseline("ExampleOrg here"))
    (core / "core" / "glossary.md").write_text("ExampleOrg here\nExampleOrg also here\n", encoding="utf-8")

    new = seam.new_violations(core)
    assert [v.rule.name for v in new] == ["org-name"]
    assert new[0].line == 2  # the grandfathered line is known; the new one fails


def test_swapping_a_baselined_line_for_a_different_one_fails(core, monkeypatch):
    # The reviewer's finding: a count would mask this (still one org-name). The
    # fingerprint doesn't — the grandfathered line is gone, a new one took its place.
    monkeypatch.setattr(seam, "BASELINE", _baseline("ExampleOrg was here"))
    (core / "core" / "glossary.md").write_text("A different ExampleOrg line entirely\n", encoding="utf-8")

    new = seam.new_violations(core)
    assert [v.rule.name for v in new] == ["org-name"]
    assert new[0].line == 1


def test_editing_a_baselined_line_re_flags_it(core, monkeypatch):
    monkeypatch.setattr(seam, "BASELINE", _baseline("ExampleOrg builds widgets"))
    (core / "core" / "glossary.md").write_text("ExampleOrg builds gadgets\n", encoding="utf-8")

    assert len(seam.new_violations(core)) == 1  # fingerprint changed → no longer grandfathered


def test_a_new_rule_in_a_baselined_file_still_fails(core, monkeypatch):
    monkeypatch.setattr(seam, "BASELINE", _baseline("ExampleOrg"))
    (core / "core" / "glossary.md").write_text("ExampleOrg\nDefault to Dutch.\n", encoding="utf-8")

    assert [v.rule.name for v in seam.new_violations(core)] == ["named-language"]
