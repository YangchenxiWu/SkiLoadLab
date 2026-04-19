from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HR dropout scaffold for carving_v2.")
    parser.add_argument(
        "--config",
        default="experiments/hr_dropout/config_template.json",
        help="Path to HR dropout config JSON.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "hr_dropout_plan.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "status": "scaffold_only",
                "config_path": str(config_path.resolve()),
                "methods": config.get("methods", []),
                "detection": config.get("dropout_detection", {}),
                "todo": [
                    "Implement short-gap detector against real exported HR timestamps.",
                    "Keep no_correction and linear interpolation as the first comparison baselines.",
                    "Treat Kalman-style correction as optional and secondary.",
                ],
            },
            handle,
            indent=2,
        )

    print(f"[OK] Wrote scaffold summary: {summary_path.resolve()}")


if __name__ == "__main__":
    main()
