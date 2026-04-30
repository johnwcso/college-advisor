import json
import time
from curl_cffi import requests

def scrape_all_us_news():
    print("Fetching all US News National Universities...\n")
    
    all_schools = []
    page = 1
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    while True:
        # Notice the _page={page} parameter at the end
        api_url = f"https://www.usnews.com/best-colleges/api/search?_sort=rank&_sortDirection=asc&schoolType=national-universities&_page={page}"
        
        response = requests.get(api_url, impersonate="chrome", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed on page {page} with status code: {response.status_code}")
            break
            
        data = response.json()
        items = data.get("data", {}).get("items", [])
        
        # If the items list is empty, we've reached the end of the rankings
        if not items:
            break
            
        print(f"📄 Scraped page {page} (found {len(items)} schools)...")
        all_schools.extend(items)
        
        page += 1
        time.sleep(1) # Wait 1 second between requests to be polite to their API

    print(f"\n✅ Success! Fetched {len(all_schools)} colleges in total.\n")
    
    # Save the massive dataset
    with open("usnews_rankings_full.json", "w", encoding="utf-8") as f:
        json.dump(all_schools, f, indent=2)
        
    print("💾 Saved full dataset to usnews_rankings_full.json")
    print("You can now feed this structured JSON to your local AI / OpenClaw agents!")

if __name__ == "__main__":
    scrape_all_us_news()
