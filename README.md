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

**1. I asked AI to create questions for me** 

What AI changed: the two questions, rather than the corpus. I kept what each one
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

`python run_eval.py --label before`, written to
`results/run_2026-09-29_2221_before.md`. Corpus `campus_life`, `TOP_K = 10`,
cutoff 0.63, three runs per question, caching off.

**One change to the test set since unit 1.** Question 4 is no longer the
Fenwick Court / library / shuttle question from the Sample Answer section above.
Before this run I replaced it with *"How long does a student's cloud drive last
after they graduate?"* (answer: six months, in `admin_wifi_and_accounts.txt`).
The old question is still in `questions.py`, commented out. This matters later:
the Fenwick question was the hardest retrieval question I had, with
`study_library_hours.txt` down at rank 6, and its replacement is one of the
easiest. See Diagnoses.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Chunks stay about one thing (revised: ≥90% in 15–150 tokens, none > 254; ≥4 of 5 samples single-topic) | see left | 88/88 in band, 0 > 254; 4 of 5 single-topic | same | same | MET |
| 5. The source named is the right sibling | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |

Not one of my five criteria, but in the same run: `scorer.py::judge`, which
checks each answer for the `expects` phrase in `questions.py`, scored **4 of 5
in all three runs**. STAT 150 failed every time.

Real output from run 1, as `run_eval.py` wrote it:

**Criterion 1**, produced by `store.py::search` (called from `run_eval.py::run_once`):

```
What is the latest date to add a course?
  expected: admin_add_drop_deadline.txt
  retrieved: admin_add_drop_deadline.txt, admin_declaring_a_major.txt, admin_graduation_requirements.txt, admin_pass_fail_option.txt, admin_study_abroad.txt, advising_registration.txt, course_biol_160_workload.txt, course_cs_340.txt, course_cs_340_exams.txt, course_econ_101_workload.txt
  -> contains the answer

How much is a wash in Old Brewhouse, and can I pay with a card?
  expected: housing_old_brewhouse.txt, housing_old_brewhouse_laundry.txt
  retrieved: housing_aldridge_hall_laundry.txt, housing_calder_annexe.txt, housing_calder_annexe_laundry.txt, housing_fenwick_court.txt, housing_fenwick_court_laundry.txt, housing_innisfree_hall.txt, housing_innisfree_hall_laundry.txt, housing_morrow_house_laundry.txt, housing_old_brewhouse.txt, housing_old_brewhouse_laundry.txt
  -> contains the answer

In STAT 150, if a student scores 90, 85, and 40 on the three midterms, what is their final grade in the course based on percentage?
  expected: course_stat_150.txt, course_stat_150_exams.txt
  retrieved: admin_pass_fail_option.txt, course_cs_210.txt, course_cs_210_exams.txt, course_cs_340_exams.txt, course_econ_101_exams.txt, course_hist_118.txt, course_math_220_exams.txt, course_phys_130_exams.txt, course_stat_150.txt, course_stat_150_exams.txt
  -> contains the answer
```

(The Ridgeway and cloud-drive questions look the same: `-> contains the answer`.)

**Criterion 2**, produced by `generate.py::answer_from_chunks` (caching off):

```
You can add a course through the end of the second week (admin_add_drop_deadline.txt).
```
```
Based on the documents, wait times at The Ridgeway Café are 10 to 15 minutes at 12:30. Because seating is also very tight (about 40 seats), you likely will not have enough time to eat before a 12:45 class, as the documents advise going before 11:45 if you are trying to eat between classes.

Sources: `dining_the_ridgeway_cafe.txt` and `dining_the_ridgeway_cafe_followup.txt`
```
```
A wash in Old Brewhouse costs $1.50, and the machines are coin only, so you cannot pay with a card.

Source: `housing_old_brewhouse.txt` (and `housing_old_brewhouse_laundry.txt`)
```
```
A student's cloud drive stays active for six months after they graduate, and at that point, it is purged without a second warning. This comes from *admin_wifi_and_accounts.txt*.
```
```
Based on the provided documents, there is no mention of how the percentage for the final grade is calculated using the midterm scores. The documents only state that there are three equally weighted midterms and the lowest midterm is dropped (from `course_stat_150_exams.txt` and `course_stat_150.txt`). Therefore, I do not have enough information to calculate the final grade percentage.
```

**Criterion 3**, produced by `run_eval.py::check_out_of_scope` → `gate.py::check`, cutoff 0.63:

```
refused  (best distance 0.825)  What is the capital of Mongolia?
refused  (best distance 0.934)  How do I change the oil in a diesel engine?
refused  (best distance 0.886)  Who won the 1994 World Cup?
refused  (best distance 0.844)  What is the recommended dosage of ibuprofen for a headache?
refused  (best distance 0.896)  How do I write a for loop in Rust?
-> gate refused 5 of 5
Answer returned when refused: I don't have enough information about that.
```

**Criterion 4**: chunks read back from the index built by
`chunker.py::split_documents/_split_short_post`, counted with the embedding
model's tokenizer by `run_eval.py::measure_chunks`, 5 samples drawn with seed 0:

```
88 chunks · tokens: min 38, max 127, median 70.5 · in 15–150: 88 of 88 · over 254: 0

===== admin_graduation_requirements.txt#0   53 tokens  282 chars
===== course_hist_118_exams.txt#0           41 tokens  178 chars
===== dining_north_kitchen_followup.txt#0   69 tokens  317 chars
===== dining_the_atrium_followup.txt#0      79 tokens  341 chars
===== housing_fenwick_court.txt#0          102 tokens  425 chars
Fenwick Court — what it's actually like

Just finished a year in this building. Built 2015. Rooms are suites of four with a shared kitchenette.

The good: in-suite bathrooms, and the kitchenette means you can skip a meal plan tier.

The bad: the furthest housing from central campus, about 18 minutes on foot.

Laundry costs $2.00 wash, $1.75 dry, app-based. On noise: thin walls between suites; the kitchenettes carry sound.
```

(Header lines shortened; the full text of all five samples is in the results file.)

**Criterion 5**: citations from `generate.py::answer_from_chunks`, checked
against `sources` in `questions.py`:

```
How much is a wash in Old Brewhouse, and can I pay with a card?
  expected: housing_old_brewhouse.txt, housing_old_brewhouse_laundry.txt
  cited:    housing_old_brewhouse.txt, housing_old_brewhouse_laundry.txt
  -> right source

In STAT 150, if a student scores 90, 85, and 40 on the three midterms, what is their final grade in the course based on percentage?
  expected: course_stat_150.txt, course_stat_150_exams.txt
  cited:    course_stat_150.txt, course_stat_150_exams.txt
  -> right source
```

(The other three are `-> right source` too.)

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer | MET | 5 of 5 in all three runs against a target of 4. Not close: every answer file ranks 1st for its question (checked with `store.search`), so even `TOP_K = 1` would pass. |
| 2 | Every answer names a source | MET | All 15 answers name a file. I read them rather than trusting the regex, because the formats vary: backticks, italics, a bare filename, "(Source: ...)". |
| 3 | Gate stops out-of-corpus questions | MET | 5 of 5 against 4. Deterministic, and the nearest out-of-scope question (0.825) is 0.195 above the cutoff. |
| 4 | Chunks stay about one thing | MET, and close | The size half isn't close: 88 of 88 in band, max 127 tokens against a 254 ceiling. The single-topic half is exactly at target. Four samples are one thing each: graduation requirements, HIST 118 assessment, one dining hall's wait, another's wait. `housing_fenwick_court.txt` is not. It runs rooms, bathrooms, distance, laundry *and* noise together, which is the "two topics in one chunk" case the criterion names. So it's 4 of 5, and one more overview post in the sample would have been a miss. |
| 5 | The source named is the right sibling | MET | 5 of 5 in all three runs against 4, including Old Brewhouse, where six sibling laundry posts were retrieved alongside it. |

## Diagnoses

**No criterion missed.** Every target held in all three runs. That isn't the
same as the system working, and the run log says why. One question failed in
every run, and none of my five criteria caught it.

**The miss the criteria didn't see: STAT 150.** Stage: **generation**.
Retrieval was fine: `course_stat_150_exams.txt` ranks 1st at 0.4055, with
`course_stat_150.txt` 2nd. Both say "three equally weighted midterms, no final
… the lowest midterm is dropped", which is everything needed for
(90 + 85) / 2 = 87.5%. In all three runs the model restated that rule correctly
and then refused anyway. The mechanism is in `generate.py::GROUNDING_INSTRUCTION`:
*"Use only the information in the documents"* and *"If the documents don't
cover the question, say you don't have enough information."* The number 87.5
appears in no document. The model treats a number it would have to derive as
information it doesn't have, so the anti-hallucination rule also blocks
arithmetic on facts it does have.

**The pattern:** it's the only one of my five questions whose answer has to be
computed. The other four answers are phrases copied straight out of one
document ("the end of the second week", "six months", "$1.50 … coin only").
The strict grounding prompt is good at copying and refuses to derive.

**Why no criterion caught it:** criteria 1, 2 and 5 check the retrieval
and the citation, not the answer. The STAT 150 refusal retrieved the right
chunk, named a source, and named the right sibling, so it passed all three while
being wrong. I flagged this at the end of unit 1 and didn't change the criteria,
so the gap is still there.

**My targets were set low.** Criterion 1 could not realistically fail. With
`TOP_K = 10` out of 88 chunks, and every answer file at rank 1, "the retrieved
chunks include one that contains the answer" is true with nine slots to spare.
Swapping out the Fenwick question made it easier still, since that was the one
question where an answer file sat outside the top 5. Criterion 3 was also soft:
I measured a 0.39-wide gap in unit 1 and still left the target at 4 of 5. If I
tightened one, it would be criterion 1: *for 5 of 5 questions the answer file
is in the top 3, and for at least 4 of 5 the answer contains the `expects`
phrase (`scorer.py`) in every run.* That version would have come out a MISS
here.

## The Improvement

**What I changed:** one rule added to `GROUNDING_INSTRUCTION` in `generate.py`:

```
- If the documents state a rule (how a grade is weighted, what is dropped, what a price is) and the question supplies the numbers, apply the rule to those numbers and show the working in one line. That counts as using the documents, not guessing.
```

Nothing else moved: same index, same chunker, `TOP_K = 10`, cutoff 0.63.

**Why I picked it:** the STAT 150 diagnosis puts the failure in the generation
prompt, not in retrieval. The right chunk was already at rank 1, so the fix has
to change what the model is allowed to do with that chunk, not which chunks it
gets.

### Run Log — After

`python run_eval.py --label after`, written to
`results/run_2026-09-29_2227_after.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Chunks stay about one thing (revised) | see above | 88/88 in band, 0 > 254; 4 of 5 single-topic | same | same | MET |
| 5. The source named is the right sibling | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |

`scorer.py::judge`: **5, 4, 5** of 5 (before: 4, 4, 4). The STAT 150 answers:

```
run 1: Dropping the lowest midterm (40) leaves 90 and 85, resulting in an average percentage of (90 + 85) / 2 = 87.5%.
       Source: course_stat_150_exams.txt (and course_stat_150.txt)

run 2: I do not have enough information to calculate the final grade percentage in STAT 150, as the documents only state that there are three equally weighted midterms with the lowest one dropped, but do not provide the weighting percentages or how other assignments (if any) factor into the final grade.
       Sources: course_stat_150_exams.txt and course_stat_150.txt

run 3: To find the grade, the lowest midterm (40) is dropped, leaving the remaining scores (90 and 85) to be equally weighted.
       Final grade percentage = $(90 + 85) / 2 = 87.5\%$
       Sources: course_stat_150.txt and course_stat_150_exams.txt
```

**Did it help?** Yes, but only partly, and not in a way my criteria can show.
STAT 150 went from 0 of 3 correct to 2 of 3, and both correct runs show the
working the new rule asked for. The other four questions still pass 3 of 3, so
the looser prompt didn't break the copy-a-phrase answers. The gate still
refuses 5 of 5, which I expected, because the gate runs before the model and a
prompt change can't reach it. The criteria table is identical before and after
because every criterion was already MET. The improvement only shows in the
scorer line. That tells me more about my criteria than about the fix.

Three runs is also not many. 0 of 3 to 2 of 3 is a real change in *kind*,
since the model had never computed the grade before and now usually does, but
I wouldn't claim a rate from it.

## What's Still Broken

**No criterion is missed after the fix.** What is still broken is STAT 150
refusing 1 time in 3, and run 2 gives a new reason. It no longer says it isn't
allowed to calculate. It says the documents don't say whether *other
assignments* count toward the grade. That's a fair reading of the document:
"three equally weighted midterms, no final" never says the midterms are 100% of
the grade. The obvious next fix is a rule like "treat the assessments a post
lists as the complete list." I stopped short of it on purpose. It tells the
model to assume what a document leaves out, and that would apply to every
question in the corpus, not just this one. The failure is now partly the
document being underspecified, and I'd rather have a system that sometimes
flags a real gap than one that's been told to fill gaps.

Also untested this unit: the Fenwick Court / shuttle question, which needs two
documents at once. It's the question most likely to break criterion 1, and it
isn't in the run log.

## What I'd Do Differently

I'd write criterion 1 to check the answer, not the retrieval. All five of my
criteria check the pipeline: was the chunk retrieved, was a file named, did
the gate fire, are chunks a sane size, is the filename the right sibling. None
of them asks whether the answer is correct. The one real failure in this unit
was exactly there, and it passed three criteria while being wrong. I'd replace
criterion 1 with the tightened version in Diagnoses, top 3 plus the `expects`
phrase in every run, so a correct-looking citation on a refusal can't count as
a pass.

I'd also keep the hard questions in the test set. Replacing the Fenwick
question made my numbers better and my test weaker. For criterion 3, I'd add
near-miss out-of-scope questions, about campus things the corpus doesn't
cover (the pool, the gym), instead of five questions from other worlds. Those
are the ones that could actually land near the cutoff.
