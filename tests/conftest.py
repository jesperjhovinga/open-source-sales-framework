import json

import pytest

PREFILTER = {
    "headline_prefilter": {
        "disqualify_keywords": ["student", "recruiter"],
        "buyer_title_keywords": ["head of", "director"],
        "specialist_keywords": ["data", "analytics"],
    }
}


def icp_markdown(config: dict | None = None) -> str:
    block = json.dumps(config if config is not None else PREFILTER, indent=2)
    return f"# ICP\n\nMachine-readable config:\n\n```json\n{block}\n```\n"


@pytest.fixture
def icp_md():
    """Build an icp.md body around a given headline_prefilter config."""
    return icp_markdown


@pytest.fixture
def repo(tmp_path):
    """A minimal repo root: ACTIVE_CONTEXT.md naming one filled org context."""
    (tmp_path / "ACTIVE_CONTEXT.md").write_text("acme\n", encoding="utf-8")
    org = tmp_path / "contexts" / "acme"
    org.mkdir(parents=True)
    (org / "icp.md").write_text(icp_markdown(), encoding="utf-8")
    (org / "tone-of-voice.md").write_text("# Tone of voice\n\nDirect, no hype.\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def engagement_records():
    """Two actors, one of whom engaged twice (a reaction and a comment)."""
    return [
        {"type": "post", "actor": {"id": "ignored"}},
        {
            "type": "reaction",
            "reactionType": "LIKE",
            "actor": {"id": "a1", "name": "Ada Lovelace", "linkedinUrl": "url/ada", "position": "Head of Data at Acme"},
            "query": {"post": "post-1"},
        },
        {
            "type": "comment",
            "actor": {"id": "a1", "name": "Ada Lovelace", "linkedinUrl": "url/ada", "position": "Head of Data at Acme"},
            "query": {"post": "post-2"},
        },
        {
            "type": "reaction",
            "reactionType": "CELEBRATE",
            "actor": {"id": "a2", "name": "Bob", "linkedinUrl": "url/bob", "position": "Student at Uni"},
            "query": {"post": "post-1"},
        },
    ]
