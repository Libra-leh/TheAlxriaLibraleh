#!/usr/bin/env python3
"""
BookDNA Fiction Scraper
=======================
Scrapes https://bookdna.com/bookshelf/fiction and extracts the
"All Time Best" fiction books ranked by community "Loved by N people" count.

Output: books.json — array sorted by loved_count desc:
  { "title", "author", "cover", "loved_count", "url" }

Usage:
  python3 scrape_bookdna.py                        # page 1, all books
  python3 scrape_bookdna.py --pages 3              # first 3 pages
  python3 scrape_bookdna.py --min-loved 20 --pretty

Requirements:
  pip install requests beautifulsoup4
"""

import re
import json
import time
import argparse
import sys
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing deps. Run: pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL  = "https://bookdna.com"
SHELF_URL = "https://bookdna.com/bookshelf/fiction"
OUTPUT    = "books.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://bookdna.com/",
}

LOVED_RE = re.compile(r'Loved by (\d+)\s*people', re.IGNORECASE)


def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            print(f"  Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


def parse_books(html):
    """
    Parse books from page HTML.

    Structure on bookdna.com (flat siblings, NOT nested):
        <strong>Loved by 118 people</strong>   <- text node we find
        <h2><a href="/book/...">Title</a></h2> <- find_next('h2')
        By <a href="/search/author/...">Author</a>
        <img alt="Book cover of ..." src="..."> <- find_next('img')

    Books without a "Loved by" string are promoted listings -> skipped.
    """
    soup  = BeautifulSoup(html, "html.parser")
    books = []
    seen  = set()

    for text_node in soup.find_all(string=LOVED_RE):
        match = LOVED_RE.search(text_node)
        if not match:
            continue
        loved_count = int(match.group(1))

        # text_node.parent = <strong>, .parent.parent = containing block
        base = text_node.parent.parent

        # Title
        h2 = base.find_next("h2")
        if not h2:
            continue
        title_el = h2.find("a") or h2
        title = title_el.get_text(strip=True)
        if not title or title in seen:
            continue
        seen.add(title)

        # Book URL
        href     = title_el.get("href", "") if title_el.name == "a" else ""
        book_url = urljoin(BASE_URL, href) if href else ""

        # Author
        author_a = base.find_next("a", href=re.compile(r"/search/author/"))
        author   = author_a.get_text(strip=True) if author_a else ""

        # Cover image - upgrade to higher resolution
        img   = base.find_next("img", alt=re.compile(r"Book cover", re.I))
        cover = ""
        if img:
            cover = re.sub(r"width=\d+", "width=400", img.get("src", ""))

        books.append({
            "title":       title,
            "author":      author,
            "cover":       cover,
            "loved_count": loved_count,
            "url":         book_url,
        })

    books.sort(key=lambda b: b["loved_count"], reverse=True)
    return books


def scrape(pages=1, min_loved=1):
    all_books = []
    seen      = set()

    for page in range(1, pages + 1):
        url = SHELF_URL if page == 1 else f"{SHELF_URL}?page={page}"
        print(f"Fetching page {page}: {url}")
        html  = fetch_page(url)
        found = parse_books(html)
        print(f"  Found {len(found)} books with loved counts")

        for b in found:
            key = b["title"].lower().strip()
            if key not in seen:
                seen.add(key)
                all_books.append(b)

        if page < pages:
            time.sleep(1)

    all_books = [b for b in all_books if b["loved_count"] >= min_loved]
    all_books.sort(key=lambda b: b["loved_count"], reverse=True)
    return all_books


def main():
    p = argparse.ArgumentParser(description="Scrape BookDNA best fiction list")
    p.add_argument("--pages",     type=int, default=1,      help="Pages to scrape (default: 1)")
    p.add_argument("--min-loved", type=int, default=1,      help="Min loved count (default: 1)")
    p.add_argument("--output",    type=str, default=OUTPUT, help=f"Output file (default: {OUTPUT})")
    p.add_argument("--pretty",    action="store_true",      help="Pretty-print JSON")
    args = p.parse_args()

    print(f"BookDNA Fiction Scraper")
    print(f"  Pages:     {args.pages}")
    print(f"  Min loved: {args.min_loved}")
    print(f"  Output:    {args.output}\n")

    try:
        books = scrape(pages=args.pages, min_loved=args.min_loved)
    except RuntimeError as e:
        print(f"\nError: {e}")
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2 if args.pretty else None)

    print(f"\nDone — {len(books)} books saved to {args.output}")
    if books:
        print("\nTop 10:")
        for i, b in enumerate(books[:10], 1):
            print(f"  {i:2}. [{b['loved_count']:3}❤] {b['title']} — {b['author']}")


if __name__ == "__main__":
    main()
