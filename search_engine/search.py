"""
search.py
=========
Query processing + ranking on top of the inverted index.

Implements everything the assignment asks for in the search layer:
    * single-word and multi-word queries
    * boolean AND / OR retrieval
    * ranked results using TF-IDF
    * title + highlighted snippet for each result

Ranking: TF-IDF with cosine-style accumulation
-----------------------------------------------
For a query term t and document d we score:

    tf  = 1 + log10(term frequency of t in d)      # dampened term frequency
    idf = log10(N / df(t))                          # rarer terms count more
    weight(t, d) = tf * idf

A document's score is the sum of weight(t, d) over all query terms it matches,
divided by sqrt(doc length) so long documents don't win just by being long.

This is a classic, defensible scheme. The trade-off (discuss in your report):
TF-IDF is fast and simple but ignores word order and meaning -- "machine
learning" and "learning machine" score identically.
"""

import math
import re

from preprocess import tokenize, _TOKEN_PATTERN


class SearchEngine:
    def __init__(self, index):
        self.index = index

    # --------------------------------------------------------- candidate sets
    def _matching_docs(self, terms, mode):
        """
        Return the set of doc IDs that satisfy the boolean mode.

        mode == "AND": a document must contain EVERY query term.
        mode == "OR" : a document must contain AT LEAST ONE query term.
        """
        postings_sets = []
        for term in terms:
            doc_ids = set(self.index.get_postings(term).keys())
            postings_sets.append(doc_ids)

        if not postings_sets:
            return set()

        if mode == "AND":
            result = postings_sets[0]
            for doc_ids in postings_sets[1:]:
                result = result & doc_ids        # intersection
            return result
        else:  # "OR"
            result = set()
            for doc_ids in postings_sets:
                result = result | doc_ids        # union
            return result

    # ------------------------------------------------------------- TF-IDF rank
    def _score(self, terms, candidate_ids):
        """Assign a TF-IDF score to each candidate document."""
        total_docs = self.index.num_documents
        scores = {}

        for term in terms:
            postings = self.index.get_postings(term)
            df = len(postings)
            if df == 0:
                continue
            idf = math.log10(total_docs / df)

            for doc_id, positions in postings.items():
                if doc_id not in candidate_ids:
                    continue
                tf = 1 + math.log10(len(positions))
                scores[doc_id] = scores.get(doc_id, 0.0) + tf * idf

        # Normalise by document length so long docs aren't unfairly favoured.
        for doc_id in scores:
            length = self.index.doc_lengths.get(doc_id, 1) or 1
            scores[doc_id] /= math.sqrt(length)

        return scores

    # --------------------------------------------------------------- snippets
    def _make_snippet(self, doc_id, query_terms, window=30):
        """
        Build a short preview centred on the first query-term hit, and wrap
        every matching word in <mark>...</mark> for highlighting in the UI.
        """
        text = self.index.documents[doc_id]["text"]
        words = text.split()

        # Find the first word whose stem matches a query term.
        hit_index = 0
        for i, word in enumerate(words):
            stem_matches = tokenize(word)
            if stem_matches and stem_matches[0] in query_terms:
                hit_index = i
                break

        start = max(0, hit_index - window // 2)
        end = min(len(words), start + window)
        snippet_words = words[start:end]

        # Highlight matching words (compare on stem so "running" matches "run").
        highlighted = []
        for word in snippet_words:
            stems = tokenize(word)
            if stems and stems[0] in query_terms:
                highlighted.append(f"<mark>{word}</mark>")
            else:
                highlighted.append(word)

        prefix = "... " if start > 0 else ""
        suffix = " ..." if end < len(words) else ""
        return prefix + " ".join(highlighted) + suffix

    # -------------------------------------------------------------- public API
    def search(self, query, mode="OR", top_k=10):
        """
        Run a full query and return a dict:

            {
              "results": [ {title, url, snippet, score}, ... ],   # top_k only
              "total_matches": <int>,   # ALL docs that satisfied the query
            }

        We return total_matches separately from results so the UI can show
        "top 10 of 143 matches". This is what makes the AND vs OR difference
        visible: even when the top-ranked documents overlap, the total number
        of matching documents differs (OR >= AND).

        mode is "AND" or "OR".
        """
        query_terms = tokenize(query)
        if not query_terms:
            return {"results": [], "total_matches": 0}

        candidate_ids = self._matching_docs(query_terms, mode)
        if not candidate_ids:
            return {"results": [], "total_matches": 0}

        scores = self._score(query_terms, candidate_ids)

        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        ranked = ranked[:top_k]

        results = []
        for doc_id, score in ranked:
            doc = self.index.documents[doc_id]
            results.append({
                "title": doc["title"],
                "url": doc["url"],
                "snippet": self._make_snippet(doc_id, set(query_terms)),
                "score": round(score, 4),
            })
        return {"results": results, "total_matches": len(candidate_ids)}


# ----------------------------------------------------------------------------
# Command-line search (handy for the demo and for testing without the web UI).
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    from inverted_index import InvertedIndex

    index_path = os.path.join("data", "index.pkl")
    if not os.path.exists(index_path):
        raise SystemExit("Run scrape.py then build_index.py first.")

    engine = SearchEngine(InvertedIndex.load(index_path))

    print("Specialized Search Engine -- type a query (blank to quit).")
    print("Tip: prefix with 'AND:' or 'OR:' to choose the mode (default OR).")
    while True:
        raw = input("\nquery> ").strip()
        if not raw:
            break
        mode = "OR"
        if raw.upper().startswith("AND:"):
            mode, raw = "AND", raw[4:].strip()
        elif raw.upper().startswith("OR:"):
            mode, raw = "OR", raw[3:].strip()

        response = engine.search(raw, mode=mode)
        hits = response["results"]
        total = response["total_matches"]
        if not hits:
            print("  no results.")
        else:
            print(f"  showing top {len(hits)} of {total} matching documents")
        for rank, hit in enumerate(hits, 1):
            # Strip the <mark> tags for plain console output.
            clean = re.sub(r"</?mark>", "", hit["snippet"])
            print(f"\n  {rank}. {hit['title']}  (score {hit['score']})")
            print(f"     {hit['url']}")
            print(f"     {clean}")
