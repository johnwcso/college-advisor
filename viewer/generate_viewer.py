#!/usr/bin/env python3
import json
import markdown
import html
from pathlib import Path

def main():
    print("=== College Advisor: UI Generator ===")
    
    # Load the LLM recommendation
    reports = list(Path("output/reports").glob("*.md"))
    report_html = "<p>No recommendation report generated yet.</p>"
    if reports:
        report_text = reports[0].read_text(encoding="utf-8")
        report_html = markdown.markdown(report_text)
        
    # Load the extracted facts AND the raw crawled pages
    facts_html = ""
    
    # We will loop through the crawl output directories directly
    for crawl_dir in sorted(Path("data/crawl_output").iterdir()):
        if not crawl_dir.is_dir() or crawl_dir.name == "student_profiles":
            continue
            
        college_id = crawl_dir.name
        college_name = college_id.replace("_", " ").title()
        
        # 1. Try to load the LLM facts (if they exist)
        llm_facts = {}
        facts_path = Path(f"data/college_facts/{college_id}_facts.json")
        if facts_path.exists():
            try:
                llm_facts = json.loads(facts_path.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        test_policy = llm_facts.get("test_policy") or "Not extracted"
        rd_deadline = llm_facts.get("regular_decision_deadline") or "Not extracted"
        sailing = "Yes" if llm_facts.get("sailing_team_mentioned") else "No / Not extracted"
        tuition = llm_facts.get("tuition_cost") or "Not extracted"
        
        # 2. Load the raw crawled pages
        pages_html = ""
        page_count = 0
        pages_file = crawl_dir / "pages.jsonl"
        
        if pages_file.exists():
            try:
                lines = [line for line in pages_file.read_text(encoding="utf-8").splitlines() if line.strip()]
                page_count = len(lines)
                
                for line in lines:
                    page_data = json.loads(line)
                    url = page_data.get("url") or "Unknown URL"
                    title = page_data.get("title") or "No Title"
                    
                    # FIXED: Handle None text safely
                    raw_text_content = page_data.get("text")
                    if raw_text_content is None:
                        raw_text = "No text content found for this page (possibly a redirect, timeout, or non-HTML file)."
                    else:
                        raw_text = html.escape(raw_text_content[:1500]) + "...\n\n[Text truncated for display]"
                    
                    pages_html += f"""
                    <details class="raw-page-card">
                        <summary><span class="page-title">{html.escape(title)}</span> <span class="page-url">{html.escape(url)}</span></summary>
                        <div class="raw-text-container">
                            <a href="{html.escape(url)}" target="_blank" class="visit-link">Visit Original Page &rarr;</a>
                            <pre class="raw-text">{raw_text}</pre>
                        </div>
                    </details>
                    """
            except Exception as e:
                pages_html = f"<p>Error loading raw pages: {e}</p>"
        
        facts_html += f"""
        <details class="college-card">
            <summary>{college_name} <span class="page-badge">{page_count} pages crawled</span></summary>
            <div class="college-card-content">
                
                <h4 class="section-label">AI Extracted Quick Facts</h4>
                <div class="fact-grid">
                    <div class="fact-item">
                        <div class="fact-label">Test Policy</div>
                        <div class="fact-value">{test_policy}</div>
                    </div>
                    <div class="fact-item">
                        <div class="fact-label">RD Deadline</div>
                        <div class="fact-value">{rd_deadline}</div>
                    </div>
                    <div class="fact-item">
                        <div class="fact-label">Sailing Mention</div>
                        <div class="fact-value">{sailing}</div>
                    </div>
                    <div class="fact-item">
                        <div class="fact-label">Tuition</div>
                        <div class="fact-value">{tuition}</div>
                    </div>
                </div>
                
                <h4 class="section-label" style="margin-top: 2rem;">Raw Crawled Pages ({page_count})</h4>
                <p class="meta-tag">Click a page below to read the exact text the crawler downloaded.</p>
                <div class="pages-list">
                    {pages_html}
                </div>
                
            </div>
        </details>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>College Admissions Strategy Dashboard</title>
        <style>
            :root {{
                --bg: #f3f4f6; --surface: #ffffff; --text: #1f2937; 
                --primary: #2563eb; --border: #e5e7eb; --muted: #6b7280;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg); color: var(--text);
                line-height: 1.6; padding: 2rem; max-width: 1200px; margin: 0 auto;
            }}
            h1 {{ color: var(--text); padding-bottom: 1rem; font-size: 2.5rem; }}
            .grid {{ display: grid; grid-template-columns: 1fr; gap: 2rem; }}
            
            .report-section {{
                background: var(--surface); padding: 2.5rem; border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid var(--border);
            }}
            .report-section h1, .report-section h2, .report-section h3 {{ color: var(--primary); margin-top: 1.5rem; }}
            
            .facts-section h2 {{ margin-top: 2rem; margin-bottom: 1.5rem; font-size: 1.8rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem;}}
            
            /* Interactive College Cards */
            details.college-card {{
                background: var(--surface); border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem;
                overflow: hidden; border: 1px solid var(--border);
                transition: all 0.2s ease;
            }}
            details.college-card[open] {{ box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-color: #bfdbfe; }}
            
            details.college-card > summary {{
                padding: 1.5rem; font-weight: 700; font-size: 1.3rem;
                cursor: pointer; list-style: none; display: flex; 
                justify-content: space-between; align-items: center;
                border-left: 5px solid var(--primary);
                background: var(--surface);
            }}
            details.college-card > summary:hover {{ background: #f8fafc; }}
            details.college-card > summary::-webkit-details-marker {{ display: none; }}
            
            .page-badge {{ font-size: 0.85rem; font-weight: 500; background: #eff6ff; color: #1d4ed8; padding: 0.25rem 0.75rem; border-radius: 9999px; }}
            
            .college-card-content {{ padding: 2rem; background: #fafafa; border-top: 1px solid var(--border); }}
            .section-label {{ font-size: 1.1rem; color: var(--text); margin-bottom: 1rem; margin-top: 0; text-transform: uppercase; letter-spacing: 0.05em; }}
            .meta-tag {{ font-size: 0.9rem; color: var(--muted); margin-top: -0.5rem; margin-bottom: 1.5rem; }}
            
            /* Fact Grid Layout */
            .fact-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
            .fact-item {{ background: var(--surface); padding: 1.2rem; border-radius: 8px; border: 1px solid var(--border); box-shadow: 0 1px 2px rgba(0,0,0,0.02); }}
            .fact-label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }}
            .fact-value {{ font-size: 1.1rem; font-weight: 600; color: var(--text); margin-top: 0.5rem; word-break: break-word; }}
            
            /* Raw Page Cards */
            .pages-list {{ display: flex; flex-direction: column; gap: 0.5rem; }}
            details.raw-page-card {{
                background: var(--surface); border: 1px solid var(--border); border-radius: 6px; overflow: hidden;
            }}
            details.raw-page-card > summary {{
                padding: 1rem; cursor: pointer; list-style: none; display: flex; flex-direction: column; gap: 0.25rem;
                background: var(--surface); font-size: 0.95rem;
            }}
            details.raw-page-card > summary:hover {{ background: #f9fafb; }}
            details.raw-page-card > summary::-webkit-details-marker {{ display: none; }}
            details.raw-page-card[open] > summary {{ border-bottom: 1px solid var(--border); background: #f9fafb; }}
            
            .page-title {{ font-weight: 600; color: var(--text); }}
            .page-url {{ font-size: 0.8rem; color: var(--muted); font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            
            .raw-text-container {{ padding: 1.5rem; background: #ffffff; }}
            .visit-link {{ display: inline-block; margin-bottom: 1rem; color: var(--primary); text-decoration: none; font-size: 0.9rem; font-weight: 500; }}
            .visit-link:hover {{ text-decoration: underline; }}
            
            .raw-text {{ 
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; 
                font-size: 0.85rem; line-height: 1.5; color: #374151; 
                background: #f3f4f6; padding: 1.5rem; border-radius: 6px; 
                overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;
                max-height: 400px; overflow-y: auto;
            }}
        </style>
    </head>
    <body>
        <h1>Admissions Strategy Dashboard</h1>
        <div class="grid">
            <div class="report-section">
                <h2>AI Advisor Strategy Report</h2>
                {report_html}
            </div>
            <div class="facts-section">
                <h2>College Intelligence Database</h2>
                {facts_html}
            </div>
        </div>
    </body>
    </html>
    """

    out_file = Path("output/viewer.html")
    out_file.write_text(html_content, encoding="utf-8")
    print(f"✅ Dashboard generated! Open this file in your browser: {out_file.absolute()}")

if __name__ == "__main__":
    main()
