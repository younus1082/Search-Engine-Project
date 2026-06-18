"""
scrape.py
=========
Collects educational articles from Wikipedia using the official MediaWiki API,
and saves them to data/docs.json.

We use the API (not raw HTML scraping) on purpose:
  * It is allowed by Wikipedia and far less likely to get us rate-limited/blocked.
  * It returns clean plain text, so our preprocessing stays simple.

Each saved document is a dict:
    {
      "id":    <int>,        # our own sequential document ID
      "title": <str>,        # article title  -> shown in results
      "url":   <str>,        # link back to the source
      "text":  <str>         # plain-text body -> what we index & snippet from
    }

Run:
    python scrape.py
"""

import json
import time
import os
import requests

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
API_URL = "https://en.wikipedia.org/w/api.php"

# Wikipedia categories that fit the "educational content" domain.
# Feel free to add/remove categories to change the flavour of your corpus.
CATEGORIES = [
    "Category:Mathematics",
    "Category:Physics",
    "Category:Computer science",
    "Category:Machine learning",
    "Category:Biology",
]

ARTICLES_PER_CATEGORY = 80          # ~400 docs total -> enough for good ranking
REQUEST_DELAY_SECONDS = 0.5         # be polite: wait between API calls
OUTPUT_PATH = os.path.join("data", "docs.json")

# A descriptive User-Agent is required by Wikipedia's API etiquette.
HEADERS = {
    "User-Agent": "SpecializedSearchEngine/1.0 (university assignment; contact: student@example.com)"
}


def get_article_titles(category, limit):
    """Return up to `limit` article titles that belong to `category`."""
    titles = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": min(limit, 500),
        "cmtype": "page",          # only real articles, not sub-categories
        "format": "json",
    }
    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    members = response.json().get("query", {}).get("categorymembers", [])
    for member in members:
        titles.append(member["title"])
    return titles[:limit]


def get_article_text(title):
    """Return the plain-text extract of a single article (or '' on failure)."""
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,          # plain text, no HTML
        "exsectionformat": "plain",
        "titles": title,
        "format": "json",
    }
    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    for _page_id, page in pages.items():
        return page.get("extract", "") or ""
    return ""


def scrape():
    """Crawl every configured category and write all documents to disk."""
    documents = []
    seen_titles = set()            # avoid indexing the same article twice
    doc_id = 0

    for category in CATEGORIES:
        print(f"[+] Fetching titles from {category} ...")
        try:
            titles = get_article_titles(category, ARTICLES_PER_CATEGORY)
        except requests.RequestException as error:
            print(f"    ! could not fetch category ({error}); skipping")
            continue

        for title in titles:
            if title in seen_titles:
                continue
            seen_titles.add(title)

            try:
                text = get_article_text(title)
            except requests.RequestException as error:
                print(f"    ! failed on '{title}' ({error}); skipping")
                continue
            finally:
                time.sleep(REQUEST_DELAY_SECONDS)

            # Skip stubs / disambiguation pages with almost no content.
            if len(text) < 200:
                continue

            documents.append({
                "id": doc_id,
                "title": title,
                "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_"),
                "text": text,
            })
            doc_id += 1
            print(f"    ({doc_id:>3}) saved: {title}")

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(documents, handle, ensure_ascii=False, indent=2)

    print(f"\n[done] {len(documents)} documents written to {OUTPUT_PATH}")


if __name__ == "__main__":
    scrape()
