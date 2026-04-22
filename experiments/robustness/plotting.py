from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PLOT_METRICS = [
    ("segmentation_stability", "Median Segmentation Stability"),
    ("boundary_shift_mean_s", "Median Boundary Shift (s)"),
    ("vertical_drop_abs_error_m", "Median |Vertical Drop Error| (m)"),
    ("cl_alpha_abs_deviation", "Median |CL(alpha) Deviation|"),
]


def plot_core_robustness(
    summary_df: pd.DataFrame,
    out_path: Path,
    subset_name: str | None = None,
    figure_title: str | None = None,
) -> None:
    if subset_name is not None and "subset_name" in summary_df.columns:
        summary_df = summary_df[summary_df["subset_name"] == subset_name].copy()

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    axes_flat = axes.flatten()
    level_order = {"low": 0, "medium": 1, "high": 2}

    for ax, (metric_name, title) in zip(axes_flat, PLOT_METRICS):
        metric_df = summary_df[summary_df["metric_name"] == metric_name].copy()
        for perturbation_type, group in metric_df.groupby("perturbation_type"):
            if "perturbation_level_label" in group.columns:
                group = group.copy()
                group["_x"] = group["perturbation_level_label"].map(level_order).fillna(group["perturbation_level"])
                group = group.sort_values("_x")
                x = group["perturbation_level_label"]
            else:
                group = group.sort_values("perturbation_level")
                x = group["perturbation_level"]
            ax.plot(
                x,
                group["median"],
                marker="o",
                linewidth=1.8,
                label=str(perturbation_type),
            )
        ax.set_title(title)
        ax.set_xlabel("Perturbation Level")
        ax.grid(alpha=0.25)

    axes_flat[0].set_ylabel("Stability")
    axes_flat[1].set_ylabel("Shift")
    axes_flat[2].set_ylabel("Magnitude")
    axes_flat[3].set_ylabel("Magnitude")
    handles, labels = axes_flat[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=min(4, len(labels)), frameon=False)
    if figure_title:
        fig.suptitle(figure_title)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def export_position_sanity_figures(
    output_dir: Path,
    session_label: str,
    run_id: str,
    repeat_id: int = 1,
) -> None:
    artifact_dir = output_dir / "artifacts"
    baseline_csv = output_dir / "baseline_run_metrics.csv"
    recomputed_csv = output_dir / "recomputed_run_metrics.csv"

    low = artifact_dir / f"primary__{session_label}__{run_id}__position__low__r{repeat_id}.csv"
    medium = artifact_dir / f"primary__{session_label}__{run_id}__position__medium__r{repeat_id}.csv"
    if not low.exists() or not medium.exists():
        return

    baseline_df = pd.read_csv(baseline_csv)
    recomputed_df = pd.read_csv(recomputed_csv)
    base_row = baseline_df[
        (baseline_df["session_label"] == session_label) & (baseline_df["run_id"] == run_id)
    ].iloc[0]
    low_row = recomputed_df[
        (recomputed_df["session_label"] == session_label)
        & (recomputed_df["run_id"] == run_id)
        & (recomputed_df["perturbation_type"] == "position")
        & (recomputed_df["perturbation_level"] == 2.0)
        & (recomputed_df["repeat_id"] == repeat_id)
    ].iloc[0]
    med_row = recomputed_df[
        (recomputed_df["session_label"] == session_label)
        & (recomputed_df["run_id"] == run_id)
        & (recomputed_df["perturbation_type"] == "position")
        & (recomputed_df["perturbation_level"] == 5.0)
        & (recomputed_df["repeat_id"] == repeat_id)
    ].iloc[0]

    baseline_track_path = Path("output/carving_v2_cleaned") / session_label / "track_signals.csv"
    baseline_track = pd.read_csv(baseline_track_path)
    baseline_track["time"] = pd.to_datetime(baseline_track["time"], utc=True, format="mixed")
    st = pd.to_datetime(base_row["start_time_utc"], utc=True, format="mixed")
    en = pd.to_datetime(base_row["end_time_utc"], utc=True, format="mixed")
    baseline_track = baseline_track[(baseline_track["time"] >= st) & (baseline_track["time"] <= en)].copy()

    low_track = pd.read_csv(low)
    medium_track = pd.read_csv(medium)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(baseline_track["lon"], baseline_track["lat"], label="baseline", linewidth=2.2)
    ax.plot(low_track["lon"], low_track["lat"], label="position low", linewidth=1.6)
    ax.plot(medium_track["lon"], medium_track["lat"], label="position medium", linewidth=1.6)
    ax.set_title(f"TEST Artifact: Position Perturbation Sanity\n{session_label} {run_id}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.savefig(output_dir / "TEST_position_trajectory_overlay.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(len(baseline_track)), baseline_track["elev_m"], label="baseline", linewidth=2.2)
    ax.plot(range(len(low_track)), low_track["elev_m"], label="position low", linewidth=1.6)
    ax.plot(range(len(medium_track)), medium_track["elev_m"], label="position medium", linewidth=1.6)
    ax.set_title(f"TEST Artifact: Position Perturbation Elevation Profile\n{session_label} {run_id}")
    ax.set_xlabel("Point Index")
    ax.set_ylabel("Elevation (m)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.savefig(output_dir / "TEST_position_elevation_profile.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
