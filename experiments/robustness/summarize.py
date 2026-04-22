from __future__ import annotations

import pandas as pd


SUMMARY_METRICS = [
    "segmentation_stability",
    "matched_duration_fraction",
    "boundary_shift_mean_s",
    "vertical_drop_abs_error_m",
    "cl_alpha_abs_deviation",
    "top_k_consistency",
    "rank_spearman",
    "mean_absolute_rank_shift",
    "run_rank_shift_abs",
    "phase_contrast_abs_deviation",
]


def build_summary_table(long_df: pd.DataFrame) -> pd.DataFrame:
    melted = long_df.melt(
        id_vars=["subset_name", "perturbation_type", "perturbation_level", "perturbation_level_label", "top_k_used"],
        value_vars=SUMMARY_METRICS,
        var_name="metric_name",
        value_name="metric_value",
    )
    grouped = melted.groupby(
        ["subset_name", "perturbation_type", "perturbation_level", "perturbation_level_label", "top_k_used", "metric_name"],
        dropna=False,
    )["metric_value"]
    summary = grouped.agg(
        n="count",
        median="median",
        mean="mean",
        sd="std",
    ).reset_index()

    q1 = grouped.quantile(0.25).reset_index(name="q1")
    q3 = grouped.quantile(0.75).reset_index(name="q3")
    merge_cols = ["subset_name", "perturbation_type", "perturbation_level", "perturbation_level_label", "top_k_used", "metric_name"]
    summary = summary.merge(q1, on=merge_cols)
    summary = summary.merge(q3, on=merge_cols)
    summary["iqr"] = summary["q3"] - summary["q1"]
    return summary
