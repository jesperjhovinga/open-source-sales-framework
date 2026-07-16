import pytest

from bdcore.cards import REQUIRED_SECTIONS, failures, validate


@pytest.fixture
def card():
    """A card with every required section and nothing unresolved."""
    return "\n\n".join(f"{section}\nfilled in." for section in REQUIRED_SECTIONS)


def test_complete_card_has_no_problems(card):
    assert validate(card) == []


def test_missing_section_is_reported(card):
    stripped = card.replace("## Guardrails\nfilled in.", "")
    assert "missing required section: ## Guardrails" in validate(stripped)


def test_human_required_markers_are_counted(card):
    problems = validate(card + "\nHUMAN-REQUIRED\nHUMAN-REQUIRED\n")
    assert any("2 unresolved HUMAN-REQUIRED" in p for p in problems)


def test_placeholders_are_reported_with_a_sample(card):
    problems = validate(card + "\n{{org_name}} and {{tone}}\n")
    assert any("2 unfilled template placeholder(s)" in p and "{{org_name}}" in p for p in problems)


def test_draft_status_is_a_note_not_a_failure(card):
    problems = validate(card + "\nStatus: DRAFT\n")
    assert problems and failures(problems) == []


def test_failures_excludes_notes_but_keeps_real_problems(card):
    problems = validate(card + "\nStatus: DRAFT\nHUMAN-REQUIRED\n")
    assert len(failures(problems)) == 1
