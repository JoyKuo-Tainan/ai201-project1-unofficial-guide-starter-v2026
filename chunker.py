"""
Stage 2 of the pipeline: splitting documents into chunks.


─────────────────────────────────────────────────────────────────────────────
MILESTONE 3

Two problems with the fixed-size baseline, both measured rather than assumed:

  1. On `advice_threads` it produced a 2-character chunk. That was not a
     splitting decision, it was arithmetic. The window advances
     800 - 120 = 680 characters, so `thread_meal_plan_tier.txt` (682 chars)
     emitted the whole document as chunk 0 and then characters 680-682 —
     "t." — as chunk 1. No document in that corpus even reaches 800, so
     every cut it made there was spurious.

  2. On `campus_life` the 800 was never doing any work, exactly as the brief
     says above. The longest document is 549 characters. Nothing to cut.

So `split_documents` now picks a strategy per corpus, because the three
corpora have different shapes and one set of numbers cannot fit all of them:

    corpus           doc chars (min/med/max)   strategy
    campus_life        178 /   305 /   549     _split_short_post
    advice_threads     317 /   531 /   793     _split_thread
    city_guides      1,436 / 2,116 / 2,510     _split_sections

The strategy is chosen by corpus name first (STRATEGIES, below), falling back
to detecting the shape of the document itself — reply markers, then markdown
headings, then plain short post. That fallback is what handles `practice`,
and any corpus of my own, without needing an entry in the table.

Two guarantees hold across all three strategies:
  - No chunk is shorter than config.MIN_CHUNK_CHARS, unless the whole source
    document is shorter than that (campus_life has one such document, 178).
  - No chunk is cut in the middle of a sentence.

`fallback_split` is untouched and still reachable, as the brief asks.
─────────────────────────────────────────────────────────────────────────────
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


# ─── Shared helpers ──────────────────────────────────────────────────────────
# All three strategies below build a list of plain strings. split_documents
# wraps them into Chunks, so none of them has to know about Chunk at all.

# "--- reply 1 (24 votes) ---", the separator advice_threads uses.
REPLY_MARKER = re.compile(r"^-{2,}\s*reply\b.*$", re.MULTILINE | re.IGNORECASE)

# "# Title" / "## Getting around", the structure city_guides uses.
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)


def _paragraphs(text: str, budget: int) -> list[str]:
    """
    Blank-line-separated paragraphs, with anything over `budget` broken at
    sentence ends rather than mid-word.

    No shipped corpus has a paragraph this long (the largest is 530
    characters, in `practice`), but a corpus of my own might.
    """
    units: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= budget:
            units.append(para)
            continue

        sentences: list[str] = []
        for sentence in re.split(r"(?<=[.!?])\s+", para):
            sentence = sentence.strip()
            # A single "sentence" longer than the budget has no punctuation to
            # cut on. Only here do we fall back to cutting on character count.
            while len(sentence) > budget:
                sentences.append(sentence[:budget].strip())
                sentence = sentence[budget:].strip()
            if sentence:
                sentences.append(sentence)
        units.extend(_pack(sentences, budget))

    return units


def _pack(units: list[str], budget: int) -> list[str]:
    """Greedily join units with a blank line, staying under `budget`."""
    packed: list[str] = []
    current = ""
    for unit in units:
        if not current:
            current = unit
        elif len(current) + 2 + len(unit) <= budget:
            current = f"{current}\n\n{unit}"
        else:
            packed.append(current)
            current = unit
    if current:
        packed.append(current)
    return packed


def _merge_short(pieces: list[str], min_chars: int | None = None) -> list[str]:
    """
    Fold any piece below the floor into its neighbour.

    This is the guard the fixed-size chunker was missing. A leftover tail like
    "t." never survives as its own chunk — it goes back onto the piece it was
    cut from. A document that is simply shorter than the floor is left alone,
    because there is no text to merge it with.
    """
    min_chars = min_chars or config.MIN_CHUNK_CHARS
    if len(pieces) <= 1:
        return pieces

    merged: list[str] = []
    for piece in pieces:
        if merged and len(piece) < min_chars:
            merged[-1] = f"{merged[-1]}\n\n{piece}"
        else:
            merged.append(piece)

    # A short *first* piece had nothing before it to merge into.
    if len(merged) > 1 and len(merged[0]) < min_chars:
        merged[1] = f"{merged[0]}\n\n{merged[1]}"
        merged.pop(0)

    return merged


# ─── The three strategies ────────────────────────────────────────────────────


def _split_short_post(doc: Document) -> list[str]:
    """
    campus_life. One post, one chunk.

    The useful information in this corpus sits in a single sentence, and the
    documents are 178-549 characters — already about the size a chunk wants to
    be. Cutting them can only separate a claim from the condition attached to
    it ("no exams" from "two essays and a final project"). So the answer to
    the brief's question, "whether one post should stay one chunk", is yes.

    The paragraph path below only runs if a post is somehow over the bound,
    which no campus_life document is.
    """
    if len(doc.text) <= config.MAX_CHUNK_CHARS:
        return [doc.text]
    return _merge_short(_pack(_paragraphs(doc.text, config.MAX_CHUNK_CHARS),
                              config.MAX_CHUNK_CHARS))


def _split_thread(doc: Document) -> list[str]:
    """
    advice_threads. Group replies, keep the question attached, overlap by one.

    Three decisions here, each one costing something:

      - Cut on reply markers, not character counts. A reply is one person's
        complete opinion, so the boundary is already in the text.

      - Put the "THREAD: ..." question at the top of every chunk. Without it a
        retrieved reply reads "Yeah. Cuts an 18 minute walk to about 6." and
        is useless on its own. This duplicates the question across chunks from
        the same thread, which is the cost.

      - Group replies up to THREAD_CHUNK_CHARS and overlap neighbouring chunks
        by THREAD_REPLY_OVERLAP replies. The corpus README warns that "a reply
        boundary and a useful boundary are not the same thing" — answers here
        are spread across replies that argue with each other, so one reply per
        chunk would split a disagreement in half.
    """
    text = doc.text
    markers = list(REPLY_MARKER.finditer(text))
    if not markers:
        return _split_short_post(doc)

    title = text[: markers[0].start()].strip()
    bounds = [m.start() for m in markers] + [len(text)]
    replies = [text[a:b].strip() for a, b in zip(bounds, bounds[1:])]
    replies = [r for r in replies if r]

    budget = config.THREAD_CHUNK_CHARS
    overlap = config.THREAD_REPLY_OVERLAP

    groups: list[list[str]] = []
    i = 0
    while i < len(replies):
        group = [replies[i]]
        j = i + 1
        while j < len(replies) and len("\n\n".join(group + [replies[j]])) <= budget:
            group.append(replies[j])
            j += 1
        groups.append(group)
        if j >= len(replies):
            break
        i = max(j - overlap, i + 1)   # max() keeps this moving forward

    pieces = ["\n\n".join(group) for group in groups]
    if title:
        pieces = [f"{title}\n\n{piece}" for piece in pieces]
    return _merge_short(pieces)


def _split_sections(doc: Document) -> list[str]:
    """
    city_guides. Split on headings, and say which guide each chunk is from.

    These documents are 1,436-2,510 characters, divided into labelled sections
    ("## Getting there", "## Where to eat"). A fixed 800-character window cuts
    straight through those headings; the heading is the single best clue to
    what the paragraph under it is about, so losing it is expensive.

    Small sections are packed together up to MAX_CHUNK_CHARS, and a section
    bigger than the bound is split at paragraph breaks with its heading
    repeated on each piece. The document's own "# Title" is then prepended to
    every chunk, so a chunk about parking still names the town it belongs to.
    That last step can push a chunk over the bound by the length of the title,
    which is a deliberate trade: attribution matters more than an exact cap.
    """
    text = doc.text
    headings = list(MARKDOWN_HEADING.finditer(text))
    if not headings:
        return _merge_short(_pack(_paragraphs(text, config.MAX_CHUNK_CHARS),
                                  config.MAX_CHUNK_CHARS))

    doc_title = ""
    if headings[0].start() == 0:
        first_line = text.split("\n", 1)[0].strip()
        if first_line.startswith("# "):
            doc_title = first_line

    bounds = [m.start() for m in headings] + [len(text)]
    sections = [text[: bounds[0]].strip()]                      # any preamble
    sections += [text[a:b].strip() for a, b in zip(bounds, bounds[1:])]
    sections = [s for s in sections if s]

    units: list[str] = []
    for section in sections:
        if len(section) <= config.MAX_CHUNK_CHARS:
            units.append(section)
            continue
        heading, _, body = section.partition("\n")
        heading = heading.strip()
        room = config.MAX_CHUNK_CHARS - len(heading) - 2
        for part in _pack(_paragraphs(body, room), room):
            units.append(f"{heading}\n\n{part}")

    pieces = _pack(units, config.MAX_CHUNK_CHARS)
    if doc_title:
        pieces = [
            piece if piece.startswith(doc_title) else f"{doc_title}\n\n{piece}"
            for piece in pieces
        ]
    return _merge_short(pieces)


# Corpus name wins when we recognise it; otherwise the shape of the document
# decides. See the note at the top of this file.
STRATEGIES = {
    "campus_life": _split_short_post,
    "advice_threads": _split_thread,
    "city_guides": _split_sections,
}


def strategy_for(doc: Document, corpus: str | None = None):
    """Which of the three strategies handles this document."""
    named = STRATEGIES.get(corpus or config.CORPUS)
    if named is not None:
        return named
    if REPLY_MARKER.search(doc.text):
        return _split_thread
    if MARKDOWN_HEADING.search(doc.text):
        return _split_sections
    return _split_short_post


def split_documents(
    documents: list[Document],
    corpus: str | None = None,
) -> list[Chunk]:
    """
    Split documents into chunks. ⚠️ REPLACE THE BODY OF THIS IN MILESTONE 3.

    [Milestone 3: done. The body now dispatches to one of the three strategies
    above instead of calling fallback_split. The brief's original wording is
    kept below.]

    Right now it just calls the fallback. That is the plain, generic behaviour
    the brief is talking about.

    When you write your own strategy, set `produced_by` to
    "chunker.py::split_documents" so your README's Sample Chunks section names
    the right function. `app.py chunks` prints that string for you.

    Things worth thinking about before you write any code:
      - Are your documents short posts or long guides?
      - Is the useful information in one sentence, or spread over a paragraph?
      - Would splitting on paragraph breaks keep more thoughts intact than
        splitting on a character count?

    `produced_by` names the strategy as well as this function, so a README's
    Sample Chunks section can say which of the three made each chunk.
    """
    chunks: list[Chunk] = []
    for doc in documents:
        strategy = strategy_for(doc, corpus)
        for index, text in enumerate(strategy(doc)):
            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=index,
                    produced_by=f"chunker.py::split_documents/{strategy.__name__}",
                )
            )
    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    # A corpus can mix strategies when the choice falls through to shape
    # detection, so name every producer rather than just the first chunk's.
    producers = sorted({c.produced_by for c in chunks})
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {', '.join(producers)}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
