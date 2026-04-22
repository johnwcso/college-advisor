#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def score_college(college, profile):
    score = 0
    reasons = []

    majors_offered = set(m.lower() for m in college.get("majors_available", []))
    intended = set(m.lower() for m in profile.get("academic", {}).get("intended_majors", []))
    if intended and (intended & majors_offered):
        score += 30
        reasons.append("Matches intended major")

    student_sailing = profile.get("activities", {}).get("recruiting_interest", {}).get("varsity_or_high_level_team_needed", False)
    club_ok = profile.get("activities", {}).get("recruiting_interest", {}).get("club_team_ok", True)

    college_sailing = college.get("sailing_team", {})
    if college_sailing.get("has_team"):
        if college_sailing.get("level") == "varsity":
            score += 20
            reasons.append("Varsity sailing available")
        elif college_sailing.get("level") == "club" and club_ok:
            score += 10
            reasons.append("Club sailing available")

    allowed_countries = profile.get("geography", {}).get("allowed_countries", [])
    if allowed_countries and college.get("country") in allowed_countries:
        score += 15
        reasons.append(f"Located in {college.get('country')}")

    aid_needed = profile.get("financial", {}).get("budget_band") == "aid_needed"
    if aid_needed and college.get("aid", {}).get("need_blind_international"):
        score += 20
        reasons.append("Need-blind for internationals")
    elif aid_needed and college.get("aid", {}).get("merit_available"):
        score += 5
        reasons.append("Merit aid available")

    return score, reasons


def main():
    parser = argparse.ArgumentParser(description="Score catalog and generate crawl list")
    parser.add_argument("--profile", required=True, help="Path to student profile JSON")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f"Error: Profile {args.profile} not found.")
        sys.exit(1)

    with open(profile_path, encoding="utf-8") as f:
        profile = json.load(f)

    cat_path = Path("config/catalog.json")
    if not cat_path.exists():
        dummy_catalog = [
            {
                "id": "yale-university",
                "name": "Yale University",
                "country": "USA",
                "majors_available": ["Zoology", "Biology", "Economics"],
                "sailing_team": {"has_team": True, "level": "varsity", "conference": "NEISA"},
                "aid": {"need_blind_international": True, "merit_available": False},
                "official_seeds": ["https://admissions.yale.edu"],
                "allow_regex": "yale\\.edu",
                "deny_regex": "login"
            },
            {
                "id": "harvard-university",
                "name": "Harvard University",
                "country": "USA",
                "majors_available": ["Biology", "Computer Science"],
                "sailing_team": {"has_team": True, "level": "varsity", "conference": "NEISA"},
                "aid": {"need_blind_international": True, "merit_available": False},
                "official_seeds": ["https://college.harvard.edu/admissions"],
                "allow_regex": "harvard\\.edu",
                "deny_regex": "login"
            }
        ]
        cat_path.parent.mkdir(parents=True, exist_ok=True)
        cat_path.write_text(json.dumps(dummy_catalog, indent=2), encoding="utf-8")
        print("Created sample config/catalog.json")

    with open(cat_path, encoding="utf-8") as f:
        catalog = json.load(f)

    results = []
    for college in catalog:
        score, reasons = score_college(college, profile)
        results.append({
            "name": college["name"],
            "score": score,
            "reasons": reasons,
            "seeds": college.get("official_seeds", []),
            "allow_regex": college.get("allow_regex", ""),
            "deny_regex": college.get("deny_regex", "")
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    # FIXED: Safely handle application_strategy whether it's a string or a dictionary
    strategy = profile.get("application_strategy", {})
    if isinstance(strategy, str):
        target_size = strategy
    else:
        target_size = strategy.get("target_list_size", 10)

    if isinstance(target_size, str):
        try:
            # Extract "8" from "8-10 (focused)"
            target_size = int(target_size.split("-")[0]) if "-" in target_size else int(target_size.split()[0])
        except Exception:
            target_size = 10

    top_colleges = results[:target_size]

    print(f"=== College Discovery for {profile.get('student_id')} ===")
    for i, c in enumerate(top_colleges, 1):
        print(f"{i}. {c['name']} (Score: {c['score']})")
        print(f"   Matches: {', '.join(c['reasons'])}")

    settings_path = Path("config/settings.json")
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}

    crawler_config = {
        "settings": settings,
        "colleges": [
            {
                "name": c["name"],
                "seeds": c["seeds"],
                "allow_regex": c["allow_regex"],
                "deny_regex": c["deny_regex"]
            }
            for c in top_colleges
        ]
    }

    out_path = Path("config/colleges.json")
    out_path.write_text(json.dumps(crawler_config, indent=2), encoding="utf-8")

    print(f"\n✅ Wrote {len(top_colleges)} target colleges to config/colleges.json.")
    print("Next: Run crawler/college_crawl.py to fetch data for these schools.")


if __name__ == "__main__":
    main()
