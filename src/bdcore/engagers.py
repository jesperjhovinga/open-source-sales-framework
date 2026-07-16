"""Prospect sourcing — turn raw Apify engagement records into a pre-filtered CSV.

Reads Apify JSON, deduplicates by actor ID, applies the headline ICP pre-filter
loaded from `context.icp`, and writes the sourcing CSV. The pre-filter scores a
LinkedIn *headline* only — never a verified fit. Everything that survives is
`soft_pass`, meaning "worth researching", not "qualified".
"""

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple

from bdcore.context import ContextError, config_block

FIELDS = [
    "first_name",
    "last_name",
    "linkedin_url",
    "job_title",
    "company_name",
    "company_size_est",
    "email",
    "phone",
    "location",
    "icp_score",
    "icp_notes",
    "engagement_type",
    "posts_engaged",
    "source_profile",
    "sourced_date",
]

# Headline separators splitting "<title> at <company>". Input-parsing heuristics,
# not ICP policy — see docs/roadmap.md C1+C3 for the open question on whether
# these belong in the headline_prefilter config instead.
POSITION_SEPARATORS = (" at ", " bij ", " @ ", " - ", " | ")

REQUIRED_PREFILTER_KEYS = ("disqualify_keywords", "buyer_title_keywords", "specialist_keywords")


class Prefilter(NamedTuple):
    disqualify: list[str]
    buyer: list[str]
    specialist: list[str]


def load_prefilter(root: Path | None = None) -> Prefilter:
    """Load the headline pre-filter from the active org's `context.icp` surface.

    No defaults, no fallback lists — an org that hasn't defined its keywords
    gets a blocking error, not a guess.
    """
    config = config_block("icp", "headline_prefilter", root)
    if not isinstance(config, dict):
        raise ContextError("context.icp headline_prefilter is not a JSON object")

    for key in REQUIRED_PREFILTER_KEYS:
        value = config.get(key)
        if not isinstance(value, list) or not value:
            raise ContextError(f"context.icp headline_prefilter.{key} is missing or empty")

    return Prefilter(
        disqualify=config["disqualify_keywords"],
        buyer=config["buyer_title_keywords"],
        specialist=config["specialist_keywords"],
    )


def score_headline(position: str, prefilter: Prefilter) -> tuple[str, str]:
    """Score a LinkedIn headline against the org's ICP keywords. Returns (score, reason)."""
    p = (position or "").lower()

    for term in prefilter.disqualify:
        if term in p:
            return "fail", f"disqualifier keyword: {term}"

    has_buyer = any(t in p for t in prefilter.buyer)
    has_specialist = any(s in p for s in prefilter.specialist)

    if has_buyer and has_specialist:
        return "soft_pass", "buyer title + specialist context (headline)"
    if has_buyer:
        return "soft_pass", "buyer title in headline; company unverified"
    if has_specialist:
        return "soft_pass", "specialist context; seniority unverified"
    if not position:
        return "soft_pass", "no position data — needs enrichment"
    return "fail", "no buyer or specialist signal in headline"


def split_name(name: str) -> tuple[str, str]:
    parts = name.strip().split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def split_position(position: str) -> tuple[str, str]:
    """Split a headline into (title, company) on the first known separator."""
    lowered = position.lower()
    for sep in POSITION_SEPARATORS:
        if sep in lowered:
            idx = lowered.index(sep)
            return position[:idx].strip(), position[idx + len(sep) :].strip()
    return position, ""


def dedupe_actors(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Collapse engagement records into one entry per actor ID."""
    actors: dict[str, dict[str, Any]] = {}
    for r in records:
        if r.get("type") not in ("reaction", "comment"):
            continue
        actor = r.get("actor")
        if not isinstance(actor, dict):
            continue  # malformed record — no actor object
        aid = actor.get("id")
        if not aid:
            continue  # actor without an id — nothing to dedupe on
        entry = actors.setdefault(
            aid,
            {
                "name": actor.get("name", ""),
                "linkedin_url": actor.get("linkedinUrl", ""),
                "position": actor.get("position", ""),
                "posts_engaged": set(),
                "engagement_types": set(),
                "has_comment": False,
            },
        )
        entry["posts_engaged"].add(r.get("query", {}).get("post", ""))
        if r.get("type") == "comment":
            entry["engagement_types"].add("comment")
            entry["has_comment"] = True
        else:
            entry["engagement_types"].add(r.get("reactionType", "LIKE").lower())
    return actors


def process(records: list[dict[str, Any]], prefilter: Prefilter, seed_url: str = "") -> list[dict[str, str]]:
    """Dedupe, score, and sort engagement records into CSV-ready rows."""
    today = date.today().isoformat()
    rows: list[dict[str, str]] = []

    for actor in dedupe_actors(records).values():
        position = actor["position"] or ""
        score, notes = score_headline(position, prefilter)
        title, company = split_position(position)
        first, last = split_name(actor["name"])
        # sorted() so a reaction-only actor's type is stable across runs (sets are hash-ordered)
        engagement = "comment" if actor["has_comment"] else next(iter(sorted(actor["engagement_types"])), "reaction")

        rows.append(
            {
                "first_name": first,
                "last_name": last,
                "linkedin_url": actor["linkedin_url"],
                "job_title": title,
                "company_name": company,
                "company_size_est": "",
                "email": "",
                "phone": "",
                "location": "",
                "icp_score": score,
                "icp_notes": notes,
                "engagement_type": engagement,
                "posts_engaged": " | ".join(sorted(p for p in actor["posts_engaged"] if p)),
                "source_profile": seed_url,
                "sourced_date": today,
            }
        )

    # soft_pass before fail; within each group, comments before reactions.
    order = {"soft_pass": 0, "fail": 1}
    rows.sort(key=lambda r: (order.get(r["icp_score"], 2), 0 if r["engagement_type"] == "comment" else 1))
    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run(input_path: Path, output_path: Path, seed_url: str = "", root: Path | None = None) -> list[dict[str, str]]:
    records = json.loads(Path(input_path).read_text(encoding="utf-8"))
    rows = process(records, load_prefilter(root), seed_url)
    write_csv(rows, Path(output_path))
    return rows
