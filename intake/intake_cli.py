#!/usr/bin/env python3
import json
import uuid
import sys
from datetime import datetime, timezone
from pathlib import Path


def set_nested(d, path, value):
    keys = path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def main():
    print("=== College Advisor: Student Intake ===")
    student_id = input("Enter Student ID (or press Enter for auto-generate): ").strip()
    if not student_id:
        student_id = uuid.uuid4().hex[:8]

    q_path = Path("intake/questionnaire.json")
    if not q_path.exists():
        print("Error: intake/questionnaire.json not found. Run from college-advisor root.")
        sys.exit(1)

    with open(q_path, encoding="utf-8") as f:
        questionnaire = json.load(f)

    now = datetime.now(timezone.utc).isoformat()
    profile = {
        "student_id": student_id,
        "profile_version": "1.0",
        "created_at": now,
        "updated_at": now,
        "academic": {},
        "geography": {},
        "financial": {},
        "activities": {},
        "experience_preferences": {},
        "constraints": {},
        "application_strategy": {}
    }

    print("\nAnswer the following to build your profile:")

    for q in questionnaire.get("questions", []):
        prompt = q["prompt"]
        q_type = q["type"]
        options = q.get("options", [])

        cond = q.get("condition")
        if cond and "includes sailing" in cond:
            hooks = profile.get("activities", {}).get("primary_hooks", [])
            if not any("sailing" in h.lower() for h in hooks):
                continue

        print(f"\n> {prompt}")

        if q_type == "choice":
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
            ans = input("Select number: ").strip()
            try:
                raw = options[int(ans) - 1]
                val = raw.split(" — ")[0] if " — " in raw else raw
            except Exception:
                val = options[0] if options else ""
            set_nested(profile, q["field"], val)

        elif q_type == "multi_choice":
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
            ans = input("Select numbers (comma separated): ").strip()
            vals = []
            for a in ans.split(","):
                try:
                    vals.append(options[int(a.strip()) - 1])
                except Exception:
                    pass
            set_nested(profile, q["field"], vals)

        elif q_type == "boolean":
            ans = input("(y/n): ").strip().lower()
            set_nested(profile, q["field"], ans.startswith("y"))

        elif q_type in ["text_list", "text_list_optional"]:
            ans = input("Comma separated values: ").strip()
            if ans:
                set_nested(profile, q["field"], [x.strip() for x in ans.split(",") if x.strip()])
            elif q_type == "text_list_optional":
                set_nested(profile, q["field"], [])

        elif q_type == "number_optional":
            ans = input("Number: ").strip()
            if ans.isdigit():
                set_nested(profile, q["field"], int(ans))
            else:
                set_nested(profile, q["field"], None)

        else:
            ans = input("Answer: ").strip()
            set_nested(profile, q["field"], ans)

    out_path = Path(f"data/student_profiles/profile_{student_id}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Profile saved to {out_path}")
    print(f"Next: Run discovery/discover_colleges.py --profile {out_path}")
    print(f"or run  python3 discovery/discover_colleges.py --profile {out_path}")

if __name__ == "__main__":
    main()
