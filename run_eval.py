#!/usr/bin/env python3
"""
Run your test questions repeatedly and write the results down.

    python run_eval.py                 three runs, the default
    python run_eval.py --runs 5        more runs
    python run_eval.py --label after   name this run, e.g. before/after a fix

This does the mechanical half of unit 2 for you: it asks each of your questions
the same way three separate times, with caching turned off so you get three
real answers, and writes everything into results/ as a table with one row per
question.

It also puts every question in `OUT_OF_SCOPE` through retrieval and the gate
and records what happened, so criterion 3 — the one about out-of-corpus
questions — has evidence in the same file as the other four. That part costs
nothing: a question the gate refuses never reaches the model.

That table is the raw material for your run log, not the run log itself. The
submission template wants one row per *criterion* — aggregating your questions
up into your criteria is your work, not the script's.

[Unit 2: it now also writes that second table — one row per criterion, three
runs each — straight underneath the first, followed by the real output behind
each criterion. See `CRITERIA` and `score_criteria`. The Verdict column is a
suggestion against the targets in criteria.md; the call is still yours, and
criterion 4's single-topic half can only be judged by reading the samples.]

⚠️ What it does NOT do is decide whether an answer was right.

That judgment is yours, and you'll build it in class in unit 2 as `scorer.py`.
Until that file exists, the Run columns carry the raw answers and you read them
yourself. Once it exists — a file called `scorer.py`, with a function
`judge(question, expects, answer, results) -> bool` — this script finds it
automatically and the Run columns carry verdicts instead.

Deciding what counts as correct is the actual lesson. It would be easy to hand
you a scorer; you'd learn nothing from it.
"""

import argparse
import datetime as dt
import random
import re
import statistics
import sys
from pathlib import Path

import config
import questions as qs


# The five criteria from criteria.md, and the least each run has to reach.
# `need` takes the number of questions (or out-of-scope questions) and returns
# the count that meets the target — "4 of 5" is `n - 1`, "every" is `n`.
CRITERIA = [
    {"id": 1, "name": "Retrieved chunks contain the answer", "need": lambda n: n - 1},
    {"id": 2, "name": "Every answer names a source", "need": lambda n: n},
    {"id": 3, "name": "Gate stops out-of-corpus questions", "need": lambda n: n - 1},
    {"id": 4, "name": "Chunks stay small enough to be about one thing", "need": None},
    {"id": 5, "name": "The source named is the right sibling", "need": lambda n: n - 1},
]

# Criterion 4, as revised in unit 2.
TOKEN_FLOOR = 15
TOKEN_BAND_TOP = 150
TOKEN_CEILING = 254
BAND_SHARE = 0.90
CHUNK_SAMPLES = 5

# A filename as it appears in an answer's citation.
CITED_FILE = re.compile(r"[A-Za-z0-9_\-]+\.(?:txt|md)")


def load_scorer():
    """Use scorer.py if the student has built it. Otherwise run unscored."""
    try:
        import scorer  # noqa: PLC0415
    except ImportError:
        return None
    judge = getattr(scorer, "judge", None)
    return judge if callable(judge) else None


def run_once(question: str, top_k, threshold, corpus, variant):
    """One question, one run. Returns the answer and what retrieval gave us."""
    from store import search
    import gate
    from generate import answer_from_chunks

    results = search(question, top_k=top_k, corpus=corpus, variant=variant)
    decision = gate.check(results, threshold=threshold)

    if not decision.passed:
        return gate.REFUSAL, results, decision

    # cache=False on purpose. Three runs have to be three real answers.
    answer = answer_from_chunks(question, results, cache=False)
    return answer, results, decision


def main():
    parser = argparse.ArgumentParser(description="Run the test questions and log the results.")
    parser.add_argument("--runs", type=int, default=3, help="runs per question (default 3)")
    parser.add_argument("--label", default="", help="a name for this run, e.g. 'before'")
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--variant", default="default")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    corpus = args.corpus or config.CORPUS
    top_k = args.top_k or config.TOP_K
    threshold = config.THRESHOLD if args.threshold is None else args.threshold

    items = qs.answered()
    if not items:
        print(
            "questions.py has no questions in it yet.\n"
            "Milestone 2 asks you to write five. Fill them in and run this again.",
            file=sys.stderr,
        )
        sys.exit(1)

    judge = load_scorer()
    if judge is None:
        print("No scorer.py found — running unscored. Verdict column will be blank.")
        print("You'll build scorer.py in class in unit 2.\n")

    if args.runs < 3:
        print(f"⚠️  {args.runs} run(s). The submission asks for three.\n")

    transcript = []
    rows = []

    for item in items:
        question = item["question"]
        expects = item.get("expects", "")
        print(f"\n{question}")

        run_results = []
        for run in range(1, args.runs + 1):
            answer, results, decision = run_once(
                question, top_k, threshold, corpus, args.variant
            )
            passed = judge(question, expects, answer, results) if judge else None
            run_results.append(passed)

            mark = {True: "pass", False: "fail", None: "—"}[passed]
            print(f"  run {run}: {mark}  (best distance {decision.best_distance:.3f})")

            transcript.append(
                {
                    "question": question,
                    "run": run,
                    "answer": answer,
                    "sources": sorted({r.source for r in results}),
                    "expected_sources": list(item.get("sources", [])),
                    "best_distance": decision.best_distance,
                    "gate_passed": decision.passed,
                }
            )

        rows.append({"question": question, "expects": expects, "runs": run_results})

    gate_rows = check_out_of_scope(top_k, threshold, corpus, args.variant)
    chunk_stats = measure_chunks(corpus, args.variant)

    write_report(
        rows, transcript, gate_rows, args, corpus, top_k, threshold,
        scored=judge is not None, chunk_stats=chunk_stats,
    )


def check_out_of_scope(top_k, threshold, corpus, variant):
    """Put every OUT_OF_SCOPE question through retrieval and the gate.

    Criterion 3 in criteria.md is about questions the corpus doesn't cover, and
    it needs evidence in the run log like the other four. This costs nothing:
    a question the gate refuses never reaches the model, so there is no API
    call and no reason to run it three times — retrieval is deterministic and
    the gate is a comparison against a fixed number.
    """
    from store import search
    import gate

    questions = getattr(qs, "OUT_OF_SCOPE", [])
    if not questions:
        return []

    print("\nOut-of-scope questions (the gate should refuse these):")
    rows = []
    for question in questions:
        results = search(question, top_k=top_k, corpus=corpus, variant=variant)
        decision = gate.check(results, threshold=threshold)
        refused = not decision.passed
        print(f"  {'refused' if refused else 'LET THROUGH'}  "
              f"(best distance {decision.best_distance:.3f})  {question}")
        rows.append(
            {
                "question": question,
                "refused": refused,
                "best_distance": decision.best_distance,
            }
        )

    kept = sum(r["refused"] for r in rows)
    print(f"  -> gate refused {kept} of {len(rows)}")
    return rows


def _token_counter():
    """Count tokens the way the embedding model sees them, or None if we can't.

    The bundled model is Chroma's ONNX build of all-MiniLM-L6-v2, whose
    tokenizer truncates at 256 by default — switched off here, because a chunk
    that runs past the ceiling is exactly what criterion 4 is looking for.
    """
    import store

    model = store._embedder()
    onnx = getattr(model, "_ef", None)
    if onnx is not None:
        tokenizer = onnx.tokenizer
        tokenizer.no_truncation()
        tokenizer.no_padding()
        return lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)
    tokenizer = getattr(model, "tokenizer", None)
    if tokenizer is not None:
        return lambda text: len(tokenizer(text, add_special_tokens=False)["input_ids"])
    return None


def measure_chunks(corpus, variant):
    """Criterion 4: token sizes of every chunk in the index, plus a sample.

    Reads the chunks back out of the index this run searched, so it measures
    what retrieval actually saw. Chunking is deterministic, so like the gate
    this is one measurement, not three.
    """
    import store

    count = _token_counter()
    if count is None:
        return None

    collection = store._client().get_collection(config.collection_name(corpus, variant))
    got = collection.get(include=["documents", "metadatas"])
    chunks = sorted(
        zip(got["documents"], got["metadatas"]),
        key=lambda c: (str(c[1].get("source")), int(c[1].get("index", 0))),
    )
    if not chunks:
        return None

    tokens = [count(text) for text, _ in chunks]
    in_band = sum(TOKEN_FLOOR <= t <= TOKEN_BAND_TOP for t in tokens)
    over = sum(t > TOKEN_CEILING for t in tokens)

    picks = random.Random(0).sample(range(len(chunks)), min(CHUNK_SAMPLES, len(chunks)))
    samples = [
        {
            "source": chunks[i][1].get("source", "unknown"),
            "index": chunks[i][1].get("index", 0),
            "produced_by": chunks[i][1].get("produced_by", "unknown"),
            "tokens": tokens[i],
            "chars": len(chunks[i][0]),
            "text": chunks[i][0],
        }
        for i in sorted(picks)
    ]

    stats = {
        "total": len(chunks),
        "in_band": in_band,
        "over": over,
        "min": min(tokens),
        "max": max(tokens),
        "median": statistics.median(tokens),
        "producers": sorted({str(m.get("produced_by")) for _, m in chunks}),
        "size_met": in_band >= BAND_SHARE * len(chunks) and over == 0,
        "samples": samples,
    }
    print(f"\nChunks: {in_band} of {len(chunks)} in {TOKEN_FLOOR}–{TOKEN_BAND_TOP} "
          f"tokens, {over} over {TOKEN_CEILING}")
    return stats


def cited_files(answer: str) -> set[str]:
    return set(CITED_FILE.findall(answer or ""))


def score_criteria(transcript, gate_rows, chunk_stats, n_runs):
    """Turn the per-question transcript into one row per criterion.

    1  a question counts if any file in its `sources` was retrieved
    2  an answer counts if it names at least one file
    3  an out-of-scope question counts if the gate refused it
    4  every chunk measured against the token band (the single-topic half
       is left to you — read the samples)
    5  a question counts if its answer cites at least one of its `sources`
       and no other file, so a sibling in the citation fails it
    """
    by_run = {r: [e for e in transcript if e["run"] == r] for r in range(1, n_runs + 1)}
    n_questions = len(by_run.get(1, []))
    with_sources = [e for e in by_run.get(1, []) if e["expected_sources"]]
    n_sourced = len(with_sources)

    def right_sibling(entry):
        cited = cited_files(entry["answer"])
        expected = set(entry["expected_sources"])
        return bool(cited & expected) and cited <= expected

    counts = {1: [], 2: [], 5: []}
    for r in range(1, n_runs + 1):
        entries = by_run[r]
        sourced = [e for e in entries if e["expected_sources"]]
        counts[1].append(sum(bool(set(e["sources"]) & set(e["expected_sources"])) for e in sourced))
        counts[2].append(sum(bool(cited_files(e["answer"])) for e in entries))
        counts[5].append(sum(right_sibling(e) for e in sourced))

    refused = sum(r["refused"] for r in gate_rows)

    def row(crit, runs, of):
        if not of:
            return {**crit, "target": "—", "runs": ["—"] * n_runs, "verdict": "not measured"}
        need = crit["need"](of)
        return {
            **crit,
            "target": f"{need} of {of}",
            "runs": [f"{c} of {of}" for c in runs],
            "verdict": "MET" if all(c >= need for c in runs) else "MISSED",
        }

    rows = [
        row(CRITERIA[0], counts[1], n_sourced),
        row(CRITERIA[1], counts[2], n_questions),
        row(CRITERIA[2], [refused] * n_runs, len(gate_rows)),
    ]

    crit4 = CRITERIA[3]
    target4 = (f"≥{BAND_SHARE:.0%} in {TOKEN_FLOOR}–{TOKEN_BAND_TOP} tokens, "
               f"none > {TOKEN_CEILING}; ≥{CHUNK_SAMPLES - 1} of {CHUNK_SAMPLES} "
               f"samples single-topic")
    if chunk_stats is None:
        rows.append({**crit4, "target": target4, "runs": ["—"] * n_runs,
                     "verdict": "not measured"})
    else:
        cell = (f"{chunk_stats['in_band']}/{chunk_stats['total']} in band, "
                f"{chunk_stats['over']} > {TOKEN_CEILING}")
        size = "size MET" if chunk_stats["size_met"] else "size MISSED"
        rows.append({**crit4, "target": target4, "runs": [cell] * n_runs,
                     "verdict": f"{size}; single-topic: judge the samples below"})

    rows.append(row(CRITERIA[4], counts[5], n_sourced))
    return rows


def criterion_lines(criteria_rows, transcript, gate_rows, chunk_stats, threshold):
    """The per-criterion table, then the real output behind each row (run 1)."""
    n = len(criteria_rows[0]["runs"]) if criteria_rows else 0
    run_headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    run_divider = "|".join(["---"] * n)

    lines = [
        "",
        "### Run log — one row per criterion",
        "",
        "Aggregated from the same runs by `run_eval.py::score_criteria`. Targets",
        "are the ones in `criteria.md`; criteria 3 and 4 are deterministic, so the",
        "same number goes in every run column. The Verdict is a suggestion — a",
        "target missed in any one run is a MISS.",
        "",
        f"| Criterion | Target | {run_headers} | Verdict |",
        f"|---|---|{run_divider}|---|",
    ]
    for row in criteria_rows:
        lines.append(f"| {row['id']}. {row['name']} | {row['target']} | "
                     f"{' | '.join(row['runs'])} | {row['verdict']} |")

    first = [e for e in transcript if e["run"] == 1]
    lines += [
        "",
        "#### Real output per criterion (run 1)",
        "",
        "Pasted exactly as the system produced it.",
        "",
        "**Criterion 1** — produced by `store.py::search` "
        "(called from `run_eval.py::run_once`).",
        "",
        "```",
    ]
    for e in first:
        hit = set(e["sources"]) & set(e["expected_sources"])
        lines += [
            e["question"],
            f"  expected: {', '.join(e['expected_sources']) or '(no sources listed)'}",
            f"  retrieved: {', '.join(e['sources']) or 'none'}",
            f"  -> {'contains the answer' if hit else 'MISSING'}",
            "",
        ]
    lines[-1:] = ["```", ""]

    lines += [
        "**Criterion 2** — produced by `generate.py::answer_from_chunks` "
        "(called from `run_eval.py::run_once`, caching off).",
        "",
    ]
    for e in first:
        lines += [f"*{e['question']}*", "", "```", e["answer"], "```", ""]

    lines += [
        f"**Criterion 3** — produced by `run_eval.py::check_out_of_scope` → "
        f"`gate.py::check`, cutoff {threshold}.",
        "",
        "```",
    ]
    for g in gate_rows:
        verdict = "refused" if g["refused"] else "LET THROUGH"
        lines.append(f"{verdict}  (best distance {g['best_distance']:.3f})  {g['question']}")
    if gate_rows:
        import gate
        lines.append(f"-> gate refused {sum(g['refused'] for g in gate_rows)} of {len(gate_rows)}")
        lines.append(f"Answer returned when refused: {gate.REFUSAL}")
    lines += ["```", ""]

    lines += [
        "**Criterion 4** — chunks read back from the index built by "
        "`chunker.py::split_documents`, counted with the embedding model's "
        f"tokenizer by `run_eval.py::measure_chunks`. {CHUNK_SAMPLES} chunks "
        "sampled with seed 0.",
        "",
        "```",
    ]
    if chunk_stats is None:
        lines.append("not measured — no tokenizer available for this embedder")
    else:
        s = chunk_stats
        lines += [
            f"{s['total']} chunks · tokens: min {s['min']}, max {s['max']}, "
            f"median {s['median']} · in {TOKEN_FLOOR}–{TOKEN_BAND_TOP}: "
            f"{s['in_band']} of {s['total']} · over {TOKEN_CEILING}: {s['over']}",
            f"produced by: {', '.join(s['producers'])}",
        ]
        for c in s["samples"]:
            lines += [
                "",
                f"===== {c['source']}#{c['index']}  {c['produced_by']}  "
                f"{c['tokens']} tokens  {c['chars']} chars",
                c["text"],
            ]
    lines += ["```", ""]

    lines += [
        "**Criterion 5** — citations from `generate.py::answer_from_chunks`, "
        "checked against `sources` in `questions.py`.",
        "",
        "```",
    ]
    for e in first:
        if not e["expected_sources"]:
            continue
        cited = cited_files(e["answer"])
        expected = set(e["expected_sources"])
        ok = bool(cited & expected) and cited <= expected
        lines += [
            e["question"],
            f"  expected: {', '.join(e['expected_sources'])}",
            f"  cited:    {', '.join(sorted(cited)) or 'nothing'}",
            f"  -> {'right source' if ok else 'WRONG or sibling'}",
            "",
        ]
    lines[-1:] = ["```"]
    return lines


def write_report(rows, transcript, gate_rows, args, corpus, top_k, threshold, scored,
                 chunk_stats=None):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = len(rows[0]["runs"]) if rows else 0
    run_headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    run_divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        f"- Produced by: `run_eval.py::main`",
        f"- Retrieval: `store.py::search`, chunks from `chunker.py::split_documents`",
        f"- Corpus: `{corpus}` (index variant `{args.variant}`)",
        f"- top-k: {top_k} · relevance cutoff: {threshold}",
        f"- Runs per question: {n}, caching off",
        f"- When: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "This table is one row per QUESTION. The run log your README asks for is",
        "one row per CRITERION, so aggregate these into it — criterion 1 is how many",
        "of your questions had the answer in the retrieved chunks, and so on.",
        "",
        f"| Question | {run_headers} |",
        f"|---|{run_divider}|",
    ]

    for row in rows:
        cells = []
        for passed in row["runs"]:
            cells.append({True: "pass", False: "fail", None: " "}[passed])
        question = row["question"].replace("|", "\\|")
        lines.append(f"| {question} | {' | '.join(cells)} |")

    if not scored:
        lines += [
            "",
            "> The Run columns are blank because `scorer.py` doesn't exist yet.",
            "> Judge each question yourself by reading the output below, or build",
            "> the scorer first and re-run.",
        ]

    criteria_rows = score_criteria(transcript, gate_rows, chunk_stats, n)
    lines += criterion_lines(criteria_rows, transcript, gate_rows, chunk_stats, threshold)

    if gate_rows:
        refused = sum(r["refused"] for r in gate_rows)
        lines += [
            "",
            "---",
            "",
            "## The relevance gate on out-of-corpus questions",
            "",
            f"Produced by `run_eval.py::check_out_of_scope`, cutoff {threshold}. "
            f"Refused {refused} of {len(gate_rows)}.",
            "",
            "Retrieval is deterministic and the gate is a comparison against a",
            "fixed number, so these do not vary between runs — one pass over the",
            "list is the whole measurement.",
            "",
            "| Out-of-scope question | Best distance | Gate |",
            "|---|---|---|",
        ]
        for row in gate_rows:
            question = row["question"].replace("|", "\\|")
            verdict = "refused" if row["refused"] else "**let through**"
            lines.append(f"| {question} | {row['best_distance']:.3f} | {verdict} |")

    lines += ["", "---", "", "## Real output", "",
              "This is what the system actually produced. Paste the relevant parts",
              "into your README underneath the table — the rubric asks for real",
              "output as text, not a description of it.", ""]

    for entry in transcript:
        lines += [
            f"### {entry['question']} — run {entry['run']}",
            "",
            f"- Best distance: {entry['best_distance']:.4f} "
            f"({'passed' if entry['gate_passed'] else 'refused by'} the gate)",
            f"- Sources retrieved: {', '.join(entry['sources']) or 'none'}",
            "",
            "```",
            entry["answer"],
            "```",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")

    import generate as gen

    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print(gen.usage())
    print("\nCommit this file. It's the evidence the run actually happened.")


if __name__ == "__main__":
    main()