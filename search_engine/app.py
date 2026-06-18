"""
app.py
======
A small Flask web interface for the search engine (the bonus "web interface").

Routes:
    GET /          -> the search homepage (search bar)
    GET /search    -> results page; reads ?q=<query>&mode=<AND|OR>

The heavy lifting lives in search.py; this file only wires HTTP to it.

Run:
    python app.py
then open http://127.0.0.1:5000
"""

import json
import os
import time

from flask import Flask, render_template, request
from markupsafe import Markup

from inverted_index import InvertedIndex
from search import SearchEngine

app = Flask(__name__)

DOCS_PATH = os.path.join("data", "docs.json")
INDEX_PATH = os.path.join("data", "index.pkl")

# Build the index on first startup if it isn't on disk yet. This lets the app
# deploy on a host (e.g. Render) straight from the repo: only data/docs.json
# needs to be committed, and the index is created automatically on boot.
if not os.path.exists(INDEX_PATH):
    if not os.path.exists(DOCS_PATH):
        raise SystemExit("data/docs.json missing. Run scrape.py first (or commit docs.json).")
    print("[startup] index not found; building it from docs.json ...")
    with open(DOCS_PATH, "r", encoding="utf-8") as handle:
        documents = json.load(handle)
    new_index = InvertedIndex()
    new_index.build_from_documents(documents)
    new_index.save(INDEX_PATH)

# Load the index ONCE at startup (not per request) so searches are instant.
engine = SearchEngine(InvertedIndex.load(INDEX_PATH))
TOTAL_DOCS = engine.index.num_documents


@app.route("/")
def home():
    return render_template("index.html", total_docs=TOTAL_DOCS)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    mode = request.args.get("mode", "OR").upper()
    if mode not in ("AND", "OR"):
        mode = "OR"

    results = []
    total_matches = 0
    elapsed = 0.0
    if query:
        start = time.perf_counter()
        response = engine.search(query, mode=mode, top_k=10)
        elapsed = time.perf_counter() - start

        results = response["results"]
        total_matches = response["total_matches"]

        # The snippet already contains <mark> tags we generated ourselves,
        # so mark it safe to render as HTML (it is not user input).
        for hit in results:
            hit["snippet"] = Markup(hit["snippet"])

    return render_template(
        "results.html",
        query=query,
        mode=mode,
        results=results,
        total_matches=total_matches,
        elapsed=f"{elapsed * 1000:.0f}",
        total_docs=TOTAL_DOCS,
    )


if __name__ == "__main__":
    app.run(debug=True)
