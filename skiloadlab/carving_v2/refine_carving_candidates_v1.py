from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SECOND_PASS_RULES = [
    ("median_turn_amp_deg", ">=", 22.0),
    ("large_turn_block_frac", ">=", 0.50),
    ("turns_per_min", ">=", 6.0),
    ("turn_switches", ">=", 30.0),
    ("mean_abs_heading_delta_deg", ">=", 12.0),
    ("drop_per_hdist", ">=", 0.11),
]


def _count_second_pass_hits(row: pd.Series) -> int:
    hits = 0
    for field, op, threshold in SECOND_PASS_RULES:
        value = float(row[field])
        if op == ">=" and value >= threshold:
            hits += 1
    return hits


def refine_candidates_v1(inp: Path, out: Path) -> pd.DataFrame:
    df = pd.read_csv(inp)
    if "carving_label" not in df.columns:
        raise ValueError(f"Expected 'carving_label' in {inp}")

    out_df = df.copy()
    out_df["carving_label_v0"] = out_df["carving_label"]
    out_df["second_pass_rule_hits"] = out_df.apply(_count_second_pass_hits, axis=1)

    refined_labels: list[str] = []
    refined_included: list[str] = []
    refined_exclusion_reason: list[str] = []
    refined_notes: list[str] = []

    for _, row in out_df.iterrows():
        v0_label = str(row["carving_label_v0"])
        if v0_label == "carving":
            refined_labels.append("strict_carving")
            refined_included.append("yes")
            refined_exclusion_reason.append("")
            refined_notes.append("preserved_from_v0_high_specificity")
            continue

        if v0_label == "uncertain":
            if int(row["second_pass_rule_hits"]) >= 4:
                refined_labels.append("carving_like")
                refined_included.append("no")
                refined_exclusion_reason.append("sensitivity_only")
                refined_notes.append("promoted_from_uncertain_second_pass")
            else:
                refined_labels.append("non_carving_borderline")
                refined_included.append("no")
                refined_exclusion_reason.append("borderline_not_carving_like_enough")
                refined_notes.append("uncertain_second_pass_not_promoted")
            continue

        refined_labels.append("non_carving")
        refined_included.append("no")
        refined_exclusion_reason.append(str(row.get("exclusion_reason", "")) or "non_carving_v0")
        refined_notes.append(str(row.get("label_notes", "")) or "retained_non_carving_from_v0")

    out_df["carving_label_v1"] = refined_labels
    out_df["included_main_analysis_v1"] = refined_included
    out_df["exclusion_reason_v1"] = refined_exclusion_reason
    out_df["label_notes_v1"] = refined_notes

    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out, index=False)
    return out_df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refine v0 carving candidate labels into strict_carving / carving_like / borderline / non_carving."
    )
    parser.add_argument("--in", dest="inp", default="output/carving_v2_cleaned/runs_carving_candidates_v0.csv")
    parser.add_argument("--out", default="output/carving_v2_cleaned/runs_carving_candidates_v1.csv")
    args = parser.parse_args()

    out_df = refine_candidates_v1(inp=Path(args.inp), out=Path(args.out))
    counts = out_df["carving_label_v1"].value_counts(dropna=False).to_dict()
    print(f"[OK] Saved {len(out_df)} rows to {Path(args.out).resolve()}")
    print(f"[OK] Label counts v1: {counts}")


if __name__ == "__main__":
    main()
