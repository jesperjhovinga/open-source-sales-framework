import json

import pytest

from bdcore.context import ContextError
from bdcore.engagers import (
    FIELDS,
    Prefilter,
    dedupe_actors,
    load_prefilter,
    process,
    run,
    score_headline,
    split_name,
    split_position,
)


@pytest.fixture
def prefilter():
    return Prefilter(
        disqualify=["student", "recruiter"],
        buyer=["head of", "director"],
        specialist=["data", "analytics"],
    )


def test_load_prefilter_reads_the_icp_surface(repo):
    assert load_prefilter(repo).buyer == ["head of", "director"]


def test_load_prefilter_without_config_fails_loud(repo):
    (repo / "contexts" / "acme" / "icp.md").write_text("# ICP\n\nProse only.\n", encoding="utf-8")
    with pytest.raises(ContextError, match="headline_prefilter"):
        load_prefilter(repo)


@pytest.mark.parametrize("missing", ["disqualify_keywords", "buyer_title_keywords", "specialist_keywords"])
def test_load_prefilter_rejects_incomplete_config(repo, icp_md, missing):
    config = {
        "headline_prefilter": {
            "disqualify_keywords": ["student"],
            "buyer_title_keywords": ["head of"],
            "specialist_keywords": ["data"],
        }
    }
    del config["headline_prefilter"][missing]
    (repo / "contexts" / "acme" / "icp.md").write_text(icp_md(config), encoding="utf-8")
    with pytest.raises(ContextError, match=missing):
        load_prefilter(repo)


def test_load_prefilter_rejects_empty_keyword_list(repo, icp_md):
    config = {
        "headline_prefilter": {
            "disqualify_keywords": [],
            "buyer_title_keywords": ["head of"],
            "specialist_keywords": ["data"],
        }
    }
    (repo / "contexts" / "acme" / "icp.md").write_text(icp_md(config), encoding="utf-8")
    with pytest.raises(ContextError, match="disqualify_keywords"):
        load_prefilter(repo)


def test_disqualifier_beats_a_buyer_title(prefilter):
    # A recruiter hiring a Head of Data is not a buyer — disqualify wins.
    score, reason = score_headline("Recruiter for Head of Data roles", prefilter)
    assert score == "fail"
    assert "recruiter" in reason


@pytest.mark.parametrize(
    ("headline", "expected", "reason_fragment"),
    [
        ("Head of Data at Acme", "soft_pass", "buyer title + specialist"),
        ("Director of Operations", "soft_pass", "company unverified"),
        ("Data Engineer at Acme", "soft_pass", "seniority unverified"),
        ("", "soft_pass", "needs enrichment"),
        ("Chef at a restaurant", "fail", "no buyer or specialist signal"),
    ],
)
def test_score_headline(prefilter, headline, expected, reason_fragment):
    score, reason = score_headline(headline, prefilter)
    assert score == expected
    assert reason_fragment in reason


def test_score_headline_is_case_insensitive(prefilter):
    assert score_headline("HEAD OF DATA", prefilter)[0] == "soft_pass"


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        ("Head of Data at Acme", ("Head of Data", "Acme")),
        ("Directeur bij Acme", ("Directeur", "Acme")),
        ("CTO @ Acme", ("CTO", "Acme")),
        ("CTO - Acme", ("CTO", "Acme")),
        ("CTO | Acme", ("CTO", "Acme")),
        ("Freelancer", ("Freelancer", "")),
    ],
)
def test_split_position(position, expected):
    assert split_position(position) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Ada Lovelace", ("Ada", "Lovelace")),
        ("Ada van der Berg", ("Ada", "van der Berg")),
        ("Cher", ("Cher", "")),
        ("", ("", "")),
    ],
)
def test_split_name(name, expected):
    assert split_name(name) == expected


def test_dedupe_collapses_one_actor_across_posts(engagement_records):
    actors = dedupe_actors(engagement_records)
    assert set(actors) == {"a1", "a2"}
    assert actors["a1"]["posts_engaged"] == {"post-1", "post-2"}
    assert actors["a1"]["has_comment"] is True


def test_dedupe_ignores_non_engagement_records(engagement_records):
    assert "ignored" not in dedupe_actors(engagement_records)


def test_process_scores_sorts_and_shapes_rows(engagement_records, prefilter):
    rows = process(engagement_records, prefilter, seed_url="url/seed")

    assert [r["icp_score"] for r in rows] == ["soft_pass", "fail"]  # soft_pass sorts first
    ada, bob = rows
    assert (ada["first_name"], ada["last_name"]) == ("Ada", "Lovelace")
    assert (ada["job_title"], ada["company_name"]) == ("Head of Data", "Acme")
    assert ada["engagement_type"] == "comment"  # a comment outranks a reaction
    assert sorted(ada["posts_engaged"].split(" | ")) == ["post-1", "post-2"]
    assert ada["source_profile"] == "url/seed"
    assert bob["icp_score"] == "fail"


def test_process_emits_every_declared_column(engagement_records, prefilter):
    assert list(process(engagement_records, prefilter)[0]) == FIELDS


def test_run_writes_csv_using_the_active_org_config(repo, engagement_records, tmp_path):
    source = tmp_path / "engagers.json"
    source.write_text(json.dumps(engagement_records), encoding="utf-8")
    out = tmp_path / "out.csv"

    rows = run(source, out, seed_url="url/seed", root=repo)

    assert len(rows) == 2
    header, *body = out.read_text(encoding="utf-8").splitlines()
    assert header == ",".join(FIELDS)
    assert len(body) == 2
