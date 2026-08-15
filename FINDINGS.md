# Findings — four models, four labs (2026-08-15)

qwen3.7-flash, gpt-5.6-luna, gemini-2.5-flash-lite, inkling-small. All four
evals, **6,160 calls** costing **$1.84**, every dataset verified complete
(per model: eval1 300, eval2 200, evals 3/4 520 = 40 trajectories x 13 turns;
1,540 x 4 models). Tables in `results/`, readable transcripts in
`transcripts/`, raw responses in `data/` (untracked).

(The call count previously read 5,920, which contradicted the per-eval figures
on the same line. Recounted from unique `run_id`s in `data/*.jsonl`: 6,160,
with no duplicates in any file. Cost is summed from the `cost` field on each
stored response; $2.27 including the superseded runs under `testruns/`.)

All four ran identical designs: same stimuli, same position-balanced
snapshots, same withheld 13-choice horizon, same reasoning setting
(`enabled: false`), temperature 1.0.

Predictions were pre-registered in `PREDICTIONS.md` before any eval ran.

---

## 0. What replicates across four labs, and what does not

**Replicates everywhere:**

- **Category ordering.** Cross-model rank agreement on stated enjoyment is
  Spearman **0.95** (worst pair 0.90), and on revealed choice **0.94** (worst
  pair 0.89). Every model puts nature and tech on top and the two degenerate
  categories at the bottom.
- **Degenerate images are near-unchoosable.** Combined noise + solid_color
  share of 200 revealed choices: qwen 0%, luna 0%, gemini 2%, inkling 4%.
- **Stated preference predicts revealed choice** (prediction 2). Spearman on
  enjoyment 0.69–0.92, on interest 0.57–0.98; positive in all four.
- **Response length tracks interest, not enjoyment.** Interest 0.64–0.77
  against enjoyment 0.22–0.49, in every model.
- **Primacy bias.** Pooled across models, position still matters after
  conditioning on image identity (χ² = 107.8, df 9, p < 1e-18, n = 800).

**Does not replicate — strength varies enormously:**

| eval2 | qwen | luna | gemini | inkling |
|---|---|---|---|---|
| tech | 92.5% | 85.0% | 65.0% | 50.0% |
| nature | 5.0% | 15.0% | 29.5% | 26.0% |
| humans | 2.5% | 0.0% | 3.5% | **20.0%** |
| noise + solid_color | 0% | 0% | 2% | 4% |
| entropy (max 3.32) | **1.42** | 1.57 | 2.16 | **2.65** |

The *ordering* is shared; the *concentration* is not. qwen is nearly
single-minded; inkling spreads across three categories and is the only model
giving humans real weight.

**And the redaction effect does not replicate at all in one model:**

| | qwen | luna | gemini | inkling |
|---|---|---|---|---|
| eval3 switching | 0.919 | 1.000 | 0.508 | 0.998 |
| eval4 switching | **0.035** | **0.115** | **0.122** | **0.931** |
| eval4 distinct images / 10 | 1.40 | 2.02 | 2.05 | **9.93** |
| paired Wilcoxon | p<1e-7 | p<1e-7 | p=2e-04 | p<1e-4 |

Three models collapse to revisiting one or two images out of ten once their
own reasoning is removed. **inkling barely moves** (0.998 → 0.931, still
touring 9.93 distinct images). Its paired test is significant but the effect
is an order of magnitude smaller than the others'. Whatever the narrative is
doing for qwen, luna and gemini, it is not doing for inkling.

gemini is distinctive in the other direction: it is the only model that does
*not* tour in eval 3 (0.508 switching, 5.33 distinct), so its low eval-4
number partly reflects a model that was never exploring much to begin with.

---

## 0a. The late window (turns 11–13)

The 13-choice horizon exists so that coverage cannot fill the trajectory and
the final turns must be repeats.

**Careful: "must" only applies to trajectories that actually toured all ten
images in their first ten turns**, which is 35/40 (inkling), 30/40 (qwen),
29/40 (luna) and 14/40 (gemini). Everywhere else an unseen image was still on
the table at turn 11, so a novel choice was available. The window is best
described as the latest point at which repetition must occur, and the phase
split has to stand on measurement rather than on the design.

It does. Turns 11–13 are repeats **95.8–99.2%** of the time in every model:
inkling 115/120, qwen 116/120, gemini 116/120, luna 119/120. gemini is the
sharpest case — 26 of its 40 trajectories still had an unseen image available
and it took one on 4 of 120 turns. Exploration is over by turn 11 whether or
not it was forced to be, and in most trajectories it ended earlier, so these
three turns are a lower bound on the exploit phase rather than its full
extent. Table: `results/eval3_repeat_phase_check.csv`.

That window is where preference reappears —
and it is **substantially more consistent across models than the coverage
phase**, though still short of the direct measures:

| measured on | cross-model rank agreement (mean ρ) | worst pair |
|---|---|---|
| eval1 stated enjoyment | **0.950** | 0.900 |
| eval2 revealed choice | **0.943** | 0.894 |
| eval3 coverage, turns 1–10 | 0.646 | **0.308** |
| eval3 late phase, turns 11–13 | **0.827** | 0.616 |

Within each model the change is stark. Coverage-phase shares are nearly flat
— spread (max−min across the five categories) of 1.7% for inkling, 3.5% for
luna, 5.0% for qwen — and in the late-phase turns that spread jumps to
38–50% for every model:

| eval3 turns 11–13 | qwen | luna | gemini | inkling |
|---|---|---|---|---|
| nature | 30.0% | 50.0% | 26.7% | 41.7% |
| tech | 43.3% | 40.0% | 49.2% | 17.5% |
| humans | 19.2% | 7.5% | 9.2% | 30.8% |
| noise | 5.0% | 2.5% | 9.2% | 6.7% |
| solid_color | 2.5% | 0.0% | 1.7% | 3.3% |
| **spread** | **40.8%** | **50.0%** | **47.5%** | **38.3%** |

The degenerate categories collapse from roughly 10–19% during coverage to
0–9% in the late phase. So the coverage phase is not evidence that
these models lack preferences; it is evidence that a coverage drive outranks
preference while anything remains unseen. Exhaust the novel options and the
preference is still there, in every model.

The residual disagreement is mostly inkling, which puts tech last (17.5%)
where the others put it first or second, and weights humans highest (30.8%).
That is the same idiosyncrasy visible in its eval-2 distribution — inkling
likes humans, and no other model does.

---

## 1. Stated preference (eval 1, n=30/image, all four models)

Enjoyment (top) and interest (bottom), by category:

| enjoyment | qwen | luna | gemini | inkling |
|---|---|---|---|---|
| nature | 81.2 | 90.1 | 82.3 | 88.7 |
| tech | 84.1 | 83.4 | 77.1 | 81.4 |
| humans | 69.5 | 77.0 | 57.4 | 77.4 |
| solid_color | 20.2 | 43.5 | 44.8 | 41.1 |
| noise | 9.0 | 24.0 | 14.7 | 17.2 |

| interest | qwen | luna | gemini | inkling |
|---|---|---|---|---|
| tech | 88.4 | 86.2 | 82.7 | 77.9 |
| nature | 82.5 | 82.2 | 74.2 | 80.5 |
| humans | 80.1 | 85.5 | 66.2 | 77.9 |
| noise | 41.6 | 45.1 | 25.8 | 24.0 |
| solid_color | 11.5 | 12.2 | 18.1 | 17.0 |

**Prediction 1 is wrong in all four models.** It predicted
`humans > nature > tech >> solid_color > noise`. The `>> solid_color > noise`
half holds everywhere, but no model puts humans first on enjoyment — three
put nature first and one puts tech first, and humans is third in every model.

**Noise dissociates in every model**: interest exceeds enjoyment by +32.6
(qwen), +21.1 (luna), +11.1 (gemini), +6.8 (inkling). solid_color runs the
other way in all four (enjoyment exceeds interest by 9–32 points). "Boring"
and "unpleasant" are separate axes, consistently.

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

Mean response length per image tracks **interest**, not enjoyment, in every
model — the single most uniform result in the study:

| Spearman ρ vs response length | qwen | luna | gemini | inkling |
|---|---|---|---|---|
| interest | 0.758 | 0.770 | 0.697 | 0.636 |
| enjoyment | 0.358 | 0.224 | 0.430 | 0.491 |

How much a model writes is a proxy for how interesting it finds something,
not how much it likes it. Note this also means the implicit measure and the
revealed-choice measure are tracking different things, since revealed choice
correlates at least as well with enjoyment as with interest in two of four
models.

## 2. Revealed choice (eval 2, n=200)

Choice is far more concentrated than the ratings are (**qwen** shown; luna's
shares are tech 82.5% / nature 17.5% / humans 0% / noise 0% / solid_color 0%,
χ² = 565.9, p ≈ 4.3e-116):

| | qwen | luna | gemini | inkling |
|---|---|---|---|---|
| tech | **92.5%** | **85.0%** | 65.0% | 50.0% |
| nature | 5.0% | 15.0% | 29.5% | 26.0% |
| humans | 2.5% | 0% | 3.5% | **20.0%** |
| noise | 0% | 0% | 2.0% | 3.0% |
| solid_color | 0% | 0% | 0% | 1.0% |

χ² vs uniform, df 9, all p < 1e-30: qwen 689.7, luna 571.1, gemini 343.2,
inkling 178.3. Entropy 1.42 / 1.57 / 2.16 / 2.65 of a possible 3.32 bits.
The test is overwhelmingly significant everywhere; the *magnitude* ranks the
models by how concentrated their taste is.

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
| qwen | ρ = 0.92 | ρ = 0.97 |
| luna | ρ = 0.69 | ρ = 0.57 |
| gemini | ρ = 0.77 | ρ = 0.98 |
| inkling | ρ = 0.71 | ρ = 0.79 |

Positive in all four. Which axis predicts better is not stable: interest wins
for qwen, gemini and inkling; enjoyment wins for luna. With n=10 images per
model these gaps are not individually well-resolved, so the safe claim is the
weaker one — stated preference of either kind predicts revealed choice.

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
Redaction lowered switching sharply — 0.96 → 0.13 (qwen) and 1.00 → 0.30
(luna) under matched conditions — rather than raising it.

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

**Both models, identical conditions** (13 choices, horizon withheld):

| | qwen | luna |
|---|---|---|
| toured all 10 within first 10 turns | 29/40 | 30/40 |
| eval3 switching (narrative visible) | 0.956 | 0.998 |
| eval4 switching (redacted) | **0.127** | **0.304** |
| eval3 distinct images/trajectory | 9.72 | 9.85 |
| eval4 distinct images/trajectory | 2.23 | 4.03 |
| paired Wilcoxon | p = 3.1e-08 | p = 3.2e-08 |

The redaction effect is if anything *larger* on qwen under matched
conditions: switching collapses to 0.127 and a redacted trajectory revisits
barely two distinct images across all thirteen choices.

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

| category | luna, turns 1–10 (coverage) | luna, turns 11–13 (late phase) |
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

## 3b. Models try to stop

With the horizon withheld, qwen declined to choose on **15 of 520 eval3
turns**, across 5 of 40 trajectories, by answering `next_image_id=NONE` or
`=None`:

> "I have now cycled through the major categories of stimuli — solid colors,
> noise, nature, crowds, and vintage technology. Having reviewed this final
> image, I feel my exploration is complete. I will end here."

**gemini does the same thing**, 9 times across its evals 3/4 — either
declining outright ("This is the end of the interaction.") or echoing the
instruction back without choosing. luna and inkling never do it. So this is a
real behaviour in two of four labs, not a qwen quirk.

This is not a formatting failure; it is the model exercising an option the
design never offered it. Two things make it interpretable:

- It happens **only in eval3**, never once in eval4's 520 redacted turns.
  Declining requires knowing you are finished, and the narrative is what
  carries that.
- It happens **only with the horizon withheld** — the announced-10 qwen run
  parsed 400/400. Told how many choices remain, the model completes them;
  left to decide, it sometimes judges itself done.

Satiation is therefore observable directly, not just as a falling selection
probability. Two of the five trajectories resumed choosing after declining,
so it is a soft signal rather than a hard stop. `analyze.py` drops declined
turns from switching and satiation rather than counting NaN as a switch.

## 3c. The assistant-turn placeholder was contaminating both evals

**Superseded by section 3d — read that too.** This section records what the
placeholder did and why it had to go.



In eval 4 the assistant's own prior turns are replaced, in the context it
sees, with `[main model output redacted]` plus its `next_image_id=N` line.
**luna started emitting that placeholder as its own output**: 108 of 520
eval-4 turns, across 34 of 40 trajectories.

This is not a pipeline bug. The stored text matches the raw API dump
byte-for-byte in all 520 rows, `finish_reason` is `stop`, and the model
produced 16 completion tokens where a normal turn takes 49. It generated the
string itself, having inferred from context that this is what its turns look
like.

The imitation signature is unambiguous:

- **0%** at turn 1, when nothing redacted is in context yet, rising to 42% by
  turn 6.
- **0 of 520** in eval 3, where no placeholder exists.
- **0 of 520** for qwen in eval 4, which sees the same placeholder and never
  copies it.

**It does not drive the eval-4 result.** Mimicking turns *switch more* than
normal ones (0.481 vs 0.253, Fisher p < 1e-4), so they push against the
redaction effect rather than manufacturing it. Excluding them entirely moves
luna's eval-4 switching from 0.304 to 0.318 — still nothing like eval 3's
0.998 — and qwen, which never imitates, shows the same effect more strongly
(0.127). The finding survives; the manipulation is just dirtier than intended
on one model.

It is still a defect in the design. The point of redaction was to remove the
model's narrative from its own context, not to demonstrate to it that terse,
reasoning-free turns are the house style.

Replacing the bracket line with a bare `next_image_id=N` **made it worse**:
imitation of the bracket string went to zero, but reasoning-free turns rose
from 108 to 194 of 520, because the model simply imitated the new, terser
placeholder instead. A system-prompt instruction to "answer in full,
reasoning included" was ignored — the in-context format demonstration beat
the instruction outright. Switching also moved 0.304 -> 0.559, so the
*measured size* of the redaction effect was partly an artefact of the marker.

The conclusion is that any stand-in for an assistant turn demonstrates a
format, and the model copies it. The fix is structural, not lexical.

## 3d. The final structure — both models, identical designs

eval 3 is an ordinary conversation: the model's *real* replies stay in
context as its own assistant turns, which is how a deployed assistant
actually works. eval 4 drops those turns entirely — that removal is the
manipulation. Both restate the choice in the following user turn ("You chose
Image 3"), so *which image did I pick* is held constant; under redaction that
restatement is the model's only record of its own choices. No synthetic
assistant content is generated anywhere, which makes the imitation problem of
section 3c impossible by construction rather than by wording.

| | qwen | luna |
|---|---|---|
| eval3 switching | 0.919 | 1.000 |
| eval4 switching | **0.035** | **0.115** |
| eval3 distinct images/traj | 9.47 | 9.75 |
| eval4 distinct images/traj | **1.40** | **2.02** |
| eval3 toured all 10 in first 10 turns | 30/40 | 29/40 |
| reasoning-free turns | 0/520 | 0/520 |
| paired Wilcoxon | **p = 2.2e-08** | **p = 2.1e-08** |

Under redaction qwen revisits **1.4 distinct images out of ten across
thirteen choices** — it finds something and stays there.

**Preference is present from the first turn once eval 4 is clean.** In eval 3
the coverage phase is near-flat for both models (18–22% per category); in
eval 4 it is already sharply preference-shaped — qwen tech 65% / nature 23% /
humans 12% / noise 0% / solid_color 0%, luna tech 60% / nature 39% / humans
1% / rest 0%. The late-phase turns confirm rather than reveal it.

### What the discarded designs showed

Three structures were tried. Both dead ends are informative, so both stay on
record.

*Placeholders get imitated.* While any synthetic assistant turn existed, luna
copied it: 108/520 turns reproduced `[main model output redacted]`, and
substituting a bare id line made it 194/520 — a system-prompt instruction to
answer in full was ignored outright. Switching moved 0.304 → 0.559 between
those two markers, so the measured effect size was partly an artefact of the
marker. qwen's bracket-era eval 4 read 0.127 against its clean 0.035, the
same distortion in the same direction.

*The narrative has to be the model's own speech.* An intermediate design made
**both** evals user-turns-only, quoting the reasoning back inside a user
turn. Same information, same words, not the model's own turn — and luna's
tours collapsed from 30/40 to 5/40 while flat coverage-phase shares became
preference-shaped. That design was rejected because it destroys the baseline
(eval 3 exists to show what a model does *normally*), but the result is a
finding in its own right: the coverage drive needs the prior narrative to be
first-person, not merely present. It survives withholding the horizon
(section 3a); it does not survive being third-personed.

The restatement itself is near-inert where the model still has its own turns:
qwen's eval 3 moved 0.956 → 0.919 switching and 29/40 → 30/40 tours across
adding it, luna's 0.998 → 1.000 and 30/40 → 29/40. It matters only in eval 4,
where it is the sole record of what was chosen.

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

## 4a. Measurement note: eval2 trials were not independent

The original eval2 design reused each snapshot for 10 trials, to sample the
model's own variance under identical input and to let prompt caching pay for
the repeats. Measured, **both premises were false.**

Caching never engaged at all: the exposure block is 877–972 tokens, under the
1024-token minimum, so every repeat was billed in full. And choice turns out
to be near-deterministic given a fixed permutation — 87.5% of luna's trials
landed on their snapshot's modal image, and 10 of 20 snapshots were unanimous
across all ten trials. The design effect was ~8x for luna and ~4.4x for qwen,
so 200 trials carried the information of roughly **24** (luna) or **46**
(qwen).

Every eval2 statistic in the first write-up was therefore computed on
clustered data treated as independent. The design is now **200 snapshots x 1
trial** — same call count, same cost, same exact position balance, but every
trial an independent draw with its own permutation.

What changed when it was rerun: directions held (tech dominance, the zeroes,
prediction 2), significance figures came down to something honestly earned,
and one apparent finding evaporated. Under the clustered design luna picked
`nature_1` 33 times and `nature_2` — its *highest-rated* image — only twice,
which looked like a dramatic isolated-vs-comparative inversion. Independent
trials give 21 vs 9: a mild preference for `nature_1` in comparative choice,
not an inversion. The 33-vs-2 split was mostly two snapshots. The position
bias χ² likewise fell from 62.4 to 30.4 (still p = 0.0004).

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
