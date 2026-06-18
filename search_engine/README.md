# Marginalia — a specialized search engine for educational content

A search engine built **from scratch** over a corpus of educational articles
scraped from Wikipedia. It implements its own inverted index, boolean
(AND/OR) query processing, and TF-IDF ranking — **no pre-built search or
indexing libraries** (no Elasticsearch, Whoosh, etc.). A small Flask web
interface is included for the bonus marks.

## Domain

**Educational content** — encyclopedic articles on mathematics, physics,
computer science, machine learning, and biology. The corpus is collected
from Wikipedia via its official API.

## Project structure

```
search_engine/
├── scrape.py           # 1. collect articles from the Wikipedia API -> data/docs.json
├── build_index.py      # 2. build the inverted index            -> data/index.pkl
├── preprocess.py       #    text cleaning: tokenize, stopwords, stemming (NLTK)
├── inverted_index.py   #    the inverted index (core requirement)
├── search.py           # 3. query processing + TF-IDF ranking + snippets
├── app.py              # 4. Flask web interface (bonus)
├── templates/          #    index.html (search bar) + results.html
├── static/style.css    #    UI styling
├── data/               #    docs.json + index.pkl live here
├── requirements.txt
└── README.md
```

## How it works

1. **Scrape** (`scrape.py`) pulls plain-text articles from Wikipedia categories
   and saves them as `data/docs.json`. Using the API (not raw HTML) keeps the
   text clean and respects Wikipedia's usage rules.
2. **Preprocess** (`preprocess.py`) lowercases text, splits it into word
   tokens, removes stopwords, and stems each token (Porter stemmer). Documents
   and queries go through the *same* pipeline so their terms line up.
3. **Index** (`inverted_index.py`) maps every term to the documents that
   contain it, storing the **positions** of each occurrence:

   ```
   term -> { doc_id -> [pos1, pos2, ...] }
   ```

   Positions give us term frequency (for ranking) and snippet locations for
   free.
4. **Search** (`search.py`):
   - **Boolean retrieval** — AND intersects the documents for each term; OR
     unions them.
   - **Ranking** — TF-IDF: `tf = 1 + log10(freq)`, `idf = log10(N / df)`,
     score `= Σ tf·idf`, normalised by `sqrt(document length)`.
   - **Snippets** — a preview centred on the first matched term, with matched
     words wrapped in `<mark>` for highlighting.

## Setup & run

```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. collect the corpus (takes a few minutes; needs internet)
python scrape.py

# 3. build the inverted index
python build_index.py

# 4a. search from the command line
python search.py
#    (prefix a query with "AND:" or "OR:" to choose the mode)

# 4b. ...or launch the web interface
python app.py
#    then open http://127.0.0.1:5000
```

A small sample `data/docs.json` is included so you can run
`build_index.py` and try the engine immediately, before scraping the full
corpus.

## Allowed libraries

Per the assignment, NumPy, Pandas, and NLTK (preprocessing only) are permitted.
This project uses **NLTK** for preprocessing; NumPy and Pandas are allowed but
were not needed, so they are not dependencies. `requests` is used for data
collection and `flask` for the optional web interface — neither is a search or
indexing library.

## Notes / known trade-offs

- **TF-IDF** ignores word order and meaning: "machine learning" and "learning
  machine" score identically. A phrase-query mode could use the stored
  positions to fix this.
- **Stemming is aggressive**: the Porter stemmer occasionally over-stems
  (e.g. "university" → "univers"), which can merge unrelated words.
- The index is held in memory and pickled to disk; it suits a few thousand
  documents comfortably but is not designed for web-scale corpora.
