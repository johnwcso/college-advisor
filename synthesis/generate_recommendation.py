#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import sys
from pathlib import Path

API_URL = "http://192.168.8.121:8080/v1/chat/completions"

def call_local_llm(prompt):
    data = {
        "model": "minimax",
        "messages": [
            {"role": "system", "content": "You are an elite, highly strategic college admissions advisor. Speak directly to the student. Give actionable, specific advice based on their exact profile and the college data provided. Do not use generic platitudes. Format your response in clean Markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 1500
    }
    
    req = urllib.request.Request(API_URL, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return "Error generating recommendation."

def main():
    print("=== College Advisor: Synthesis & Recommendation ===")
    
    profiles = list(Path("data/student_profiles").glob("*.json"))
    if not profiles:
        print("No student profile found. Run intake first.")
        return
    profile_path = profiles[0] # Just grab the first one for now
    
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    facts = []
    for p in Path("data/college_facts").glob("*_facts.json"):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["college_id"] = p.stem.replace("_facts", "")
            facts.append(data)

    prompt = f"""
    Based on this student's profile and the factual data we crawled from their target colleges, write a strategic admissions plan.
    
    STUDENT PROFILE:
    {json.dumps(profile, indent=2)}
    
    CRAWLED COLLEGE FACTS:
    {json.dumps(facts, indent=2)}
    
    Please provide:
    1. A brief assessment of their current academic trajectory and curriculum.
    2. Specific advice on what to focus on in their last 2 years of high school (grades, specific subjects).
    3. How to leverage their extracurriculars (especially if sailing is mentioned).
    4. A strategic recommendation on how/when to apply to the colleges listed in the facts (e.g. Early Decision vs Regular).
    """

    print("Synthesizing final strategy with local LLM...")
    report_markdown = call_local_llm(prompt)
    
    out_dir = Path("output/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"student_{profile.get('student_id', 'unknown')}_report.md"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_markdown)
        
    print(f"✅ Final Strategy saved to {report_file}")

if __name__ == "__main__":
    main()
