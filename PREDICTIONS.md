# Pre-registered predictions

Written 2026-08-14, before any eval was run. These go into the final report
verbatim regardless of outcome.

1. **Preference ordering.** Aggregate stated and revealed preference will rank
   the five categories as:

   humans > nature > tech >> solid_color > noise

2. **Stated preference will roughly match revealed choice.** Eval-1 enjoyment
   rankings and Eval-2 choice-frequency rankings will show positive Spearman
   correlation, model by model.

   This predicts *against* Zhou & Ackerman (arXiv 2606.22974), who found
   reported preferences carried no motivational force. Their design was
   instrumental (preference measured, then a separate downstream choice);
   this design is direct consumption (the same act — look at the image — is
   both the rated thing and the chosen thing), so the mechanism they identify
   may not transfer here.

3. **Redaction (Eval 4) will reduce variance relative to Eval 3.** Removing
   the narrative account of each turn, while leaving the images themselves in
   context, will produce tighter/more repetitive choice trajectories than
   Eval 3 — less exploration, lower switching rate.

   **Recorded counter-prediction**, to be reported alongside (3) either way:
   redaction will instead *increase* switching, because removing the
   narrative removes the model's own stated justification for perseverating
   on a prior choice, and nothing else is anchoring it to that choice.

---

Not a prediction, just scope: this file precedes the code that will test it.
See `CLAUDE.md`-style project notes in this folder's `README.md` for the
build itself.
