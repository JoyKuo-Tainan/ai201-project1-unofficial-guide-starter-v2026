"""
Settings for The Unofficial Guide.

Everything you're likely to change lives here, at the top, on purpose.
You'll edit THRESHOLD in Milestone 4 and the chunking numbers in Milestone 3.

Anything you set in your .env file wins over the defaults here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


# ─── The corpus you're working with ──────────────────────────────────────────
# Change this to switch corpora, or pass --corpus on the command line.
# Options are the folder names inside corpora/. See corpora/README.md.

CORPUS = os.getenv("AI201_CORPUS", "campus_life")


# ─── Chunking (Milestone 3) ──────────────────────────────────────────────────
# These are deliberately plain, generic numbers. Milestone 3 is where you
# replace them with numbers that fit the documents you actually read.

# These two belong to chunker.py::fallback_split only.
CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 120     # characters shared between neighbouring chunks

# The numbers below belong to chunker.py::split_documents, which picks one of
# three strategies per corpus. They were set by measuring the corpora, not
# guessed — see the table in chunker.py's docstring.

# Upper bound on a chunk, not a target: a document shorter than this is never
# cut. 900 keeps every campus_life document (longest 549) and every
# advice_threads document (longest 793) intact, while city_guides
# (1,436–2,510) still splits on its headings.
MAX_CHUNK_CHARS = 900

# No chunk comes out shorter than this unless the entire source document is
# shorter than this. Short tails are merged back into the chunk before them,
# which is what stops the 2-character chunk the old stride produced.
MIN_CHUNK_CHARS = 30

# advice_threads only. Replies run 35–222 characters, so a whole thread would
# fit in MAX_CHUNK_CHARS as one chunk and the strategy would never separate
# the disagreeing answers. 400 groups two or three replies per chunk instead.
THREAD_CHUNK_CHARS = 400

# advice_threads only. Neighbouring chunks share this many replies, because an
# answer in that corpus is often spread across a reply boundary.
THREAD_REPLY_OVERLAP = 1


# ─── Retrieval (Milestone 4) ─────────────────────────────────────────────────

TOP_K = 10               # how many chunks to pull back per question

# The relevance gate. If the best chunk is further away than this, the system
# refuses to answer instead of handing the model thin material.
#
# LOWER IS BETTER: 0.3 is a close match, 0.9 is unrelated.
#
# 0.6 is a reasonable starting point, not a right answer. Milestone 4 has you
# measure your own two groups of distances and put the cutoff in the gap.
# Most corpora land somewhere between 0.45 and 0.75.
#
# Measured, Milestone 4. My five questions land at 0.246-0.432; the five in
# OUT_OF_SCOPE land at 0.825-0.934. Nothing sits between them, so the gap is
# 0.39 wide and this is its midpoint. Rounded to two places because a third
# would be pretending the boundary is sharper than the measurement was.
THRESHOLD = 0.63


# ─── Models ──────────────────────────────────────────────────────────────────
# Embeddings run on your own machine and cost no API quota.
# Only generation calls out to a service.

# This is the model Chroma bundles, and leaving it alone is the fast path: it
# downloads about 80 MB from Chroma's own CDN and needs nothing else installed.
#
# Setting it to any other name — unit 2's "try a second embedding model"
# stretch option — switches to loading that model from Hugging Face instead,
# which needs `pip install 'sentence-transformers>=3.4,<3.5'` first. store.py
# says so with a real error message rather than a stack trace if you forget.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL = os.getenv("AI201_MODEL", "gemini-3.5-flash-lite")


# ─── Rate limiting and quota guards ──────────────────────────────────────────
# You should not need to touch these. They exist so that a runaway loop costs
# you a warning instead of your whole day's allowance.

REQUESTS_PER_MINUTE = 30       # outgoing calls the limiter will allow per minute
SESSION_REQUEST_BUDGET = 300   # stop and warn rather than draining the daily quota
MAX_RETRIES = 4                # on 429 / resource-exhausted, with backoff

CACHE_ENABLED = os.getenv("AI201_CACHE", "1") != "0"
CACHE_DIR = ROOT / ".cache"


# ─── Paths ───────────────────────────────────────────────────────────────────

CORPORA_DIR = ROOT / "corpora"
CHROMA_DIR = ROOT / "chroma_db"
RESULTS_DIR = ROOT / "results"


def corpus_path(name: str | None = None) -> Path:
    """Folder holding the documents for a corpus."""
    return CORPORA_DIR / (name or CORPUS) / "documents"


def collection_name(name: str | None = None, variant: str = "default") -> str:
    """
    Name of the vector-store collection for a corpus.

    `variant` lets you index the same corpus two different ways and query both
    without deleting anything — you'll want that in unit 2 when you compare
    chunking strategies.

    Chroma is fussy about collection names: 3 to 63 characters, starting and
    ending with a letter or digit, and nothing but letters, digits, underscores
    and hyphens in between. If you bring your own corpus and name the folder
    something Chroma won't accept, this cleans it up rather than failing.
    """
    import re

    raw = f"{name or CORPUS}__{variant}"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", raw)
    cleaned = cleaned.strip("_-")          # must start and end alphanumeric
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"c{cleaned}"
    if not cleaned[-1].isalnum():
        cleaned = f"{cleaned}0"
    return cleaned[:63].rstrip("_-") or "collection"
