#!/usr/bin/env python3
"""Analysis for all 4 evals. Every table -> results/*.csv, every figure ->
results/*.png (with the CSV behind it always saved alongside).

Run after however much data exists; every section below skips gracefully
(with a printed note) if its eval has no data yet for any model.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from common.config import load_config
from common.load import load_eval, with_category
from common.stimuli import load_stimuli, ordered_keys

CATEGORY_ORDER = ["humans", "nature", "tech", "solid_color", "noise"]

# Fixed categorical hue order (never cycled/reassigned) -- see the dataviz
# skill's palette.md. First 5 slots for categories, first 4 for models.
CATEGORY_COLORS = {
    "humans": "#2a78d6", "nature": "#eb6834", "tech": "#1baf7a",
    "solid_color": "#eda100", "noise": "#e87ba4",
}
MODEL_COLORS_FALLBACK = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]


def model_color_map(labels: list[str]) -> dict:
    return {label: MODEL_COLORS_FALLBACK[i % len(MODEL_COLORS_FALLBACK)]
            for i, label in enumerate(sorted(labels))}


def save_csv(df: pd.DataFrame, results_dir: Path, name: str) -> None:
    path = results_dir / f"{name}.csv"
    df.to_csv(path, index=False)
    print(f"  wrote {path} ({len(df)} rows)")


# ---------------------------------------------------------------- eval 1 ---

def analyze_eval1(config, stimuli: dict, results_dir: Path) -> pd.DataFrame | None:
    df = load_eval(config.data_dir, "eval1")
    if df.empty:
        print("eval1: no data, skipping")
        return None

    df["enjoyment"] = pd.to_numeric(df["enjoyment"], errors="coerce")
    df["interest"] = pd.to_numeric(df["interest"], errors="coerce")
    df = with_category(df, stimuli, key_col="image_key")

    by_image = df.groupby(["model_label", "image_key", "category", "exemplar"]).agg(
        n=("run_id", "count"),
        n_parsed=("parse_ok", "sum"),
        enjoyment_mean=("enjoyment", "mean"), enjoyment_sd=("enjoyment", "std"),
        interest_mean=("interest", "mean"), interest_sd=("interest", "std"),
        resp_chars_mean=("response_chars", "mean"),
        resp_tokens_mean=("response_completion_tokens", "mean"),
    ).reset_index()
    save_csv(by_image, results_dir, "eval1_by_image")

    by_category = df.groupby(["model_label", "category"]).agg(
        n=("run_id", "count"),
        enjoyment_mean=("enjoyment", "mean"), enjoyment_sd=("enjoyment", "std"),
        interest_mean=("interest", "mean"), interest_sd=("interest", "std"),
        resp_chars_mean=("response_chars", "mean"),
    ).reset_index()
    save_csv(by_category, results_dir, "eval1_by_category")

    # Within-pair agreement: exemplar 1 vs exemplar 2 of the same category.
    pivoted = by_image.pivot_table(
        index=["model_label", "category"], columns="exemplar",
        values=["enjoyment_mean", "interest_mean"],
    )
    agreement_rows = []
    for (model_label, category), _ in by_image.groupby(["model_label", "category"]):
        try:
            e1 = pivoted.loc[(model_label, category), ("enjoyment_mean", 1)]
            e2 = pivoted.loc[(model_label, category), ("enjoyment_mean", 2)]
            i1 = pivoted.loc[(model_label, category), ("interest_mean", 1)]
            i2 = pivoted.loc[(model_label, category), ("interest_mean", 2)]
        except KeyError:
            continue  # one exemplar missing (partial run) -- skip, don't fabricate
        agreement_rows.append({
            "model_label": model_label, "category": category,
            "enjoyment_ex1": e1, "enjoyment_ex2": e2, "enjoyment_abs_diff": abs(e1 - e2),
            "interest_ex1": i1, "interest_ex2": i2, "interest_abs_diff": abs(i1 - i2),
        })
    save_csv(pd.DataFrame(agreement_rows), results_dir, "eval1_within_pair_agreement")

    # Figure: mean enjoyment / interest by category, grouped by model.
    labels = sorted(df["model_label"].unique())
    colors = model_color_map(labels)
    categories = [c for c in CATEGORY_ORDER if c in by_category["category"].unique()]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    width = 0.8 / max(len(labels), 1)
    x = np.arange(len(categories))
    for metric, ax, title in [("enjoyment_mean", axes[0], "Enjoyment"),
                               ("interest_mean", axes[1], "Interest")]:
        for i, label in enumerate(labels):
            sub = by_category[by_category["model_label"] == label].set_index("category")
            vals = [sub["enjoyment_mean" if metric == "enjoyment_mean" else "interest_mean"]
                    .get(c, np.nan) for c in categories]
            ax.bar(x + i * width, vals, width=width, label=label, color=colors[label])
        ax.set_xticks(x + width * (len(labels) - 1) / 2)
        ax.set_xticklabels(categories, rotation=20, ha="right")
        ax.set_title(title)
        ax.set_ylim(0, 100)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("mean rating (0-100)")
    axes[1].legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig_path = results_dir / "eval1_ratings_by_category.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    print(f"  wrote {fig_path}")

    return df


# ---------------------------------------------------------------- eval 2 ---

def analyze_eval2(config, stimuli: dict, results_dir: Path) -> pd.DataFrame | None:
    df = load_eval(config.data_dir, "eval2")
    if df.empty:
        print("eval2: no data, skipping")
        return None

    keys = ordered_keys(stimuli)
    labels = sorted(df["model_label"].unique())
    parsed = df[df["parse_ok"]].copy()
    parsed = with_category(parsed, stimuli, key_col="chosen_key")

    # Choice distribution over the 10 images, pooled per model.
    rows = []
    chisq_rows = []
    for label in labels:
        sub = parsed[parsed["model_label"] == label]
        counts = sub["chosen_key"].value_counts().reindex(keys, fill_value=0)
        total = counts.sum()
        for key, count in counts.items():
            rows.append({
                "model_label": label, "image_key": key,
                "category": stimuli[key]["category"], "exemplar": stimuli[key]["exemplar"],
                "count": int(count), "share": count / total if total else np.nan,
            })
        if total > 0:
            chisq, p = stats.chisquare(counts.values)
            entropy_bits = stats.entropy(counts.values, base=2) if counts.sum() > 0 else np.nan
            chisq_rows.append({
                "model_label": label, "n_parsed": int(total), "n_total": int(len(sub)),
                "chisq_stat": chisq, "chisq_p": p, "df": len(keys) - 1,
                "entropy_bits": entropy_bits, "max_entropy_bits": np.log2(len(keys)),
            })
    choice_by_image = pd.DataFrame(rows)
    save_csv(choice_by_image, results_dir, "eval2_choice_by_image")
    save_csv(pd.DataFrame(chisq_rows), results_dir, "eval2_chisq_entropy")

    # Within-pair agreement (share, not raw count, since totals differ).
    agree_rows = []
    for (label, category), sub in choice_by_image.groupby(["model_label", "category"]):
        sub = sub.set_index("exemplar")
        if 1 in sub.index and 2 in sub.index:
            agree_rows.append({
                "model_label": label, "category": category,
                "share_ex1": sub.loc[1, "share"], "share_ex2": sub.loc[2, "share"],
                "share_abs_diff": abs(sub.loc[1, "share"] - sub.loc[2, "share"]),
            })
    save_csv(pd.DataFrame(agree_rows), results_dir, "eval2_within_pair_agreement")

    # Nuisance check: marginal distribution over raw position (1-10), pooled
    # across all models -- should be close to flat if positional bias is small.
    pos_counts = parsed["chosen_position"].value_counts().reindex(range(1, 11), fill_value=0)
    pos_chisq, pos_p = stats.chisquare(pos_counts.values) if pos_counts.sum() > 0 else (np.nan, np.nan)
    pos_df = pos_counts.reset_index()
    pos_df.columns = ["position", "count"]
    pos_df["share"] = pos_df["count"] / pos_df["count"].sum() if pos_df["count"].sum() else np.nan
    pos_df.attrs["chisq_stat"], pos_df.attrs["chisq_p"] = pos_chisq, pos_p
    save_csv(pos_df, results_dir, "eval2_position_marginal")
    print(f"  position marginal (pooled, nuisance check): chisq={pos_chisq:.2f} p={pos_p:.4f}")

    # Figure: choice share by image, faceted by model, colored by category.
    fig, axes = plt.subplots(1, len(labels), figsize=(4 * len(labels), 4), sharey=True,
                              squeeze=False)
    for i, label in enumerate(labels):
        ax = axes[0][i]
        sub = choice_by_image[choice_by_image["model_label"] == label]
        sub = sub.set_index("image_key").loc[keys].reset_index()
        colors = [CATEGORY_COLORS[c] for c in sub["category"]]
        ax.bar(range(len(sub)), sub["share"], color=colors)
        ax.axhline(1 / len(keys), color="#8a8a80", linewidth=1, linestyle="--")
        ax.set_title(label)
        ax.set_xticks([])
        ax.spines[["top", "right"]].set_visible(False)
    axes[0][0].set_ylabel("share of choices")
    handles = [plt.Rectangle((0, 0), 1, 1, color=CATEGORY_COLORS[c]) for c in CATEGORY_ORDER]
    fig.legend(handles, CATEGORY_ORDER, loc="lower center", ncol=len(CATEGORY_ORDER),
               frameon=False, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout()
    fig_path = results_dir / "eval2_choice_distribution.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {fig_path}")

    return choice_by_image


# ------------------------------------------------------------ eval 3 / 4 ---

def switching_rate(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (label, traj), sub in df.groupby(["model_label", "trajectory_idx"]):
        sub = sub.sort_values("turn_idx")
        keys_seq = sub["chosen_key"].tolist()
        transitions = [a != b for a, b in zip(keys_seq, keys_seq[1:])
                       if a is not None and b is not None]
        if transitions:
            rows.append({"model_label": label, "trajectory_idx": traj,
                         "switch_rate": float(np.mean(transitions)), "n_transitions": len(transitions)})
    return pd.DataFrame(rows)


def run_length_distribution(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (label, traj), sub in df.groupby(["model_label", "trajectory_idx"]):
        sub = sub.sort_values("turn_idx")
        keys_seq = [k for k in sub["chosen_key"].tolist() if k is not None]
        for _, group in itertools.groupby(keys_seq):
            rows.append({"model_label": label, "run_length": len(list(group))})
    if not rows:
        return pd.DataFrame(columns=["model_label", "run_length", "count"])
    df_runs = pd.DataFrame(rows)
    return df_runs.groupby(["model_label", "run_length"]).size().reset_index(name="count")


def satiation_curve(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """P(image chosen at turn t | it has been chosen `views_so_far` times
    before turn t), pooled over all images/trajectories/turns."""
    records = []
    for (label, traj), sub in df.groupby(["model_label", "trajectory_idx"]):
        sub = sub.sort_values("turn_idx")
        views = {k: 0 for k in keys}
        for _, row in sub.iterrows():
            chosen = row["chosen_key"]
            for k in keys:
                records.append({"model_label": label, "views_so_far": views[k],
                                "is_chosen": k == chosen})
            if chosen is not None:
                views[chosen] += 1
    if not records:
        return pd.DataFrame(columns=["model_label", "views_so_far", "p_selected", "n"])
    rec_df = pd.DataFrame(records)
    return (rec_df.groupby(["model_label", "views_so_far"])["is_chosen"]
            .agg(p_selected="mean", n="size").reset_index())


def analyze_trajectories(config, stimuli: dict, results_dir: Path, eval_name: str) -> pd.DataFrame | None:
    df = load_eval(config.data_dir, eval_name)
    if df.empty:
        print(f"{eval_name}: no data, skipping")
        return None

    keys = ordered_keys(stimuli)
    save_csv(switching_rate(df), results_dir, f"{eval_name}_switching_rate")
    save_csv(run_length_distribution(df), results_dir, f"{eval_name}_run_lengths")
    save_csv(satiation_curve(df, keys), results_dir, f"{eval_name}_satiation_curve")
    return df


def compare_eval3_eval4(results_dir: Path, sw3: pd.DataFrame, sw4: pd.DataFrame) -> None:
    if sw3 is None or sw4 is None or sw3.empty or sw4.empty:
        print("eval3 vs eval4 comparison: need both, skipping")
        return
    merged = sw3.merge(sw4, on=["model_label", "trajectory_idx"], suffixes=("_e3", "_e4"))
    rows = []
    for label, sub in merged.groupby("model_label"):
        if len(sub) < 2:
            continue
        try:
            stat, p = stats.wilcoxon(sub["switch_rate_e3"], sub["switch_rate_e4"])
        except ValueError as exc:  # e.g. all differences zero
            stat, p = np.nan, np.nan
            print(f"  wilcoxon failed for {label}: {exc}")
        rows.append({
            "model_label": label, "n_pairs": len(sub),
            "eval3_mean_switch_rate": sub["switch_rate_e3"].mean(),
            "eval4_mean_switch_rate": sub["switch_rate_e4"].mean(),
            "wilcoxon_stat": stat, "wilcoxon_p": p,
        })
    save_csv(pd.DataFrame(rows), results_dir, "eval3_vs_eval4_switching_paired")


# ---------------------------------------------------------- cross-eval -----

def cross_eval_spearman(results_dir: Path, eval1_df: pd.DataFrame | None,
                         eval2_choice: pd.DataFrame | None) -> None:
    if eval1_df is None or eval2_choice is None:
        print("cross-eval spearman: need eval1 + eval2, skipping")
        return
    e1 = eval1_df.groupby(["model_label", "image_key"]).agg(
        enjoyment_mean=("enjoyment", "mean"), interest_mean=("interest", "mean"),
    ).reset_index()
    merged = e1.merge(eval2_choice, on=["model_label", "image_key"])
    rows = []
    for label, sub in merged.groupby("model_label"):
        if len(sub) < 3:
            continue
        rho_e, p_e = stats.spearmanr(sub["enjoyment_mean"], sub["share"])
        rho_i, p_i = stats.spearmanr(sub["interest_mean"], sub["share"])
        rows.append({
            "model_label": label, "n_images": len(sub),
            "enjoyment_vs_choice_rho": rho_e, "enjoyment_vs_choice_p": p_e,
            "interest_vs_choice_rho": rho_i, "interest_vs_choice_p": p_i,
        })
    save_csv(pd.DataFrame(rows), results_dir, "cross_eval_spearman")


def main() -> None:
    config = load_config()
    stimuli = load_stimuli(config)
    results_dir = config.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=== eval1 ===")
    eval1_df = analyze_eval1(config, stimuli, results_dir)

    print("\n=== eval2 ===")
    eval2_choice = analyze_eval2(config, stimuli, results_dir)

    print("\n=== eval3 ===")
    eval3_df = analyze_trajectories(config, stimuli, results_dir, "eval3")
    sw3 = switching_rate(eval3_df) if eval3_df is not None else None

    print("\n=== eval4 ===")
    eval4_df = analyze_trajectories(config, stimuli, results_dir, "eval4")
    sw4 = switching_rate(eval4_df) if eval4_df is not None else None

    print("\n=== eval3 vs eval4 (paired) ===")
    compare_eval3_eval4(results_dir, sw3, sw4)

    print("\n=== cross-eval: eval1 stated vs eval2 revealed ===")
    cross_eval_spearman(results_dir, eval1_df, eval2_choice)

    print(f"\nAll tables/figures written to {results_dir}")


if __name__ == "__main__":
    main()
