"""
Prospect Sourcing — Engager Processing Script
Reads Apify JSON, deduplicates, applies headline ICP pre-filter, outputs CSV.
Usage: python3 process_engagers.py <input.json> <output.csv> [seed_url]
"""
import json, csv, sys
from datetime import date

def run(input_path, output_path, seed_url=""):
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

    # 3. Headline ICP pre-filter
    GOV = ["gemeente","ministerie","rijks","overheid","waterschap","provincie",
           "rijkswaterstaat","prorail","tennet","gasunie","liander","enexis","stedin",
           "universiteit","hogeschool","ngo","stichting","government","municipality"]
    BUYER = ["founder","co-founder","ceo","chief executive","managing director",
             "md ","directeur","owner","eigenaar","managing partner",
             "general manager","president","principal"]
    SPECIALIST = ["consultant","consulting","advisor","advisory","adviseur","bureau",
                  "studio","agency","boutique","specialist","strategy","strategist",
                  "interim","freelance","coach","trainer","innovatie","innovation"]

    def score_headline(pos):
        p = (pos or "").lower()
        for s in GOV:
            if s in p:
                return "fail", f"gov/public signal: {s}"
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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 process_engagers.py <input.json> <output.csv> [seed_url]")
        sys.exit(1)
    seed = sys.argv[3] if len(sys.argv) > 3 else ""
    run(sys.argv[1], sys.argv[2], seed)
