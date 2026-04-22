#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
from pathlib import Path
import re

# Your specific llama.cpp server
API_URL = "http://192.168.8.121:8080/v1/chat/completions"

def call_local_llm(prompt, text_chunk):
    data = {
        # llama-server ignores this if it only loaded one model, but requires the field
        "model": "minimax", 
        "messages": [
            {
                "role": "system", 
                "content": "You are a data extraction bot. You only output raw, valid JSON. Never output conversational text or markdown formatting."
            },
            {
                "role": "user", 
                "content": f"{prompt}\n\nWebsite Text:\n{text_chunk[:12000]}"
            }
        ],
        "temperature": 0.0,  # 0.0 is best for factual extraction
        "max_tokens": 500
    }
    
    req = urllib.request.Request(
        API_URL, 
        data=json.dumps(data).encode("utf-8"), 
        headers={"Content-Type": "application/json"}
    )
    
    try:
        # 60 second timeout - MiniMax might take a moment to read 12k chars
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            
            # Clean up the output in case the LLM wrapped it in ```json ... ```
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            return json.loads(content.strip())
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

def main():
    print("=== College Advisor: LLM Extraction Layer ===")
    crawl_dir = Path("data/crawl_output")
    out_dir = Path("data/college_facts")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not crawl_dir.exists():
        print("No crawl data found.")
        return

    for p in crawl_dir.glob("*/pages.jsonl"):
        college_name = p.parent.name
        print(f"\nProcessing {college_name}...")
        
        combined_text = ""
        try:
            pages = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
            for page in pages:
                if page.get("text"):
                    # Give preference to admissions and finaid pages
                    if "admission" in page.get("url", "").lower() or "finaid" in page.get("url", "").lower():
                        combined_text = f"\n--- URL: {page.get('url')} ---\n{page.get('text')[:3000]}\n" + combined_text
                    else:
                        combined_text += f"\n--- URL: {page.get('url')} ---\n{page.get('text')[:1000]}\n"
        except Exception as e:
            print(f"Error reading {p}: {e}")
            continue

        prompt = """
Based ONLY on the website text provided below, extract these exactly 4 keys into a JSON object:
{
  "regular_decision_deadline": "string or null",
  "test_policy": "string or null (e.g. Test Optional)",
  "sailing_team_mentioned": boolean,
  "tuition_cost": "string or null"
}
Output ONLY the JSON object. Do not explain your reasoning.
        """
        
        print("Sending to llama-server (192.168.8.121:8080)...")
        extracted_facts = call_local_llm(prompt, combined_text)
        
        if extracted_facts:
            out_file = out_dir / f"{college_name}_facts.json"
            with open(out_file, "w") as f:
                json.dump(extracted_facts, f, indent=2)
            print(f"✅ Saved facts to {out_file}")
            print(json.dumps(extracted_facts, indent=2))
        else:
            print(f"Failed to extract facts for {college_name}.")

if __name__ == "__main__":
    main()
