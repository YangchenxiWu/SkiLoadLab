from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class RunObject:
    subset_name: str
    run_id: str
    session_label: str
    label: str
    baseline_row: dict[str, object]
    track: pd.DataFrame
    hr_stream: pd.DataFrame
    dem_path: str


def load_final_runs_table(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if len(df) == 0:
        raise ValueError(f"Final runs table is empty: {path}")
    return df


def select_subset(df: pd.DataFrame, subset_name: str) -> pd.DataFrame:
    if subset_name == "primary":
        out = df[df["included_primary_analysis"] == "yes"].copy()
    elif subset_name == "strict":
        out = df[df["included_strict_subset"] == "yes"].copy()
    elif subset_name == "all_valid":
        out = df.copy()
    else:
        raise ValueError(f"Unsupported subset_name: {subset_name}")

    if len(out) == 0:
        raise ValueError(f"No runs found for subset: {subset_name}")

    out["start_time_utc"] = pd.to_datetime(out["start_time_utc"], utc=True, format="mixed")
    out["end_time_utc"] = pd.to_datetime(out["end_time_utc"], utc=True, format="mixed")
    return out.reset_index(drop=True)


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


def _prepare_hr_stream(stream: pd.DataFrame, nominal_csv_start_utc: pd.Timestamp, anchor_delta_s: float) -> pd.DataFrame:
    out = stream.copy()
    out["Time"] = pd.to_timedelta(out["Time"], errors="coerce")
    out["HR (bpm)"] = pd.to_numeric(out["HR (bpm)"], errors="coerce")
    out = out.dropna(subset=["Time"]).reset_index(drop=True)
    out["timestamp_utc"] = nominal_csv_start_utc + out["Time"] + pd.to_timedelta(anchor_delta_s, unit="s")

    dt_s = out["timestamp_utc"].diff().dt.total_seconds().shift(-1)
    median_dt = float(dt_s.dropna().median()) if dt_s.dropna().size else 1.0
    if median_dt <= 0:
        median_dt = 1.0
    out["dt_s"] = dt_s.fillna(median_dt).clip(lower=0.0, upper=10.0)
    return out


def load_session_hr_streams(raw_dir: Path, anchors_json: Path) -> dict[str, pd.DataFrame]:
    anchors = pd.read_json(anchors_json)
    streams: dict[str, pd.DataFrame] = {}

    for _, row in anchors.iterrows():
        session_label = str(row["session_label"])
        csv_path = Path(str(row["csv_path"]))
        if not csv_path.is_absolute():
            csv_path = raw_dir / csv_path.name
        _, stream = _read_polar_csv(csv_path)
        nominal_start = pd.to_datetime(row["nominal_csv_start_utc"], utc=True, format="mixed")
        anchor_delta_s = float(row["anchor_delta_s"])
        streams[session_label] = _prepare_hr_stream(stream, nominal_start, anchor_delta_s)

    return streams


def load_session_track_segments(runs_root: Path, session_label: str) -> pd.DataFrame:
    track_path = runs_root / session_label / "track_signals.csv"
    if not track_path.exists():
        raise FileNotFoundError(f"Track signals not found: {track_path}")
    track = pd.read_csv(track_path)
    track["time"] = pd.to_datetime(track["time"], utc=True, format="mixed")
    return track


def build_run_objects(
    final_runs_csv: Path,
    subset_name: str,
    runs_root: Path,
    raw_dir: Path,
    anchors_json: Path,
    dem_path: Path,
    max_runs: int | None = None,
) -> list[RunObject]:
    final_runs = select_subset(load_final_runs_table(final_runs_csv), subset_name=subset_name)
    if max_runs is not None:
        final_runs = final_runs.head(int(max_runs)).copy()

    hr_streams = load_session_hr_streams(raw_dir=raw_dir, anchors_json=anchors_json)
    track_cache: dict[str, pd.DataFrame] = {}
    run_objects: list[RunObject] = []

    for _, row in final_runs.iterrows():
        session_label = str(row["session_label"])
        if session_label not in track_cache:
            track_cache[session_label] = load_session_track_segments(runs_root=runs_root, session_label=session_label)

        session_track = track_cache[session_label]
        run_track = session_track[
            (session_track["time"] >= row["start_time_utc"]) & (session_track["time"] <= row["end_time_utc"])
        ].copy()
        if len(run_track) == 0:
            raise ValueError(f"No track points found for {session_label} {row['run_id']}")

        run_objects.append(
            RunObject(
                subset_name=subset_name,
                run_id=str(row["run_id"]),
                session_label=session_label,
                label=str(row["carving_class_final"]),
                baseline_row=row.to_dict(),
                track=run_track.reset_index(drop=True),
                hr_stream=hr_streams[session_label].copy(),
                dem_path=str(dem_path),
            )
        )

    return run_objects
