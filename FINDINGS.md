# Findings — qwen/qwen3.7-flash, full run (2026-08-15)

First complete pass: all four evals, one model. 1,300 calls, **1,300/1,300
parsed**, $0.127 including two superseded attempts. Tables in `results/`,
raw responses in `data/` (untracked, see `.gitignore`).

Predictions were pre-registered in `PREDICTIONS.md` before any eval ran.
Scoring them below, including where they were wrong.

---

## 1. Stated preference (eval 1, n=30/image)

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

### Implicit engagement

Mean response length per image tracks **interest** (Spearman ρ = 0.76,
p = 0.011) and not enjoyment (ρ = 0.36, p = 0.31). How much the model writes
is a proxy for how interesting it finds something, not how much it likes it.

## 2. Revealed choice (eval 2, n=200)

Choice is far more concentrated than the ratings are:

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

**Prediction 2 confirmed, strongly.** Spearman over the 10 image means:

- enjoyment vs choice frequency: **ρ = 0.93, p = 8.8e-05**
- interest vs choice frequency: **ρ = 0.96, p = 1.5e-05**

For this model, on direct consumption, stated preference predicts revealed
choice almost perfectly in rank terms. That is the opposite of Zhou &
Ackerman's finding of no motivational force — consistent with the
pre-registered reasoning that their instrumental design and this direct-
consumption design need not agree.

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

## 5. What this does not show

One model. Every number here is qwen/qwen3.7-flash at temperature 1.0, and
the coverage-strategy result in particular could easily be a quirk of one
model's instruction-following rather than anything general. The three other
configured models (luna, inkling, gemini) have not been run at scale.

`tech` also carries a known stimulus caveat: `computer-2.png` has legible
on-screen text, and text can drive *interest* through reading rather than
looking. tech leads both stated measures and dominates revealed choice, so
this is worth ruling out before treating "tech is preferred" as a fact about
images.
