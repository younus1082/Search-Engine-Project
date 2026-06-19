# Marginalia — A Specialized Search Engine with an Inverted Index

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://marginalia-tv2m.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-web%20interface-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![No Search Libraries](https://img.shields.io/badge/inverted%20index-from%20scratch-orange)]()

A specialized search engine built **entirely from scratch** over a corpus of
educational articles collected from Wikipedia. It implements its own inverted
index, boolean (AND / OR) query processing, and TF-IDF ranking — with **no
pre-built search or indexing libraries** (no Elasticsearch, Whoosh, etc.). A
clean Flask web interface with keyword highlighting is included.

### Live demo: **https://marginalia-tv2m.onrender.com/**

> The demo is hosted on a free tier, so the first request after a period of
> inactivity may take ~30–50 seconds to wake up. After that it responds instantly.

---

## Domain

**Educational content** — encyclopedic articles on Mathematics, Physics,
Computer Science, Machine Learning, and Biology, collected from the official
Wikipedia (MediaWiki) API. The full index covers **156 documents** and
**11,689 unique terms**.

## Features

- **Inverted index built from scratch** — maps each term to the documents and
  positions where it appears, using only plain Python data structures.
- **Boolean retrieval** — `AND` (all words) and `OR` (any word) query modes.
- **TF-IDF ranking** — relevance scoring with document-length normalisation.
- **Single- and multi-word queries.**
- **Snippets with keyword highlighting** — each result shows the title, link,
  a relevant snippet, and a relevance score.
- **Clean, responsive web interface** with an animated homepage.

## How it works

The system runs as a four-stage pipeline:

```
scrape.py         collect articles from the Wikipedia API     data/docs.json
build_index.py    build the inverted index                    data/index.pkl
search.py         query  boolean filter  TF-IDF rank  snippets
app.py            Flask web interface wrapping the search engine
```

1. **Preprocessing** (`preprocess.py`) — lowercases text, tokenises it, removes
   stopwords, and applies Porter stemming. Documents and queries pass through
   the **same** pipeline so their terms line up.
2. **Inverted index** (`inverted_index.py`) — stores:

   ```
   term    { document_id    [position1, position2, ...] }
   ```

   Storing positions gives term frequency, snippet locations, and a path to
   phrase queries from a single structure.
3. **Ranking** (`search.py`) — TF-IDF:

   ```
   tf  = 1 + log10(frequency of term in document)
   idf = log10( N / number of documents containing the term )
   score = Σ (tf × idf)  ÷  √(document length)
   ```

## Tech stack

- **Python** — core language
- **NLTK** — preprocessing only (tokenisation, stopwords, stemming)
- **Flask** — web interface (bonus)
- **requests** — data collection from the Wikipedia API
- **gunicorn** — production server used in deployment

## Project structure

```
Search-Engine-Project/
├── README.md
├── screenshots/
└── search_engine/
    ├── scrape.py            # collect articles from the Wikipedia API
    ├── build_index.py       # build and save the inverted index
    ├── preprocess.py        # tokenize, stopwords, stemming (NLTK)
    ├── inverted_index.py    # the inverted index (core requirement)
    ├── search.py            # query processing + TF-IDF ranking + snippets
    ├── app.py               # Flask web interface
    ├── templates/           # index.html (search bar) + results.html
    ├── static/style.css     # UI styling
    ├── data/                # docs.json (+ index.pkl, generated)
    └── requirements.txt
```

## Getting started (run locally)

```bash
# clone the repository
git clone https://github.com/younus1082/Search-Engine-Project.git
cd Search-Engine-Project/search_engine

# install dependencies
pip install -r requirements.txt

# (optional) collect a fresh corpus from Wikipedia — needs internet
python scrape.py

# build the inverted index
python build_index.py

# launch the web interface
python app.py
# then open http://127.0.0.1:5000
```

A sample `data/docs.json` is included, so you can run `build_index.py` and try
the engine immediately without scraping first.

You can also search from the command line:

```bash
python search.py
# prefix a query with "AND:" or "OR:" to choose the mode (default OR)
```

## Usage

- Type a single word (e.g. `calculus`) or multiple words (e.g. `neural network`).
- Choose a match mode:
  - **Any word (OR)** — returns documents containing at least one term (broader).
  - **All words (AND)** — returns documents containing every term (narrower).
- Results are ranked by TF-IDF relevance, with matching keywords highlighted.

## Deployment

The app is deployed on **Render** directly from this repository:

- **Root Directory:** `search_engine`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

The inverted index is built automatically on first startup from the committed
`data/docs.json`, so no manual build step is required on the host.

## Limitations & future work

- TF-IDF treats queries as a bag of words — it ignores word order and meaning,
  so `machine learning` and `learning machine` score identically.
- Porter stemming can occasionally be aggressive and merge unrelated words.
- The corpus contains a few non-article pages collected via category membership;
  filtering the crawl to genuine articles would improve quality.
- The index is held in memory, which suits a few thousand documents but not
  web-scale collections.

Possible improvements: phrase queries using the stored positions, field
weighting (title matches counting more than body matches), and lemmatisation
instead of stemming.

## Report

The full project report is available here:
[Marginalia_Search_Engine_Project_Report.pdf](Marginalia_Search_Engine_Project_Report.pdf)
