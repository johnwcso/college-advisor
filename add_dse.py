python3 -c '
import json

# 1. Update the questionnaire
with open("intake/questionnaire.json", "r") as f:
    q = json.load(f)
q["questions"][0]["options"] = ["IB", "A-levels", "AP", "Hong Kong DSE", "GCE", "other"]
with open("intake/questionnaire.json", "w") as f:
    json.dump(q, f, indent=2)

# 2. Update the schema so it passes validation
with open("schema/student_profile.schema.json", "r") as f:
    s = json.load(f)
s["properties"]["academic"]["properties"]["curriculum"]["enum"] = ["IB", "A-levels", "AP", "Hong Kong DSE", "GCE", "other"]
with open("schema/student_profile.schema.json", "w") as f:
    json.dump(s, f, indent=2)

print("✅ Added Hong Kong DSE to both questionnaire.json and student_profile.schema.json")
'
