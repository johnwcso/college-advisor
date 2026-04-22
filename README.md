# Autonomous College Advisor Agent

An autonomous, locally-hosted AI web scraper and admissions advisor. This project implements a bi-directional "Agentic Loop" (Hypothesis → Execution → Reflection) to discover target colleges, crawl their websites for ground-truth data, extract structured facts using a local Large Language Model (LLM), and generate a personalized admissions strategy dashboard.

This tool runs 100% locally and requires no external API keys (uses `llama.cpp` for local inference).

## Architecture: The Agentic Loop

The system is built as a 4-layer architecture, inspired by Andrej Karpathy's LLM OS concepts:

1. **Intake & Refinement (Student Reflection)**: A conversational LLM interface that builds and iteratively updates a student's profile JSON based on changing SAT scores, budgets, and extracurriculars (like varsity sailing).
2. **Discovery & Targeting (System Hypothesis)**: Scores a college catalog against the student's evolving constraints to hypothesize the best target schools and generate crawl seeds.
3. **Web Crawler (Execution)**: A Playwright-based crawler that navigates university domains, bypassing basic protections to download raw HTML/text from Admissions and Financial Aid subdomains.
4. **Extraction & Synthesis (System Reflection)**: A local LLM (e.g., MiniMax via `llama.cpp`) reads the raw crawled text, extracts hard facts (Tuition, Deadlines, Test Policies), and writes a personalized Markdown advisory report based on the data. 

Finally, a UI generator compiles the AI advice and raw crawled data into a standalone, interactive HTML dashboard.

## Prerequisites

- Python 3.10+
- A local LLM server running via `llama.cpp` (default expects `http://localhost:8080/v1/chat/completions`)
- `playwright` browsers installed

## Installation

```bash
# Clone the repository
git clone https://github.com/johnwcso/college-advisor.git
cd college-advisor

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

## Usage: Running the Pipeline

### 1. Build or Refine Your Profile
Generate your initial profile, or tell the AI what changed to update it.
```bash
python3 intake/intake_cli.py
# Or, to update an existing profile conversationally:
python3 intake/refine_profile.py
```

### 2. College Discovery
Generate the crawler configuration based on your profile.
```bash
python3 discovery/discover_colleges.py --profile data/student_profiles/profile_<id>.json
```

### 3. Crawl Websites
Fetch ground-truth data from the targeted schools.
```bash
python3 crawler/college_crawl.py --config config/colleges.json
```

### 4. Verification & Auto-Improve (Optional)
Check the crawled data for structural errors.
```bash
python3 verification/verify_college_data.py
python3 improve/auto_improve.py
```

### 5. LLM Extraction & Synthesis
Extract JSON facts from the raw text and generate a personalized advisory report. *(Ensure your `llama.cpp` server is running).*
```bash
python3 extraction/extract_college_facts.py
python3 synthesis/generate_recommendation.py
```

### 6. View the Dashboard
Generate the interactive UI to view the final strategy and all raw crawled pages.
```bash
python3 viewer/generate_viewer.py
```
Open `output/viewer.html` in your web browser.

## Configuration
If your `llama.cpp` server runs on a different IP (e.g., `192.168.8.121:8080`), edit the `API_URL` variable at the top of the scripts in `extraction/`, `synthesis/`, and `intake/`.
