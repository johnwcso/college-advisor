import json
import os

def run_onboarding():
    print("🎓 Welcome to the Agentic College Advisor Setup 🎓")
    print("Let's build your student profile for the AI.\n")

    profile = {}
    profile["target_majors"] = input("1. What majors are you interested in? (e.g., CS, Biology, Linguistics): ")
    profile["target_regions"] = input("2. Preferred regions/countries? (e.g., US West Coast, UK, global): ")
    profile["budget_limit"] = input("3. What is your maximum annual budget (Cost After Aid) in USD?: ")
    profile["extracurriculars"] = input("4. Key extracurriculars the college MUST support? (e.g., ILCA 4/6 sailing team, Robotics): ")
    profile["academic_stats"] = input("5. Current academics? (e.g., IB all 6s, 1500 SAT): ")
    
    print("\n⚙️ Generating Agent Context...")
    
    system_context = f"""
You are an expert college advisor agent. You are advising a student with the following profile:
- Academics: {profile['academic_stats']}
- Majors: {profile['target_majors']}
- Regions: {profile['target_regions']}
- Max Budget: ${profile['budget_limit']}/yr
- Required Extracurriculars: {profile['extracurriculars']}

INSTRUCTIONS:
1. Search the local LightRAG database (QS, US News, THE data) to find schools matching the rank, region, and budget.
2. If the student requires specific extracurriculars (like sailing teams), use the `crawl_website` tool to scan the target university's official .edu athletics/clubs pages.
3. Cross-reference financial aid data from the US News dataset before recommending a school.
    """
    
    profile["agent_system_prompt"] = system_context.strip()
    
    with open("student_profile.json", "w") as f:
        json.dump(profile, f, indent=2)
        
    print("✅ Profile saved to student_profile.json! Your OpenClaw agent is ready to launch.")

if __name__ == "__main__":
    run_onboarding()
