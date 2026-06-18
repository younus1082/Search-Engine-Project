"""
inverted_index.py
=================
The heart of the project: a hand-built inverted index.

NO search/indexing libraries are used here (no Elasticsearch, Whoosh, etc.) --
just plain Python dictionaries, exactly as the assignment requires.

What an inverted index is
-------------------------
A normal ("forward") index maps:   document -> the words it contains.
An INVERTED index flips that:      word     -> the documents that contain it.

That flip is what makes search fast: to answer a query we look up the query
terms directly instead of scanning every document.

Our structure
-------------
self.index maps:

    term -> {
        doc_id -> [pos1, pos2, ...]      # positions of the term in that doc
    }

Storing positions (not just a count) gives us, for free:
    * term frequency  = len(positions)        -> used by TF-IDF ranking
    * snippet location = positions[0]          -> where to cut the preview
    * a path to phrase queries later if wanted

We also keep:
    self.documents    -> id -> {title, url, text}  (to display results)
    self.doc_lengths  -> id -> number of tokens     (for ranking normalisation)
"""

import pickle
from collections import defaultdict

from preprocess import tokenize


class InvertedIndex:
    def __init__(self):
        # term -> {doc_id -> [positions]}
        self.index = defaultdict(lambda: defaultdict(list))
        # doc_id -> document metadata (title, url, raw text)
        self.documents = {}
        # doc_id -> token count (used to normalise term frequencies)
        self.doc_lengths = {}

    # ------------------------------------------------------------------ build
    def add_document(self, doc_id, title, url, text):
        """Tokenise one document and fold every token into the index."""
        self.documents[doc_id] = {"title": title, "url": url, "text": text}
        tokens = tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)

        # Record the position of every token under its term.
        for position, term in enumerate(tokens):
            self.index[term][doc_id].append(position)

    def build_from_documents(self, documents):
        """Build the whole index from a list of doc dicts (see scrape.py)."""
        for doc in documents:
            self.add_document(doc["id"], doc["title"], doc["url"], doc["text"])
        print(f"[index] {len(self.documents)} documents, "
              f"{len(self.index)} unique terms")

    # ------------------------------------------------------------------ lookup
    def get_postings(self, term):
        """Return {doc_id -> [positions]} for a single, already-stemmed term."""
        return self.index.get(term, {})

    def document_frequency(self, term):
        """In how many documents does this term appear? (used for IDF)"""
        return len(self.index.get(term, {}))

    @property
    def num_documents(self):
        return len(self.documents)

    # ------------------------------------------------------------- persistence
    def save(self, path):
        """Pickle the index to disk so we don't rebuild it on every run."""
        # defaultdict with a lambda can't be pickled, so convert to plain dicts.
        plain_index = {term: dict(postings)
                       for term, postings in self.index.items()}
        with open(path, "wb") as handle:
            pickle.dump({
                "index": plain_index,
                "documents": self.documents,
                "doc_lengths": self.doc_lengths,
            }, handle)
        print(f"[index] saved to {path}")

    @classmethod
    def load(cls, path):
        """Recreate an InvertedIndex from a pickle written by save()."""
        with open(path, "rb") as handle:
            data = pickle.load(handle)
        index = cls()
        index.index = defaultdict(lambda: defaultdict(list))
        for term, postings in data["index"].items():
            for doc_id, positions in postings.items():
                index.index[term][doc_id] = positions
        index.documents = data["documents"]
        index.doc_lengths = data["doc_lengths"]
        return index
