from __future__ import annotations

from pathlib import Path

import pandas as pd


V1_REFERENCE_COLUMNS = [
    "combined_load_v2",
    "z_internal",
    "z_mech",
    "z_trimp",
    "vertical_drop_m",
    "duration_s",
]

V2_RUN_LEVEL_COLUMNS = [
    "session_label",
    "subject_id",
    "run_label",
    "run_index_within_session",
    "carving_inclusion",
    "carving_inclusion_reason",
    "repeated_run_block",
    "vertical_drop_m",
    "duration_s",
    "z_internal",
    "z_mech",
    "combined_load_v2",
]


def initialize_carving_run_level_table(source_df: pd.DataFrame) -> pd.DataFrame:
    table = source_df.copy()
    if "session_label" not in table.columns:
        table["session_label"] = "TODO_session_label"
    if "subject_id" not in table.columns:
        table["subject_id"] = "TODO_subject_id"
    if "run_label" not in table.columns:
        table["run_label"] = [f"run_{idx:03d}" for idx in range(1, len(table) + 1)]
    if "run_index_within_session" not in table.columns:
        table["run_index_within_session"] = range(1, len(table) + 1)

    # TODO: replace this placeholder with the actual carving-only inclusion rule after
    # tomorrow's Polar exports are reviewed.
    if "carving_inclusion" not in table.columns:
        table["carving_inclusion"] = pd.Series([pd.NA] * len(table), dtype="object")
    if "carving_inclusion_reason" not in table.columns:
        table["carving_inclusion_reason"] = "TODO_define_rule"

    # TODO: refine repeated-runs / within-subject framing once the expanded dataset is loaded.
    if "repeated_run_block" not in table.columns:
        table["repeated_run_block"] = pd.Series([pd.NA] * len(table), dtype="object")

    for column in V2_RUN_LEVEL_COLUMNS:
        if column not in table.columns:
            table[column] = pd.NA

    ordered = table[V2_RUN_LEVEL_COLUMNS + [c for c in table.columns if c not in V2_RUN_LEVEL_COLUMNS]]
    return ordered


def compare_with_v1_schema(
    table: pd.DataFrame,
    v1_columns: list[str] | None = None,
    out_path: Path | None = None,
) -> pd.DataFrame:
    v1_columns = v1_columns or V1_REFERENCE_COLUMNS
    comparison = pd.DataFrame(
        {
            "column": sorted(set(v1_columns) | set(table.columns)),
        }
    )
    comparison["in_v1_reference"] = comparison["column"].isin(v1_columns)
    comparison["in_v2_table"] = comparison["column"].isin(table.columns)
    comparison["status"] = comparison.apply(
        lambda row: (
            "shared"
            if row["in_v1_reference"] and row["in_v2_table"]
            else "v2_only"
            if row["in_v2_table"]
            else "v1_only"
        ),
        axis=1,
    )

    # TODO: add explicit field-by-field semantic mapping once the final carving_v2 schema settles.
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        comparison.to_csv(out_path, index=False)
    return comparison
