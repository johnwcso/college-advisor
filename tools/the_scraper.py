import requests
import json
import csv
import time

def scrape_the_subject_rankings(year="2026"):
    # The internal name formats used by the THE API
        # Updated internal name formats used by the THE API
    subjects = [
        "computer_science_rankings",
        "business_economics_rankings",
        "psychology_rankings",
        "engineering_technology_rankings",
        "physical_sciences_rankings",
        "social_sciences_rankings",
        "clinical_pre_clinical_health_ran",
        "arts_humanities_rankings",
        "life_sciences_rankings",
        "education_rankings",
        "law_rankings"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    all_data = []

    for subject in subjects:
        print(f"Scraping {subject} for {year}...")
        
        # This is the hidden JSON endpoint THE uses to populate their tables
        api_url = f"https://www.timeshighereducation.com/json/ranking_tables/{subject}/{year}"
        
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch {subject}. Status: {response.status_code}")
                continue

            data = response.json()
            # The actual ranking list is stored in the 'data' array
            universities = data.get("data", [])
            
            for uni in universities:
                row = {
                    "Subject": subject.replace("_rankings", "").replace("_", " ").title(),
                    "Rank": uni.get("rank", "N/A"),
                    "Institution": uni.get("name", "N/A"),
                    "Location": uni.get("location", "N/A"),
                    "Overall Score": uni.get("scores_overall", "N/A"),
                    "Teaching": uni.get("scores_teaching", "N/A"),
                    "Research Environment": uni.get("scores_research", "N/A"),
                    "Research Quality": uni.get("scores_citations", "N/A"),
                    "Industry": uni.get("scores_industry_income", "N/A"),
                    "International Outlook": uni.get("scores_international_outlook", "N/A")
                }
                all_data.append(row)
                
            # Sleep briefly to be polite to their servers
            time.sleep(2)
            
        except Exception as e:
            print(f"Error parsing {subject}: {e}")

    # Export to CSV
    if all_data:
        keys = all_data[0].keys()
        filename = f"THE_Subject_Rankings_{year}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_data)
        print(f"Successfully saved {len(all_data)} records to {filename}")

if __name__ == "__main__":
    scrape_the_subject_rankings("2026")

