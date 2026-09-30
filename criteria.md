# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.


> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:** My corpus has near-identical families — 7 residence halls
each with a `_laundry` and `_noise` file, 9 courses each with `_exams` and
`_workload`. Siblings differ mainly in the proper noun, which barely moves an
embedding, and `TOP_K` is 5 while there are 7 laundry files. I expect one
question to lose to a sibling, so 4 of 5 rather than 5 of 5.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:** So we can check if the source is real. All five because
citing is bookkeeping here, not judgement: no document in this corpus is long
enough to be split, so every chunk is one whole document with one filename in
its metadata. A miss would be a bug, not a hard question.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** Four of my five out-of-scope questions (Mongolia, diesel
engines, the 1994 World Cup, Rust) share no vocabulary with a campus corpus, so
they should sit far above the cutoff. The fifth is the ibuprofen one, and
`health_center.txt` is in my corpus talking about walk-in hours and urgent
visits — that's the one I expect to land near enough to slip through. So 4 of 5,
with the medical question as the one I've budgeted to lose.

**Measured in Milestone 4:** the gap was clean, and wider than I expected. My
five questions land at 0.246–0.432 and the five out-of-scope ones at 0.825–0.934,
with nothing in between, so `THRESHOLD` is 0.63 — the midpoint of a 0.39-wide gap.

The prediction above was wrong about which question was at risk, and wrong about
there being one at all. The ibuprofen question doesn't land near `health_center.txt`;
its nearest chunk is `money_textbooks.txt` at 0.844, because "recommended dosage"
shares no vocabulary with walk-in hours either. Sharing a *topic* with a document
is not the same as sharing words with it, and the embedding measures the second.
At 0.63 all five are refused, so this target should come out 5 of 5 rather than
the 4 of 5 I budgeted for.

---

## 4. Chunks stay small enough to be about one thing

Every chunk is between 30 and 900 characters, and of 5 chunks I sample, at
least 4 cover a single topic — one hall's laundry, one course's exams — rather
than running two topics together.

**Why this target:** The ceiling is the part I care about. A chunk's embedding
is an average of everything in it, so a long chunk spanning three topics sits
between all three and matches none of them well, and even when it is retrieved
the model has to hunt for the answer among sentences that have nothing to do
with the question. 900 is where that stops, and it matters most where documents
are long: `city_guides` runs 1,436–2,510 characters and has to be split at
headings.

I put the floor at 30 and not higher because short isn't the same as broken —
"Machines take $1.75 wash, $1.50 dry, card only" is a complete answer and
should be allowed to stand as one. 30 is only there to catch the actual defect,
the 2-character chunk the old stride produced, which was a heading with nothing
under it.


> **Revised in unit 2:** At least 90% of chunks are between 15 and 150 tokens,
> with no chunk exceeding 254 tokens. Of 5 chunks I sample, at least 4 still
> cover a single topic.
>
> **Why revised:** The original measured the wrong unit. The embedding model
> doesn't see characters, it sees WordPiece tokens, and Chroma's
> `all-MiniLM-L6-v2` cuts every input off at 256 of them — 254 once `[CLS]` and
> `[SEP]` are counted. Anything past that is silently left out of the embedding,
> so 254 tokens is the real ceiling and 900 characters was only a proxy for it.
> In `campus_life` every document is one chunk, running 38–127 tokens with a
> median of 70, so 150 is where a chunk would start to look like two documents'
> worth of text rather than one hall's laundry or one course's exams. The floor
> is 15 because "Machines take $1.75 wash, $1.50 dry, card only" is 16 tokens
> and should still count as a complete chunk. 90% rather than 100% because the
> band is about staying focused, and only the 254 ceiling is a hard limit.
---

## 5. The source named is the right sibling

For at least 4 of my 5 test questions, the document named as the source
actually contains the fact in the answer — and when the question names a
specific hall, dining location, or course, the source is that one and not a
sibling file.

**Why this target:** Criterion 2 only checks that *a* name appears, and in this
corpus the most likely wrong answer is a real filename from the right family
but the wrong hall, which looks perfectly plausible in a citation. 4 of 5
because it inherits the near-duplicate problem from criterion 1 — if retrieval
hands me the wrong sibling, the attribution is wrong with it.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
