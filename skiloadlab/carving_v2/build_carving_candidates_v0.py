from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _bearing_deg(lat1: pd.Series, lon1: pd.Series, lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    lat1r = np.radians(lat1)
    lat2r = np.radians(lat2)
    dlonr = np.radians(lon2 - lon1)
    y = np.sin(dlonr) * np.cos(lat2r)
    x = np.cos(lat1r) * np.sin(lat2r) - np.sin(lat1r) * np.cos(lat2r) * np.cos(dlonr)
    return ((np.degrees(np.arctan2(y, x)) + 360.0) % 360.0).astype(float)


def _wrap180(x: pd.Series) -> pd.Series:
    return ((x + 180.0) % 360.0) - 180.0


def _compute_turn_features(track: pd.DataFrame) -> dict[str, float]:
    moving = track[(track["speed_ms"] >= 4.0) & (track["step_dist_m"] >= 2.0)].copy().reset_index(drop=True)
    if len(moving) < 5:
        return {
            "moving_points": int(len(moving)),
            "moving_frac": float(len(moving) / len(track)) if len(track) else float("nan"),
            "turn_switches": 0,
            "turns_per_min": 0.0,
            "median_turn_amp_deg": 0.0,
            "large_turn_block_frac": 0.0,
            "mean_abs_heading_delta_deg": float("nan"),
        }

    moving["bearing_deg"] = _bearing_deg(
        moving["lat"].shift(1),
        moving["lon"].shift(1),
        moving["lat"],
        moving["lon"],
    )
    moving["bearing_smooth_deg"] = (
        moving["bearing_deg"].rolling(window=5, center=True, min_periods=1).mean()
    )
    moving["heading_delta_deg"] = _wrap180(moving["bearing_smooth_deg"].diff())
    moving["turn_sign"] = np.sign(moving["heading_delta_deg"])
    moving.loc[moving["heading_delta_deg"].abs() < 5.0, "turn_sign"] = 0.0

    turning = moving[moving["turn_sign"] != 0.0].copy()
    turn_switches = int(((turning["turn_sign"] * turning["turn_sign"].shift(1)) < 0).sum())

    amps: list[float] = []
    if not turning.empty:
        blocks = (turning["turn_sign"] != turning["turn_sign"].shift(1)).cumsum()
        for _, group in turning.groupby(blocks):
            amps.append(float(group["heading_delta_deg"].sum()))

    amp_arr = np.abs(np.asarray(amps, dtype=float)) if amps else np.asarray([], dtype=float)
    large_turn_block_frac = float(np.mean(amp_arr >= 20.0)) if amp_arr.size else 0.0

    return {
        "moving_points": int(len(moving)),
        "moving_frac": float(len(moving) / len(track)),
        "turn_switches": turn_switches,
        "median_turn_amp_deg": float(np.median(amp_arr)) if amp_arr.size else 0.0,
        "large_turn_block_frac": large_turn_block_frac,
        "mean_abs_heading_delta_deg": float(moving["heading_delta_deg"].abs().mean()),
    }


def _compute_run_features(run_row: pd.Series, track: pd.DataFrame) -> dict[str, float]:
    work = track.copy()
    work["acc_ms2"] = work["speed_ms"].diff() / work["dt"].replace(0, np.nan)
    turn = _compute_turn_features(work)

    path_len_m = float(work["step_dist_m"].sum())
    speed_pos = work.loc[work["speed_ms"] > 0.0, "speed_ms"]
    speed_keep_ratio = float(speed_pos.median() / max(work["speed_ms"].quantile(0.9), 1e-9)) if len(speed_pos) else float("nan")

    duration_min = float(run_row["duration_s"]) / 60.0 if float(run_row["duration_s"]) > 0 else float("nan")
    turns_per_min = float(turn["turn_switches"] / duration_min) if np.isfinite(duration_min) and duration_min > 0 else 0.0

    return {
        **turn,
        "turns_per_min": turns_per_min,
        "stop_frac": float((work["speed_ms"] < 3.0).mean()),
        "decel_frac": float((work["acc_ms2"] < -1.5).mean()),
        "speed_keep_ratio": speed_keep_ratio,
        "path_len_m": path_len_m,
        "drop_per_hdist": float(run_row["vertical_drop_m"] / max(path_len_m, 1e-9)),
    }


def _candidate_screen(row: pd.Series) -> tuple[bool, str]:
    if float(row["duration_s"]) < 60.0:
        return False, "duration_lt_60s"
    if float(row["vertical_drop_m"]) < 50.0:
        return False, "vertical_drop_lt_50m"
    if float(row["speed_mean_ms"]) < 5.0:
        return False, "speed_mean_lt_5ms"
    if float(row["anchor_delta_s"]) > 300.0:
        return False, "alignment_delta_gt_300s"
    if float(row["n_hr_samples"]) <= 0.0:
        return False, "no_hr_samples"
    return True, ""


def _assign_carving_label(row: pd.Series) -> tuple[str, str, str, str]:
    candidate_pool_v0 = bool(row["candidate_pool_v0"])
    if not candidate_pool_v0:
        return "non_carving", "no", str(row["candidate_screen_reason"]), "screen_fail"

    if (
        float(row["turns_per_min"]) < 3.5
        or float(row["large_turn_block_frac"]) < 0.35
        or float(row["speed_keep_ratio"]) < 0.68
        or float(row["drop_per_hdist"]) < 0.08
        or float(row["moving_frac"]) < 0.40
    ):
        return "non_carving", "no", "trajectory_review_fail", "weak_arc_or_excess_traverse"

    if (
        float(row["turns_per_min"]) >= 5.5
        and float(row["large_turn_block_frac"]) >= 0.55
        and float(row["speed_keep_ratio"]) >= 0.76
        and float(row["drop_per_hdist"]) >= 0.11
        and float(row["moving_frac"]) >= 0.47
    ):
        return "carving", "yes", "", "strong_arc_pattern_v0"

    return "uncertain", "no", "borderline_pattern", "borderline_v0_review"


def build_candidates_v0(run_level_csv: Path, runs_root: Path, out_csv: Path) -> pd.DataFrame:
    run_level = pd.read_csv(run_level_csv)
    run_level["start_time_utc"] = pd.to_datetime(run_level["start_time_utc"], utc=True, format="mixed")
    run_level["end_time_utc"] = pd.to_datetime(run_level["end_time_utc"], utc=True, format="mixed")

    output_rows: list[dict[str, object]] = []

    for session_label, session_runs in run_level.groupby("session_label", sort=False):
        track_path = runs_root / session_label / "track_signals.csv"
        if not track_path.exists():
            raise FileNotFoundError(f"Track signals file not found: {track_path}")

        track = pd.read_csv(track_path)
        track["time"] = pd.to_datetime(track["time"], utc=True, format="mixed")

        for _, row in session_runs.iterrows():
            mask = (track["time"] >= row["start_time_utc"]) & (track["time"] <= row["end_time_utc"])
            run_track = track.loc[mask].copy().reset_index(drop=True)

            feature_row = row.to_dict()
            if len(run_track) < 5:
                feature_row.update(
                    {
                        "moving_points": 0,
                        "moving_frac": float("nan"),
                        "turn_switches": 0,
                        "turns_per_min": 0.0,
                        "median_turn_amp_deg": 0.0,
                        "large_turn_block_frac": 0.0,
                        "mean_abs_heading_delta_deg": float("nan"),
                        "stop_frac": float("nan"),
                        "decel_frac": float("nan"),
                        "speed_keep_ratio": float("nan"),
                        "path_len_m": float("nan"),
                        "drop_per_hdist": float("nan"),
                    }
                )
            else:
                feature_row.update(_compute_run_features(row, run_track))

            candidate_pool, candidate_reason = _candidate_screen(pd.Series(feature_row))
            feature_row["candidate_pool_v0"] = candidate_pool
            feature_row["candidate_screen_reason"] = candidate_reason

            carving_label, included_main_analysis, exclusion_reason, label_notes = _assign_carving_label(
                pd.Series(feature_row)
            )
            feature_row["carving_label"] = carving_label
            feature_row["included_main_analysis"] = included_main_analysis
            feature_row["exclusion_reason"] = exclusion_reason
            feature_row["label_notes"] = label_notes
            output_rows.append(feature_row)

    out = pd.DataFrame(output_rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a trajectory-featured carving candidate table and assign v0 carving labels."
    )
    parser.add_argument("--run_level", default="output/carving_v2_cleaned/run_level_aligned.csv")
    parser.add_argument("--runs_root", default="output/carving_v2_cleaned")
    parser.add_argument("--out", default="output/carving_v2_cleaned/runs_carving_candidates_v0.csv")
    args = parser.parse_args()

    out = build_candidates_v0(
        run_level_csv=Path(args.run_level),
        runs_root=Path(args.runs_root),
        out_csv=Path(args.out),
    )
    counts = out["carving_label"].value_counts(dropna=False).to_dict()
    print(f"[OK] Saved {len(out)} rows to {Path(args.out).resolve()}")
    print(f"[OK] Label counts: {counts}")


if __name__ == "__main__":
    main()
