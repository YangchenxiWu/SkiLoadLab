from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_float(x: object) -> float:
    val = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    return float(val) if pd.notna(val) else float("nan")


def _interval_iou(
    baseline_start: pd.Timestamp,
    baseline_end: pd.Timestamp,
    perturbed_start: pd.Timestamp,
    perturbed_end: pd.Timestamp,
) -> float:
    """Run-interval IoU used as segmentation stability.

    This is not an exact-match criterion. It measures the intersection-over-union
    between the baseline run time interval and the perturbed recomputed run time
    interval, so values lie on [0, 1]. A value near 0 means the perturbed run
    boundaries shifted enough to create little or no temporal overlap with the
    baseline interval.
    """
    inter = max(0.0, (min(baseline_end, perturbed_end) - max(baseline_start, perturbed_start)).total_seconds())
    union = max((max(baseline_end, perturbed_end) - min(baseline_start, perturbed_start)).total_seconds(), 1e-9)
    return float(inter / union)


def _matched_duration_fraction(
    baseline_start: pd.Timestamp,
    baseline_end: pd.Timestamp,
    perturbed_start: pd.Timestamp,
    perturbed_end: pd.Timestamp,
) -> float:
    inter = max(0.0, (min(baseline_end, perturbed_end) - max(baseline_start, perturbed_start)).total_seconds())
    baseline_duration = max((baseline_end - baseline_start).total_seconds(), 1e-9)
    return float(inter / baseline_duration)


def compare_outputs(
    baseline_df: pd.DataFrame,
    baseline_reference: dict[str, object],
    baseline_row: pd.Series,
    perturbed_row: dict[str, object],
    perturbation_metadata: dict[str, object],
    repeat_id: int,
) -> dict[str, object]:
    run_id = str(baseline_row["run_id"])
    run_uid = str(baseline_row["run_uid"])
    comparison_df = baseline_df.copy()
    replace_mask = comparison_df["run_uid"].astype(str) == run_uid
    comparison_df.loc[replace_mask, "vertical_drop_m"] = perturbed_row["vertical_drop_m"]
    comparison_df.loc[replace_mask, "impulse_hr_above_rest_bpms"] = perturbed_row["impulse_hr_above_rest_bpms"]
    comparison_df.loc[replace_mask, "combined_load_v2"] = perturbed_row["combined_load_v2"]
    comparison_df["_baseline_rank"] = pd.to_numeric(baseline_df["combined_load_v2"], errors="coerce").rank(
        method="average", ascending=False
    )
    comparison_df["_perturbed_rank"] = pd.to_numeric(comparison_df["combined_load_v2"], errors="coerce").rank(
        method="average", ascending=False
    )

    top_k = int(baseline_reference["top_k"])
    baseline_top = set(baseline_reference["baseline_top_k_run_uids"])
    perturbed_top = set(
        comparison_df.nlargest(min(top_k, len(comparison_df)), "combined_load_v2")["run_uid"].astype(str).tolist()
    )
    top_k_consistency = float(len(baseline_top & perturbed_top) / max(len(baseline_top), 1))
    rank_mask = comparison_df["_baseline_rank"].notna() & comparison_df["_perturbed_rank"].notna()
    rank_spearman = (
        float(comparison_df.loc[rank_mask, "_baseline_rank"].corr(comparison_df.loc[rank_mask, "_perturbed_rank"], method="pearson"))
        if rank_mask.sum() >= 2
        else float("nan")
    )
    run_rank_shift_abs = (
        abs(
            float(comparison_df.loc[replace_mask, "_perturbed_rank"].iloc[0])
            - float(comparison_df.loc[replace_mask, "_baseline_rank"].iloc[0])
        )
        if replace_mask.sum() == 1
        else float("nan")
    )
    mean_absolute_rank_shift = (
        float((comparison_df.loc[rank_mask, "_perturbed_rank"] - comparison_df.loc[rank_mask, "_baseline_rank"]).abs().mean())
        if rank_mask.sum() >= 1
        else float("nan")
    )

    early = comparison_df[comparison_df["subset_phase"] == "early"]["combined_load_v2"]
    late = comparison_df[comparison_df["subset_phase"] == "late"]["combined_load_v2"]
    perturbed_phase_contrast = float(late.mean() - early.mean()) if len(early) and len(late) else float("nan")
    baseline_phase_contrast = _safe_float(baseline_reference["baseline_phase_contrast_combined_load_v2"])

    baseline_start = pd.to_datetime(baseline_row["start_time_utc"], utc=True, format="mixed")
    baseline_end = pd.to_datetime(baseline_row["end_time_utc"], utc=True, format="mixed")
    perturbed_start = pd.to_datetime(perturbed_row["start_time_utc"], utc=True, format="mixed")
    perturbed_end = pd.to_datetime(perturbed_row["end_time_utc"], utc=True, format="mixed")

    out = {
        "run_id": run_id,
        "run_uid": run_uid,
        "session_label": str(baseline_row["session_label"]),
        "subset_name": str(baseline_row["subset_name"]),
        "perturbation_type": perturbation_metadata["perturbation_type"],
        "perturbation_level": float(perturbation_metadata["perturbation_level"]),
        "perturbation_level_label": str(perturbation_metadata.get("perturbation_level_label", perturbation_metadata["perturbation_level"])),
        "repeat_id": int(repeat_id),
        "seed": int(perturbation_metadata["seed"]),
        "top_k_used": int(baseline_reference["top_k"]),
        "pipeline_status": str(perturbed_row.get("pipeline_status", "unknown")),
        "failure_reason": str(perturbed_row.get("failure_reason", "")),
        "baseline_duration_s": _safe_float(baseline_row["duration_s"]),
        "baseline_vertical_drop_m": _safe_float(baseline_row["vertical_drop_m"]),
        "baseline_impulse_hr_above_rest_bpms": _safe_float(baseline_row["impulse_hr_above_rest_bpms"]),
        "baseline_combined_load_v2": _safe_float(baseline_row["combined_load_v2"]),
        "perturbed_duration_s": _safe_float(perturbed_row["duration_s"]),
        "perturbed_vertical_drop_m": _safe_float(perturbed_row["vertical_drop_m"]),
        "perturbed_impulse_hr_above_rest_bpms": _safe_float(perturbed_row["impulse_hr_above_rest_bpms"]),
        "perturbed_combined_load_v2": _safe_float(perturbed_row["combined_load_v2"]),
        "segmentation_stability": _interval_iou(baseline_start, baseline_end, perturbed_start, perturbed_end),
        "matched_duration_fraction": _matched_duration_fraction(
            baseline_start, baseline_end, perturbed_start, perturbed_end
        ),
        "boundary_shift_start_s": abs((perturbed_start - baseline_start).total_seconds()),
        "boundary_shift_end_s": abs((perturbed_end - baseline_end).total_seconds()),
        "boundary_shift_mean_s": (
            abs((perturbed_start - baseline_start).total_seconds())
            + abs((perturbed_end - baseline_end).total_seconds())
        )
        / 2.0,
        "vertical_drop_error_m": _safe_float(perturbed_row["vertical_drop_m"]) - _safe_float(baseline_row["vertical_drop_m"]),
        "vertical_drop_abs_error_m": abs(_safe_float(perturbed_row["vertical_drop_m"]) - _safe_float(baseline_row["vertical_drop_m"])),
        "cl_alpha_deviation": _safe_float(perturbed_row["combined_load_v2"]) - _safe_float(baseline_row["combined_load_v2"]),
        "cl_alpha_abs_deviation": abs(_safe_float(perturbed_row["combined_load_v2"]) - _safe_float(baseline_row["combined_load_v2"])),
        "top_k_consistency": top_k_consistency,
        "rank_spearman": rank_spearman,
        "mean_absolute_rank_shift": mean_absolute_rank_shift,
        "run_rank_shift_abs": run_rank_shift_abs,
        "phase_contrast_deviation": _safe_float(perturbed_phase_contrast) - baseline_phase_contrast,
        "phase_contrast_abs_deviation": abs(_safe_float(perturbed_phase_contrast) - baseline_phase_contrast),
    }

    for key, value in perturbation_metadata.items():
        if key not in out:
            out[f"meta_{key}"] = value

    return out
