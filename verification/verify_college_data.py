#!/usr/bin/env python3
import json
from pathlib import Path


def main():
    print("=== College Advisor: Verification Layer ===")
    crawl_dir = Path("data/crawl_output")
    if not crawl_dir.exists():
        print("No crawl data found. Run college_crawl.py first.")
        return

    issues = []
    total_pages = 0
    college_count = 0

    for p in crawl_dir.glob("*/pages.jsonl"):
        college_count += 1
        college_name = p.parent.name
        try:
            pages = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
            total_pages += len(pages)

            if len(pages) < 3:
                issues.append({
                    "type": "structural",
                    "college": college_name,
                    "reason": f"Only {len(pages)} pages crawled. Site may be blocking Playwright."
                })

            has_admissions = any("admission" in page.get("url", "").lower() for page in pages)
            has_aid = any("financial" in page.get("url", "").lower() for page in pages)

            if not has_admissions:
                issues.append({
                    "type": "missing_data",
                    "college": college_name,
                    "reason": "No admissions pages found in crawl."
                })

            if not has_aid:
                issues.append({
                    "type": "missing_data",
                    "college": college_name,
                    "reason": "No financial aid pages found."
                })

            for page in pages:
                text = page.get("text", "") or ""
                if not text:
                    continue

                if "test-optional" in text.lower() and "sat required" in text.lower():
                    issues.append({
                        "type": "consistency",
                        "college": college_name,
                        "url": page.get("url"),
                        "reason": "Conflicting test policy language on same page."
                    })

        except Exception as e:
            issues.append({
                "type": "error",
                "college": college_name,
                "reason": f"Failed to parse pages.jsonl: {e}"
            })

    print(f"Verified {total_pages} pages across {college_count} colleges.")

    if issues:
        print(f"\nFound {len(issues)} potential issues requiring review:")
        for i in issues:
            url_part = f"({i.get('url')}) " if "url" in i else ""
            print(f"  [{i['type'].upper()}] {i['college']}: {url_part}{i['reason']}")
    else:
        print("\n✅ Verification passed: No structural anomalies or obvious data conflicts found.")


if __name__ == "__main__":
    main()
