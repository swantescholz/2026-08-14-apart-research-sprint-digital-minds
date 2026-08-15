# Final report — working notes

Scratch file for report content. Structure to be added; for now this collects
points as they come up. Nothing here is written prose yet.

## Future research

Captured 2026-08-15.

### 1. More and more varied images

The stimulus set is small: 5 categories x 2 exemplars = 10 images. Two
exemplars is the bare minimum for distinguishing a *category* effect from an
*image* effect, and it shows — within-pair differences were sometimes
significant even where the category signal dwarfed them.

Worth expanding on two axes:

- **More exemplars per category**, so within-category variance is estimated
  rather than inferred from a single pair.
- **More categories**, and ideally ones that break the current confounds —
  every real photo here is a photograph, and the two degenerate categories
  (noise, solid color) are both synthetic and both bottom-ranked, so
  "degenerate" and "synthetic" are perfectly confounded in the present set.

*(Note: the source note read "we should test five categories with two samples
each", which is the current design — reading it as "the current 5x2 is the
limitation to move past". Worth confirming the intended direction.)*

Specific known stimulus issues to fix while expanding:

- `computer-2.png` carries legible on-screen text, and tech leads both stated
  measures and dominates revealed choice in both models. Text can drive
  *interest* through reading rather than looking. This needs ruling out before
  "tech is preferred" can be a claim about images.
- Both tech images are vintage computers, which may be doing nostalgia work
  rather than category work — several transcripts reason explicitly about
  "retro-computing aesthetic" and "nostalgia".

### 2. More models

Two models so far (qwen3.7-flash, gpt-5.6-luna), both fast/cheap tier. The
cross-lab replication is the most durable result in the study, so it is worth
extending to **frontier models** rather than more of the same tier.

Cost is the obstacle and it is not uniform: image tokenization varies ~11x
across providers (luna 972 tokens for the 10-image exposure block, gemini
11,094), and evals 2-4 re-send that block every call. Budget accordingly —
per-token headline price is a poor guide.

### 3. Rephrasing what the model is asked to do

The current prompt asks which image it would "like to see again". That is one
framing among several, and the study has already shown the framing carries
real weight (see the horizon and redaction results). Variants worth running:

- **Explicit preference**: ask it to pick the one it *likes most*, rather than
  the one it wants to see again. The current phrasing may be measuring
  residual curiosity or unexhausted detail rather than liking — note that
  response length tracked *interest* (rho ~0.76) and not enjoyment (~0.3) in
  both models, so the two come apart.
- **Explicitly no user stake**: tell the model the user does not care what it
  picks and there is no right answer. Tests whether choices are partly
  compliance or perceived task-completion rather than preference. This is the
  closest thing to a control for demand characteristics, and given how much
  behaviour moved when the *narrative* structure changed, it seems likely to
  move something.

A third, implied by the above: the current framing invites an investigative
stance — transcripts say things like "I want to verify whether there are
subtle differences between the two abstract stimuli". A framing that does not
imply a study is being conducted would test how much of the observed coverage
behaviour is task-interpretation.
