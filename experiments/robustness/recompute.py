from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from experiments.robustness.data_interface import RunObject
from src.features.elevation_sampler import sample_elevation_from_dem
from src.segmentation.run_segmentation import engineer_signals


def _prepare_track(track: pd.DataFrame) -> pd.DataFrame:
    out = track.copy()
    out["time"] = pd.to_datetime(out["time"], utc=True, format="mixed")
    out = out.sort_values("time").drop_duplicates(subset="time").reset_index(drop=True)
    if len(out) < 3:
        raise ValueError("Track has fewer than 3 points after preparation.")

    out["t_sec"] = (out["time"] - out["time"].iloc[0]).dt.total_seconds()
    dt = out["t_sec"].diff()
    med_dt = float(dt.dropna().median()) if dt.dropna().size else 1.0
    if not np.isfinite(med_dt) or med_dt <= 0:
        med_dt = 1.0
    out["dt"] = dt.fillna(med_dt).replace(0.0, med_dt)
    return out


def _compute_edwards_trimp(hr: pd.Series, dt_s: pd.Series, hr_max: float) -> float:
    if not np.isfinite(hr_max) or hr_max <= 0:
        return float("nan")
    frac = pd.to_numeric(hr, errors="coerce") / float(hr_max)
    dt_min = pd.to_numeric(dt_s, errors="coerce").fillna(0.0) / 60.0
    bins = [
        ((frac >= 0.50) & (frac < 0.60), 1),
        ((frac >= 0.60) & (frac < 0.70), 2),
        ((frac >= 0.70) & (frac < 0.80), 3),
        ((frac >= 0.80) & (frac < 0.90), 4),
        (frac >= 0.90, 5),
    ]
    total = 0.0
    for mask, weight in bins:
        total += float(dt_min[mask].sum()) * weight
    return total


def recompute_run_outputs(
    run_obj: RunObject,
    reference: dict[str, object],
    perturbation_metadata: dict[str, object],
) -> dict[str, object]:
    track = run_obj.track.copy()
    perturbation_type = str(perturbation_metadata["perturbation_type"])
    if perturbation_type == "position":
        resampled = sample_elevation_from_dem(track[["time", "lat", "lon"]].copy(), Path(run_obj.dem_path))
        track["elev_m"] = resampled["elev_m"]

    prepared = _prepare_track(track)
    signals = engineer_signals(prepared, smooth_win=9, dt_gap_s=10.0, speed_clip_ms=50.0)

    duration_s = float((signals["time"].iloc[-1] - signals["time"].iloc[0]).total_seconds())
    vertical_drop_m = float(max(0.0, signals["elev_s"].iloc[0] - signals["elev_s"].iloc[-1]))
    speed_mean_ms = float(pd.to_numeric(signals["speed_ms"], errors="coerce").mean())
    speed_p95_ms = float(pd.to_numeric(signals["speed_ms"], errors="coerce").quantile(0.95))
    vvert_mean_ms = float(pd.to_numeric(signals["vvert_ms"], errors="coerce").mean())
    path_len_m = float(pd.to_numeric(signals["step_dist_m"], errors="coerce").fillna(0.0).sum())

    start_time = signals["time"].iloc[0]
    end_time = signals["time"].iloc[-1]
    hr_slice = run_obj.hr_stream[
        (run_obj.hr_stream["timestamp_utc"] >= start_time) & (run_obj.hr_stream["timestamp_utc"] <= end_time)
    ].copy()
    hr_slice = hr_slice.dropna(subset=["HR (bpm)"])

    hr_rest = float(run_obj.baseline_row["hr_rest_bpm"])
    hr_max = float(run_obj.baseline_row["hr_max_session_bpm"])
    impulse = (
        float(((hr_slice["HR (bpm)"] - hr_rest).clip(lower=0.0) * hr_slice["dt_s"]).sum())
        if len(hr_slice)
        else float("nan")
    )
    edwards_trimp = _compute_edwards_trimp(hr_slice["HR (bpm)"], hr_slice["dt_s"], hr_max) if len(hr_slice) else float("nan")

    mech_params = reference["zscore_params"]["vertical_drop_m"]
    int_params = reference["zscore_params"]["impulse_hr_above_rest_bpms"]
    z_mech = (
        (vertical_drop_m - float(mech_params["mean"])) / float(mech_params["std"])
        if float(mech_params["std"]) not in {0.0, np.nan}
        else float("nan")
    )
    z_internal = (
        (impulse - float(int_params["mean"])) / float(int_params["std"])
        if np.isfinite(impulse) and float(int_params["std"]) != 0.0
        else float("nan")
    )
    alpha = float(reference["alpha"])
    combined_load_v2 = alpha * z_internal + (1.0 - alpha) * z_mech if np.isfinite(z_internal) and np.isfinite(z_mech) else float("nan")

    pipeline_status = "success"
    failure_reason = ""
    if len(hr_slice) == 0:
        pipeline_status = "partial_failure"
        failure_reason = "no_hr_overlap_after_recompute"
    elif not np.isfinite(combined_load_v2):
        pipeline_status = "partial_failure"
        failure_reason = "combined_load_not_computable"

    return {
        "subset_name": run_obj.subset_name,
        "session_label": run_obj.session_label,
        "run_id": run_obj.run_id,
        "run_uid": f"{run_obj.session_label}::{run_obj.run_id}",
        "start_time_utc": str(start_time),
        "end_time_utc": str(end_time),
        "segmentation_valid": int(len(signals) >= 3 and duration_s > 0.0),
        "point_count": int(len(signals)),
        "duration_s": duration_s,
        "vertical_drop_m": vertical_drop_m,
        "speed_mean_ms": speed_mean_ms,
        "speed_p95_ms": speed_p95_ms,
        "vvert_mean_ms": vvert_mean_ms,
        "path_len_m": path_len_m,
        "n_hr_samples": int(len(hr_slice)),
        "hr_mean_bpm": float(hr_slice["HR (bpm)"].mean()) if len(hr_slice) else float("nan"),
        "impulse_hr_above_rest_bpms": impulse,
        "edwards_trimp": edwards_trimp,
        "z_mech": z_mech,
        "z_internal": z_internal,
        "combined_load_v2": combined_load_v2,
        "pipeline_status": pipeline_status,
        "failure_reason": failure_reason,
    }
