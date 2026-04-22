from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.robustness.data_interface import RunObject


def build_perturbation_registry(
    subset_names: list[str],
    perturbation_levels: dict[str, list[object]],
    repeats: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for subset_name in subset_names:
        for perturbation_type, levels in perturbation_levels.items():
            for level_spec in levels:
                if isinstance(level_spec, dict):
                    level_value = float(level_spec["value"])
                    level_label = str(level_spec.get("label", level_value))
                else:
                    level_value = float(level_spec)
                    level_label = str(level_value)
                for repeat_id in range(1, int(repeats) + 1):
                    rows.append(
                        {
                            "subset_name": subset_name,
                            "perturbation_type": perturbation_type,
                            "perturbation_level": level_value,
                            "perturbation_level_label": level_label,
                            "repeat_id": int(repeat_id),
                        }
                    )
    return pd.DataFrame(rows)


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(int(seed))


def _jitter_latlon(track: pd.DataFrame, meters: float, seed: int) -> pd.DataFrame:
    out = track.copy()
    gen = _rng(seed)
    lat_scale = meters / 111_111.0
    lon_scale = meters / (111_111.0 * np.cos(np.radians(out["lat"].clip(-89.0, 89.0))))
    out["lat"] = out["lat"] + gen.normal(0.0, lat_scale, size=len(out))
    out["lon"] = out["lon"] + gen.normal(0.0, lon_scale, size=len(out))
    return out


def _downsample(track: pd.DataFrame, stride: int) -> pd.DataFrame:
    stride = max(int(round(stride)), 1)
    out = track.iloc[::stride].copy()
    if len(out) < 3:
        out = track.iloc[[0, len(track) // 2, len(track) - 1]].copy()
    return out.reset_index(drop=True)


def _temporal_jitter(track: pd.DataFrame, seconds: float, seed: int) -> pd.DataFrame:
    out = track.copy()
    gen = _rng(seed)
    out["time"] = pd.to_datetime(out["time"], utc=True, format="mixed")
    rel_t = (out["time"] - out["time"].iloc[0]).dt.total_seconds()
    dt = rel_t.diff().fillna(rel_t.diff().dropna().median() if rel_t.diff().dropna().size else 1.0)
    dt = dt.clip(lower=0.2)

    noise = gen.normal(0.0, float(seconds), size=len(out))
    perturbed_dt = (dt + noise).clip(lower=0.2)
    perturbed_dt.iloc[0] = dt.iloc[0]

    original_duration = float(rel_t.iloc[-1]) if len(rel_t) else 0.0
    if len(perturbed_dt) > 1:
        current_duration = float(perturbed_dt.iloc[1:].sum())
        if current_duration > 0 and original_duration > 0:
            perturbed_dt.iloc[1:] = perturbed_dt.iloc[1:] * (original_duration / current_duration)

    new_rel_t = perturbed_dt.cumsum() - perturbed_dt.iloc[0]
    out["time"] = out["time"].iloc[0] + pd.to_timedelta(new_rel_t, unit="s")
    return out


def _structural_missingness(track: pd.DataFrame, missing_seconds: float, seed: int) -> tuple[pd.DataFrame, dict[str, object]]:
    out = track.copy()
    if float(missing_seconds) <= 0.0 or len(out) < 5:
        return out, {"removed_points": 0}

    gen = _rng(seed)
    t0 = out["time"].iloc[0]
    seconds_from_start = (out["time"] - t0).dt.total_seconds()
    max_start = max(float(seconds_from_start.max() - missing_seconds), 0.0)
    start_s = float(gen.uniform(0.0, max_start)) if max_start > 0 else 0.0
    end_s = start_s + float(missing_seconds)
    keep = ~((seconds_from_start >= start_s) & (seconds_from_start <= end_s))
    perturbed = out.loc[keep].copy()
    if len(perturbed) < 3:
        perturbed = out.iloc[[0, len(out) // 2, len(out) - 1]].copy()
    removed_points = int(len(out) - len(perturbed))
    return perturbed.reset_index(drop=True), {"removed_points": removed_points, "missing_window_s": [start_s, end_s]}


def perturb_run(
    run_obj: RunObject,
    perturbation_spec: dict[str, object],
    seed: int,
) -> tuple[RunObject, dict[str, object]]:
    perturbation_type = str(perturbation_spec["perturbation_type"])
    level = float(perturbation_spec["perturbation_level"])
    track = run_obj.track.copy()
    metadata: dict[str, object] = {
        "perturbation_type": perturbation_type,
        "perturbation_level": level,
        "perturbation_level_label": str(perturbation_spec.get("perturbation_level_label", level)),
        "seed": int(seed),
    }

    if perturbation_type == "elevation":
        gen = _rng(seed)
        track["elev_m"] = pd.to_numeric(track["elev_m"], errors="coerce") + gen.normal(0.0, level, size=len(track))
    elif perturbation_type == "position":
        track = _jitter_latlon(track, meters=level, seed=seed)
    elif perturbation_type == "sampling":
        track = _downsample(track, stride=max(int(round(level)), 1))
    elif perturbation_type == "temporal":
        track = _temporal_jitter(track, seconds=level, seed=seed)
    elif perturbation_type == "structural_missingness":
        track, extra = _structural_missingness(track, missing_seconds=level, seed=seed)
        metadata.update(extra)
    else:
        raise ValueError(f"Unsupported perturbation_type: {perturbation_type}")

    metadata["n_points_after_perturbation"] = int(len(track))
    return replace(run_obj, track=track.reset_index(drop=True)), metadata
