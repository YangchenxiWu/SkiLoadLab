import subprocess
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]


def test_robustness_framework_test_run(tmp_path: Path):
    template_path = REPO / "experiments/robustness/config/test_run.yaml"
    config = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    config["output_dir"] = str(tmp_path / "robustness_results")
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
    template_path = REPO / "experiments/robustness/config/test_run.yaml"
    config = yaml.safe_load(template_path.read_text(encoding="utf-8"))
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

    manifest = yaml.safe_load((out_dir / "custom_manifest.json").read_text(encoding="utf-8"))
    assert manifest["subset_names"] == ["primary", "strict"]
    assert manifest["output_paths"]["robustness_metrics_long"] == str((out_dir / "custom_long.csv").resolve())
    assert manifest["output_paths"]["robustness_summary_table"] == str((out_dir / "custom_summary.csv").resolve())
    assert manifest["output_paths"]["run_manifest"] == str((out_dir / "custom_manifest.json").resolve())
    assert manifest["output_paths"]["figure_core"] == str((out_dir / "custom_core.png").resolve())
    assert manifest["output_paths"]["figure_primary"] == str((out_dir / "custom_primary.png").resolve())
    assert manifest["output_paths"]["figure_strict"] == str((out_dir / "custom_strict.png").resolve())
