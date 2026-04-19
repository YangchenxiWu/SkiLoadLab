from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run carving_v2 robustness experiment scaffold.")
    parser.add_argument(
        "--config",
        default="experiments/robustness/config_template.json",
        help="Path to robustness config JSON.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "robustness_plan.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "status": "scaffold_only",
                "config_path": str(config_path.resolve()),
                "planned_perturbations": config.get("perturbations", {}),
                "planned_metrics": config.get("metrics", []),
                "todo": [
                    "Implement perturbation generators.",
                    "Connect perturbations to segmentation and run-level fusion workflow.",
                    "Compute stability metrics after real carving_v2 data are available.",
                ],
            },
            handle,
            indent=2,
        )

    print(f"[OK] Wrote scaffold summary: {summary_path.resolve()}")


if __name__ == "__main__":
    main()
