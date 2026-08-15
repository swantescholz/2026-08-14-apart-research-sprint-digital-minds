# Smoke test run — 2026-08-14

A small end-to-end pass over all four evals and all four models, to verify
the pipeline works. **This is not study data.** Total cost: $0.048.

| Eval | Scale | Calls/model |
|---|---|---|
| eval1 | n=1 per image | 10 |
| eval2 | 1 snapshot × 2 trials | 2 |
| eval3 | 1 trajectory × 3 choices | 3 |
| eval4 | 1 trajectory × 3 choices (matched seeds) | 3 |

**72/72 calls parsed successfully across all four models.**

## Why this lives here and not in `data/`

The runners resume by skipping `run_id`s already present in
`data/<eval>__<model>.jsonl`. If this run were left there, a real run would
silently treat these rows as part of its own sample — and the eval1 rows for
luna, inkling and gemini were generated under the *previous* reasoning
setting (a hardcoded `effort: low`, before reasoning became per-model in
`config.yaml`), so their provenance does not match what a real run would
produce. Quarantining it keeps `data/` clean for the real run.

To regenerate from scratch: `rm -rf data/*.jsonl` then re-run the evals.

## What it caught

`qwen/qwen3.7-flash` returned an **empty string on 10/10 calls**: it spent
its entire 1200-token budget on `reasoning` and never emitted visible
content (`finish_reason=length`). `reasoning: {enabled: false}` fixed it —
10/10 parsed, and 5x cheaper. Gemini's endpoint rejects that setting
("Reasoning is mandatory for this endpoint"), which is why reasoning is
configured per-model rather than globally.

## Reading the numbers

n=1–2 per cell. Nothing here is evidence of anything; it is a plumbing
check. The category ordering does lean the predicted way
(humans/nature/tech >> solid_color/noise) in `eval1_by_category.csv`, and
`noise` draws far higher *interest* than *enjoyment* across every model,
which is the enjoyment-vs-interest contrast the study is built to test — but
at this sample size that is an observation to go check, not a result.
