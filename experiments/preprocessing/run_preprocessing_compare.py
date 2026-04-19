from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run preprocessing comparison scaffold.")
    parser.add_argument(
        "--config",
        default="experiments/preprocessing/config_template.json",
        help="Path to preprocessing config JSON.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "preprocessing_plan.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "status": "scaffold_only",
                "config_path": str(config_path.resolve()),
                "methods": config.get("methods", []),
                "signal_column": config.get("signal_column"),
                "todo": [
                    "Implement a reusable smoothing baseline.",
                    "Reuse the same comparison interface for HR and trajectory/elevation signals.",
                    "Only promote Kalman-style filtering if simpler baselines are insufficient.",
                ],
            },
            handle,
            indent=2,
        )

    print(f"[OK] Wrote scaffold summary: {summary_path.resolve()}")


if __name__ == "__main__":
    main()
