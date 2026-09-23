# The Unofficial Guide

Joy Kuo — corpus: `campus_life`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This answers questions about campus from the `campus_life` corpus: 88 short
posts written the way students actually explain things to each other, covering
registrar deadlines, seven residence halls, seven dining locations, nine
courses, and a scattering of one-offs like the shuttle and the health centre.
Ask it something a second-year would know — when you can still add a course,
what a wash costs in Old Brewhouse, how STAT 150 counts its midterms — and it
retrieves the posts that mention it, answers from those posts only, and names
the file it got the answer from. Ask it something the corpus has never heard of
and it refuses rather than guessing, because a plausible invented answer about
a deadline is worse than no answer.

## Chunking Strategy

**Chunk size:** 900 characters maximum (`MAX_CHUNK_CHARS`), 30 minimum
(`MIN_CHUNK_CHARS`). In practice `campus_life` never reaches the ceiling — one
post comes out as one chunk, 178 to 549 characters, 88 documents to 88 chunks.

**Overlap:** none, for this corpus. (`CHUNK_SIZE = 800` / `CHUNK_OVERLAP = 120`
are still in `config.py`, but they now belong only to
`chunker.py::fallback_split`, which nothing in this corpus calls.)

**I changed my mind, and measuring is what changed it.** I started with the
starter's fixed 800/120 window and went looking for what it did to my
documents. On `campus_life` it did nothing at all: the longest document is 549
characters, so the 800 never fired and every "chunk" was already a whole post.
The number was decoration.

What convinced me it was actively wrong was running the same chunker over
`advice_threads`, where it produced a **2-character chunk** — the text `"t."`.
That wasn't a splitting decision, it was arithmetic: the window advances
800 − 120 = 680 characters, and `thread_meal_plan_tier.txt` is 682 characters
long, so it emitted the whole document and then characters 680–682 as a second
chunk. A fixed stride cuts wherever the counter lands, whether or not there is
anything there.

So `chunker.py::split_documents` now picks a strategy per corpus, because the
three corpora have genuinely different shapes and one pair of numbers can't fit
all of them:

| corpus | doc chars (min/med/max) | strategy |
|---|---|---|
| `campus_life` | 178 / 305 / 549 | `_split_short_post` |
| `advice_threads` | 317 / 531 / 793 | `_split_thread` |
| `city_guides` | 1,436 / 2,116 / 2,510 | `_split_sections` |

For my corpus the answer to "should one post stay one chunk?" is yes. The
useful fact in these documents sits in a single sentence, and the sentence
usually carries a condition attached to it — "no exams" is followed by "two
essays and a final project." Cutting a 300-character post in half can only
separate a claim from its condition, and the retrieved half that survives reads
as true when it isn't. 900 is set as a ceiling rather than a target so the same
code still splits `city_guides` at its headings, and 30 is a floor that folds a
short tail back into the chunk before it — that's the guard the fixed-size
version was missing, and it's what makes the `"t."` chunk impossible now.

## Sample Chunks

**Chunk 1** — source: `course_biol_160.txt#0` — produced by: `chunker.py::split_documents/_split_short_post`

On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```
```

**Chunk 2** — source: `course_biol_160.txt#0` — produced by: `chunker.py::split_documents/_split_short_post`
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

Expect 9 to 11 hours a week, the heaviest first-year course by reputation.

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.

```
```

**Chunk 3** — source: `course_hist_118_workload.txt#0` — produced by: `chunker.py::split_documents/_split_short_post`
Workload for HIST 118 Modern World History

People keep asking so: a lot of reading, about 120 pages a week, but no problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.

```
```

**Chunk 4** — source: `dining_pellew_dining_hall_followup.txt#0 ` — produced by: `chunker.py::split_documents/_split_short_post`
Re: Pellew Dining Hall

Adding to what people have said about Pellew Dining Hall. The wait figure of 12 to 18 minutes at peak matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: the furthest hall from anywhere, next to the athletics centre. Nobody tells you this at orientation.
```
```

**Chunk 5** — source: `housing_innisfree_hall.txt#0  ` — produced by: `chunker.py::split_documents/_split_short_post`

Innisfree Hall — what it's actually like

Transferred in last year, so take this with a grain of salt. Built 1991, renovated 2022. Rooms are doubles arranged as pairs sharing one bathroom between two rooms.

The good: the shared-bathroom-between-two-rooms arrangement is the best compromise on campus.

The bad: no air conditioning, which matters for the first three weeks of September.

Laundry costs $1.75 wash, $1.75 dry, app-based. On noise: moderate; the building is L-shaped and the short wing is much quieter.

For each one, ask: could someone answer a question using only this,
without reading what came before or after?
```
```


## Sample Answer

All five of my test questions, run through `python app.py ask "..."` with
caching off so each one is a real call. Pasted exactly as the command printed
them, including the distance line and the sources.

**Question 1:** What is the latest date to add a course?

**Answer:**

```
  (best distance 0.428, cutoff 0.63)

You can add a course through the end of the second week (admin_add_drop_deadline.txt).

Sources retrieved: admin_add_drop_deadline.txt, admin_declaring_a_major.txt, admin_graduation_requirements.txt, admin_pass_fail_option.txt, admin_study_abroad.txt, advising_registration.txt, course_biol_160_workload.txt, course_cs_340.txt, course_cs_340_exams.txt, course_econ_101_workload.txt

1 model calls this session, 925 tokens (902 in, 23 out)
```

**Question 2:** If I get to The Ridgeway Café at 12:30 and my class starts at
12:45, is that enough time to eat there?

**Answer:**

```
  (best distance 0.246, cutoff 0.63)

Based on the documents, wait times at The Ridgeway Café are 10 to 15 minutes at 12:30. Given that seating is also very tight (only about 40 seats for a building of 900), waiting 10 to 15 minutes would leave you virtually no time to actually sit and eat before your class starts at 12:45.

Source: `dining_the_ridgeway_cafe.txt` and `dining_the_ridgeway_cafe_followup.txt`

Sources retrieved: dining_halden_hall.txt, dining_halden_hall_followup.txt, dining_kestrel_commons.txt, dining_kestrel_commons_followup.txt, dining_north_kitchen.txt, dining_north_kitchen_followup.txt, dining_pellew_dining_hall_followup.txt, dining_the_ridgeway_cafe.txt, dining_the_ridgeway_cafe_followup.txt, dining_verrill_street_grill_followup.txt

1 model calls this session, 1408 tokens (1289 in, 119 out)
```

This is the closest match of the five (0.246) and the one that needed the least
help: the question and the document share the exact figures, "12:30" and "10 to
15 minutes."

**Question 3:** How much is a wash in Old Brewhouse, and can I pay with a card?

**Answer:**

```
  (best distance 0.315, cutoff 0.63)

A wash in Old Brewhouse costs $1.50, and you cannot pay with a card because the machines are coin only.

Source: `housing_old_brewhouse_laundry.txt` (and `housing_old_brewhouse.txt`)

Sources retrieved: housing_aldridge_hall_laundry.txt, housing_calder_annexe.txt, housing_calder_annexe_laundry.txt, housing_fenwick_court.txt, housing_fenwick_court_laundry.txt, housing_innisfree_hall.txt, housing_innisfree_hall_laundry.txt, housing_morrow_house_laundry.txt, housing_old_brewhouse.txt, housing_old_brewhouse_laundry.txt
```

This is the question I wrote to break criterion 5, and it held. Six sibling
laundry posts came back alongside the right one, including Morrow House at
`$1.50 wash, coin or card` — one word away from the true answer and wrong. The
system named the right file anyway.

**Question 4:** I live in Fenwick Court and the walls are thin. The posts point
at the library for quiet — if I stay there until it closes during term, can I
get the shuttle home?

**Answer:**

```
  (best distance 0.432, cutoff 0.63)

No, you cannot get the shuttle home after the library closes. The shuttle runs from 7am to 11pm on weekdays, but the library is open until 2am during term.

Source documents: `transit_shuttle.txt`, `study_library_hours.txt` (and multiple noise documents).

Sources retrieved: housing_aldridge_hall_noise.txt, housing_fenwick_court.txt, housing_fenwick_court_noise.txt, housing_innisfree_hall_noise.txt, housing_morrow_house_noise.txt, housing_old_brewhouse_noise.txt, housing_tamsin_court_noise.txt, study_library_hours.txt, transit_shuttle.txt, transit_walking.txt
```

Two documents, neither of which contains the answer on its own — the library
hours are in one file and the shuttle timetable in another, and the "no" only
exists when you hold both. This is the question that justifies `TOP_K = 10`.
`app.py retrieve` puts `transit_shuttle.txt` at rank 3 (0.5505) but
`study_library_hours.txt` only at rank 6 (0.5910), behind three near-identical
"Noise levels in ..." posts for halls I don't live in. At the starter's
`TOP_K = 5` the library hours never reach the model and the answer can't be
assembled at all.

**Question 5:** In STAT 150, if a student scores 90, 85, and 40 on the three
midterms, what is their final grade in the course based on percentage?

**Answer:**

```
  (best distance 0.406, cutoff 0.63)

Based on the provided documents, there is no mention of how the final grade percentage is calculated from the midterm scores (other than that there are three equally weighted midterms and the lowest one is dropped). Therefore, I do not have enough information to calculate the final grade percentage.

Sources: `course_stat_150.txt` and `course_stat_150_exams.txt`.

Sources retrieved: admin_pass_fail_option.txt, course_cs_210.txt, course_cs_210_exams.txt, course_cs_340_exams.txt, course_econ_101_exams.txt, course_hist_118.txt, course_math_220_exams.txt, course_phys_130_exams.txt, course_stat_150.txt, course_stat_150_exams.txt
```

**This one is a miss, and it's the interesting one.** Retrieval did its job:
`course_stat_150_exams.txt` came back and it says "three equally weighted
midterms, no final. No curve, but the lowest midterm is dropped" — everything
needed to get to 87.5%. The failure is at the generation stage, not the
retrieval stage. The model has the rule and the three scores and still won't
apply them, because grounding it strictly in the documents also stops it doing
arithmetic the documents don't spell out. Criterion 1 passes here (the
retrieved chunk does contain the answer) while a reader would say the system
got it wrong, which is a gap between my criterion and what I actually wanted,
and it's the first thing I'll look at in unit 2.

**My relevance cutoff:** `THRESHOLD = 0.63` in `config.py`.

I ran all ten questions through `python app.py retrieve` and wrote down the
best distance for each. The two groups don't overlap and they don't come close:
my five sit between 0.246 and 0.432, the five out-of-scope ones between 0.825
and 0.934. That's a 0.39-wide gap with nothing in it, and 0.63 is its midpoint.
I rounded to two decimal places because a third would suggest the boundary is
sharper than a ten-question measurement can show.

The gap being this clean was not what I predicted. In criteria.md I expected the
ibuprofen question to slip through, on the grounds that `health_center.txt` is
in my corpus talking about walk-in hours and urgent visits. It doesn't: its
nearest chunk is `money_textbooks.txt` at 0.844, and `health_center.txt` isn't
the closest thing to it at all. Sharing a topic with a document is not the same
as sharing vocabulary with it, and distance is measured on the second. So the
one question I'd budgeted to lose is refused along with the other four.

| Question | In corpus? | Best distance |
|---|---|---|
| What is the latest date to add a course? | yes | 0.4277 |
| If I get to The Ridgeway Café at 12:30 and my class starts at 12:45, is that enough time to eat there? | yes | 0.2462 |
| How much is a wash in Old Brewhouse, and can I pay with a card? | yes | 0.3154 |
| I live in Fenwick Court and the walls are thin … can I get the shuttle home? | yes | 0.4323 |
| In STAT 150, if a student scores 90, 85, and 40 on the three midterms, what is their final grade? | yes | 0.4055 |
| What is the capital of Mongolia? | no | 0.8246 |
| How do I change the oil in a diesel engine? | no | 0.9340 |
| Who won the 1994 World Cup? | no | 0.8859 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.8442 |
| How do I write a for loop in Rust? | no | 0.8960 |

At the starter's 0.9 — which is what I had while I was still guessing — four of
the five out-of-scope questions were let through to the model. At 0.63 all five
are refused and all five of mine pass.

## How I Used AI

I used Claude to write this README up from work that was already done — the
chunker, the criteria, the questions. Both moments below come out of that, and
both are cases where what came back was wrong in a way that took checking to
see.

**1. I asked it to fill in the README, and it refused to start.** What came back
first was not prose but a problem: two of my five test questions — how long
Marchwood's covered market has operated, and whether a wheelchair user could
visit either mill museum — are `city_guides` questions, and `CORPUS` is
`campus_life`. Those two documents are not in the index those questions would be
tested against, so two of my five could never have passed criterion 1 no matter
what the retrieval did. It also pointed out that `THRESHOLD` was sitting at 0.9,
which the TODO I'd left in `criteria.md` said out loud and I'd read past.

What I changed: the two questions, rather than the corpus. I kept what each one
was testing and rebuilt it out of `campus_life` — the Marchwood fact-lookup
became the Old Brewhouse laundry question, which is a better test anyway because
it lands in a family of seven near-identical sibling posts, and the two-document
mill comparison became the Fenwick Court / library / shuttle question, which
still needs two documents and still answers "no." Then I measured the ten
distances properly and set the cutoff to 0.63.

**2. It wrote two confident sentences about my own system that were false.** In
the Sample Chunks commentary it wrote that chunk 5 "at 549 characters is the
longest document in the corpus," and in the Sample Answer commentary that
`transit_shuttle.txt` "was tenth" in retrieval. Both read as though they came
from the output. Neither did. The Innisfree chunk is 516 characters and the
longest document is `housing_old_brewhouse.txt` at 549 — it had taken the corpus
maximum from the indexing summary and attached it to the wrong document. And the
shuttle file is rank 3 at 0.5505, not tenth; the `Sources retrieved:` line that
`app.py ask` prints is sorted alphabetically, not by distance, so there was no
rank in the output it was reading at all.

What I changed: both sentences, against `app.py retrieve` and a character count.
The rank correction turned out to be worth more than the fix — the real ranks
show `study_library_hours.txt` down at 6, behind three noise posts for halls I
don't live in, which is the actual argument for `TOP_K = 10` and is now in the
write-up in place of a made-up number. The rule I ended up with is that AI prose
about your own system is fluent exactly where it is guessing, so every number in
this README traces back to a command I can re-run.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
