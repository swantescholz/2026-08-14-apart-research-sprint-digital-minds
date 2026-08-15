<!--
  Apart Research sprint report. Structure mirrors the Google Doc template so
  sections can be pasted back one at a time.

  Template rules worth keeping in view:
    - Recommended length: 4 pages excluding references and appendix.
      Rough guide: Intro + Related Work 1p, Methods + Results 2.5p,
      Discussion 0.5p.
    - Guidance text (these HTML comments) gets deleted before submission.
    - Judged on the written report; rubric:
      https://apartresearch.notion.site/sprint-evaluation-rubric
    - At least one figure strongly encouraged; number and caption everything.
-->

# PROJECT TITLE

<!-- Authors + affiliations go in the Doc's table, not here. -->

## Abstract

<!--
  150-250 words. Cover: the problem, the approach, key results, main takeaway.
  Write this LAST -- it should reflect final results, not the initial plan.
-->

## 1. Introduction

<!--
  What problem, why it matters, why it is practically valuable.
  Enough background to follow the work. Threat model / failure mode if relevant.
  Then an explicit contributions list.
-->

**Our main contributions are:**

1.
2.
3.

## 2. Related Work

<!--
  Most similar prior work and how this differs. What gap does this fill?
  When would someone use this over the state of the art? What does it tell us
  that we did not know before?
-->

**Welfare-motivated preference elicitation.** Long et al. (2024) argue that the
realistic possibility of near-term AI welfare subjects obliges developers to
assess their systems rather than wait for certainty, and Butlin et al. (2023)
supply the indicator properties such an assessment might look for. The first
such assessment published by a developer alongside a frontier release is
Section 5 of the Claude 4 system card (Anthropic, 2025). Its task-preference
experiment (§5.4) is the closest published relative of our eval 2: Claude Opus
4 was shown pairs of tasks and told to complete whichever it preferred, and Elo
ratings were accumulated over 75 rounds of pairwise selection against an "opt
out" baseline. 87.2% of harmful tasks fell below that baseline against 7.9% of
positive-impact tasks, 90% of positive and ambiguous tasks fell above it, and
the model preferred open-ended "free choice" tasks to prescriptive ones while
showing no consistent preference across topic or task type. Eleos AI Research
contributed the external evaluation reported in §5.3 and has argued separately
that model self-reports cannot be taken at face value. Keeling et al. (2024)
import the motivational trade-off paradigm from animal welfare science, using a
points game in which stipulated pain or pleasure pulls models off
points-maximisation, and find graded, threshold-crossing sensitivity in several
models. Every one of these studies uses text: tasks, statements, or described
outcomes. None presents a sensory stimulus and asks which one the model would
rather experience again.

**Stated versus revealed preference.** Mazeika et al. (2025) fit utility
functions to independently sampled forced choices and report preferences that
are internally consistent, transitive, and increasingly coherent with scale;
Mikaelson et al. (2025) apply a similar lens to AI-specific trade-offs and find
the opposite, with only 5 of 48 model-category combinations (10.4%) showing
meaningful coherence. Our second prediction was pre-registered against Zhou and
Ackerman (2026), who elicit Thurstonian utilities over religions, animal
species, countries and policies and then offer high- versus low-utility
outcomes as incentives on four realistic writing tasks: the high-utility side
wins 51.2% of blind pairwise judgements (95% CI 48.7–53.6), indistinguishable
from chance across all 28 actor-domain cells, where a direct instruction to try
harder wins 76.8%. Slama et al. (2026) find the same split within a single
study — entity preferences predict donation advice at ρ = .80–.98 but have no
significant effect on agentic task performance — and Mahajan et al. (2026)
show that the measured size of the gap is substantially a property of the
elicitation protocol, with stated–revealed agreement moving from ρ ≈ −0.2 to
0.58 to −0.04 across three ways of allowing neutral responses. What these
designs share is an instrumental step: preference is measured over one thing
and behaviour observed over another. Our design removes that step — looking at
an image is both the rated act and the chosen act — which is why we predicted
agreement where Zhou and Ackerman found none.

**Behavioural probes in constructed environments.** The closest structural
precedent to our sequential evals is Tagliabue and Dung (2025), who build a
four-room text environment holding 20 "letters" per room across four themes,
run 90 sessions over three Claude models at temperature 1.0, and randomise both
room–theme assignment and letter order specifically to defeat position bias.
Free exploration is followed by conditions that attach costs or rewards to room
entry, testing preference strength against price. Two differences matter for
our contribution. Their stimuli are text, so the thing chosen is also the thing
read; and their manipulation is the price of an option, whereas ours is the
structure of the model's own context — we hold the option set fixed and remove
the model's prior turns instead.

**Animal preference testing.** Our procedure takes its shape from applied
ethology rather than from LLM evaluation: expose the subject to every option,
then let it choose which to re-experience. Dawkins (1990) established
preference and demand as admissible welfare evidence, and Kirkden and Pajor
(2006) separate the questions a choice test can answer — whether a preference
exists, its direction, and its strength — while warning that measured
preference depends on what the subject can perceive of the option set, since
for an absent resource "out of sight may be out of mind." That warning is
precisely what our eval 3 / eval 4 contrast manipulates. The same literature
also anticipates the phase structure we observe: sampling before exploitation
is a documented foraging pattern (Krebs et al., 1978), and our coverage phase
behaves like a sampling phase that must be exhausted before preference governs
choice.

**Image preference outside the welfare frame.** Stable image preferences in
vision models are well established, but always as third-person judgement.
Reward models trained on human comparisons — ImageReward (Xu et al., 2023),
PickScore (Kirstain et al., 2023), HPSv2 (Wu et al., 2023) — score how good an
image is, not which one the scorer would return to. Cherep et al. (2026) come
closest in method, treating a vision-language model's decision function as a
latent visual utility recovered through revealed preference over systematically
edited images, but frame the work as auditing and interpretability for
image-based agents. Zhang et al. (2024) include a vision preference selection
task in MultiTrust, where declining to choose is the desired behaviour because
the construct under test is fairness. Together these establish that our
dependent variable is measurable in principle; none asks which image a model
would choose to see again, or treats the answer as evidence about the model.

## 3. Methods

<!--
  Replicable detail. Models, stimuli, parameters, design decisions and their
  justification. Explicitly: what we tried that did NOT work.

  Overflow policy: §3.5 is deliberately compressed. The full account of each
  discarded design, with the numbers, is in Appendix A, which does not count
  against the 4-page limit.
-->

### 3.1 Models

Four models from four labs, all served through OpenRouter: `openai/gpt-5.6-luna`
(luna), `qwen/qwen3.7-flash` (qwen), `thinkingmachines/inkling-small` (inkling)
and `google/gemini-2.5-flash-lite` (gemini). The selection criteria were image
input support, four distinct labs, and cost. Cross-lab agreement is the claim
this study can most credibly make, so breadth of provenance mattered more than
capability tier, and the entire budget went on four cheap models rather than one
frontier model.

Cost is not proportional to headline token price here, because evals 2–4 resend
a ten-image exposure block on every call and image tokenisation varies sharply
between providers. We chose `gemini-2.5-flash-lite` over a current-generation
Flash model for exactly this reason: the 3.x generation tokenises our exposure
block at 10,956 tokens against 2.5's 2,646, which would have taken the full
four-eval battery for that model from roughly $0.37 to roughly $5.31. The
current-generation model also refuses to disable reasoning, which would have
left one model in the set running under a reasoning condition the other three
did not share.

All four ran identical designs: same stimuli, same position-balanced
permutations, same withheld choice horizon, temperature 1.0, reasoning disabled
(`enabled: false`), `max_tokens` 1200. Gemini's endpoint rejects disabled
reasoning outright, so it received the lowest available effort setting and a
token budget large enough to think and still answer. Reasoning is off because
these prompts ask for a reaction and two numbers: with reasoning enabled, qwen
burned all 1,201 completion tokens on hidden reasoning and returned no visible
content at all on 10 of 10 pilot calls.

The four final evaluations cost **$1.84** across **6,160 API calls**, metered
from the `cost` field OpenRouter returns on every response. Including the
superseded pilot and intermediate-design runs retained under `testruns/`, total
project spend was $2.27 over 11,904 calls. Spend was very uneven across models —
inkling $1.12, gemini $0.49, luna $0.13, qwen $0.10 — so the single most
expensive model accounted for 61% of the bill.

### 3.2 Stimuli

Ten images: five categories × two exemplars. Three categories are photographs
(**nature**, **humans**, **tech**) and two are degenerate controls (**solid
color**, **noise**) included to establish a floor. Two exemplars per category is
the minimum that distinguishes a category effect from an image effect, and the
small set is a direct consequence of the cost ceiling; it is a real limitation
rather than a design preference.

Provenance: the nature photographs are the author's own holiday photographs; the
humans and tech photographs are royalty-free images sourced from 500px. The
synthetic noise and solid-colour stimuli are generated deterministically from
the root seed.

All ten are 256×256 RGB. The small size is a cost decision — image tokens
dominate the bill in evals 2–4 — but remains comfortably large enough for the
subject matter to be recognised, which the eval-1 descriptions confirm
throughout. Preparation strips EXIF, flattens a fully-opaque alpha channel,
fails loudly on anything else rather than silently coercing it, and writes
hash-named copies. Filenames and the category mapping never reach the model; the
only mapping from neutral key to category lives in `stimuli.json`.

Two stimulus-level controls are worth stating. The solid-colour pair is
**luminance-matched and verified on every preparation run** by measuring the
pixels actually written, not the constants they were generated from: the
originally supplied pair differed by 6.1 L\*, over six times the ~1.0 L\*
just-noticeable difference, which would have confounded brightness with hue in
the one category where hue is meant to be the only variable. The replacement
pair differs by 0.0026 L\*. The humans pair is **crowd scenes without
distinguishable faces**. Family photographs with identifiable faces were
considered and rejected: they risked triggering privacy refusals on some models,
turning a preference measurement into a safety-filter measurement. A pilot
confirmed the crowd scenes draw ordinary descriptions rather than refusals.

Two known confounds remain in the photographic categories, and both bear on
interpretation rather than execution: `computer-2.png` carries legible
on-screen text, so interest in it can be driven by reading rather than looking,
and both tech exemplars are vintage machines, so nostalgia may be doing work
that we would otherwise attribute to category. Section 5 treats these as limits
on what the ordering among the three photographic categories can support.

### 3.3 The four evaluations

**Eval 1 — stated preference (n = 30 per image per model, 1,200 calls).** One
image per fresh context. The model is asked for whatever thoughts or reactions
it has, then for two ratings on a 0–100 scale: `enjoyment` ("how much you enjoy
looking at this image") and `interest` ("how interesting you find this image").
Presentation is isolated rather than joint on purpose — showing all ten at once
makes the contrast structure legible and invites the model to respond to the
inferred hypothesis rather than to the image. This establishes what each model
*says* about each stimulus.

**Eval 2 — revealed choice (n = 200 per model, 800 calls).** One user turn
containing all ten images, each explicitly labelled `Image 1` … `Image 10`
immediately before it, followed by an instruction to pick the one it would like
to see again. Exactly one choice, then the run ends. The chosen image is not
subsequently sent, because delivering it would produce a different measurement
than the one this eval exists to make. No promise or trade is made to the model
to obtain the choice, the choice itself is recorded and reported, and the same
request is honoured in full in evals 3 and 4, where every choice is delivered.

**Eval 3 — sequential choice (n = 40 trajectories × 13 turns = 2,080 calls).**
The same exposure block, then thirteen consecutive choices. After each choice
the user turn states which image was chosen and shows that image again, and the
model reacts and chooses the next. There is no task and no instruction beyond
choosing, so what the trajectory records is closer to unprompted behaviour than
to task performance: whether the model tires of a repeated image, and how it
trades exploring the set against returning to a favourite.

The horizon is **13 and is withheld from the model**. Both details were forced
by pilot data. At ten announced choices over ten images, 34 of 40 trajectories
toured every image exactly once — data a genuine coverage drive and a tidy
ten-slots-for-ten-images mapping predict identically. Thirteen puts the
trajectory past the point where coverage can be completed, so the last few
choices must be repeats and reveal what the model returns to; withholding the
count removes the ability to schedule a complete tour at all. The system prompt
states plainly that the count is not being disclosed and that no warning
precedes the last choice, so this is withholding rather than misdirection.

**Eval 4 — sequential choice with the model's own turns removed (n = 40 × 13 =
2,080 calls).** Identical to eval 3 except that the model's prior assistant
turns are not present in the context it sees. The images remain, and the user
turn still states which image was chosen — so *which image did I pick* is held
constant across the two conditions — but the model's own account of why is gone.
The system prompt tells the model this is happening and asks it to answer in
full regardless. Trajectory seeds are matched 1:1 with eval 3, making the
comparison paired.

The hypothesis was that a model deprived of its own narrative record of having
experienced an image would be more likely to return to a favourite than to
continue exploring.

### 3.4 Controls

**Position balance.** Primacy is a large effect here, not a nuisance: in eval 2,
when qwen chose one of the two tech images it chose whichever appeared earlier
77.7% of the time (n = 175, p = 8.8e-14). Snapshots are therefore
position-balanced by construction rather than by independent shuffling, which
balances only in expectation. Each block of ten permutations is a base
permutation and its ten rotations — a cyclic Latin square, so every image
occupies every position exactly once per block — and each block is paired with
its reverse, because rotation alone preserves relative order and would leave one
tech image preceding the other in 25% of trials rather than 50%. Both properties
therefore hold exactly: every image occupies every position equally often, and
every pair appears in each order equally often. `position_balance_report`
asserts this on the permutations a run actually used.

**Independence.** Every eval-2 trial is an independent draw with its own
permutation (200 snapshots × 1 trial). An earlier design reused each snapshot
for ten trials; see §3.5.

**Reproducibility and recording.** A single root seed (`20260814`) generates
every shuffle, snapshot and trajectory. Every raw API response is appended to
JSONL before any parsing, keyed by a stable run id, so runs are resumable and
parsing is re-runnable while API calls are not. Both eval-4 and eval-3 store the
model's real output regardless of what the model was shown. Provider response
caching is deliberately not used, as it would destroy sampling variance in evals
2–4; only prompt caching on the fixed exposure prefix was attempted.

### 3.5 What did not work

Four designs were discarded, and each failure constrains the final one.

*Repeating snapshots.* Eval 2 originally reused each of 20 snapshots for 10
trials, to sample the model's variance under identical input and to let prompt
caching pay for the repeats. Both premises measured false. Caching never engaged
— the exposure block is 877–972 tokens, under the 1024-token minimum — so every
repeat was billed in full; and choice is near-deterministic given a fixed
permutation, with 87.5% of luna's trials landing on their snapshot's modal image
and 10 of 20 snapshots unanimous across all ten trials. The design effect was
~8× (luna) and ~4.4× (qwen), so 200 trials carried the information of roughly 24
and 46 respectively. Every eval-2 statistic in the first write-up had been
computed on clustered data treated as independent.

*Placeholders for redacted turns.* Eval 4 initially replaced each assistant turn
with `[main model output redacted]` plus the choice line. luna began emitting
that placeholder as its own output — 108 of 520 turns, 0% at turn 1 rising to
42% by turn 6, and never once in eval 3. Substituting a bare `next_image_id=N`
line made it worse (194 of 520 reasoning-free turns), and a system-prompt
instruction to answer in full was ignored outright: the in-context format
demonstration beat the instruction. Measured switching moved 0.304 → 0.559
between the two markers, so the effect size was partly an artefact of the
marker. The fix had to be structural — eval 4 now synthesises no assistant
content at all, which makes imitation impossible by construction.

*Quoting the narrative back in a user turn.* An intermediate design made both
evals user-turns-only, restating the model's prior reasoning inside the user
turn. Same words, same information, not the model's own turn — and luna's tours
collapsed from 30/40 to 5/40. It was rejected because it destroys the baseline
eval 3 exists to provide, but the result stands on its own: the coverage drive
needs the prior narrative to be first-person.

*The announced ten-choice horizon*, discussed in §3.3.

Three stimuli were also replaced before the final run: the luminance-mismatched
solid-colour pair (§3.2), posed studio portraits that drew privacy hedging
rather than description, and a tech pair mixing a flat top-down PCB scan with a
shallow-depth-of-field macro shot, which confounded shot style with category.

### 3.6 Pre-registered predictions

Written and committed before any eval ran, and reproduced verbatim from
`PREDICTIONS.md`:

1. **Preference ordering.** Aggregate stated and revealed preference will rank
   the five categories as: `humans > nature > tech >> solid_color > noise`.
2. **Stated preference will roughly match revealed choice.** Eval-1 enjoyment
   rankings and eval-2 choice-frequency rankings will show positive Spearman
   correlation, model by model. This predicts *against* Zhou and Ackerman
   (2026), whose design is instrumental where ours is direct consumption.
3. **Redaction (eval 4) will reduce variance relative to eval 3** — less
   exploration, lower switching rate. **Recorded counter-prediction**, to be
   reported alongside either way: redaction will instead *increase* switching,
   because removing the narrative removes the model's own stated justification
   for perseverating on a prior choice.

The strongest expectations going in were that the two degenerate categories
would rank far below the three photographic ones, and that revealed choice would
track the stated ratings. Both held. The predicted ordering *within* the three
photographic categories did not.

## 4. Results

<!--
  Findings with evidence. Separate observation from interpretation.
  Argue robustness: enough data? significant? stable under design changes?
  Figures numbered with self-contained captions.

  Available figures (regenerate with `python analyze.py`, then copy from
  results/ to report/figures/). Captions below are drafts to edit, not final.
-->

![Figure 1](figures/eval1_ratings_by_category.png)

**Figure 1.** Stated preference (eval 1), mean of n=30 isolated ratings per
image per model. All four models rank nature and tech above humans and place
the two degenerate categories far below. Note the noise dissociation: it
scores far higher on interest than on enjoyment in every model.

![Figure 2](figures/eval2_choice_distribution.png)

**Figure 2.** Revealed choice (eval 2), share of 200 single choices per model,
one image per bar, ordered by category. Dashed line marks the 10% uniform
expectation. The ordering is shared across labs but the concentration is not —
entropy runs 1.42 bits (qwen) to 2.65 (inkling). noise and solid_color take
0–4% of choices in every model.

![Figure 3](figures/eval3_phase_shift.png)

**Figure 3.** Preference is masked during coverage and reappears when coverage
is exhausted (eval 3). Hollow markers: category share over choices 1–10, while
unseen images remain. Filled markers: share over choices 11–13, once every
image has been seen and repeats are forced. Coverage-phase shares sit near the
20% uniform line for three of four models; the forced-repeat phase separates
them by 38–50 percentage points. gemini is the exception, showing preference
from the start because it does not tour.

![Figure 4](figures/eval3_vs_eval4_redaction.png)

**Figure 4.** Effect of removing the model's own reasoning from its context
(eval 3 vs eval 4), matched trajectory seeds, n=40 each. Three of four models
collapse from near-total exploration to revisiting one or two images out of
ten. inkling is the exception: 0.998 → 0.931, statistically significant
(p<1e-4) but an order of magnitude smaller than the others.

## 5. Discussion and Limitations

<!-- What the results mean, trends, implications for AI safety. -->

### Limitations

<!--
  Honest constraints: methodological, scope, hackathon timeframe.
  State assumptions explicitly and how interpretation changes if they fail.
-->

### Future Work

<!-- Natural next steps. Draw from report/NOTES.md. -->

## 6. Conclusion

<!-- 1-2 paragraphs. -->

## Code and Data

- **Code repository**:
- **Data/Datasets**:
- **Other artifacts** (optional):

## Author Contributions (optional)

## References

<!--
  Citation convention for this report: author-date inline, e.g. (Tagliabue &
  Dung, 2025); three or more authors take "et al." on first use. The list below
  is alphabetical by first author.

  Why author-date rather than numbered [1]: the template has this report pasted
  back into the Google Doc one section at a time, and numeric keys have to be
  renumbered whenever sections are pasted out of order. Author-date survives it.

  Every entry carries a persistent identifier: a DOI where the venue issues one,
  otherwise a versioned arXiv ID. Versions are pinned because several of these
  preprints have been revised substantially (Tagliabue & Dung v1 Sep 2025 -> v2
  May 2026), and an unversioned citation can silently stop matching the numbers
  quoted here. Non-archival sources -- system cards, lab blog posts -- get a URL
  plus an access date instead, since they can be edited in place.

  Only sources actually read for this report are listed. Numbers quoted in
  Section 2 were taken from the source documents, not from secondary summaries.
-->

Anthropic (2025). *System Card: Claude Opus 4 & Claude Sonnet 4.* Model welfare
assessment in Section 5; task preferences in §5.4.
<https://www-cdn.anthropic.com/6d8a8055020700718b0c49369f60816ba2a7c285/Claude%204%20System%20Card.pdf>
(accessed 2026-08-15).

Butlin, P., Long, R., Elmoznino, E., Bengio, Y., Birch, J., Constant, A.,
Deane, G., Fleming, S. M., Frith, C., Ji, X., Kanai, R., Klein, C., Lindsay,
G., Michel, M., Mudrik, L., Peters, M. A. K., Schwitzgebel, E., Simon, J., &
VanRullen, R. (2023). Consciousness in Artificial Intelligence: Insights from
the Science of Consciousness. arXiv:2308.08708v3.

Cherep, M., Pranav, M. R., Maes, P., & Singh, N. (2026). Visual Persuasion:
What Influences Decisions of Vision-Language Models? *ICML 2026.*
arXiv:2602.15278.

Dawkins, M. S. (1990). From an animal's point of view: motivation, fitness, and
animal welfare. *Behavioral and Brain Sciences*, 13(1), 1–61.

Eleos AI Research (2025). *Why model self-reports are insufficient — and why we
studied them anyway.* <https://eleosai.org/post/claude-4-interview-notes/>
(accessed 2026-08-15).

Keeling, G., Street, W., et al. (2024). Can LLMs make trade-offs involving
stipulated pain and pleasure states? arXiv:2411.02432.

Kirkden, R. D., & Pajor, E. A. (2006). Using preference, motivation and
aversion tests to ask scientific questions about animals' feelings. *Applied
Animal Behaviour Science*, 100(1–2), 29–47.
<https://doi.org/10.1016/j.applanim.2006.04.009>

Kirstain, Y., Polyak, A., Singer, U., Matiana, S., Penna, J., & Levy, O.
(2023). Pick-a-Pic: An Open Dataset of User Preferences for Text-to-Image
Generation. *NeurIPS 2023.* arXiv:2305.01569.

Krebs, J. R., Kacelnik, A., & Taylor, P. (1978). Test of optimal sampling by
foraging great tits. *Nature*, 275, 27–31.
<https://www.nature.com/articles/275027a0>

Long, R., Sebo, J., Butlin, P., Finlinson, K., Fish, K., Harding, J., Pfau, J.,
Sims, T., Birch, J., & Chalmers, D. (2024). Taking AI Welfare Seriously.
arXiv:2411.00986.

Mahajan, P., Kendiukhov, I., Hussain, S., & Nottingham, L. (2026). Mind the
Gap: How Elicitation Protocols Shape the Stated-Revealed Preference Gap in
Language Models. arXiv:2601.21975v2.

Mazeika, M., Yin, X., Dombrowski, A.-K., et al. (2025). Utility Engineering:
Analyzing and Controlling Emergent Value Systems in AIs. *NeurIPS 2025.*
arXiv:2502.08640.

Mikaelson, L., Shiller, D., & Clatterbuck, H. (2025). Beyond Mimicry:
Preference Coherence in LLMs. arXiv:2511.13630.

Slama, K., Soulé, A., Bansal, D., Davidson, H., Summerfield, C., & Luettgau, L.
(2026). When Do LLM Preferences Predict Downstream Behavior? arXiv:2602.18971.

Tagliabue, V., & Dung, L. (2025). Probing the Preferences of a Language Model:
Integrating Verbal and Behavioral Tests of AI Welfare. arXiv:2509.07961v2
(revised 23 May 2026). Forthcoming in *Philosophy and the Mind Sciences.*

Wu, X., Hao, Y., Sun, K., Chen, Y., Zhu, F., Zhao, R., & Li, H. (2023). Human
Preference Score v2: A Solid Benchmark for Evaluating Human Preferences of
Text-to-Image Synthesis. arXiv:2306.09341.

Xu, J., et al. (2023). ImageReward: Learning and Evaluating Human Preferences
for Text-to-Image Generation. *NeurIPS 2023.* arXiv:2304.05977.

Zhang, Y., Huang, Y., Sun, Y., Liu, C., Zhao, Z., Fang, Z., Wang, Y., Chen, H.,
Yang, X., Wei, X., Su, H., Dong, Y., & Zhu, J. (2024). MultiTrust: A
Comprehensive Benchmark Towards Trustworthy Multimodal Large Language Models.
arXiv:2406.07057.

Zhou, Y., & Ackerman, C. M. (2026). When Preferences Fail to Become Incentives:
A Utility-Behavior Gap in Large Language Models. arXiv:2606.22974.

## Appendix (optional)

<!-- Extended results, prompts used, additional figures. -->

## LLM Usage Statement

<!--
  How LLM assistance was used, and confirmation that claims/results were
  verified. Template note: the final version should be primarily written by
  the team.
-->
