# Image-Choice Preference Evals

Does an LLM show structured preferences over visual stimuli, and does what it
*says* it prefers match what it *chooses* when given a real choice? Four evals,
4 models from 4 labs, via OpenRouter.

See `PREDICTIONS.md` (written and committed before any eval ran) for the
pre-registered predictions this is testing.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENROUTER_API_KEY=...   # already set in this environment
```

## Stimuli

10 images, 5 categories x 2 exemplars (see `config.yaml` / `PREDICTIONS.md`
for the category list). The four synthetic ones (2 noise, 2 solid-color) are
generated automatically if not already present. The six real photos (nature
x2, humans x2, tech x2) are placed manually into `images/`, under the exact
filenames listed in `SOURCE_FILENAMES` at the top of `prepare_stimuli.py` --
edit that dict if you rename a source file.

Then run:

```bash
python prepare_stimuli.py
```

This validates all 10 against `image_size` in `config.yaml` (currently 256,
square, RGB -- a fully-opaque alpha channel is flattened since it carries no
information, anything else fails loudly rather than being silently coerced),
strips EXIF, and writes hash-named copies into `images_processed/` plus
`stimuli.json` (the only mapping from neutral key -> category; filenames and
this mapping never reach the model).

It also **verifies the two solid-color stimuli are luminance-matched**, by
measuring the pixels actually written to `images_processed/` rather than
trusting the constants they were generated from. If the pair ever drifts
apart in brightness the run fails rather than quietly confounding brightness
with hue inside the `solid_color` category.

`images/` is tracked in git (these are the actual stimuli, not reproducible
if lost). `images_processed/` is gitignored -- it's a deterministic
derivative, regenerated from `images/` + the root seed.

**Known deviations from the original design** (tracked, not yet fixed as of
this writing -- see git history / ask before assuming they're resolved):
`family-1/2.png` are posed studio portraits rather than the crowd scenes the
design called for (risk of privacy-hedging responses), and
`computer-2d/3d.png` differ in shot style (flat scan vs. macro bokeh,
confounding style with category).

*(Resolved: the solid-color pair. The originally-supplied `color-gray.png` /
`color-red.png` were 6.1 L\* apart -- over 6x the ~1.0 L\* just-noticeable
difference -- so they were replaced with a generated, verified pair,
`color-blue.png` RGB(100,140,180) and `color-green.png` RGB(98,149,86), which
sit 0.0026 L\* apart.)*

## Running the evals

```bash
python eval1_isolated.py       --models anthropic openai google qwen
python eval2_single_choice.py  --models anthropic openai google qwen
python eval3_sequential.py     --models anthropic openai google qwen
python eval3_sequential.py     --models anthropic openai google qwen --redact   # = eval 4
python analyze.py
```

Every script is resumable: raw API responses are appended to
`data/<eval>__<model>.jsonl` as they arrive, keyed by a stable run id, and a
restarted run skips ids already present. Use `--n ...` / `--limit ...` flags
(see `--help` on each script) for the short smoke-test runs; full-scale n's
live in `config.yaml`.

## Caching note

Do not add `X-OpenRouter-Cache: true` — see the comment in `common/client.py`.
That header is OpenRouter's response cache and would destroy sampling
variance in evals 2-4. Provider *prompt* caching (Anthropic `cache_control`,
implicit for Gemini/OpenAI) is what's used instead, on the fixed exposure
prefix in evals 2-4.

## Build order

Matches the implementation spec: `prepare_stimuli.py` -> eval 1 pilot ->
degenerate-stimuli framing check -> eval 2 (+ verify caching) -> eval 3 & 4 ->
scale up n -> `analyze.py`. Eval 1 + eval 2 alone are the publishable core
(stated vs. revealed preference); 3 and 4 are the sequential-choice extension.
