import pytest

from bdcore.specs import DRAFT_APPROVE, Spec, SpecError, all_specs, draft_approve_specs, load_spec


@pytest.fixture
def specs_root(tmp_path):
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "outreach-drafting.spec.md").write_text(
        "# Spec: Outreach Drafting\n\n"
        "**ID**: `outreach-drafting`\n"
        "**Version**: `v0.1`\n"
        "**Rep-risk zone**: Draft→Approve\n"
        "**Status**: draft\n",
        encoding="utf-8",
    )
    (tmp_path / "specs" / "account-research.spec.md").write_text(
        "# Spec: Account Research\n\n**ID**: `account-research`\n**Version**: `v0.2`\n**Rep-risk zone**: Autonomous\n",
        encoding="utf-8",
    )
    return tmp_path


def test_load_spec_reads_the_header(specs_root):
    spec = load_spec("outreach-drafting", specs_root)
    assert spec == Spec(
        id="outreach-drafting",
        version="v0.1",
        zone=DRAFT_APPROVE,
        path=specs_root / "specs" / "outreach-drafting.spec.md",
    )


def test_load_spec_reads_a_different_zone(specs_root):
    assert load_spec("account-research", specs_root).zone == "Autonomous"


def test_unknown_spec_fails_loud(specs_root):
    with pytest.raises(SpecError, match="no spec"):
        load_spec("does-not-exist", specs_root)


def test_spec_without_a_zone_fails_loud(specs_root):
    (specs_root / "specs" / "broken.spec.md").write_text("**ID**: `broken`\n**Version**: `v0.1`\n", encoding="utf-8")
    with pytest.raises(SpecError, match="Rep-risk zone"):
        load_spec("broken", specs_root)


def test_spec_without_a_version_fails_loud(specs_root):
    (specs_root / "specs" / "nover.spec.md").write_text(
        "**ID**: `nover`\n**Rep-risk zone**: Autonomous\n", encoding="utf-8"
    )
    with pytest.raises(SpecError, match="Version"):
        load_spec("nover", specs_root)


def test_all_specs_finds_every_spec(specs_root):
    assert sorted(s.id for s in all_specs(specs_root)) == ["account-research", "outreach-drafting"]


def test_draft_approve_specs_filters_by_zone(specs_root):
    assert [s.id for s in draft_approve_specs(specs_root)] == ["outreach-drafting"]
