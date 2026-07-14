"""
Prospect Sourcing — Engager Processing Script
Reads Apify JSON, deduplicates, applies headline ICP pre-filter, outputs CSV.
Usage: python3 process_engagers.py <input.json> <output.csv> [seed_url] [--icp <path/to/icp.md>]
"""
import json, csv, sys, re, argparse
from datetime import date
from pathlib import Path


def resolve_icp_path():
    """
    Walk up from this script's own location to find the repo root (the
    directory containing ACTIVE_CONTEXT.md), read the active org slug, and
    return the path to that org's contexts/<slug>/icp.md.

    Fails loud (prints a one-line message and exits 1) if ACTIVE_CONTEXT.md
    can't be found, the slug is empty, or the slug is "_template".
    """
    here = Path(__file__).resolve()
    root = None
    for parent in here.parents:
        if (parent / "ACTIVE_CONTEXT.md").is_file():
            root = parent
            break

    if root is None:
        print(f"ERROR: no ACTIVE_CONTEXT.md found in any parent directory of {here} — cannot resolve the active org.")
        sys.exit(1)

    active_path = root / "ACTIVE_CONTEXT.md"
    slug = None
    for line in active_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("<!--"):
            continue
        slug = s
        break

    if not slug:
        print(f"ERROR: {active_path} has no non-comment slug line — cannot resolve the active org.")
        sys.exit(1)
    if slug == "_template":
        print(f"ERROR: {active_path} names '_template' as the active org — set it to a real org slug.")
        sys.exit(1)

    return root / "contexts" / slug / "icp.md"


def load_prefilter_config(icp_path):
    """
    Read the icp.md file at icp_path, extract the headline_prefilter JSON
    config, and validate its shape.

    Fails loud (prints a one-line message and exits 1) if the file is
    missing, marked STATUS: UNFILLED, has no parseable ```json block
    containing a "headline_prefilter" key, or any of the three required
    keyword lists is missing/empty. No defaults, no fallback lists.
    """
    icp_path = Path(icp_path)
    if not icp_path.is_file():
        print(f"ERROR: icp.md not found at {icp_path} — cannot load headline pre-filter config.")
        sys.exit(1)

    content = icp_path.read_text(encoding="utf-8")

    if "STATUS: UNFILLED" in content:
        print(f"ERROR: {icp_path} is marked STATUS: UNFILLED — the icp surface is not filled in for this org.")
        sys.exit(1)

    blocks = re.findall(r"```json\s*(.*?)```", content, re.DOTALL)
    if not blocks:
        print(f"ERROR: no ```json fenced block found in {icp_path} — cannot load headline pre-filter config.")
        sys.exit(1)

    config = None
    for block in blocks:
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "headline_prefilter" in parsed:
            config = parsed["headline_prefilter"]
            break

    if config is None:
        print(f"ERROR: no ```json block in {icp_path} contains a 'headline_prefilter' key — cannot load headline pre-filter config.")
        sys.exit(1)

    for key in ("disqualify_keywords", "buyer_title_keywords", "specialist_keywords"):
        vals = config.get(key) if isinstance(config, dict) else None
        if not isinstance(vals, list) or len(vals) == 0:
            print(f"ERROR: {icp_path} headline_prefilter.{key} is missing or empty — cannot load headline pre-filter config.")
            sys.exit(1)

    return config["disqualify_keywords"], config["buyer_title_keywords"], config["specialist_keywords"]


def run(input_path, output_path, seed_url="", icp_override=None):
    icp_path = Path(icp_override) if icp_override else resolve_icp_path()
    DISQUALIFY, BUYER, SPECIALIST = load_prefilter_config(icp_path)

    with open(input_path) as f:
        data = json.load(f)

    # 1. Extract engagers only (skip post-type records)
    engagers_raw = [r for r in data if r.get("type") in ("reaction", "comment")]

    # 2. Deduplicate by actor ID
    actors = {}
    for r in engagers_raw:
        a = r["actor"]
        aid = a["id"]
        post = r.get("query", {}).get("post", "")
        etype = "comment" if r.get("type") == "comment" else r.get("reactionType", "LIKE").lower()
        if aid not in actors:
            actors[aid] = {
                "name": a.get("name", ""),
                "linkedin_url": a.get("linkedinUrl", ""),
                "position": a.get("position", ""),
                "posts_engaged": set(),
                "engagement_types": set(),
                "has_comment": False
            }
        actors[aid]["posts_engaged"].add(post)
        actors[aid]["engagement_types"].add(etype)
        if r.get("type") == "comment":
            actors[aid]["has_comment"] = True

    # 3. Headline ICP pre-filter (keyword lists loaded from context.icp())
    def score_headline(pos):
        p = (pos or "").lower()
        for s in DISQUALIFY:
            if s in p:
                return "fail", f"disqualifier keyword: {s}"
        has_buyer = any(t in p for t in BUYER)
        has_spec = any(s in p for s in SPECIALIST)
        if has_buyer and has_spec:
            return "soft_pass", "buyer title + specialist context (headline)"
        if has_buyer:
            return "soft_pass", "buyer title in headline; company unverified"
        if has_spec:
            return "soft_pass", "specialist context; seniority unverified"
        if not pos:
            return "soft_pass", "no position data — needs enrichment"
        return "fail", "no buyer or specialist signal in headline"

    def split_name(n):
        p = n.strip().split()
        return (p[0], " ".join(p[1:])) if len(p) > 1 else (p[0] if p else "", "")

    today = date.today().isoformat()
    rows = []

    for aid, a in actors.items():
        name = a["name"]
        pos = a["position"] or ""
        score, notes = score_headline(pos)

        title_part, company_part = pos, ""
        for sep in [" at ", " bij ", " @ ", " - ", " | "]:
            if sep in pos.lower():
                idx = pos.lower().index(sep)
                title_part = pos[:idx].strip()
                company_part = pos[idx + len(sep):].strip()
                break

        first, last = split_name(name)
        posts_list = [p for p in a["posts_engaged"] if p]
        eng_type = "comment" if a["has_comment"] else list(a["engagement_types"])[0] if a["engagement_types"] else "reaction"

        rows.append({
            "first_name": first,
            "last_name": last,
            "linkedin_url": a["linkedin_url"],
            "job_title": title_part,
            "company_name": company_part,
            "company_size_est": "",
            "email": "",
            "phone": "",
            "location": "",
            "icp_score": score,
            "icp_notes": notes,
            "engagement_type": eng_type,
            "posts_engaged": " | ".join(posts_list),
            "source_profile": seed_url,
            "sourced_date": today
        })

    # Sort: soft_pass first, then fail; within each group, comments before reactions
    score_order = {"soft_pass": 0, "fail": 1}
    rows.sort(key=lambda r: (score_order.get(r["icp_score"], 2),
                             0 if r["engagement_type"] == "comment" else 1))

    fields = ["first_name","last_name","linkedin_url","job_title","company_name",
              "company_size_est","email","phone","location","icp_score","icp_notes",
              "engagement_type","posts_engaged","source_profile","sourced_date"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    soft = sum(1 for r in rows if r["icp_score"] == "soft_pass")
    fail = sum(1 for r in rows if r["icp_score"] == "fail")
    print(f"Total unique engagers: {len(rows)}")
    print(f"  soft_pass (needs research): {soft}")
    print(f"  fail (excluded): {fail}")
    print(f"Saved to: {output_path}")
    return rows


def parse_args(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("input_json")
    parser.add_argument("output_csv")
    parser.add_argument("seed_url", nargs="?", default="")
    parser.add_argument("--icp", dest="icp", default=None,
                         help="Path to an icp.md to read directly, bypassing ACTIVE_CONTEXT.md resolution.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 process_engagers.py <input.json> <output.csv> [seed_url] [--icp <path/to/icp.md>]")
        sys.exit(1)
    args = parse_args(sys.argv[1:])
    run(args.input_json, args.output_csv, args.seed_url, icp_override=args.icp)
