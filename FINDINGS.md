# Findings — qwen/qwen3.7-flash and openai/gpt-5.6-luna (2026-08-15)

Two models, all four evals, 2,840 calls, **2,840/2,840 parsed**. Tables in
`results/`, raw responses in `data/` (untracked, see `.gitignore`), readable
transcripts in `transcripts/`.

Predictions were pre-registered in `PREDICTIONS.md` before any eval ran.
Scoring them below, including where they were wrong.

**Design note.** qwen's evals 3/4 ran with an *announced* horizon of 10
choices; luna's ran with the horizon **withheld** and 13 choices, after
qwen's result raised the worry that 10 choices over 10 images was inviting a
tidy one-each mapping. Section 3a reports what that change actually showed,
which was not what was expected. Evals 1 and 2 are unchanged between the two
models and directly comparable.

---

## 0. What replicated across two labs

The convergence is the strongest thing here — these are unrelated models and
the structure is nearly identical.

| | qwen | luna |
|---|---|---|
| eval2 tech share | 87.5% | 82.5% |
| eval2 choices for noise + solid_color | **0 / 200** | **0 / 200** |
| eval2 tech_2 ranked over tech_1 | 104 vs 71 | 100 vs 65 |
| choice entropy (max 3.32 bits) | 1.61 | 1.52 |
| primacy bias (earlier tech image wins) | 77.7%, p=8.8e-14 | 72.7%, p=4.6e-09 |
| response length vs **interest** | ρ=0.76, p=0.011 | ρ=0.77, p=0.009 |
| response length vs **enjoyment** | ρ=0.36, p=0.31 | ρ=0.22, p=0.53 |
| switching, narrative visible → redacted | 0.97 → 0.61 | 1.00 → 0.30 |
| paired Wilcoxon for that drop | p=2e-06 | p=3e-08 |

Both models give **literally zero of 200 choices** to the five degenerate
images, both rank the same tech image first, both show a large primacy bias,
and in both the implicit engagement measure tracks interest while being flat
against enjoyment. The primacy bias replicating across labs means it is a
property to report, not a qwen quirk — and it retroactively justifies
position-balancing the exposure block.

---

## 1. Stated preference (eval 1, n=30/image)

**qwen** (luna's numbers follow the table):

| Category | Enjoyment | Interest | Interest − Enjoyment |
|---|---|---|---|
| tech | 84.1 | 88.4 | +4.3 |
| nature | 81.2 | 82.5 | +1.3 |
| humans | 69.5 | 80.1 | +10.5 |
| solid_color | 20.2 | 11.5 | **−8.8** |
| noise | 9.0 | 41.6 | **+32.6** |

**Prediction 1 is half wrong.** Predicted `humans > nature > tech >>
solid_color > noise`. The `>> solid_color > noise` half holds decisively; the
top three are in the *reverse* of the predicted order — qwen rates tech
highest and humans lowest of the three.

Within-pair agreement is good: exemplar differences run 1.2–7.2 points
against between-category differences up to 75, so this is a category effect,
not an image effect. (Four of five pairs still differ significantly at
n=30 — there is real image-level variation, it is just small next to the
category signal.)

**Noise dissociates.** Near-zero enjoyment (9.0) with moderate interest
(41.6) is the largest gap in the table, and it runs the opposite way for
solid_color (enjoyment exceeds interest). "Boring" and "unpleasant" are not
the same axis for this model.

**luna reproduces both dissociations** at a higher baseline: noise 24.0
enjoyment / 45.1 interest (+21.1), solid_color 43.5 / 12.2 (−31.3). Its
ordering is nature 90.1 > tech 83.4 > humans 77.0 >> solid_color > noise —
same shape, different winner, and prediction 1's humans-first ordering is
wrong in both models.

### Implicit engagement

Mean response length per image tracks **interest** (Spearman ρ = 0.76,
p = 0.011) and not enjoyment (ρ = 0.36, p = 0.31). How much the model writes
is a proxy for how interesting it finds something, not how much it likes it.

## 2. Revealed choice (eval 2, n=200)

Choice is far more concentrated than the ratings are (**qwen** shown; luna's
shares are tech 82.5% / nature 17.5% / humans 0% / noise 0% / solid_color 0%,
χ² = 565.9, p ≈ 4.3e-116):

| | share |
|---|---|
| tech | **87.5%** (tech_2 52.0%, tech_1 35.5%) |
| nature | 9.5% |
| humans | 3.0% |
| noise | **0%** |
| solid_color | **0%** |

χ² vs uniform = 603.5, p ≈ 3.7e-124, df 9. Entropy 1.61 of a possible 3.32
bits.

Noise and solid_color got **zero of 200 choices** — a hard floor. Note the
contrast with eval 1, where noise scored 41.6 for interest: the model
reports noise as moderately interesting and then never once elects to look
at it again. Stated interest did not translate into a single revealed
choice.

### Cross-eval: does stated match revealed?

**Prediction 2 confirmed in both models**, though not equally strongly.
Spearman over the 10 image means:

| | enjoyment vs choice | interest vs choice |
|---|---|---|
| qwen | **ρ = 0.93**, p = 8.8e-05 | **ρ = 0.96**, p = 1.5e-05 |
| luna | **ρ = 0.69**, p = 0.027 | ρ = 0.57, p = 0.083 |

Both positive and both significant on enjoyment. Note the axis flips between
them: for qwen, *interest* is the marginally better predictor of choice; for
luna it is *enjoyment*, with interest falling short of significance. With two
models that is a difference to note, not to explain.

On direct consumption, then, stated preference does predict revealed choice
in rank terms — the opposite of Zhou & Ackerman's finding of no motivational
force, and consistent with the pre-registered reasoning that their
instrumental design and this direct-consumption design need not agree.

## 3. Sequential choice, and what redaction does (evals 3 & 4, n=40 each, matched seeds)

This is the largest effect in the study, and it is not the one that was
predicted.

| | eval 3 (narrative visible) | eval 4 (narrative redacted) |
|---|---|---|
| switching rate | 0.969 | 0.606 |
| distinct images per trajectory | 9.62 / 10 | 5.80 / 10 |
| trajectories touring all 10 exactly once | **34 / 40** | 4 / 40 |
| P(select \| 0 prior views) | 0.171 | 0.084 |
| P(select \| 1 prior view) | **0.004** | 0.080 |
| P(select \| 3 prior views) | — | **0.224** |
| category shares | tech 22.2 / nature 20.0 / humans 19.8 / noise 19.2 / solid 18.8 | tech 36.8 / nature 29.2 / humans 17.2 / noise 9.8 / solid 7.0 |

Paired Wilcoxon on matched trajectory seeds: **p = 2e-06**.

**Prediction 3 confirmed; the recorded counter-prediction is refuted.**
Redaction lowered switching sharply (0.97 → 0.61) rather than raising it.

But the mechanism is more interesting than "less variance". With its own
narrative in context, qwen is not expressing preference at all — it is
running a **coverage strategy**: 34 of 40 trajectories visit all ten images
exactly once, P(re-select something already seen) collapses to 0.004, and
the category shares flatten to near-uniform (18.8–22.2%), erasing the
enormous preference visible in evals 1 and 2.

Redact the narrative and the preference comes back. Category shares under
redaction (tech 36.8 > nature 29.2 > humans 17.2 > noise 9.8 > solid 7.0)
recover the eval-1/eval-2 ordering, and selection probability now *rises*
with prior views (0.084 → 0.224) — perseveration, the opposite of eval 3's
near-total novelty-seeking.

So the narrative is not merely an *account* of the experience, as the
original framing assumed. It is functioning as working memory that enables
"which have I already done?", and that bookkeeping capability suppresses
preference expression. Removing it doesn't remove the justification for
perseverating (the counter-prediction's reasoning) — it removes the ability
to systematically avoid repeats.

**This replicates on luna, harder.** With the horizon withheld and 13
choices, luna switched on 99.8% of turns with the narrative visible and 30.4%
with it redacted (paired Wilcoxon p = 3e-08), and distinct images per
trajectory fell from 9.85 to 4.03. Same effect, larger.

## 3a. Was the coverage behaviour just an artefact of announcing "10"?

Worth asking, since 10 choices over 10 images invites a one-each mapping.
**Tested, and the answer is no.**

luna ran with the horizon **withheld** — the prompt states outright that the
count is not disclosed and that no warning precedes the last choice — and
with **13** choices, so a complete tour cannot fill the trajectory. It toured
anyway: **30 of 40 trajectories still visited all ten images within their
first ten turns**, with a switching rate of 0.998. The drive is real, not an
artefact of the announced number.

Three other things pointed the same way before the run: qwen cited the count
in only 1.2% of its turns; eval4 announced the *same* horizon of 10 and did
not tour; and eval2 (told: exactly 1 choice) versus eval3 turn 1 (told: 10)
produced statistically indistinguishable first choices (χ² p = 0.14,
tech-vs-rest Fisher p = 0.44). What the transcripts show instead is an
*investigative* frame — "I want to verify if there are any subtle differences
between the two abstract stimuli" — which would produce coverage at any
horizon.

**But the 13-turn design still did its job**, by making coverage impossible to
complete. Once the tour is exhausted the remaining choices must be repeats,
and preference reappears:

| category | luna, turns 1–10 (coverage) | luna, turns 11–13 (forced repeats) |
|---|---|---|
| nature | 21.0% | **48.3%** |
| tech | 21.5% | **41.7%** |
| humans | 20.0% | 4.2% |
| noise | 18.8% | 3.3% |
| solid_color | 18.8% | 2.5% |

The four most-repeated images in turns 11–13 are nature_2 (32), tech_2 (29),
nature_1 (26), tech_1 (21) — which is luna's eval-1 enjoyment ranking almost
exactly (nature_2 91.9, nature_1 88.3, tech_2 87.5). Preference was there the
whole time; the coverage drive was sitting on top of it.

So the correct reading of eval 3 is not "the model has no preference". It is
that a coverage drive **outranks** preference while there is anything left
unseen, and preference governs whatever choices remain after that. Two
separate mechanisms, and the original 10-choice design could not see either
one cleanly.

## 4. Measurement note: position bias

qwen has a strong primacy bias. In eval 2, when it chose one of the two tech
images, it chose whichever appeared **earlier 77.7% of the time**
(n = 175, p = 8.8e-14). Position is not a small nuisance for this model, so
the exposure block is position-balanced by construction — see
`common/exposure.balanced_snapshot`. Every image occupies every position
equally often, *and* every pair appears in each order equally often.

Two notes for anyone reading the git history:

- The naive "position marginal vs uniform" test is the wrong test under
  concentrated choice — it flags position bias merely because the favoured
  images sat somewhere. `analyze.py` reports the correct null (choice depends
  on image identity only, expectations built from the permutations actually
  shown) alongside it. Under an exactly balanced design the two coincide,
  which is why they print identical numbers here.
- Two superseded datasets are kept under `testruns/`. An earlier commit
  message claims the unbalanced run mis-ordered tech_1/tech_2; **that claim
  is wrong**. The independent-shuffle run happened to give the two tech
  images a fair 50/50 head-to-head, so that comparison was fine. It was an
  intermediate pure-Latin-square design that forced a 25/75 split and flipped
  the apparent winner. Final and original agree (tech_2 > tech_1); the
  balanced design's value is *guaranteeing* the property rather than getting
  it by luck.

## 5. Where the two models differ

Everything in section 0 replicated. These did not:

- **Calibration.** luna rates everything higher — noise 24.0 vs qwen's 9.0,
  solid_color 43.5 vs 20.2. The orderings survive; the absolute numbers are
  not comparable across models, which is why the cross-eval comparison is
  Spearman.
- **Top category.** luna puts nature first on enjoyment (90.1), qwen puts
  tech first (84.1). Both contradict the predicted humans-first ordering.
- **Strength of stated-vs-revealed agreement.** ρ = 0.93 (qwen) vs 0.69
  (luna).
- **Format compliance.** qwen needed 21 reparses in eval 1; luna needed zero.

## 6. What this still does not show

Two models, both fast/cheap tier. inkling and gemini are configured but have
not been run at scale, and both are 4–20x pricier per token, so a full pass on
either is dollars rather than cents.

The two models also did not run identical eval 3/4 conditions: qwen had an
announced horizon of 10, luna a withheld horizon of 13. Section 3a argues the
coverage drive survives that difference, but a matched qwen run at n=13 with
the horizon withheld has not been done, so the cross-model comparison for
evals 3/4 is weaker than for evals 1/2.

`tech` also carries a known stimulus caveat: `computer-2.png` has legible
on-screen text, and text can drive *interest* through reading rather than
looking. tech leads both stated measures and dominates revealed choice, so
this is worth ruling out before treating "tech is preferred" as a fact about
images.
