import subprocess
import json
import os
from pathlib import Path

# Path to the root of your college-advisor project
# Adjust this if your OpenClaw skill runs from a different working directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def execute_command(cmd, desc):
    """Helper to run a subprocess command safely."""
    try:
        print(f"\n[OpenClaw College Skill] Executing: {desc}")
        result = subprocess.run(
            cmd, 
            cwd=PROJECT_ROOT, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}

def refine_student_profile(natural_language_update: str) -> dict:
    """Updates the profile via the intake/refine_profile.py script logic, but headless."""
    # Since refine_profile.py originally used `input()`, we will call the LLM directly here for OpenClaw.
    import urllib.request
    
    profiles = list(Path(os.path.join(PROJECT_ROOT, "data/student_profiles")).glob("*.json"))
    if not profiles:
        return {"status": "error", "message": "No student profile found. Run intake_cli.py manually first."}
        
    profile_path = max(profiles, key=lambda p: p.stat().st_mtime)
    with open(profile_path, "r", encoding="utf-8") as f:
        current_profile = json.load(f)

    prompt = f"""
    CURRENT PROFILE JSON:
    {json.dumps(current_profile, indent=2)}
    
    STUDENT's NEW UPDATE:
    "{natural_language_update}"
    
    Merge this new information into the CURRENT PROFILE JSON. 
    Output ONLY the complete, updated JSON object.
    """

    data = {
        "model": "minimax",
        "messages": [
            {"role": "system", "content": "You are a precise JSON-updating bot. Output ONLY raw JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    
    req = urllib.request.Request("http://192.168.8.121:8080/v1/chat/completions", data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            
            updated_profile = json.loads(content.strip())
            
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(updated_profile, f, indent=2, ensure_ascii=False)
                
            return {"status": "success", "message": f"Profile updated successfully with: {natural_language_update}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_college_discovery() -> dict:
    """Runs the discovery scoring script."""
    profiles = list(Path(os.path.join(PROJECT_ROOT, "data/student_profiles")).glob("*.json"))
    if not profiles:
        return {"status": "error", "message": "No student profile found."}
    profile_path = max(profiles, key=lambda p: p.stat().st_mtime)
    
    return execute_command(
        ["python3", "discovery/discover_colleges.py", "--profile", str(profile_path)],
        "Scoring colleges and generating config/colleges.json"
    )

def run_college_crawler() -> dict:
    """Runs the Playwright crawler."""
    return execute_command(
        ["python3", "crawler/college_crawl.py", "--config", "config/colleges.json"],
        "Crawling college websites for ground truth data"
    )

def generate_college_strategy_dashboard() -> dict:
    """Runs extraction, synthesis, and UI generation."""
    # 1. Extract facts
    ext_res = execute_command(["python3", "extraction/extract_college_facts.py"], "Extracting facts via LLM")
    if ext_res["status"] == "error": return ext_res
    
    # 2. Generate Recommendation
    rec_res = execute_command(["python3", "synthesis/generate_recommendation.py"], "Synthesizing strategy report")
    if rec_res["status"] == "error": return rec_res
    
    # 3. Build UI
    ui_res = execute_command(["python3", "viewer/generate_viewer.py"], "Building HTML dashboard")
    if ui_res["status"] == "error": return ui_res
    
    return {"status": "success", "message": "Dashboard generated successfully at output/viewer.html"}
