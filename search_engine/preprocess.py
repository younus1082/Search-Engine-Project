"""
preprocess.py
=============
Turns a raw string of text into a clean list of normalised tokens.

This is the ONLY place NLTK is used, which keeps it cleanly inside the
assignment's "preprocessing only" rule. The actual index and search logic
below use no search libraries at all.

Pipeline (each step is a deliberate design choice -- see the report):
    1. Lowercase            -> "Search" and "search" become the same term
    2. Tokenise on words    -> split text into word tokens, drop punctuation
    3. Remove stopwords     -> drop "the", "is", "of"... they add no meaning
    4. Stemming             -> "running", "runs", "ran" -> "run"

We expose tokenize() for documents and a matching path for queries so that
the query and the index are normalised exactly the same way (critical: if they
differ, a query term would never match its indexed form).
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# ----------------------------------------------------------------------------
# One-time NLTK data download (safe to call repeatedly; it is cached).
# ----------------------------------------------------------------------------
for resource in ("stopwords", "punkt"):
    try:
        nltk.data.find(f"corpora/{resource}")
    except LookupError:
        nltk.download(resource, quiet=True)

_STEMMER = PorterStemmer()
_STOPWORDS = set(stopwords.words("english"))

# Match runs of letters/digits. This throws away punctuation and symbols.
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text):
    """
    Normalise raw text into a list of stemmed, stopword-free tokens.

    Returns tokens IN ORDER so the inverted index can store word positions
    (needed for snippets and for any future phrase queries).
    """
    text = text.lower()
    raw_tokens = _TOKEN_PATTERN.findall(text)

    tokens = []
    for token in raw_tokens:
        if token in _STOPWORDS:
            continue
        if len(token) == 1:        # single characters carry little meaning
            continue
        tokens.append(_STEMMER.stem(token))
    return tokens


if __name__ == "__main__":
    # Quick manual check.
    sample = "The Running Robots are learning to run and they ran quickly!"
    print(tokenize(sample))
