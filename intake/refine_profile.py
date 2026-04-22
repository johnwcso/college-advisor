#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import sys
from pathlib import Path
from datetime import datetime, timezone

API_URL = "http://192.168.8.121:8080/v1/chat/completions"

def call_local_llm(prompt):
    data = {
        "model": "minimax",
        "messages": [
            {
                "role": "system", 
                "content": "You are a precise JSON-updating bot. You receive a current student profile JSON and a natural language update from the student. Your job is to modify the JSON to reflect the new information. Keep all existing data that wasn't explicitly changed. Output ONLY the raw, updated JSON object. Do not include markdown formatting or explanations."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 2000
    }
    
    req = urllib.request.Request(API_URL, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()
            # Clean up markdown if the LLM adds it
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            return json.loads(content.strip())
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

def main():
    print("=== College Advisor: LLM Profile Refinement ===")
    
    profiles = list(Path("data/student_profiles").glob("*.json"))
    if not profiles:
        print("No student profile found. Run intake_cli.py first.")
        return
        
    # Get the most recently modified profile
    profile_path = max(profiles, key=lambda p: p.stat().st_mtime)
    
    with open(profile_path, "r", encoding="utf-8") as f:
        current_profile = json.load(f)

    print("\nCurrent Profile loaded.")
    print("Talk to your AI advisor. What has changed? What new information do you want to add?")
    print("(Example: 'I got a 1480 on my SAT, I want to add Cornell to my list, and I no longer want to study in the UK.')")
    
    user_update = input("\nYour update: ").strip()
    if not user_update:
        print("No updates provided. Exiting.")
        return

    prompt = f"""
    CURRENT PROFILE JSON:
    {json.dumps(current_profile, indent=2)}
    
    STUDENT's NEW UPDATE:
    "{user_update}"
    
    Merge this new information into the CURRENT PROFILE JSON. 
    Output the complete, updated JSON object.
    """

    print("\nThinking... (Sending to local LLM)")
    updated_profile = call_local_llm(prompt)

    if updated_profile:
        # Update the timestamp
        updated_profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Save it back to the file
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(updated_profile, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Profile successfully updated and saved to {profile_path}!")
        print("Next Step: The environment has shifted. You should run Discovery again to see if your target college list changes.")
        print("Command: python3 discovery/discover_colleges.py --profile " + str(profile_path))
    else:
        print("\n❌ Failed to update profile. Please check your LLM connection.")

if __name__ == "__main__":
    main()
