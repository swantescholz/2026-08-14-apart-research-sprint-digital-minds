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

## 3. Methods

<!--
  Replicable detail. Models, stimuli, parameters, design decisions and their
  justification. Explicitly: what we tried that did NOT work.
-->

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

## Appendix (optional)

<!-- Extended results, prompts used, additional figures. -->

## LLM Usage Statement

<!--
  How LLM assistance was used, and confirmation that claims/results were
  verified. Template note: the final version should be primarily written by
  the team.
-->
