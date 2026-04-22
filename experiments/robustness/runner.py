from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd
import yaml

from experiments.robustness.baseline import build_baseline_reference
from experiments.robustness.data_interface import build_run_objects
from experiments.robustness.metrics import compare_outputs
from experiments.robustness.perturbations import build_perturbation_registry, perturb_run
from experiments.robustness.recompute import recompute_run_outputs
from experiments.robustness.summarize import build_summary_table


def _configure_headless_plotting() -> None:
    cache_dir = Path(os.environ.get("SKILOADLAB_MPL_CACHE_DIR", "/tmp/skiloadlab_mpl"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))


def _load_config(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _default_output_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "baseline_run_metrics": output_dir / "baseline_run_metrics.csv",
        "baseline_reference": output_dir / "baseline_reference.json",
        "perturbation_registry": output_dir / "perturbation_registry.csv",
        "recomputed_run_metrics": output_dir / "recomputed_run_metrics.csv",
        "robustness_metrics_long": output_dir / "robustness_metrics_long.csv",
        "robustness_summary_table": output_dir / "robustness_summary_table.csv",
        "run_manifest": output_dir / "run_manifest.json",
        "figure_core": output_dir / "fig_robustness_core.png",
        "figure_primary": output_dir / "fig_robustness_core_primary.png",
        "figure_strict": output_dir / "fig_robustness_core_strict.png",
    }


def _resolve_output_paths(config: dict[str, object], output_dir: Path) -> dict[str, Path]:
    paths = _default_output_paths(output_dir)
    raw_paths = config.get("output_paths")
    if isinstance(raw_paths, dict):
        for key, value in raw_paths.items():
            if key in paths and value:
                paths[key] = Path(str(value))
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    return paths


def run_experiment(config: dict[str, object]) -> dict[str, object]:
    _configure_headless_plotting()
    from experiments.robustness.plotting import export_position_sanity_figures, plot_core_robustness

    output_dir = Path(str(config["output_dir"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = _resolve_output_paths(config, output_dir)

    subset_names = list(config.get("subset_names", ["primary"]))
    perturbations = dict(config["perturbations"])
    repeats = int(config.get("repeats", 1))
    alpha = float(config.get("alpha", 0.5))
    top_k = int(config.get("top_k", 5))
    max_runs = int(config["max_runs"]) if config.get("max_runs") is not None else None

    registry = build_perturbation_registry(subset_names=subset_names, perturbation_levels=perturbations, repeats=repeats)
    registry.to_csv(output_paths["perturbation_registry"], index=False)

    baseline_tables: list[pd.DataFrame] = []
    reference_map: dict[str, dict[str, object]] = {}
    recomputed_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []

    for subset_name in subset_names:
        run_objects = build_run_objects(
            final_runs_csv=Path(str(config["final_runs_csv"])),
            subset_name=subset_name,
            runs_root=Path(str(config["runs_root"])),
            raw_dir=Path(str(config["raw_dir"])),
            anchors_json=Path(str(config["anchors_json"])),
            dem_path=Path(str(config["dem_path"])),
            max_runs=max_runs,
        )
        subset_out = output_dir / subset_name
        subset_out.mkdir(parents=True, exist_ok=True)

        baseline_df, reference = build_baseline_reference(
            run_objects=run_objects,
            alpha=alpha,
            top_k=top_k,
            out_dir=subset_out,
        )
        baseline_tables.append(baseline_df)
        reference_map[subset_name] = reference

        subset_registry = registry[registry["subset_name"] == subset_name].copy()
        for run_index, run_obj in enumerate(run_objects):
            for _, reg in subset_registry.iterrows():
                repeat_id = int(reg["repeat_id"])
                seed = int(config.get("seed_base", 1000)) + run_index * 1000 + repeat_id * 100 + int(reg.name)
                run_uid = f"{run_obj.session_label}::{run_obj.run_id}"
                perturbation_spec = {
                    "perturbation_type": reg["perturbation_type"],
                    "perturbation_level": reg["perturbation_level"],
                    "perturbation_level_label": reg["perturbation_level_label"],
                }
                perturbed_run_obj, perturbation_metadata = perturb_run(
                    run_obj=run_obj,
                    perturbation_spec=perturbation_spec,
                    seed=seed,
                )
                if bool(config.get("save_perturbed_tracks", False)):
                    artifact_dir = output_dir / "artifacts"
                    artifact_dir.mkdir(parents=True, exist_ok=True)
                    artifact_name = (
                        f"{subset_name}__{run_obj.session_label}__{run_obj.run_id}"
                        f"__{reg['perturbation_type']}__{reg['perturbation_level_label']}__r{repeat_id}.csv"
                    )
                    perturbed_run_obj.track.to_csv(artifact_dir / artifact_name, index=False)

                recomputed = recompute_run_outputs(
                    perturbed_run_obj,
                    reference=reference,
                    perturbation_metadata=perturbation_metadata,
                )
                recomputed["perturbation_type"] = reg["perturbation_type"]
                recomputed["perturbation_level"] = reg["perturbation_level"]
                recomputed["repeat_id"] = repeat_id
                recomputed["seed"] = seed
                recomputed_rows.append(recomputed)
                metric_rows.append(
                    compare_outputs(
                        baseline_df=baseline_df,
                        baseline_reference=reference,
                        baseline_row=baseline_df[baseline_df["run_uid"].astype(str) == run_uid].iloc[0],
                        perturbed_row=recomputed,
                        perturbation_metadata=perturbation_metadata,
                        repeat_id=repeat_id,
                    )
                )

    baseline_all = pd.concat(baseline_tables, ignore_index=True)
    baseline_all.to_csv(output_paths["baseline_run_metrics"], index=False)

    reference_json = output_paths["baseline_reference"]
    reference_json.write_text(json.dumps(reference_map, indent=2), encoding="utf-8")

    recomputed_df = pd.DataFrame(recomputed_rows)
    recomputed_df.to_csv(output_paths["recomputed_run_metrics"], index=False)

    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(output_paths["robustness_metrics_long"], index=False)

    summary_df = build_summary_table(metrics_df)
    summary_df.to_csv(output_paths["robustness_summary_table"], index=False)

    plot_core_robustness(summary_df, output_paths["figure_core"])
    if "primary" in subset_names:
        plot_core_robustness(
            summary_df,
            output_paths["figure_primary"],
            subset_name="primary",
            figure_title="Primary Subset Robustness",
        )
    if "strict" in subset_names:
        plot_core_robustness(
            summary_df,
            output_paths["figure_strict"],
            subset_name="strict",
            figure_title="Strict Subset Sensitivity",
        )
    sanity_cfg = config.get("position_sanity_export")
    if isinstance(sanity_cfg, dict):
        export_position_sanity_figures(
            output_dir=output_dir,
            session_label=str(sanity_cfg["session_label"]),
            run_id=str(sanity_cfg["run_id"]),
            repeat_id=int(sanity_cfg.get("repeat_id", 1)),
        )

    manifest = {
        "config": config,
        "n_subsets": len(subset_names),
        "subset_names": subset_names,
        "n_baseline_runs": int(len(baseline_all)),
        "n_experiment_rows": int(len(metrics_df)),
        "output_dir": str(output_dir.resolve()),
        "output_paths": {key: str(path.resolve()) for key, path in output_paths.items()},
    }
    output_paths["run_manifest"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run trajectory and elevation robustness experiments.")
    parser.add_argument(
        "--config",
        default="experiments/robustness/config/test_run.yaml",
        help="Path to YAML config.",
    )
    args = parser.parse_args()
    config = _load_config(Path(args.config))
    manifest = run_experiment(config)
    print(f"[OK] Robustness outputs written to {manifest['output_dir']}")


if __name__ == "__main__":
    main()
