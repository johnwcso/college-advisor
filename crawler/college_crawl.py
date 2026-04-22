#!/usr/bin/env python3
"""
College website crawler — reads colleges.json for targets,
crawls admissions/program pages, saves JSONL per college,
and supports scheduled re-crawling via --interval.
"""
import argparse
import asyncio
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.robotparser import RobotFileParser


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def normalize_url(base: str, href: str | None) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.startswith(("javascript:", "mailto:", "tel:", "data:")):
        return None
    url, _ = urldefrag(urljoin(base, href))
    parsed = urlparse(url)
    return url if parsed.scheme in ("http", "https") else None


def safe_filename(url: str, suffix: str) -> str:
    p = urlparse(url)
    host = p.netloc.replace(":", "_")
    path = re.sub(r"[^A-Za-z0-9._-]+", "_", p.path.strip("/") or "root")[:60]
    return f"{host}__{path}__{sha1(url)}.{suffix}"


class RobotsCache:
    def __init__(self):
        self._cache = {}

    def allowed(self, url: str, ua: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = self._cache.get(robots_url, "UNCHECKED")
        if rp == "UNCHECKED":
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
            except Exception:
                rp = None
            self._cache[robots_url] = rp
        if rp is None:
            return True
        try:
            return rp.can_fetch(ua or "*", url)
        except Exception:
            return True


async def crawl_college(college: dict, settings: dict, output_dir: Path, pw):
    name = college["name"]
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    college_dir = output_dir / slug
    college_dir.mkdir(parents=True, exist_ok=True)

    if settings.get("save_text"):
        (college_dir / "text").mkdir(exist_ok=True)
    if settings.get("save_html"):
        (college_dir / "html").mkdir(exist_ok=True)
    if settings.get("screenshot"):
        (college_dir / "screenshots").mkdir(exist_ok=True)

    out_file = college_dir / "pages.jsonl"
    meta_file = college_dir / "meta.json"

    allow_re = re.compile(college["allow_regex"]) if college.get("allow_regex") else None
    deny_re = re.compile(college["deny_regex"]) if college.get("deny_regex") else None
    ua = settings.get("user_agent", "CollegeCrawler/1.0")
    robots = RobotsCache()
    max_pages = settings.get("max_pages_per_college", 40)
    max_depth = settings.get("max_depth", 2)

    def url_allowed(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if allow_re and not allow_re.search(url):
            return False
        if deny_re and deny_re.search(url):
            return False
        if settings.get("respect_robots") and not robots.allowed(url, ua):
            return False
        return True

    queue = asyncio.Queue()
    seen: set[str] = set()
    seen_lock = asyncio.Lock()
    write_lock = asyncio.Lock()
    pages_crawled = 0

    async def enqueue(url: str, depth: int):
        if not url_allowed(url):
            return
        async with seen_lock:
            if url in seen or len(seen) >= max_pages:
                return
            seen.add(url)
            await queue.put((url, depth))

    for seed in college.get("seeds", []):
        u = normalize_url(seed, seed)
        if u:
            await enqueue(u, 0)

    browser_type = getattr(pw, settings.get("browser", "chromium"))
    browser = await browser_type.launch(headless=settings.get("headless", True))
    context = await browser.new_context(user_agent=ua)

    async def worker():
        nonlocal pages_crawled
        while True:
            url, depth = await queue.get()
            page = await context.new_page()
            record = {
                "college": name,
                "url": url,
                "final_url": None,
                "status": None,
                "depth": depth,
                "title": None,
                "text": None,
                "links": [],
                "crawled_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
            try:
                resp = await page.goto(
                    url,
                    wait_until=settings.get("wait_until", "networkidle"),
                    timeout=settings.get("timeout_ms", 30000),
                )
                delay = settings.get("delay_ms", 0)
                if delay > 0:
                    await page.wait_for_timeout(delay)

                record["final_url"] = page.url
                record["status"] = resp.status if resp else None
                record["title"] = await page.title()

                try:
                    record["text"] = await page.locator("body").inner_text(timeout=5000)
                except Exception:
                    record["text"] = ""

                hrefs = await page.eval_on_selector_all(
                    "a[href]", "els => els.map(a => a.getAttribute('href'))"
                )
                links = []
                for href in hrefs:
                    nu = normalize_url(page.url, href)
                    if nu and nu not in links:
                        links.append(nu)
                record["links"] = links

                if settings.get("save_html"):
                    html = await page.content()
                    fn = safe_filename(page.url, "html")
                    (college_dir / "html" / fn).write_text(html, encoding="utf-8")

                if settings.get("save_text") and record["text"]:
                    fn = safe_filename(page.url, "txt")
                    (college_dir / "text" / fn).write_text(record["text"], encoding="utf-8")

                if settings.get("screenshot"):
                    fn = safe_filename(page.url, "png")
                    await page.screenshot(
                        path=str(college_dir / "screenshots" / fn),
                        full_page=True,
                    )

                if depth < max_depth:
                    for link in links:
                        await enqueue(link, depth + 1)

                pages_crawled += 1
                print(f"  [{name}] ({pages_crawled}/{max_pages}) {record['status']} {url[:80]}")

            except Exception as e:
                record["final_url"] = page.url
                record["error"] = f"{type(e).__name__}: {e}"
                print(f"  [{name}] ERROR {url[:80]}: {e}", file=sys.stderr)
            finally:
                async with write_lock:
                    with out_file.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                await page.close()
                queue.task_done()

    concurrency = settings.get("concurrency", 3)
    workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
    await queue.join()
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)
    await context.close()
    await browser.close()

    meta = {
        "college": name,
        "country": college.get("country"),
        "tags": college.get("tags", []),
        "seeds": college.get("seeds", []),
        "pages_crawled": pages_crawled,
        "last_crawled": datetime.now(timezone.utc).isoformat(),
    }
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[DONE] {name}: {pages_crawled} pages → {out_file}")
    return meta


def load_config(config_path: str) -> dict:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def needs_refresh(college_slug: str, output_dir: Path, interval_days: float) -> bool:
    meta_file = output_dir / college_slug / "meta.json"
    if not meta_file.exists():
        return True
    try:
        meta = json.loads(meta_file.read_text())
        last = datetime.fromisoformat(meta["last_crawled"])
        age = (datetime.now(timezone.utc) - last).total_seconds() / 86400
        return age >= interval_days
    except Exception:
        return True


async def run(args):
    config = load_config(args.config)
    settings = {**config.get("settings", {})}

    if args.browser:
        settings["browser"] = args.browser
    if args.concurrency:
        settings["concurrency"] = args.concurrency
    if args.max_pages:
        settings["max_pages_per_college"] = args.max_pages
    if args.no_headless:
        settings["headless"] = False

    output_dir = Path(args.output or settings.get("output_dir", "crawl_output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    colleges = config.get("colleges", [])

    # Filter by tag
    if args.tags:
        tag_filter = set(args.tags.split(","))
        colleges = [c for c in colleges if tag_filter & set(c.get("tags", []))]

    # Filter by name (substring match)
    if args.college:
        name_filter = args.college.lower()
        colleges = [c for c in colleges if name_filter in c["name"].lower()]

    # Filter by country
    if args.country:
        colleges = [c for c in colleges if c.get("country", "").lower() == args.country.lower()]

    if not colleges:
        raise SystemExit("No colleges matched the filters.")

    print(f"Crawling {len(colleges)} college(s)  |  output → {output_dir}\n")

    from playwright.async_api import async_playwright

    all_meta = []
    for college in colleges:
        slug = re.sub(r"[^a-z0-9]+", "_", college["name"].lower()).strip("_")

        if args.interval is not None and not needs_refresh(slug, output_dir, args.interval):
            print(f"[SKIP] {college['name']} — crawled recently (within {args.interval}d)")
            continue

        # Clear old JSONL before fresh crawl
        old_file = output_dir / slug / "pages.jsonl"
        if old_file.exists():
            old_file.unlink()

        async with async_playwright() as pw:
            meta = await crawl_college(college, settings, output_dir, pw)
            all_meta.append(meta)

    summary_path = output_dir / "summary.json"
    existing = []
    if summary_path.exists():
        try:
            existing = json.loads(summary_path.read_text())
        except Exception:
            pass
    merged = {m["college"]: m for m in existing}
    for m in all_meta:
        merged[m["college"]] = m
    summary_path.write_text(json.dumps(list(merged.values()), indent=2), encoding="utf-8")
    print(f"\nSummary written → {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="College website crawler")
    parser.add_argument("--config", default="colleges.json", help="Path to colleges.json")
    parser.add_argument("--output", help="Override output directory")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"])
    parser.add_argument("--concurrency", type=int)
    parser.add_argument("--max-pages", type=int, dest="max_pages")
    parser.add_argument("--no-headless", action="store_true", dest="no_headless")
    parser.add_argument("--tags", help="Comma-separated tags to filter colleges, e.g. ivy,sailing")
    parser.add_argument("--college", help="Crawl only colleges matching this name substring")
    parser.add_argument("--country", help="Filter by country, e.g. USA or UK")
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        metavar="DAYS",
        help="Skip colleges crawled within this many days (e.g. 7 for weekly refresh)",
    )
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

