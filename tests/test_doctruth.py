"""The checker must catch real lies without inventing them.

The false-positive tests matter as much as the detection ones: a roadmap names
paths it intends to create and an audit names paths it found missing. Flagging
either would repeat the false finding logged in docs/audit-2026-06-25.md.
"""

import pytest

from bdcore.doctruth import check, claims_in, is_normative


@pytest.fixture
def docs(tmp_path):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "glossary.md").write_text("real file\n", encoding="utf-8")
    return tmp_path


def test_detects_a_path_that_does_not_exist(docs):
    (docs / "README.md").write_text("See `core/methodology/` for blueprints.\n", encoding="utf-8")
    broken = check(docs)
    assert len(broken) == 1
    assert broken[0].path == "core/methodology/"
    assert broken[0].line == 1


def test_accepts_a_path_that_exists(docs):
    (docs / "README.md").write_text("See `core/glossary.md`.\n", encoding="utf-8")
    assert check(docs) == []


def test_trailing_slash_directory_claims_resolve(docs):
    (docs / "README.md").write_text("Look in `core/`.\n", encoding="utf-8")
    assert check(docs) == []


@pytest.mark.parametrize(
    "line",
    [
        "Artifacts go to `contexts/<org>/dossiers/x.md`.",
        "Cards live at `skills/{{name}}/SKILL.md`.",
        "Cases are `tests/*.cases.md`.",
    ],
)
def test_template_paths_are_unverifiable_and_skipped(line):
    assert claims_in(line) == []


def test_unbackticked_prose_is_not_a_claim():
    assert claims_in("we should add core/methodology/ someday") == []


def test_link_fragment_is_stripped_before_checking(docs):
    # `core/glossary.md#terms` points at a real file; the #anchor must not make it "missing".
    (docs / "README.md").write_text("See `core/glossary.md#terms`.\n", encoding="utf-8")
    assert check(docs) == []


def test_roadmap_may_name_paths_it_plans_to_create(docs):
    (docs / "docs" / "roadmap.md").write_text("- [ ] Add `core/methodology/` summaries.\n", encoding="utf-8")
    assert check(docs) == []


def test_audit_may_report_paths_it_found_missing(docs):
    (docs / "docs" / "audit-2026-06-25.md").write_text("`core/archetypes/` does not exist.\n", encoding="utf-8")
    assert check(docs) == []


@pytest.mark.parametrize(
    ("path", "normative"),
    [
        ("README.md", True),
        ("core/path-conventions.md", True),
        ("docs/roadmap.md", False),
        ("docs/audit-2026-06-25.md", False),
        # A design doc specifies paths its implementation will create; a plan
        # tells an engineer which files to create. Both name future paths.
        ("docs/superpowers/specs/2026-07-16-approval-ledger-design.md", False),
        ("docs/superpowers/plans/2026-07-16-approval-ledger.md", False),
        # F4: the audit exemption is anchored to the root docs/ dir. A nested
        # audit-*.md must stay normative, or it could name missing paths freely.
        ("skills/foo/docs/audit-notes.md", True),
        ("core/docs/audit-x.md", True),
        ("docs/superpowers/notes.md", True),
    ],
)
def test_is_normative(path, normative):
    from pathlib import Path

    assert is_normative(Path(path)) is normative


def test_tooling_scratch_dirs_are_not_scanned(docs):
    # .superpowers/ holds untracked agent briefs that name paths not yet created.
    scratch = docs / ".superpowers" / "sdd"
    scratch.mkdir(parents=True)
    (scratch / "task-2-brief.md").write_text("Create `src/bdcore/ghost.py`.\n", encoding="utf-8")
    assert check(docs) == []


def test_nested_audit_doc_cannot_lie(docs):
    nested = docs / "skills" / "foo" / "docs"
    nested.mkdir(parents=True)
    (nested / "audit-notes.md").write_text("See `core/ghost.md`.\n", encoding="utf-8")
    assert [str(c.source) for c in check(docs)] == ["skills/foo/docs/audit-notes.md"]
