# 🎓 Agentic College Advisor

An autonomous, AI-driven college advisory system. This project uses an Agentic RAG architecture (via OpenClaw and LightRAG) to help students find the perfect university by combining static dataset retrieval with real-time, stealth web scraping.

## 🧠 Architecture
- **Agent Framework:** OpenClaw (LLM Orchestration)
- **Memory/Retrieval:** LightRAG (Dual-level vector & graph retrieval)
- **Tools / Skills:**
  - `usnews_scraper.py`: Bypasses Akamai TLS fingerprinting via `curl_cffi` to extract pure JSON rankings.
  - `global_rankings_scraper.py`: Extracts QS World and THE rankings dynamically.
  - `crawler.py`: A Playwright-stealth crawler for extracting qualitative data from `.edu` admissions pages.

## 📊 Datasets Included (`/data`)
- US News National Universities Top 400 (JSON)
- QS World University Rankings 2025 (CSV)
- Times Higher Education (THE) Rankings (JSON)

## 🚀 Usage
1. Run `python3 onboarding.py` to generate your student profile.
2. Launch the OpenClaw agent. The agent will read your profile, cross-reference the datasets in `/data`, and use the `tools/` to crawl specific university websites for missing financial aid or extracurricular info.
