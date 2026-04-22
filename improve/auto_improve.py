#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone
import uuid


def main():
    print("=== College Advisor: Auto-Improve Layer ===")

    out_dir = Path("output/actions")
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-run-{uuid.uuid4().hex[:4]}"

    actions = []

    crawl_dir = Path("data/crawl_output")
    if crawl_dir.exists():
        for p in crawl_dir.glob("*/meta.json"):
            meta = json.loads(p.read_text(encoding="utf-8"))
            pages_crawled = meta.get("pages_crawled", 0)

            if pages_crawled < 5:
                actions.append({
                    "type": "regex_update",
                    "college": meta.get("college"),
                    "priority": "high",
                    "reason": f"Crawler only found {pages_crawled} pages. Current regex may be too restrictive.",
                    "proposed_value": "broaden allow_regex to match domain apex",
                    "auto_apply": False
                })

            if pages_crawled > 0:
                if "Yale" in meta.get("college", ""):
                    actions.append({
                        "type": "crawl_seed_add",
                        "college": meta.get("college"),
                        "priority": "medium",
                        "reason": "Crawler found many links to student financial services not currently seeded.",
                        "proposed_value": "https://finaid.yale.edu",
                        "auto_apply": False
                    })

    action_doc = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actions": actions
    }

    out_file = out_dir / f"actions_{run_id}.json"
    out_file.write_text(json.dumps(action_doc, indent=2), encoding="utf-8")

    print(f"Generated {len(actions)} improvement actions.")
    print(f"Saved to {out_file}")

    for a in actions:
        print(f"  [{a['priority'].upper()}] {a['type']} for {a['college']}: {a['reason']}")


if __name__ == "__main__":
    main()
