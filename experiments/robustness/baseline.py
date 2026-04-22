from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.robustness.data_interface import RunObject
from skiloadlab.core_compare import _session_phase_labels


def _zscore_with_params(x: pd.Series, mean: float, std: float) -> pd.Series:
    if not np.isfinite(std) or std == 0:
        return x * np.nan
    return (x - mean) / std


def _run_path_len(track: pd.DataFrame) -> float:
    return float(pd.to_numeric(track["step_dist_m"], errors="coerce").fillna(0.0).sum())


def build_baseline_reference(
    run_objects: list[RunObject],
    alpha: float,
    top_k: int,
    out_dir: Path,
) -> tuple[pd.DataFrame, dict[str, object]]:
    rows: list[dict[str, object]] = []
    for run_obj in run_objects:
        row = dict(run_obj.baseline_row)
        row["subset_name"] = run_obj.subset_name
        row["run_uid"] = f"{run_obj.session_label}::{run_obj.run_id}"
        row["segmentation_valid"] = 1
        row["point_count"] = int(len(run_obj.track))
        row["path_len_m"] = _run_path_len(run_obj.track)
        rows.append(row)

    baseline = pd.DataFrame(rows).reset_index(drop=True)
    baseline["run_order"] = np.arange(1, len(baseline) + 1)
    baseline["subset_phase"] = _session_phase_labels(len(baseline)).values

    mech_mean = float(pd.to_numeric(baseline["vertical_drop_m"], errors="coerce").mean())
    mech_std = float(pd.to_numeric(baseline["vertical_drop_m"], errors="coerce").std())
    int_mean = float(pd.to_numeric(baseline["impulse_hr_above_rest_bpms"], errors="coerce").mean())
    int_std = float(pd.to_numeric(baseline["impulse_hr_above_rest_bpms"], errors="coerce").std())

    baseline["z_mech"] = _zscore_with_params(pd.to_numeric(baseline["vertical_drop_m"], errors="coerce"), mech_mean, mech_std)
    baseline["z_internal"] = _zscore_with_params(
        pd.to_numeric(baseline["impulse_hr_above_rest_bpms"], errors="coerce"), int_mean, int_std
    )
    baseline["combined_load_v2"] = alpha * baseline["z_internal"] + (1.0 - alpha) * baseline["z_mech"]

    top_n = min(int(top_k), len(baseline))
    top_k_run_uids = baseline.nlargest(top_n, "combined_load_v2")["run_uid"].astype(str).tolist()

    early = baseline[baseline["subset_phase"] == "early"]["combined_load_v2"]
    late = baseline[baseline["subset_phase"] == "late"]["combined_load_v2"]
    phase_contrast = float(late.mean() - early.mean()) if len(early) and len(late) else float("nan")

    baseline_csv = out_dir / "baseline_run_metrics.csv"
    baseline.to_csv(baseline_csv, index=False)

    reference = {
        "subset_name": str(baseline["subset_name"].iloc[0]),
        "n_runs": int(len(baseline)),
        "alpha": float(alpha),
        "top_k": int(top_n),
        "zscore_params": {
            "vertical_drop_m": {"mean": mech_mean, "std": mech_std},
            "impulse_hr_above_rest_bpms": {"mean": int_mean, "std": int_std},
        },
        "baseline_top_k_run_uids": top_k_run_uids,
        "baseline_phase_contrast_combined_load_v2": phase_contrast,
    }

    reference_json = out_dir / "baseline_reference.json"
    reference_json.write_text(json.dumps(reference, indent=2), encoding="utf-8")
    return baseline, reference
