from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


BASE_COLUMNS = [
    "session_label",
    "subject_id",
    "sport",
    "run_id",
    "start_time_utc",
    "end_time_utc",
    "duration_s",
    "vertical_drop_m",
    "speed_mean_ms",
    "speed_p95_ms",
    "vvert_mean_ms",
    "n_hr_samples",
    "hr_mean_bpm",
    "hr_max_bpm",
    "hr_min_bpm",
    "impulse_hr_above_rest_bpms",
    "edwards_trimp",
    "hr_rest_bpm",
    "hr_max_session_bpm",
    "anchor_delta_s",
]


def finalize_table(inp: Path, out: Path) -> pd.DataFrame:
    df = pd.read_csv(inp)
    if "carving_label_v1" not in df.columns:
        raise ValueError(f"Expected 'carving_label_v1' in {inp}")

    out_df = df[BASE_COLUMNS].copy()
    out_df["carving_class_final"] = df["carving_label_v1"]
    out_df["included_primary_analysis"] = out_df["carving_class_final"].map(
        lambda x: "yes" if x in {"strict_carving", "carving_like"} else "no"
    )
    out_df["included_strict_subset"] = out_df["carving_class_final"].map(
        lambda x: "yes" if x == "strict_carving" else "no"
    )

    def exclusion_reason(label: str) -> str:
        if label == "strict_carving":
            return ""
        if label == "carving_like":
            return ""
        if label == "non_carving_borderline":
            return "excluded_from_primary_borderline_non_carving"
        if label == "non_carving":
            return "excluded_from_primary_non_carving"
        return "excluded_unclassified"

    def label_notes(label: str) -> str:
        if label == "strict_carving":
            return "high_specificity_subset"
        if label == "carving_like":
            return "included_in_carving_focused_primary_set"
        if label == "non_carving_borderline":
            return "retain_for_supplement_or_exploratory_comparison"
        if label == "non_carving":
            return "not_part_of_carving_focused_analytical_set"
        return ""

    out_df["exclusion_reason_final"] = out_df["carving_class_final"].map(exclusion_reason)
    out_df["label_notes_final"] = out_df["carving_class_final"].map(label_notes)

    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out, index=False)
    return out_df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a clean final carving analysis table without intermediate v0/v1 labeling columns."
    )
    parser.add_argument("--in", dest="inp", default="output/carving_v2_cleaned/runs_carving_candidates_v1.csv")
    parser.add_argument("--out", default="output/carving_v2_cleaned/runs_carving_final.csv")
    args = parser.parse_args()

    out_df = finalize_table(inp=Path(args.inp), out=Path(args.out))
    counts = out_df["carving_class_final"].value_counts(dropna=False).to_dict()
    print(f"[OK] Saved {len(out_df)} rows to {Path(args.out).resolve()}")
    print(f"[OK] Final counts: {counts}")


if __name__ == "__main__":
    main()
