"""The contract's fail-loud rules are the framework's governance promise.

Contract Rule 3 says a missing surface is a blocking error and Rule 5 says an
UNFILLED one counts as missing. These tests exist so that promise is checked,
not just documented.
"""

import pytest

from bdcore.context import ContextError, active_org, config_block, find_root, read_surface, surface_path


def test_find_root_walks_up_to_active_context(repo):
    nested = repo / "contexts" / "acme"
    assert find_root(nested) == repo


def test_find_root_without_active_context_fails_loud(tmp_path):
    with pytest.raises(ContextError, match="no ACTIVE_CONTEXT.md"):
        find_root(tmp_path)


def test_active_org_reads_the_slug(repo):
    assert active_org(repo) == "acme"


def test_active_org_skips_comments_and_headings(repo):
    (repo / "ACTIVE_CONTEXT.md").write_text("# which org\n<!-- a note -->\n\nacme\n", encoding="utf-8")
    assert active_org(repo) == "acme"


def test_active_org_rejects_the_template(repo):
    (repo / "ACTIVE_CONTEXT.md").write_text("_template\n", encoding="utf-8")
    with pytest.raises(ContextError, match="_template"):
        active_org(repo)


def test_active_org_rejects_empty_file(repo):
    (repo / "ACTIVE_CONTEXT.md").write_text("# only a comment\n", encoding="utf-8")
    with pytest.raises(ContextError, match="no non-comment slug"):
        active_org(repo)


def test_active_org_rejects_slug_without_a_context_dir(repo):
    (repo / "ACTIVE_CONTEXT.md").write_text("ghost\n", encoding="utf-8")
    with pytest.raises(ContextError, match="contexts/ghost/ does not exist"):
        active_org(repo)


def test_read_surface_returns_content(repo):
    assert "Direct, no hype." in read_surface("tone", repo)


def test_surface_path_maps_contract_name_to_file(repo):
    assert surface_path("tone", repo).name == "tone-of-voice.md"


def test_unknown_surface_fails_loud(repo):
    with pytest.raises(ContextError, match="unknown contract surface"):
        surface_path("vibes", repo)


def test_missing_surface_fails_loud(repo):
    with pytest.raises(ContextError, match="not found"):
        read_surface("pricing", repo)


def test_unfilled_surface_is_treated_as_missing(repo):
    (repo / "contexts" / "acme" / "pricing.md").write_text("# Pricing\nSTATUS: UNFILLED\n", encoding="utf-8")
    with pytest.raises(ContextError, match="UNFILLED"):
        read_surface("pricing", repo)


def test_config_block_extracts_machine_readable_config(repo):
    config = config_block("icp", "headline_prefilter", repo)
    assert config["buyer_title_keywords"] == ["head of", "director"]


def test_config_block_skips_unrelated_and_invalid_json_blocks(repo, icp_md):
    icp = repo / "contexts" / "acme" / "icp.md"
    icp.write_text('```json\n{not json,}\n```\n\n```json\n{"other": 1}\n```\n' + icp_md(), encoding="utf-8")
    assert config_block("icp", "headline_prefilter", repo)["disqualify_keywords"] == ["student", "recruiter"]


def test_config_block_missing_key_fails_loud(repo):
    (repo / "contexts" / "acme" / "icp.md").write_text("# ICP\n\nNo config here.\n", encoding="utf-8")
    with pytest.raises(ContextError, match="headline_prefilter"):
        config_block("icp", "headline_prefilter", repo)
