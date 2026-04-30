#!/usr/bin/env python3
import asyncio
import json
import re
import argparse
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run_crawler(name, seeds, allow_regex, deny_regex, max_pages, scrolls):
    out_dir = Path("output") / name.replace(" ", "_").lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "pages.jsonl"
    
    if out_file.exists():
        out_file.unlink()

    visited = set()
    queue = seeds.copy()
    crawled_data = []

    allow_pattern = re.compile(allow_regex) if allow_regex else None
    deny_pattern = re.compile(deny_regex) if deny_regex else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ]
        )
        
        # Exact User-Agent you used when capturing the cookies
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True
        )

        # INJECTING THE US NEWS AKAMAI COOKIES FROM YOUR FILE
        await context.add_cookies([
            {
                "name": "bms",
                "value": "YAAQK8hFwinw2KdAQAAMBktQVjCjkhVCHhQxPb2LFwGJEFdebn6qG7ibWphZJL54TmhbPMEO6aMfjDyiEddKM1oIH8L3PSkI0IIjFn1XrSu3FV4BPTrXKg1fgXIavGbNzqgN7u2ZbCxkavyqY0xXnZ4jwxi1HxUB3PKfO5P0AEG4R2KX6GZyFs9NOZ3CUHdQWYYE5QQpdG3H6SLAU5BmumH2TLqoKfPp2iBrdIjiOtLHTOQbHHvdCRcBGQlLjrgl2dpOtkHXn8LgU4OoztXAmM4fnr3NE9Xw6AH4lGm5gDe9czHMxm3ZwT0gnkzENuWGrBbq2WcLKr4Vvk0ZaX5KkZyPNHFTkwGsf8Gx5vzyajlyBqPplpBSyOqzQajC3PzI0OcSEZMnKDSrAexBJwQ3BX2iky49lsXibitdr7EfhU6UOf1ndAvuRDhnc2cB1SsdUo8OmYRHIui0WBifeZh73kYyCuTMFsLJfK3CvBHBk27XIPyAiNjVrxU8dxbxRFmqHEweZoUHMplEph1xiWelh3b7Zdgee4xCwuMng81sA1wgt80ujXZ79OeTeP4yHaJiIh4s1wlbrTLov7qB5t52iYYXa3FX2QtkDWK32IKH83pfWg5RbBO8mM3yA3nULhQ4mAREJlVLU1k1OBQ8W9OFo1tXGhl8f87ta6WKLasLAkfL5e6SDttrfNwPPaTWHyobFZaAGCpNPUzALatlPOckBv4F1GXxva8SJfOvMh177dDrk6uSC4Mw3QghJDlHxMzdJBqGkxtLudv0d0DoJdjJCFQ9pgYYBWtFptuFR4ZpRy8QXedgHXEHj1alS4h1ySnQXkbF3VUqMdoJJD7oPWXAUjsDqg1SRBRRPP7kUWUVFuXyeo2cCwZemHrL8IJN1tFGyvhOUXH9NWPEpwnCDZKBRkqtalYB5Oe388rQ2AHl0uKTZX",
                "domain": ".usnews.com",
                "path": "/"
            },
            {
                "name": "bmso",
                "value": "B1E8979C96EDFF75208B6F45862E65743AFC81B077965E093F7BD662208EE821YAAQK8hFwmnw2KdAQAAMBktQeJrfIJwtMrlxCpgiyivLLzSQ7whydqEWAb5ZKcZjLfiG98pqisedeRExnGLsWOgXO5z1KpKSMxUEuquQPwJWWxeiVuDun7TANRzOl8jB2jJYzdC7o4vHjy4woEgCEMYLTxsG7tPSenUNZcX3MTkvR10vWmXj9B8YmfTkrmNloxRVZ0JpfyHV43TeLyJU7fbdyTai0CEHz1ISj5w3CWP1zeksKT6keILvacjVbJQ0WODBIm3btN8tPB14CiFlUk3ZmjXu3HTbqgZjYQ0dQC0oubMPrAbEHfgRr83dZpkZHW2z9y903HqcNGoezd2HUZzbyTCIaEwwzO3rJ7GWhhNIEvJMcUSHWzRLygecrp8Ne9jZOIInApD9d612xtgzhgr6I0b6Y4mJuo40vc1MvjaqsUGJonRaXzQLjOSneRU8YVHFp",
                "domain": ".usnews.com",
                "path": "/"
            },
            {
                "name": "bmsv",
                "value": "B3A0E1CB26D7100DA61DEA24010101B7YAAQK8hFwqnw2KdAQAAMBktR5eu0eRix4ALD7gbfdsTYco4D9BE2plj6UNyhFfUw8yG4okAkjdMHLaVz1R2CwQjCrlY2pvzQuymcq6ji8LMQdsWVX6DsLxYlGQC7UxDyfEylSCp10tko0ZzUAbzCuVru3gc8q4FVWJTD4zpJXZI0Q8kznLEcRff6GWDOW2kR5PRdEqbU7VavMEwGswNNpHZ2T7orfd515L4PW4yjaZ37TvtKysUh1",
                "domain": ".usnews.com",
                "path": "/"
            }
        ])

        # We must set additional headers so the request looks legitimate
        await context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })

        try:
            stealth = Stealth()
            await stealth.apply_stealth_async(context)
        except Exception as e:
            print(f"[Warning] Stealth initialization issue: {e}")
            
        page = await context.new_page()
        page.set_default_timeout(60000)

        print(f"Crawling '{name}' | max {max_pages} pages | scrolls {scrolls} | output → {out_file}")

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited: continue
            visited.add(url)
            
            try:
                print(f"  [{name}] Fetching {url} ...")
                response = await page.goto(url, wait_until="domcontentloaded")
                
                if response and response.status in [403, 503]:
                    print(f"  [{name}] Encountered {response.status}, waiting 8s for potential challenge...")
                    await page.wait_for_timeout(8000)
                elif not response or response.status >= 400:
                    print(f"  [{name}] ({len(visited)}/{max_pages}) {response.status if response else 'ERR'} {url}")
                    continue

                if scrolls > 0:
                    for i in range(scrolls):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)

                title = await page.title()
                text = await page.evaluate("document.body.innerText")
                text = re.sub(r'\n\s*\n', '\n\n', text).strip()

                page_data = {"url": url, "title": title, "text": text}
                with open(out_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(page_data) + "\n")
                
                crawled_data.append(page_data)
                print(f"  [{name}] ({len(visited)}/{max_pages}) 200 {url} (Length: {len(text)})")

                if len(crawled_data) < max_pages:
                    hrefs = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('a')).map(a => a.href);
                    }""")

                    for href in hrefs:
                        if not href.startswith("http"): continue
                        clean_href = href.split('#')[0]
                        if clean_href in visited or clean_href in queue: continue
                        if allow_pattern and not allow_pattern.search(clean_href): continue
                        if deny_pattern and deny_pattern.search(clean_href): continue
                        queue.append(clean_href)

            except Exception as e:
                err_msg = str(e).split('\n')[0]
                print(f"  [{name}] ERROR {url}: {err_msg}")

        await browser.close()
        
    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump({"target_name": name, "pages_crawled": len(crawled_data), "scrolls": scrolls}, f, indent=2)
        
    print(f"[DONE] {name}: {len(crawled_data)} pages → {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Universal Playwright Crawler (Stealth Mode)")
    parser.add_argument("--name", required=True)
    parser.add_argument("--seeds", required=True)
    parser.add_argument("--allow", default="")
    parser.add_argument("--deny", default="")
    parser.add_argument("--max", type=int, default=20)
    parser.add_argument("--scrolls", type=int, default=3)
    
    args = parser.parse_args()
    seeds = [s.strip() for s in args.seeds.split(",")]
    asyncio.run(run_crawler(args.name, seeds, args.allow, args.deny, args.max, args.scrolls))

if __name__ == "__main__":
    main()
