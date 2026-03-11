#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in meters."""
    R = 6371000.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 2.0 * R * np.arcsin(np.sqrt(a))


def smooth(x: pd.Series, window: int = 9) -> pd.Series:
    # rolling median is robust to spikes/outliers
    return x.rolling(window=window, center=True, min_periods=1).median()


def load_track(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"time", "lat", "lon", "elev_m"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["elev_m"] = pd.to_numeric(df["elev_m"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["time", "lat", "lon", "elev_m"]).copy()
    after = len(df)
    if after == 0:
        raise ValueError("No valid rows after dropna(time,lat,lon,elev_m).")
    if after != before:
        print(f"[WARN] Dropped {before-after} rows with NaNs in core columns.")

    df = df.sort_values("time").reset_index(drop=True)

    # seconds from start
    df["t_sec"] = (df["time"] - df["time"].iloc[0]).dt.total_seconds()

    # dt with QC safeguards
    dt = df["t_sec"].diff().fillna(np.nan)
    # first dt: use median of subsequent dts
    med_dt = float(dt.dropna().median()) if dt.dropna().size else 1.0
    if not np.isfinite(med_dt) or med_dt <= 0:
        med_dt = 1.0
    dt = dt.fillna(med_dt)
    dt = dt.replace(0, np.nan).fillna(med_dt)
    df["dt"] = dt

    return df


def engineer_signals(
    df: pd.DataFrame,
    smooth_win: int = 9,
    dt_gap_s: float = 10.0,
    speed_clip_ms: float = 50.0,
):
    """
    Compute:
      - elev_s (smoothed elevation)
      - step_dist_m (horizontal step distance)
      - speed_ms
      - vvert_ms (vertical speed, m/s; negative downhill)
      - grade
      - is_gap (dt > dt_gap_s)
    And apply robust guards for gaps/outliers.
    """
    out = df.copy()

    # smoothing elevation reduces DEM stair-steps + GPS jitter
    out["elev_s"] = smooth(out["elev_m"], window=smooth_win)

    # gap detection
    out["is_gap"] = out["dt"] > float(dt_gap_s)
    gap_count = int(out["is_gap"].sum())
    if gap_count > 0:
        print(f"[WARN] Found {gap_count} large time gaps (dt > {dt_gap_s}s). Runs will not bridge gaps.")

    # horizontal step distance
    lat1 = out["lat"].shift(1)
    lon1 = out["lon"].shift(1)
    lat2 = out["lat"]
    lon2 = out["lon"]
    step_dist = haversine_m(lat1, lon1, lat2, lon2)
    step_dist = np.nan_to_num(step_dist, nan=0.0)
    out["step_dist_m"] = step_dist

    # do not allow distance across large gaps to create artificial speed
    out.loc[out["is_gap"], "step_dist_m"] = 0.0

    # speed (m/s)
    out["speed_ms"] = out["step_dist_m"] / out["dt"]
    # clip insane values (bad GPS jumps)
    out["speed_ms"] = out["speed_ms"].clip(lower=0.0, upper=float(speed_clip_ms))

    # vertical speed (m/s), negative is descending
    out["vvert_ms"] = out["elev_s"].diff().fillna(0.0) / out["dt"]
    # if gap, don't compute meaningful vertical speed across it
    out.loc[out["is_gap"], "vvert_ms"] = 0.0

    # grade (unitless), safe divide
    denom = out["step_dist_m"].replace(0, np.nan)
    out["grade"] = out["elev_s"].diff().fillna(0.0) / denom
    out["grade"] = out["grade"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out.loc[out["is_gap"], "grade"] = 0.0

    return out


def segment_runs(
    df: pd.DataFrame,
    vvert_down_th: float = -0.4,
    speed_on_ms: float = 2.0,
    min_run_s: float = 40.0,
    merge_gap_s: float = 20.0,
    break_on_time_gaps: bool = True,
):
    """
    RUN if (vvert <= vvert_down_th) and (speed >= speed_on_ms)
    - merges short non-run gaps between runs (merge_gap_s)
    - filters short runs (min_run_s)
    - optionally breaks runs at time gaps (is_gap)
    """
    # base mask
    is_run = (df["vvert_ms"] <= float(vvert_down_th)) & (df["speed_ms"] >= float(speed_on_ms))

    # optionally: gaps force is_run False (break segments)
    if break_on_time_gaps and "is_gap" in df.columns:
        is_run = is_run & (~df["is_gap"])

    t = df["t_sec"].to_numpy()

    # raw segments of is_run
    segs = []
    start = None
    for i, flag in enumerate(is_run.to_numpy()):
        if flag and start is None:
            start = i
        if (not flag) and start is not None:
            segs.append((start, i - 1))
            start = None
    if start is not None:
        segs.append((start, len(df) - 1))

    # merge short gaps between runs
    merged = []
    for s, e in segs:
        if not merged:
            merged.append([s, e])
            continue
        prev_s, prev_e = merged[-1]
        gap = float(t[s] - t[prev_e])
        if gap <= float(merge_gap_s):
            merged[-1][1] = e
        else:
            merged.append([s, e])

    # filter short runs and build output
    rows = []
    run_id = 0
    for s, e in merged:
        dur = float(t[e] - t[s])
        if dur < float(min_run_s):
            continue

        run_id += 1
        x = df.iloc[s:e + 1]

        drop = float(x["elev_s"].iloc[0] - x["elev_s"].iloc[-1])
        drop = max(0.0, drop)

        rows.append({
            "run_id": f"run_{run_id:02d}",
            "start_time": x["time"].iloc[0],
            "end_time": x["time"].iloc[-1],
            "duration_s": dur,
            "vertical_drop_m": drop,
            "speed_mean_ms": float(x["speed_ms"].mean()),
            "speed_p95_ms": float(x["speed_ms"].quantile(0.95)),
            "vvert_mean_ms": float(x["vvert_ms"].mean()),
        })

    return pd.DataFrame(rows)


def build_metadata(df_raw, df_sig, runs, args_dict, inp_path: str, out_runs: str, out_meta: str) -> dict:
    dt = df_raw["dt"]
    md = {
        "input": inp_path,
        "n_points": int(len(df_raw)),
        "time_start": str(df_raw["time"].iloc[0]),
        "time_end": str(df_raw["time"].iloc[-1]),
        "duration_sec": float(df_raw["t_sec"].iloc[-1] - df_raw["t_sec"].iloc[0]),
        "dt_median": float(dt.median()),
        "dt_p95": float(dt.quantile(0.95)),
        "dt_max": float(dt.max()),
        "gap_count": int(df_sig["is_gap"].sum()) if "is_gap" in df_sig.columns else 0,
        "speed_ms_max": float(df_sig["speed_ms"].max()),
        "speed_ms_p95": float(df_sig["speed_ms"].quantile(0.95)),
        "vvert_ms_min": float(df_sig["vvert_ms"].min()),
        "run_count": int(len(runs)),
        "outputs": {
            "runs_csv": out_runs,
            "metadata_json": out_meta,
        },
        "params": args_dict,
    }
    return md


def main():
    ap = argparse.ArgumentParser(description="Segment downhill ski runs from track_elevation.csv (v2 with QC).")
    ap.add_argument("--in", dest="inp", default="data/processed/track_elevation.csv")
    ap.add_argument("--out", default="data/processed/runs.csv")
    ap.add_argument("--meta", default="output/run_segmentation_report.json")

    # signal processing / QC
    ap.add_argument("--smooth", type=int, default=9)
    ap.add_argument("--dt_gap", type=float, default=10.0)
    ap.add_argument("--speed_clip", type=float, default=50.0)

    # segmentation thresholds
    ap.add_argument("--vvert", type=float, default=-0.4, help="Downhill vertical speed threshold (m/s, negative).")
    ap.add_argument("--speed", type=float, default=2.0, help="Min speed threshold to consider skiing (m/s).")
    ap.add_argument("--min_run", type=float, default=40.0, help="Minimum run duration (s).")
    ap.add_argument("--merge_gap", type=float, default=20.0, help="Merge gaps shorter than this (s).")

    args = ap.parse_args()

    inp = Path(args.inp)
    outp = Path(args.out)
    meta_p = Path(args.meta)
    outp.parent.mkdir(parents=True, exist_ok=True)
    meta_p.parent.mkdir(parents=True, exist_ok=True)

    df0 = load_track(inp)
    df1 = engineer_signals(
        df0,
        smooth_win=args.smooth,
        dt_gap_s=args.dt_gap,
        speed_clip_ms=args.speed_clip,
    )

    runs = segment_runs(
        df1,
        vvert_down_th=args.vvert,
        speed_on_ms=args.speed,
        min_run_s=args.min_run,
        merge_gap_s=args.merge_gap,
        break_on_time_gaps=True,
    )

    runs.to_csv(outp, index=False)

    args_dict = {
        "smooth": args.smooth,
        "dt_gap": args.dt_gap,
        "speed_clip": args.speed_clip,
        "vvert": args.vvert,
        "speed": args.speed,
        "min_run": args.min_run,
        "merge_gap": args.merge_gap,
    }

    md = build_metadata(
        df_raw=df0,
        df_sig=df1,
        runs=runs,
        args_dict=args_dict,
        inp_path=str(inp),
        out_runs=str(outp),
        out_meta=str(meta_p),
    )

    with meta_p.open("w", encoding="utf-8") as f:
        json.dump(md, f, ensure_ascii=False, indent=2, default=str)

    print(f"[OK] Saved runs: {outp.resolve()}")
    print(f"[OK] Saved metadata: {meta_p.resolve()}")
    print(f"[INFO] Run count: {len(runs)}")

    if len(runs) > 0:
        top = runs.sort_values("vertical_drop_m", ascending=False).head(5)
        print("\n=== TOP 5 by vertical_drop_m ===")
        print(top.to_string(index=False))
    else:
        print("\n[HINT] If run_count=0, try relaxing thresholds:")
        print("  --vvert -0.2  (less strict downhill)")
        print("  --speed 1.0   (allow slower motion)")
        print("  --min_run 20  (allow shorter runs)")


if __name__ == "__main__":
    main()
