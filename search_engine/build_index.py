"""
build_index.py
==============
Loads the scraped documents (data/docs.json), builds the inverted index,
and saves it to data/index.pkl so the search app can load it instantly.

Run AFTER scrape.py:
    python build_index.py
"""

import json
import os

from inverted_index import InvertedIndex

DOCS_PATH = os.path.join("data", "docs.json")
INDEX_PATH = os.path.join("data", "index.pkl")


def main():
    if not os.path.exists(DOCS_PATH):
        raise SystemExit(
            f"{DOCS_PATH} not found. Run `python scrape.py` first."
        )

    with open(DOCS_PATH, "r", encoding="utf-8") as handle:
        documents = json.load(handle)

    index = InvertedIndex()
    index.build_from_documents(documents)
    index.save(INDEX_PATH)


if __name__ == "__main__":
    main()
