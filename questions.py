"""
Your test questions.

Milestone 2 asks you to write five questions your system should be able to
answer from your corpus, specific enough to have a right answer.

  ✗ "What are good dining halls?"          — no right answer
  ✓ "What do students say about wait times at Commons during lunch?"

Fill in `QUESTIONS` below. `expects` is a word or short phrase you'd expect a
correct answer to contain — you'll use it in unit 2 when you build a scorer,
and having written it now means you decided what "correct" meant before you saw
any results.

`sources` lists the files that actually contain the answer. `run_eval.py`
uses it for criterion 1 (was one of them retrieved?) and criterion 5 (did the
answer cite one of them and not a sibling?).

`OUT_OF_SCOPE` holds five questions your documents clearly don't cover. You
need these in Milestone 4 to find where your relevance cutoff belongs, and
again in unit 2, where `run_eval.py` runs them through the gate and writes what
happened into your run log — that's the evidence for criterion 3.

Swap them for your own if you like. Keep five of them either way: criterion 3
names a target of "4 of 5", and four of three is not a thing.
"""

QUESTIONS = [
    # {"question": "...", "expects": "...", "sources": ["file_that_has_the_answer.txt"]},
    {"question": "What is the latest date to add a course?", "expects": "the end of the second week", "sources": ["admin_add_drop_deadline.txt"]},
    {"question": "If I get to The Ridgeway Café at 12:30 and my class starts at 12:45, is that enough time to eat there?", "expects": "10 to 15 minutes", "sources": ["dining_the_ridgeway_cafe.txt", "dining_the_ridgeway_cafe_followup.txt"]},
    {"question": "How much is a wash in Old Brewhouse, and can I pay with a card?", "expects": ["$1.50", "coin only"], "sources": ["housing_old_brewhouse.txt", "housing_old_brewhouse_laundry.txt"]},
    # {"question": "I live in Fenwick Court and the walls are thin. The posts point at the library for quiet — if I stay there until it closes during term, can I get the shuttle home?", "expects": "No. The library is open until 2am during term, but the shuttle only runs until 11pm, and the stop outside Fenwick Court is the one that gets skipped when the driver is behind."},
    {"question": "How long does a student's cloud drive last after they graduate?", "expects": "six months", "sources": ["admin_wifi_and_accounts.txt"]},
    {"question": "In STAT 150, if a student scores 90, 85, and 40 on the three midterms, what is their final grade in the course based on percentage?", "expects": "87.5", "sources": ["course_stat_150.txt", "course_stat_150_exams.txt"]},

]

# Questions from a different world entirely. Your gate should refuse all five.
#
# There are five of these because criterion 3 in criteria.md names a target of
# "at least 4 of 5" — you need five things to try before you can report 4 of 5.
# `run_eval.py` runs these through retrieval and the gate on every eval and
# records what happened, so criterion 3 has evidence in the run log alongside
# the others. They cost no model calls: a refusal never reaches the model.
OUT_OF_SCOPE = [
    "What is the capital of Mongolia?",
    "How do I change the oil in a diesel engine?",
    "Who won the 1994 World Cup?",
    "What is the recommended dosage of ibuprofen for a headache?",
    "How do I write a for loop in Rust?",
]


def answered() -> list[dict]:
    """The questions you've actually filled in."""
    return [q for q in QUESTIONS if q.get("question", "").strip()]
