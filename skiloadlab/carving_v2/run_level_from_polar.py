from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class SessionAnchor:
    session_label: str
    csv_path: str
    runs_path: str
    local_start: str
    inferred_utc_offset_h: int
    nominal_csv_start_utc: str
    gpx_first_time_utc: str
    anchor_delta_s: float
    run_count: int


def _read_polar_csv(csv_path: Path) -> tuple[dict[str, str], pd.DataFrame]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        summary_headers = next(reader)
        summary_values = next(reader)
        stream_headers = next(reader)
        rows = list(reader)

    summary = {key: value for key, value in zip(summary_headers, summary_values)}
    stream = pd.DataFrame(rows, columns=stream_headers)
    return summary, stream


def _parse_local_start(summary: dict[str, str]) -> pd.Timestamp:
    return pd.to_datetime(
        f"{summary['Date']} {summary['Start time']}",
        format="%Y-%m-%d %H:%M:%S",
        errors="raise",
    )


def _prepare_stream(stream: pd.DataFrame) -> pd.DataFrame:
    out = stream.copy()
    out["Time"] = pd.to_timedelta(out["Time"], errors="coerce")
    out["HR (bpm)"] = pd.to_numeric(out["HR (bpm)"], errors="coerce")
    out["Speed (km/h)"] = pd.to_numeric(out["Speed (km/h)"], errors="coerce")
    out["Distances (m)"] = pd.to_numeric(out["Distances (m)"], errors="coerce")
    out = out.dropna(subset=["Time"]).reset_index(drop=True)
    return out


def _anchor_stream(
    session_label: str,
    summary: dict[str, str],
    stream: pd.DataFrame,
    runs: pd.DataFrame,
    gpx_first_time_utc: pd.Timestamp,
) -> tuple[pd.DataFrame, SessionAnchor]:
    local_start = _parse_local_start(summary)
    runs = runs.copy()
    runs["start_time"] = pd.to_datetime(runs["start_time"], utc=True, errors="coerce")
    runs["end_time"] = pd.to_datetime(runs["end_time"], utc=True, errors="coerce")
    if pd.isna(gpx_first_time_utc):
        raise ValueError(f"{session_label}: no valid run timestamps found.")

    rough_offset_h = int(round((local_start - gpx_first_time_utc.tz_localize(None)).total_seconds() / 3600.0))
    nominal_csv_start_utc = local_start - pd.Timedelta(hours=rough_offset_h)
    anchor_delta = gpx_first_time_utc - nominal_csv_start_utc.tz_localize("UTC")

    anchored = stream.copy()
    anchored["timestamp_utc"] = nominal_csv_start_utc.tz_localize("UTC") + anchored["Time"] + anchor_delta

    dt_s = anchored["timestamp_utc"].diff().dt.total_seconds()
    median_dt = float(dt_s.dropna().median()) if dt_s.dropna().size else 1.0
    if not np.isfinite(median_dt) or median_dt <= 0:
        median_dt = 1.0
    anchored["dt_s"] = dt_s.shift(-1)
    anchored["dt_s"] = pd.to_numeric(anchored["dt_s"], errors="coerce").fillna(median_dt).clip(lower=0.0, upper=10.0)

    anchor = SessionAnchor(
        session_label=session_label,
        csv_path="",
        runs_path="",
        local_start=str(local_start),
        inferred_utc_offset_h=rough_offset_h,
        nominal_csv_start_utc=str(nominal_csv_start_utc.tz_localize("UTC")),
        gpx_first_time_utc=str(gpx_first_time_utc),
        anchor_delta_s=float(anchor_delta.total_seconds()),
        run_count=int(len(runs)),
    )
    return anchored, anchor


def _compute_edwards_trimp(hr: pd.Series, dt_s: pd.Series, hr_max: float) -> float:
    if not np.isfinite(hr_max) or hr_max <= 0:
        return float("nan")

    frac = pd.to_numeric(hr, errors="coerce") / float(hr_max)
    dt_min = pd.to_numeric(dt_s, errors="coerce").fillna(0.0) / 60.0
    zones = [
        ((frac >= 0.50) & (frac < 0.60), 1),
        ((frac >= 0.60) & (frac < 0.70), 2),
        ((frac >= 0.70) & (frac < 0.80), 3),
        ((frac >= 0.80) & (frac < 0.90), 4),
        (frac >= 0.90, 5),
    ]
    total = 0.0
    for mask, weight in zones:
        total += float(dt_min[mask].sum()) * weight
    return total


def build_run_level_table(raw_dir: Path, runs_root: Path, out_csv: Path, anchor_json: Path) -> pd.DataFrame:
    run_level_rows: list[dict[str, object]] = []
    anchors: list[dict[str, object]] = []

    for runs_path in sorted(runs_root.glob("polar_session_*/runs.csv")):
        session_label = runs_path.parent.name
        csv_path = raw_dir / f"{session_label}.csv"
        track_path = runs_path.parent / "track.csv"
        if not csv_path.exists():
            continue

        summary, stream = _read_polar_csv(csv_path)
        stream = _prepare_stream(stream)
        runs = pd.read_csv(runs_path)
        if not track_path.exists():
            raise FileNotFoundError(f"Track file not found for {session_label}: {track_path}")
        track = pd.read_csv(track_path)
        gpx_first_time_utc = pd.to_datetime(track["time"], utc=True, errors="coerce").dropna().min()
        anchored, anchor = _anchor_stream(session_label, summary, stream, runs, gpx_first_time_utc)
        anchor.csv_path = str(csv_path)
        anchor.runs_path = str(runs_path)
        anchors.append(anchor.__dict__)

        hr_rest = float(pd.to_numeric(pd.Series([summary.get("HR sit", np.nan)]), errors="coerce").iloc[0])
        hr_max = float(pd.to_numeric(pd.Series([summary.get("HR max", np.nan)]), errors="coerce").iloc[0])

        runs["start_time"] = pd.to_datetime(runs["start_time"], utc=True, errors="coerce")
        runs["end_time"] = pd.to_datetime(runs["end_time"], utc=True, errors="coerce")

        for _, run in runs.iterrows():
            mask = (anchored["timestamp_utc"] >= run["start_time"]) & (anchored["timestamp_utc"] <= run["end_time"])
            hr_slice = anchored.loc[mask].copy()
            hr_slice = hr_slice.dropna(subset=["HR (bpm)"])

            impulse = float(((hr_slice["HR (bpm)"] - hr_rest).clip(lower=0.0) * hr_slice["dt_s"]).sum()) if len(hr_slice) else float("nan")
            row = {
                "session_label": session_label,
                "subject_id": summary.get("Name", ""),
                "sport": summary.get("Sport", ""),
                "run_id": run["run_id"],
                "start_time_utc": run["start_time"],
                "end_time_utc": run["end_time"],
                "duration_s": run["duration_s"],
                "vertical_drop_m": run["vertical_drop_m"],
                "speed_mean_ms": run["speed_mean_ms"],
                "speed_p95_ms": run["speed_p95_ms"],
                "vvert_mean_ms": run["vvert_mean_ms"],
                "n_hr_samples": int(len(hr_slice)),
                "hr_mean_bpm": float(hr_slice["HR (bpm)"].mean()) if len(hr_slice) else float("nan"),
                "hr_max_bpm": float(hr_slice["HR (bpm)"].max()) if len(hr_slice) else float("nan"),
                "hr_min_bpm": float(hr_slice["HR (bpm)"].min()) if len(hr_slice) else float("nan"),
                "impulse_hr_above_rest_bpms": impulse,
                "edwards_trimp": _compute_edwards_trimp(hr_slice["HR (bpm)"], hr_slice["dt_s"], hr_max) if len(hr_slice) else float("nan"),
                "hr_rest_bpm": hr_rest,
                "hr_max_session_bpm": hr_max,
                "anchor_delta_s": anchor.anchor_delta_s,
            }
            run_level_rows.append(row)

    run_level = pd.DataFrame(run_level_rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    anchor_json.parent.mkdir(parents=True, exist_ok=True)
    run_level.to_csv(out_csv, index=False)
    anchor_json.write_text(json.dumps(anchors, indent=2), encoding="utf-8")
    return run_level


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a run-level table by anchoring Polar HR CSV streams to segmented GPX runs."
    )
    parser.add_argument("--raw_dir", default="data/carving_v2/raw")
    parser.add_argument("--runs_root", default="output/carving_v2_cleaned")
    parser.add_argument("--out", default="output/carving_v2_cleaned/run_level_aligned.csv")
    parser.add_argument("--anchors", default="output/carving_v2_cleaned/run_level_anchors.json")
    args = parser.parse_args()

    run_level = build_run_level_table(
        raw_dir=Path(args.raw_dir),
        runs_root=Path(args.runs_root),
        out_csv=Path(args.out),
        anchor_json=Path(args.anchors),
    )
    print(f"[OK] Saved {len(run_level)} run-level rows to {Path(args.out).resolve()}")


if __name__ == "__main__":
    main()
