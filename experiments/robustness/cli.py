from __future__ import annotations

import argparse
from pathlib import Path

from experiments.robustness.runner import _load_config, run_experiment


def _parse_subset_choice(subset_choice: str) -> list[str]:
    if subset_choice == "both":
        return ["primary", "strict"]
    return [subset_choice]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI for trajectory and elevation robustness experiments.")
    parser.add_argument(
        "--config",
        default="experiments/robustness/config/test_run.yaml",
        help="Path to YAML config.",
    )
    parser.add_argument(
        "--subset",
        choices=["primary", "strict", "both"],
        help="Subset selection override.",
    )
    parser.add_argument(
        "--output-dir",
        help="Explicit output directory for this run.",
    )
    parser.add_argument(
        "--long-table-path",
        help="Explicit output path for robustness_metrics_long.csv.",
    )
    parser.add_argument(
        "--summary-table-path",
        help="Explicit output path for robustness_summary_table.csv.",
    )
    parser.add_argument(
        "--manifest-path",
        help="Explicit output path for run_manifest.json.",
    )
    parser.add_argument(
        "--baseline-run-metrics-path",
        help="Explicit output path for baseline_run_metrics.csv.",
    )
    parser.add_argument(
        "--baseline-reference-path",
        help="Explicit output path for baseline_reference.json.",
    )
    parser.add_argument(
        "--perturbation-registry-path",
        help="Explicit output path for perturbation_registry.csv.",
    )
    parser.add_argument(
        "--recomputed-run-metrics-path",
        help="Explicit output path for recomputed_run_metrics.csv.",
    )
    parser.add_argument(
        "--figure-path",
        help="Explicit output path for the combined core figure.",
    )
    parser.add_argument(
        "--figure-primary-path",
        help="Explicit output path for the primary-only core figure.",
    )
    parser.add_argument(
        "--figure-strict-path",
        help="Explicit output path for the strict-only core figure.",
    )
    return parser


def _apply_cli_overrides(config: dict[str, object], args: argparse.Namespace) -> dict[str, object]:
    updated = dict(config)
    if args.subset:
        updated["subset_names"] = _parse_subset_choice(args.subset)
    if args.output_dir:
        updated["output_dir"] = args.output_dir

    output_paths = dict(updated.get("output_paths", {}))
    overrides = {
        "baseline_run_metrics": args.baseline_run_metrics_path,
        "baseline_reference": args.baseline_reference_path,
        "perturbation_registry": args.perturbation_registry_path,
        "recomputed_run_metrics": args.recomputed_run_metrics_path,
        "robustness_metrics_long": args.long_table_path,
        "robustness_summary_table": args.summary_table_path,
        "run_manifest": args.manifest_path,
        "figure_core": args.figure_path,
        "figure_primary": args.figure_primary_path,
        "figure_strict": args.figure_strict_path,
    }
    for key, value in overrides.items():
        if value:
            output_paths[key] = value
    if output_paths:
        updated["output_paths"] = output_paths
    return updated


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        parser.error(f"--config not found: {config_path}")
    config = _load_config(config_path)
    config = _apply_cli_overrides(config, args)
    manifest = run_experiment(config)
    print(f"[OK] Robustness outputs written to {manifest['output_dir']}")
    for key, path in manifest["output_paths"].items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
