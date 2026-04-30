import json
import time
import re
from curl_cffi import requests

def clean_html(raw_html):
    """Removes HTML tags from QS names."""
    if not raw_html:
        return "N/A"
    clean_text = re.sub(r'<[^>]+>', '', str(raw_html))
    return clean_text.strip()

def scrape_qs_computer_science():
    print("🌍 Starting QS World University Rankings (Computer Science)...")
    all_qs_schools = []
    page = 0
    
    qs_url = "https://www.topuniversities.com/rankings/endpoint"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    while True:
        # Notice we changed this to "subject" and added the specific major!
        params = {
            "ranking_type": "subject",
            "subject": "computer-science-information-systems",
            "year": "2024", 
            "page": page
        }
        
        print(f"  Fetching QS CS page {page}...")
        response = requests.get(qs_url, params=params, headers=headers, impersonate="chrome")
        
        if response.status_code != 200:
            print(f"❌ QS API failed: {response.status_code}")
            break
            
        data = response.json()
        items = data.get("data", [])
        
        if not items:
            break
            
        for school in items:
            all_qs_schools.append({
                "name": clean_html(school.get("title", "")),
                "cs_rank": clean_html(school.get("rank_display", "N/A")),
                "country": school.get("country", "N/A")
            })
            
        page += 1
        time.sleep(1)
        
        # Stop after 3 pages for testing (first ~45 CS programs)
        if page >= 3:
            break

    print(f"✅ Fetched {len(all_qs_schools)} Computer Science programs from QS.")
    with open("qs_cs_rankings.json", "w", encoding="utf-8") as f:
        json.dump(all_qs_schools, f, indent=2)

def scrape_the_rankings():
    print("\n🏛️ Starting Times Higher Education (THE) Scraper...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    # 1. Dynamically find the hidden JSON URL
    print("  Searching THE homepage for the latest JSON data URL...")
    homepage_url = "https://www.timeshighereducation.com/world-university-rankings/2025/world-ranking"
    
    home_resp = requests.get(homepage_url, headers=headers, impersonate="chrome")
    
    # Regex to find the hidden data file in the page source
    json_links = re.findall(r'/sites/default/files/the_data_rankings/[^"\']+\.json', home_resp.text)
    
    if not json_links:
        print("❌ Could not find the THE JSON data link on the homepage.")
        return
        
    # Construct the full URL
    the_data_url = "https://www.timeshighereducation.com" + json_links[0]
    print(f"  Found latest THE data payload: {the_data_url}")
    
    # 2. Download the data
    response = requests.get(the_data_url, headers=headers, impersonate="chrome")
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("data", [])
        
        all_the_schools = []
        for school in items:
            all_the_schools.append({
                "name": school.get("name", "N/A"),
                "the_world_rank": school.get("rank", "N/A"),
                "country": school.get("location", "N/A")
            })
            
        print(f"✅ Fetched {len(all_the_schools)} schools from THE.")
        with open("the_rankings.json", "w", encoding="utf-8") as f:
            json.dump(all_the_schools, f, indent=2)
    else:
        print(f"❌ THE API failed with status code {response.status_code}")

if __name__ == "__main__":
    scrape_qs_computer_science()
    scrape_the_rankings()
    print("\n💾 Saved data to qs_cs_rankings.json and the_rankings.json")
