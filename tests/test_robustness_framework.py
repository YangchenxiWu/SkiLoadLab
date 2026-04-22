import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
import yaml

REPO = Path(__file__).resolve().parents[1]


def _write_test_dem(path: Path, lon_center: float, lat_center: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 256
    height = 256
    res = 0.00001
    west = lon_center - (width // 2) * res
    north = lat_center + (height // 2) * res
    transform = from_origin(west, north, res, res)
    y = np.linspace(2000.0, 1600.0, height, dtype="float32").reshape(height, 1)
    x = np.linspace(0.0, 40.0, width, dtype="float32").reshape(1, width)
    data = y + x
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)


def _write_test_polar_csv(path: Path, start_utc: pd.Timestamp, duration_s: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Local start time,Device",
        f"{start_utc.strftime('%Y-%m-%d %H:%M:%S')},Polar Test",
        "Time,HR (bpm)",
    ]
    for i in range(duration_s + 1):
        hh = i // 3600
        mm = (i % 3600) // 60
        ss = i % 60
        hr = 120 + (i % 25)
        lines.append(f"{hh:02d}:{mm:02d}:{ss:02d},{hr}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_synthetic_robustness_inputs(tmp_path: Path) -> dict[str, Path]:
    base_dir = tmp_path / "synthetic_robustness"
    runs_root = base_dir / "runs_root"
    raw_dir = base_dir / "raw"
    output_dir = base_dir / "output"
    dem_path = base_dir / "dem" / "dem.tif"
    session_label = "test_session_001"
    session_dir = runs_root / session_label
    session_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_time = pd.Timestamp("2026-02-03T03:00:00Z")
    lon0 = 115.4040
    lat0 = 40.9620
    run_specs = [
        ("run_01", 0, "strict_carving", "yes", "yes", 320.0, 9000.0),
        ("run_02", 80, "strict_carving", "yes", "yes", 305.0, 8800.0),
        ("run_03", 160, "carving_like", "yes", "no", 290.0, 8200.0),
        ("run_04", 240, "carving_like", "yes", "no", 275.0, 7800.0),
    ]

    track_rows: list[dict[str, object]] = []
    final_rows: list[dict[str, object]] = []
    for idx, (run_id, offset_s, label, include_primary, include_strict, drop_m, impulse) in enumerate(run_specs):
        start = base_time + pd.Timedelta(seconds=offset_s)
        duration_s = 60
        point_count = duration_s + 1
        for i in range(point_count):
            frac = i / duration_s
            time = start + pd.Timedelta(seconds=i)
            lat = lat0 + 0.00002 * idx + 0.00045 * frac
            lon = lon0 + 0.00001 * idx + 0.00030 * np.sin(frac * np.pi)
            elev = 2000.0 - drop_m * frac
            track_rows.append(
                {
                    "time": time.isoformat(),
                    "lat": lat,
                    "lon": lon,
                    "elev_m": elev,
                    "step_dist_m": 9.5 + 0.15 * idx,
                }
            )

        final_rows.append(
            {
                "session_label": session_label,
                "run_id": run_id,
                "subject_id": "test_subject",
                "sport": "skiing",
                "start_time_utc": start.isoformat(),
                "end_time_utc": (start + pd.Timedelta(seconds=duration_s)).isoformat(),
                "duration_s": float(duration_s),
                "vertical_drop_m": float(drop_m),
                "speed_mean_ms": 8.0 + 0.2 * idx,
                "speed_p95_ms": 12.0 + 0.3 * idx,
                "vvert_mean_ms": -5.0 + 0.05 * idx,
                "n_hr_samples": duration_s + 1,
                "hr_mean_bpm": 132.0 + idx,
                "hr_max_bpm": 150.0 + idx,
                "hr_min_bpm": 118.0 + idx,
                "impulse_hr_above_rest_bpms": float(impulse),
                "edwards_trimp": 18.0 + idx,
                "hr_rest_bpm": 60.0,
                "hr_max_session_bpm": 190.0,
                "anchor_delta_s": 0.0,
                "carving_class_final": label,
                "included_primary_analysis": include_primary,
                "included_strict_subset": include_strict,
                "exclusion_reason_final": "",
                "label_notes_final": "",
            }
        )

    track_df = pd.DataFrame(track_rows).sort_values("time").reset_index(drop=True)
    track_df.to_csv(session_dir / "track_signals.csv", index=False)

    final_runs_csv = output_dir / "runs_carving_final.csv"
    pd.DataFrame(final_rows).to_csv(final_runs_csv, index=False)

    polar_csv = raw_dir / f"{session_label}.csv"
    _write_test_polar_csv(polar_csv, base_time, duration_s=320)

    anchors_json = output_dir / "run_level_anchors.json"
    anchors_df = pd.DataFrame(
        [
            {
                "session_label": session_label,
                "csv_path": str(polar_csv),
                "nominal_csv_start_utc": base_time.isoformat(),
                "anchor_delta_s": 0.0,
            }
        ]
    )
    anchors_df.to_json(anchors_json, orient="records")

    _write_test_dem(dem_path, lon_center=lon0, lat_center=lat0)

    return {
        "final_runs_csv": final_runs_csv,
        "runs_root": runs_root,
        "raw_dir": raw_dir,
        "anchors_json": anchors_json,
        "dem_path": dem_path,
    }


def _make_test_config(tmp_path: Path, dataset_paths: dict[str, Path]) -> dict[str, object]:
    template_path = REPO / "experiments/robustness/config/test_run.yaml"
    config = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    config["final_runs_csv"] = str(dataset_paths["final_runs_csv"])
    config["runs_root"] = str(dataset_paths["runs_root"])
    config["raw_dir"] = str(dataset_paths["raw_dir"])
    config["anchors_json"] = str(dataset_paths["anchors_json"])
    config["dem_path"] = str(dataset_paths["dem_path"])
    config["output_dir"] = str(tmp_path / "robustness_results")
    return config


def test_robustness_framework_test_run(tmp_path: Path):
    dataset_paths = _build_synthetic_robustness_inputs(tmp_path)
    config = _make_test_config(tmp_path, dataset_paths)
    config["max_runs"] = 4
    config["repeats"] = 1
    config["top_k"] = 2
    config["perturbations"] = {
        "elevation": [{"value": 2.0, "label": "low"}],
        "sampling": [{"value": 2, "label": "low"}],
        "temporal": [{"value": 0.75, "label": "low"}],
        "position": [{"value": 2.0, "label": "low"}],
    }

    config_path = tmp_path / "test_run.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    p = subprocess.run(
        [
            "python3",
            "-m",
            "experiments.robustness.cli",
            "--config",
            str(config_path),
            "--subset",
            "primary",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert p.returncode == 0, p.stderr + "\n" + p.stdout

    out_dir = Path(config["output_dir"])
    expected = [
        out_dir / "baseline_run_metrics.csv",
        out_dir / "baseline_reference.json",
        out_dir / "perturbation_registry.csv",
        out_dir / "recomputed_run_metrics.csv",
        out_dir / "robustness_metrics_long.csv",
        out_dir / "robustness_summary_table.csv",
        out_dir / "fig_robustness_core.png",
        out_dir / "run_manifest.json",
    ]
    for path in expected:
        assert path.exists(), path.name

    long_df = pd.read_csv(out_dir / "robustness_metrics_long.csv")
    assert len(long_df) == 16
    for col in [
        "run_id",
        "run_uid",
        "subset_name",
        "perturbation_type",
        "perturbation_level",
        "perturbation_level_label",
        "repeat_id",
        "top_k_used",
        "baseline_vertical_drop_m",
        "perturbed_vertical_drop_m",
        "segmentation_stability",
        "cl_alpha_abs_deviation",
        "top_k_consistency",
        "phase_contrast_abs_deviation",
    ]:
        assert col in long_df.columns

    assert long_df[["run_uid", "subset_name", "perturbation_type", "perturbation_level", "repeat_id"]].drop_duplicates().shape[0] == len(long_df)
    assert set(long_df["perturbation_level_label"]) == {"low"}
    assert set(long_df["top_k_used"]) == {2}

    summary_df = pd.read_csv(out_dir / "robustness_summary_table.csv")
    for col in ["subset_name", "perturbation_type", "perturbation_level", "perturbation_level_label", "top_k_used", "metric_name", "median", "iqr", "mean", "sd", "n"]:
        assert col in summary_df.columns
    assert {"segmentation_stability", "vertical_drop_abs_error_m", "cl_alpha_abs_deviation"}.issubset(set(summary_df["metric_name"]))


def test_robustness_cli_explicit_paths(tmp_path: Path):
    dataset_paths = _build_synthetic_robustness_inputs(tmp_path)
    config = _make_test_config(tmp_path, dataset_paths)
    config["output_dir"] = str(tmp_path / "cli_results")
    config["max_runs"] = 2
    config["repeats"] = 1
    config["top_k"] = 2
    config["perturbations"] = {
        "elevation": [{"value": 2.0, "label": "low"}],
        "position": [{"value": 2.0, "label": "low"}],
    }
    config_path = tmp_path / "cli_run.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    out_dir = tmp_path / "explicit_outputs"
    p = subprocess.run(
        [
            "python3",
            "-m",
            "experiments.robustness.cli",
            "--config",
            str(config_path),
            "--subset",
            "both",
            "--output-dir",
            str(out_dir),
            "--long-table-path",
            str(out_dir / "custom_long.csv"),
            "--summary-table-path",
            str(out_dir / "custom_summary.csv"),
            "--manifest-path",
            str(out_dir / "custom_manifest.json"),
            "--figure-path",
            str(out_dir / "custom_core.png"),
            "--figure-primary-path",
            str(out_dir / "custom_primary.png"),
            "--figure-strict-path",
            str(out_dir / "custom_strict.png"),
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert p.returncode == 0, p.stderr + "\n" + p.stdout

    expected = [
        out_dir / "custom_long.csv",
        out_dir / "custom_summary.csv",
        out_dir / "custom_manifest.json",
        out_dir / "custom_core.png",
        out_dir / "custom_primary.png",
        out_dir / "custom_strict.png",
    ]
    for path in expected:
        assert path.exists(), path.name

    manifest = json.loads((out_dir / "custom_manifest.json").read_text(encoding="utf-8"))
    assert manifest["subset_names"] == ["primary", "strict"]
    assert manifest["output_paths"]["robustness_metrics_long"] == str((out_dir / "custom_long.csv").resolve())
    assert manifest["output_paths"]["robustness_summary_table"] == str((out_dir / "custom_summary.csv").resolve())
    assert manifest["output_paths"]["run_manifest"] == str((out_dir / "custom_manifest.json").resolve())
    assert manifest["output_paths"]["figure_core"] == str((out_dir / "custom_core.png").resolve())
    assert manifest["output_paths"]["figure_primary"] == str((out_dir / "custom_primary.png").resolve())
    assert manifest["output_paths"]["figure_strict"] == str((out_dir / "custom_strict.png").resolve())
