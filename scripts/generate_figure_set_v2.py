from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

cache_dir = Path(os.environ.get("SKILOADLAB_MPL_CACHE_DIR", "/tmp/skiloadlab_mpl"))
cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Rectangle


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "docs" / "figures_v2"
FIGURE_SCRIPT = "scripts/generate_figure_set_v2.py"

RUNS_FINAL_CSV = REPO_ROOT / "output" / "carving_v2_cleaned" / "runs_carving_final.csv"
FORMAL_BASELINE_CSV = REPO_ROOT / "experiments" / "robustness" / "results" / "formal_run" / "baseline_run_metrics.csv"
FORMAL_LONG_CSV = REPO_ROOT / "experiments" / "robustness" / "results" / "formal_run" / "robustness_metrics_long.csv"
FORMAL_SUMMARY_CSV = REPO_ROOT / "experiments" / "robustness" / "results" / "formal_run" / "robustness_summary_table.csv"
ALPHA_SUMMARY_CSV = REPO_ROOT / "output" / "alpha_sweep_summary.csv"

FONT_FAMILY = "DejaVu Sans"
BASE_FONT_SIZE = 10
PANEL_TITLE_SIZE = 11
PERTURBATION_ORDER = ["elevation", "position", "sampling", "temporal"]
PERTURBATION_COLORS = {
    "elevation": "#1b6ca8",
    "position": "#d17c00",
    "sampling": "#2f855a",
    "temporal": "#b33c3c",
}
LEVEL_ORDER = ["low", "medium", "high"]
LEVEL_TO_X = {name: idx for idx, name in enumerate(LEVEL_ORDER)}
SUBSET_ORDER = ["combined", "primary", "strict"]
SUBSET_LABELS = {
    "combined": "Combined formal run",
    "primary": "Primary subset",
    "strict": "Strict subset",
}
ALPHA_COLORS = {
    "corr_comb_internal": "#1b6ca8",
    "corr_comb_mech": "#d17c00",
    "score_balanced": "#2f855a",
}
PHASE_ORDER = ["early", "mid", "late"]
PHASE_COLORS = {
    "z_internal": "#1b6ca8",
    "z_mech": "#d17c00",
    "combined_load_v2": "#2f855a",
}

ROBUSTNESS_METRICS = [
    {
        "metric_name": "segmentation_stability",
        "title": "Segmentation Stability",
        "ylabel": "IoU stability",
    },
    {
        "metric_name": "boundary_shift_mean_s",
        "title": "Boundary Shift (s)",
        "ylabel": "Mean absolute shift (s)",
    },
    {
        "metric_name": "vertical_drop_abs_error_m",
        "title": "Vertical Drop Error (m)",
        "ylabel": "Absolute error (m)",
    },
    {
        "metric_name": "cl_alpha_abs_deviation",
        "title": "|CL(alpha) Deviation|",
        "ylabel": "Absolute deviation",
    },
]


@dataclass
class FigureRecord:
    figure_id: str
    title: str
    purpose: str
    recommended_section: str
    source_inputs: list[str]
    generating_script: str
    output_path: str
    status: str
    caption_draft: str
    output_exists: bool


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": FONT_FAMILY,
            "font.size": BASE_FONT_SIZE,
            "axes.titlesize": PANEL_TITLE_SIZE,
            "axes.labelsize": BASE_FONT_SIZE,
            "xtick.labelsize": BASE_FONT_SIZE - 1,
            "ytick.labelsize": BASE_FONT_SIZE - 1,
            "legend.fontsize": BASE_FONT_SIZE - 1,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.18,
            "grid.linewidth": 0.6,
            "savefig.bbox": "tight",
        }
    )


def relpath(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def save_figure(fig: plt.Figure, out_path: Path, *, dpi: int = 300, also_svg: bool = True, also_pdf: bool = True) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    if also_svg:
        fig.savefig(out_path.with_suffix(".svg"), facecolor="white")
    if also_pdf:
        fig.savefig(out_path.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


def summarise_long_metrics(long_df: pd.DataFrame, subset_name: str | None = None) -> pd.DataFrame:
    df = long_df.copy()
    if subset_name is not None:
        df = df[df["subset_name"] == subset_name].copy()
    grouped = (
        df.groupby(["perturbation_type", "perturbation_level_label"], as_index=False)
        .agg(
            segmentation_stability=("segmentation_stability", list),
            boundary_shift_mean_s=("boundary_shift_mean_s", list),
            vertical_drop_abs_error_m=("vertical_drop_abs_error_m", list),
            cl_alpha_abs_deviation=("cl_alpha_abs_deviation", list),
            top_k_consistency=("top_k_consistency", list),
            mean_absolute_rank_shift=("mean_absolute_rank_shift", list),
            rank_spearman=("rank_spearman", list),
            phase_contrast_abs_deviation=("phase_contrast_abs_deviation", list),
        )
    )
    rows: list[dict[str, object]] = []
    metric_names = [
        "segmentation_stability",
        "boundary_shift_mean_s",
        "vertical_drop_abs_error_m",
        "cl_alpha_abs_deviation",
        "top_k_consistency",
        "mean_absolute_rank_shift",
        "rank_spearman",
        "phase_contrast_abs_deviation",
    ]
    for _, row in grouped.iterrows():
        for metric_name in metric_names:
            vals = pd.to_numeric(pd.Series(row[metric_name]), errors="coerce").dropna()
            rows.append(
                {
                    "subset_name": subset_name or "combined",
                    "perturbation_type": row["perturbation_type"],
                    "perturbation_level_label": row["perturbation_level_label"],
                    "metric_name": metric_name,
                    "n": int(len(vals)),
                    "median": float(vals.median()) if len(vals) else np.nan,
                    "mean": float(vals.mean()) if len(vals) else np.nan,
                    "sd": float(vals.std()) if len(vals) > 1 else np.nan,
                    "q1": float(vals.quantile(0.25)) if len(vals) else np.nan,
                    "q3": float(vals.quantile(0.75)) if len(vals) else np.nan,
                    "iqr": float(vals.quantile(0.75) - vals.quantile(0.25)) if len(vals) else np.nan,
                }
            )
    out = pd.DataFrame(rows)
    out["perturbation_level_label"] = pd.Categorical(out["perturbation_level_label"], categories=LEVEL_ORDER, ordered=True)
    return out.sort_values(["metric_name", "perturbation_type", "perturbation_level_label"]).reset_index(drop=True)


def metric_rows(summary_df: pd.DataFrame, metric_name: str) -> pd.DataFrame:
    out = summary_df[summary_df["metric_name"] == metric_name].copy()
    out["perturbation_level_label"] = pd.Categorical(out["perturbation_level_label"], categories=LEVEL_ORDER, ordered=True)
    return out.sort_values(["perturbation_type", "perturbation_level_label"])


def plot_robustness_grid(summary_df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.4), constrained_layout=True)
    axes = axes.flatten()

    for ax, metric in zip(axes, ROBUSTNESS_METRICS):
        metric_df = metric_rows(summary_df, metric["metric_name"])
        for perturbation_type in PERTURBATION_ORDER:
            group = metric_df[metric_df["perturbation_type"] == perturbation_type].copy()
            if group.empty:
                continue
            x = [LEVEL_TO_X[val] for val in group["perturbation_level_label"].astype(str)]
            y = pd.to_numeric(group["median"], errors="coerce").to_numpy(dtype=float)
            q1 = pd.to_numeric(group["q1"], errors="coerce").to_numpy(dtype=float)
            q3 = pd.to_numeric(group["q3"], errors="coerce").to_numpy(dtype=float)
            yerr = np.vstack([np.clip(y - q1, 0, None), np.clip(q3 - y, 0, None)])
            ax.errorbar(
                x,
                y,
                yerr=yerr,
                color=PERTURBATION_COLORS[perturbation_type],
                marker="o",
                linewidth=2.0,
                markersize=5,
                capsize=3,
                label=perturbation_type,
            )
        ax.set_title(metric["title"], loc="left", fontweight="bold")
        ax.set_xticks(range(len(LEVEL_ORDER)), LEVEL_ORDER)
        ax.set_xlabel("Perturbation strength")
        ax.set_ylabel(metric["ylabel"])
        ax.grid(True, axis="y", alpha=0.22)
        if metric["metric_name"] == "segmentation_stability":
            ax.set_ylim(bottom=0.0, top=min(1.02, max(1.0, ax.get_ylim()[1])))
        else:
            ax.set_ylim(bottom=0.0)

    legend_handles = [
        Line2D([0], [0], color=PERTURBATION_COLORS[name], marker="o", linewidth=2.0, label=name)
        for name in PERTURBATION_ORDER
    ]
    fig.legend(legend_handles, PERTURBATION_ORDER, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.02))
    save_figure(fig, out_path)


def make_workflow_architecture() -> FigureRecord:
    fig, ax = plt.subplots(figsize=(16, 8.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    regions = [
        ("Upstream context", (0.02, 0.06, 0.22, 0.88), "#eef4f8"),
        ("Core analytical workflow", (0.26, 0.06, 0.59, 0.88), "#f7f7f4"),
        ("Robustness extension", (0.875, 0.06, 0.105, 0.88), "#f8efef"),
    ]
    for label, (x, y, w, h), color in regions:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="#c7c7c7", linewidth=1.2))
        ax.text(x + 0.01, y + h - 0.03, label, fontsize=12, fontweight="bold", va="top")

    def box(
        x: float,
        y: float,
        w: float,
        h: float,
        lines: list[str],
        facecolor: str = "white",
        fontsize: float = 9.4,
        lw: float = 1.0,
        edgecolor: str = "#666666",
    ) -> dict[str, float]:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=facecolor, edgecolor=edgecolor, linewidth=lw))
        ax.text(x + w / 2, y + h / 2, "\n".join(lines), ha="center", va="center", fontsize=fontsize)
        return {
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "cx": x + w / 2,
            "cy": y + h / 2,
            "left": x,
            "right": x + w,
            "bottom": y,
            "top": y + h,
        }

    def arrow(
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        color: str = "#555555",
        linewidth: float = 1.6,
        scale: float = 13.0,
    ) -> None:
        patch = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=scale,
            linewidth=linewidth,
            color=color,
            connectionstyle="arc3,rad=0",
        )
        ax.add_patch(patch)

    def elbow_arrow(
        start: tuple[float, float],
        corner: tuple[float, float],
        end: tuple[float, float],
        *,
        color: str = "#555555",
        linewidth: float = 1.6,
        scale: float = 13.0,
    ) -> None:
        ax.plot(
            [start[0], corner[0]],
            [start[1], corner[1]],
            color=color,
            linewidth=linewidth,
            solid_capstyle="butt",
        )
        arrow(corner, end, color=color, linewidth=linewidth, scale=scale)

    def link(
        a: dict[str, float],
        b: dict[str, float],
        side_a: str,
        side_b: str,
        *,
        color: str = "#555555",
        linewidth: float = 1.6,
        scale: float = 13.0,
    ) -> None:
        anchors_a = {
            "left": (a["left"], a["cy"]),
            "right": (a["right"], a["cy"]),
            "top": (a["cx"], a["top"]),
            "bottom": (a["cx"], a["bottom"]),
        }
        anchors_b = {
            "left": (b["left"], b["cy"]),
            "right": (b["right"], b["cy"]),
            "top": (b["cx"], b["top"]),
            "bottom": (b["cx"], b["bottom"]),
        }
        arrow(anchors_a[side_a], anchors_b[side_b], color=color, linewidth=linewidth, scale=scale)

    def anchor(node: dict[str, float], side: str) -> tuple[float, float]:
        return {
            "left": (node["left"], node["cy"]),
            "right": (node["right"], node["cy"]),
            "top": (node["cx"], node["top"]),
            "bottom": (node["cx"], node["bottom"]),
        }[side]

    # All positions below are fixed manual coordinates. Do not replace with
    # graph/layout packing; the figure is a controlled architecture schematic.
    raw = box(0.045, 0.69, 0.17, 0.105, ["Session-level", "raw trajectory / GPX"])
    dem = box(0.045, 0.50, 0.17, 0.105, ["DEM / terrain-", "elevation context"])
    hr_stream = box(0.045, 0.31, 0.17, 0.105, ["Session-level", "HR stream"])

    main_x = 0.445
    main_w = 0.19
    main_h = 0.075
    parse = box(main_x, 0.800, main_w, main_h, ["Trajectory parsing +", "elevation enrichment"], "#fcfcfc")
    segment = box(main_x, 0.685, main_w, main_h, ["Downhill-run", "segmentation"], "#fcfcfc")
    hr = box(main_x, 0.570, main_w, main_h, ["HR anchoring and", "run-level slicing"], "#fcfcfc")
    label = box(main_x, 0.455, main_w, main_h, ["Carving-focused", "staged labeling"], "#fcfcfc")
    run_table = box(main_x, 0.340, main_w, main_h, ["Run-level", "table"], "#fcfcfc")

    internal = box(0.345, 0.220, 0.135, 0.075, ["Internal run-level", "summary"], "#fcfcfc", fontsize=8.8)
    mech = box(0.555, 0.220, 0.135, 0.075, ["Mechanical run-level", "summary"], "#fcfcfc", fontsize=8.8)

    standard_frame = box(0.345, 0.055, 0.345, 0.105, [""], "#fbfbfb")
    ax.text(
        standard_frame["cx"],
        standard_frame["top"] - 0.018,
        "Within-dataset standardization",
        fontsize=9.0,
        fontweight="bold",
        ha="center",
        va="top",
        color="#4f4f4f",
    )
    z_internal_box = box(0.385, 0.070, 0.105, 0.045, ["z_internal"], "#ffffff", fontsize=9.0)
    z_mech_box = box(0.545, 0.070, 0.105, 0.045, ["z_mech"], "#ffffff", fontsize=9.0)

    cl_alpha = box(0.695, 0.255, 0.065, 0.060, ["CL(alpha)"], "#fcfcfc", fontsize=8.8)
    alpha_diag = box(0.695, 0.175, 0.065, 0.060, ["Alpha-sweep", "diagnostics"], "#fcfcfc", fontsize=8.5)

    comparison_frame = box(0.775, 0.095, 0.070, 0.225, [""], "#f3f3f1", edgecolor="#b8b8b8")
    ax.text(
        comparison_frame["cx"],
        comparison_frame["top"] - 0.018,
        "Comparison\ndescriptors",
        fontsize=7.2,
        fontweight="bold",
        color="#5a5a5a",
        ha="center",
        va="top",
    )
    topk = box(0.785, 0.220, 0.050, 0.048, ["Top-k", "consistency"], "#ffffff", fontsize=7.6, edgecolor="#999999")
    phase = box(0.785, 0.145, 0.050, 0.048, ["Phase-wise", "contrast"], "#ffffff", fontsize=7.6, edgecolor="#999999")

    robustness_centers = [
        box(0.895, 0.340, 0.075, 0.075, ["Perturb"]),
        box(0.895, 0.245, 0.075, 0.075, ["Recompute"]),
        box(0.895, 0.150, 0.075, 0.075, ["Compare"]),
        box(0.895, 0.055, 0.075, 0.075, ["Summarize"]),
    ]

    elbow_arrow(anchor(raw, "right"), (parse["left"], raw["cy"]), anchor(parse, "left"))
    elbow_arrow(anchor(dem, "right"), (parse["left"], dem["cy"]), anchor(parse, "left"))
    elbow_arrow(anchor(hr_stream, "right"), (hr["left"], hr_stream["cy"]), anchor(hr, "left"))

    link(parse, segment, "bottom", "top")
    link(segment, hr, "bottom", "top")
    link(hr, label, "bottom", "top")
    link(label, run_table, "bottom", "top")
    elbow_arrow(anchor(run_table, "bottom"), (internal["cx"], run_table["bottom"]), anchor(internal, "top"))
    elbow_arrow(anchor(run_table, "bottom"), (mech["cx"], run_table["bottom"]), anchor(mech, "top"))
    arrow((internal["cx"], internal["bottom"]), (internal["cx"], standard_frame["top"]))
    arrow((mech["cx"], mech["bottom"]), (mech["cx"], standard_frame["top"]))
    elbow_arrow(anchor(standard_frame, "right"), (standard_frame["right"], cl_alpha["cy"]), anchor(cl_alpha, "left"))
    link(cl_alpha, alpha_diag, "bottom", "top")

    elbow_arrow(anchor(cl_alpha, "right"), (cl_alpha["right"], topk["cy"]), anchor(topk, "left"), color="#9a9a9a", linewidth=1.0, scale=11.0)
    elbow_arrow(anchor(cl_alpha, "right"), (cl_alpha["right"], phase["cy"]), anchor(phase, "left"), color="#9a9a9a", linewidth=1.0, scale=11.0)

    link(run_table, robustness_centers[0], "right", "left")
    for idx in range(len(robustness_centers) - 1):
        link(robustness_centers[idx], robustness_centers[idx + 1], "bottom", "top")

    out_path = OUT_DIR / "fig01_workflow_architecture.png"
    save_figure(fig, out_path, also_svg=True, also_pdf=True)
    return FigureRecord(
        figure_id="fig01",
        title="Workflow architecture of the carving-focused analytical pipeline",
        purpose="Show the analytical object hierarchy, standardization layer, fusion layer, comparison layer, and robustness extension without collapsing them into script-level details.",
        recommended_section="Methods",
        source_inputs=[
            relpath(REPO_ROOT / "skiloadlab" / "carving_v2" / "run_level_from_polar.py"),
            relpath(REPO_ROOT / "skiloadlab" / "carving_v2" / "finalize_carving_analysis_table.py"),
            relpath(REPO_ROOT / "skiloadlab" / "core_model.py"),
            relpath(REPO_ROOT / "skiloadlab" / "core_compare.py"),
            relpath(REPO_ROOT / "experiments" / "robustness" / "README.md"),
        ],
        generating_script=FIGURE_SCRIPT,
        output_path=relpath(out_path),
        status="core",
        caption_draft=(
            "Workflow architecture for the carving-focused analytical pipeline. The schematic "
            "separates upstream measurement context from the core run-level analysis and the "
            "downstream robustness extension. Raw session-level trajectory, DEM/elevation, and "
            "heart-rate streams are processed into segmented downhill runs, staged carving labels, "
            "and a run-level table. Internal and mechanical run-level summaries are standardized "
            "within the analysis set and fused as `CL(alpha)`. Comparison descriptors and "
            "perturbation-recomputation outputs are shown as downstream analytical layers rather "
            "than as inputs to the fusion equation."
        ),
        output_exists=out_path.exists(),
    )


def make_sample_flow(runs_df: pd.DataFrame) -> list[FigureRecord]:
    counts = runs_df["carving_class_final"].value_counts().to_dict()
    start_dates = pd.to_datetime(runs_df["start_time_utc"], utc=True, format="mixed").dt.date
    date_range = f"{start_dates.min()} to {start_dates.max()}"

    summary_table = pd.DataFrame(
        [
            {"group": "Total valid runs", "n_runs": int(len(runs_df)), "note": "All downhill-valid runs retained before carving-focused labeling"},
            {"group": "Sessions", "n_runs": int(runs_df['session_label'].nunique()), "note": f"Recording window: {date_range}"},
            {"group": "strict_carving", "n_runs": int(counts.get("strict_carving", 0)), "note": "High-confidence subset nested within the primary analytical set"},
            {"group": "carving_like", "n_runs": int(counts.get("carving_like", 0)), "note": "Included in the primary analytical set"},
            {"group": "Primary analytical set", "n_runs": int(counts.get("strict_carving", 0) + counts.get("carving_like", 0)), "note": "Defined as strict_carving + carving_like"},
            {"group": "non_carving_borderline", "n_runs": int(counts.get("non_carving_borderline", 0)), "note": "Excluded from the primary carving-focused set"},
            {"group": "non_carving", "n_runs": int(counts.get("non_carving", 0)), "note": "Excluded from the primary carving-focused set"},
        ]
    )

    csv_path = OUT_DIR / "tab01_sample_flow.csv"
    md_path = OUT_DIR / "tab01_sample_flow.md"
    summary_table.to_csv(csv_path, index=False)
    md_lines = [
        "| Group | n_runs | Note |",
        "|---|---:|---|",
    ]
    for _, row in summary_table.iterrows():
        md_lines.append(f"| {row['group']} | {row['n_runs']} | {row['note']} |")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(12.5, 5.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def node(x: float, y: float, w: float, h: float, title: str, subtitle: str, facecolor: str) -> tuple[float, float]:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=facecolor, edgecolor="#666666", linewidth=1.0))
        ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", fontsize=11, fontweight="bold")
        ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=9)
        return x + w / 2, y + h / 2

    def flow_arrow(start: tuple[float, float], end: tuple[float, float]) -> None:
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.2,
                color="#5f5f5f",
            )
        )

    total = node(0.04, 0.35, 0.18, 0.26, "64 valid downhill runs", "4 sessions\n2026-02-03 to 2026-02-06", "#eef4f8")
    label = node(0.30, 0.35, 0.18, 0.26, "Four-class labeling", "strict_carving\ncarving_like\nnon_carving_borderline\nnon_carving", "#f6f6f2")
    primary = node(0.58, 0.48, 0.18, 0.20, "Primary analytical set", "27 runs\nstrict_carving + carving_like", "#eef7ef")
    strict = node(0.80, 0.54, 0.15, 0.14, "Strict subset", "7 runs\nnested inside primary", "#e8f0f8")
    excluded = node(0.58, 0.16, 0.18, 0.20, "Excluded from primary", "37 runs\nborderline + non-carving", "#f8efef")
    split = node(0.80, 0.18, 0.15, 0.16, "Excluded classes", "19 borderline\n18 non-carving", "#fcf5f5")

    flow_arrow((0.22, 0.48), (0.30, 0.48))
    flow_arrow((0.48, 0.52), (0.58, 0.58))
    flow_arrow((0.48, 0.44), (0.58, 0.26))
    flow_arrow((0.76, 0.58), (0.80, 0.61))
    flow_arrow((0.76, 0.26), (0.80, 0.26))
    ax.text(0.76, 0.72, "strict subset nested in primary set", fontsize=8.4, ha="center", color="#4a4a4a")

    out_path = OUT_DIR / "fig02_sample_flow.png"
    save_figure(fig, out_path)
    records = [
        FigureRecord(
            figure_id="fig02",
            title="Sample flow and analytical subset structure",
            purpose="Show how the 64 valid downhill runs were labeled into four classes and how the primary and strict subsets are nested.",
            recommended_section="Methods / Results opening",
            source_inputs=[relpath(RUNS_FINAL_CSV)],
            generating_script=FIGURE_SCRIPT,
            output_path=relpath(out_path),
            status="core",
            caption_draft=(
                "Sample flow and analytical subset structure for the carving-focused dataset. "
                "Four Polar-recorded sessions collected from 2026-02-03 to 2026-02-06 yielded "
                "64 valid downhill runs before carving-focused labeling. The primary analytical "
                "set contained 27 runs, defined as `strict_carving` (n = 7) plus `carving_like` "
                "(n = 20). The strict subset contained only the 7 `strict_carving` runs and is "
                "nested within the primary set rather than an independent sample. The remaining "
                "37 valid downhill runs were excluded from the primary carving-focused analysis "
                "(`non_carving_borderline`, n = 19; `non_carving`, n = 18)."
            ),
            output_exists=out_path.exists(),
        ),
        FigureRecord(
            figure_id="tab01",
            title="Sample flow summary table",
            purpose="Provide a manuscript-ready tabular version of the carving-focused sample counts and subset definitions.",
            recommended_section="Methods / Supplementary",
            source_inputs=[relpath(RUNS_FINAL_CSV)],
            generating_script=FIGURE_SCRIPT,
            output_path=relpath(csv_path),
            status="core",
            caption_draft=(
                "Tabular summary of the same sample-flow accounting shown in fig02. The table "
                "reports the 64 valid downhill runs, the 4 recording sessions, class counts for "
                "`strict_carving` (n = 7), `carving_like` (n = 20), `non_carving_borderline` "
                "(n = 19), and `non_carving` (n = 18), and the resulting primary analytical set "
                "(n = 27). The strict subset is explicitly marked as nested within the primary set."
            ),
            output_exists=csv_path.exists() and md_path.exists(),
        ),
    ]
    return records


def make_alpha_sweep(alpha_df: pd.DataFrame) -> FigureRecord:
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    curve_labels = {
        "corr_comb_internal": "Correlation with internal component",
        "corr_comb_mech": "Correlation with mechanical component",
        "score_balanced": "Balance-oriented score",
    }
    x = pd.to_numeric(alpha_df["alpha"], errors="coerce")
    for col in ["corr_comb_internal", "corr_comb_mech", "score_balanced"]:
        y = pd.to_numeric(alpha_df[col], errors="coerce")
        mask = x.notna() & y.notna()
        ax.plot(
            x[mask],
            y[mask],
            color=ALPHA_COLORS[col],
            marker="o",
            linewidth=2.2,
            markersize=4.8,
            label=curve_labels[col],
        )
    ax.set_xlabel("alpha")
    ax.set_ylabel("Diagnostic score / correlation")
    ax.set_title("Alpha-sweep diagnostics", loc="left", fontweight="bold")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(bottom=min(0.0, float(alpha_df[["corr_comb_internal", "corr_comb_mech", "score_balanced"]].min().min()) - 0.05), top=1.02)
    ax.legend(frameon=False, loc="lower center", ncol=1)

    out_path = OUT_DIR / "fig03_alpha_sweep.png"
    save_figure(fig, out_path)
    return FigureRecord(
        figure_id="fig03",
        title="Alpha-sweep diagnostics of the run-level fusion model",
        purpose="The figure diagnoses weighting trade-offs across alpha and does not claim a universal optimal alpha.",
        recommended_section="Results",
        source_inputs=[relpath(ALPHA_SUMMARY_CSV)],
        generating_script=FIGURE_SCRIPT,
        output_path=relpath(out_path),
        status="core",
        caption_draft=(
            "Alpha-sweep diagnostics for the run-level fusion model. The fused score was computed "
            "as `CL(alpha) = alpha * z_internal + (1 - alpha) * z_mech` over alpha values from 0 "
            "to 1 in 0.05 increments using the demo-compatible run-level input table (n = 14). "
            "Lines show the correlation between `CL(alpha)` and the internal component, the "
            "correlation between `CL(alpha)` and the mechanical component, and the balance-oriented "
            "score defined as the smaller of those two correlations. Points are deterministic grid "
            "evaluations; no error bars are shown. The balanced diagnostic peaked at `alpha = 0.5` "
            "in this dataset-specific sweep, which was used as the fixed fusion setting for "
            "robustness analyses."
        ),
        output_exists=out_path.exists(),
    )


def make_core_robustness_figures(long_df: pd.DataFrame, summary_df: pd.DataFrame) -> list[FigureRecord]:
    records: list[FigureRecord] = []
    combined_summary = summarise_long_metrics(long_df, subset_name=None)
    paths = [
        ("fig04", "fig04_robustness_core.png", combined_summary, "Supplementary", "supplementary", "Pooled robustness figure for the combined formal run", "Retain the pooled combined robustness view as supplementary context rather than as a main-text result, because the strict subset is nested within the primary analytical set."),
        ("fig05", "fig05_robustness_primary.png", summary_df[summary_df["subset_name"] == "primary"].copy(), "Results", "core", "Primary-only robustness figure", "Isolate the perturbation-response pattern for the primary analytical subset without pooling the nested strict subset back into the same summary."),
        ("fig06", "fig06_robustness_strict.png", summary_df[summary_df["subset_name"] == "strict"].copy(), "Supplementary", "supplementary", "Strict-only robustness figure", "Show whether the high-confidence strict subset retains the same directional robustness narrative under the formal perturbation families."),
    ]
    for figure_id, filename, data, section, status, title, purpose in paths:
        out_path = OUT_DIR / filename
        plot_robustness_grid(data, out_path)
        if figure_id == "fig04":
            caption = (
                "Supplementary pooled robustness summary for the combined formal run. This display "
                "pools the primary and strict robustness outputs for context only; it should not be "
                "interpreted as an independent enlarged sample because the strict subset is nested "
                "within the primary analytical set. The pooled display contains 34 baseline subset "
                "entries (27 primary entries plus 7 strict-subset entries) and 4080 "
                "perturbation-comparison rows across four perturbation families, three strengths, "
                "and 10 repeats. Points show median values for each family-strength condition "
                "(n = 340 comparisons per point), and vertical error bars show the interquartile "
                "range (Q1-Q3). Panels report interval-overlap segmentation stability, mean "
                "absolute boundary shift, absolute vertical-drop error, and absolute `CL(alpha)` "
                "deviation computed with `alpha = 0.5`."
            )
        elif figure_id == "fig05":
            caption = (
                "Primary-only robustness summary for the main analytical set. The figure includes "
                "the primary carving-focused subset only (`strict_carving` plus `carving_like`, "
                "n = 27) and does not pool the nested strict subset back into the same display. "
                "Four perturbation families were evaluated at low, medium, and high strengths: "
                "elevation noise (2/5/10 m), position jitter (2/5/10 m), sampling down-selection "
                "(stride 2/3/5), and temporal jitter (0.75/1.5/3.0 s), with 10 repeated "
                "realizations per condition. Points show median perturbation-comparison values "
                "for each family-strength condition (n = 270 comparisons per point); vertical "
                "error bars show the interquartile range (Q1-Q3). Panels report interval-overlap "
                "segmentation stability, mean absolute boundary shift in seconds, absolute "
                "vertical-drop error in metres, and absolute deviation in `CL(alpha)` computed "
                "with `alpha = 0.5`."
            )
        else:
            caption = (
                "Strict-only supplementary robustness summary for the nested high-confidence "
                "subset (`strict_carving`, n = 7). The same four perturbation families and three "
                "strengths used in the primary robustness analysis are shown: elevation noise "
                "(2/5/10 m), position jitter (2/5/10 m), sampling down-selection (stride 2/3/5), "
                "and temporal jitter (0.75/1.5/3.0 s), with 10 repeated realizations per "
                "condition. Points show median perturbation-comparison values for each "
                "family-strength condition (n = 70 comparisons per point); vertical error bars "
                "show the interquartile range (Q1-Q3). Panels report interval-overlap "
                "segmentation stability, mean absolute boundary shift in seconds, absolute "
                "vertical-drop error in metres, and absolute deviation in `CL(alpha)` computed "
                "with `alpha = 0.5`."
            )
        records.append(
            FigureRecord(
                figure_id=figure_id,
                title=title,
                purpose=purpose,
                recommended_section=section,
                source_inputs=[relpath(FORMAL_LONG_CSV), relpath(FORMAL_SUMMARY_CSV)],
                generating_script=FIGURE_SCRIPT,
                output_path=relpath(out_path),
                status=status,
                caption_draft=caption,
                output_exists=out_path.exists(),
            )
        )
    return records


def make_subset_comparison(long_df: pd.DataFrame) -> FigureRecord:
    summary_map = {
        "combined": summarise_long_metrics(long_df, subset_name=None),
        "primary": summarise_long_metrics(long_df, subset_name="primary"),
        "strict": summarise_long_metrics(long_df, subset_name="strict"),
    }
    fig, axes = plt.subplots(3, 4, figsize=(16, 10), constrained_layout=True, sharex=True)

    for row_idx, subset_name in enumerate(SUBSET_ORDER):
        for col_idx, metric in enumerate(ROBUSTNESS_METRICS):
            ax = axes[row_idx, col_idx]
            metric_df = metric_rows(summary_map[subset_name], metric["metric_name"])
            for perturbation_type in PERTURBATION_ORDER:
                group = metric_df[metric_df["perturbation_type"] == perturbation_type].copy()
                if group.empty:
                    continue
                x = [LEVEL_TO_X[val] for val in group["perturbation_level_label"].astype(str)]
                y = pd.to_numeric(group["median"], errors="coerce").to_numpy(dtype=float)
                ax.plot(x, y, marker="o", linewidth=1.8, color=PERTURBATION_COLORS[perturbation_type])
            if row_idx == 0:
                ax.set_title(metric["title"], loc="left", fontweight="bold")
            if col_idx == 0:
                ax.set_ylabel(SUBSET_LABELS[subset_name])
            if row_idx == len(SUBSET_ORDER) - 1:
                ax.set_xticks(range(len(LEVEL_ORDER)), LEVEL_ORDER)
                ax.set_xlabel("Strength")
            else:
                ax.set_xticks(range(len(LEVEL_ORDER)), [])
            ax.grid(True, axis="y", alpha=0.2)
            if metric["metric_name"] == "segmentation_stability":
                ax.set_ylim(bottom=0.0, top=min(1.02, max(1.0, ax.get_ylim()[1])))
            else:
                ax.set_ylim(bottom=0.0)

    legend_handles = [
        Line2D([0], [0], color=PERTURBATION_COLORS[name], marker="o", linewidth=1.8, label=name)
        for name in PERTURBATION_ORDER
    ]
    fig.legend(legend_handles, PERTURBATION_ORDER, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.01))
    out_path = OUT_DIR / "fig07_robustness_subset_comparison.png"
    save_figure(fig, out_path)
    return FigureRecord(
        figure_id="fig07",
        title="Comparative robustness figure across subsets",
        purpose="Compare combined, primary, and strict subset robustness patterns in one figure without duplicating the standalone primary-only and strict-only panels.",
        recommended_section="Supplementary",
        source_inputs=[relpath(FORMAL_LONG_CSV)],
        generating_script=FIGURE_SCRIPT,
        output_path=relpath(out_path),
        status="supplementary",
        caption_draft=(
            "Subset-comparison view of the formal robustness outputs. Rows show the combined "
            "formal run, the primary subset (n = 27), and the nested strict subset (n = 7); "
            "columns show the four core robustness metrics: interval-overlap segmentation "
            "stability, mean absolute boundary shift, absolute vertical-drop error, and absolute "
            "`CL(alpha)` deviation. Lines show median values across perturbation-comparison rows "
            "for each perturbation family and strength. Error bars are omitted in this comparison "
            "view to emphasize directional subset-level patterns; uncertainty spread is shown in "
            "the standalone robustness panels. `CL(alpha)` was computed with `alpha = 0.5`."
        ),
        output_exists=out_path.exists(),
    )


def make_ranking_supplement(long_df: pd.DataFrame) -> FigureRecord:
    combined_summary = summarise_long_metrics(long_df, subset_name=None)
    metrics = [
        ("top_k_consistency", "Top-k consistency", "Consistency"),
        ("mean_absolute_rank_shift", "Mean absolute rank shift", "Absolute shift"),
        ("rank_spearman", "Rank Spearman", "Spearman rho"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True)

    for ax, (metric_name, title, ylabel) in zip(axes, metrics):
        metric_df = metric_rows(combined_summary, metric_name)
        for perturbation_type in PERTURBATION_ORDER:
            group = metric_df[metric_df["perturbation_type"] == perturbation_type].copy()
            if group.empty:
                continue
            x = [LEVEL_TO_X[val] for val in group["perturbation_level_label"].astype(str)]
            y = pd.to_numeric(group["median"], errors="coerce").to_numpy(dtype=float)
            ax.plot(x, y, marker="o", linewidth=2.0, color=PERTURBATION_COLORS[perturbation_type], label=perturbation_type)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xticks(range(len(LEVEL_ORDER)), LEVEL_ORDER)
        ax.set_xlabel("Perturbation strength")
        ax.set_ylabel(ylabel)
        if metric_name != "rank_spearman":
            ax.set_ylim(bottom=0.0)
        ax.grid(True, axis="y", alpha=0.2)

    legend_handles = [
        Line2D([0], [0], color=PERTURBATION_COLORS[name], marker="o", linewidth=2.0, label=name)
        for name in PERTURBATION_ORDER
    ]
    fig.legend(legend_handles, PERTURBATION_ORDER, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.06))
    out_path = OUT_DIR / "figS01_ranking_comparison.png"
    save_figure(fig, out_path)
    return FigureRecord(
        figure_id="figS01",
        title="Ranking-oriented supplementary robustness figure",
        purpose="Retain the ranking-oriented robustness outputs as a supplement-facing asset instead of mixing them back into the core four-panel figure.",
        recommended_section="Supplementary",
        source_inputs=[relpath(FORMAL_LONG_CSV)],
        generating_script=FIGURE_SCRIPT,
        output_path=relpath(out_path),
        status="supplementary",
        caption_draft=(
            "Ranking-oriented supplementary robustness summary for the combined formal run. "
            "Metrics are computed from the `CL(alpha)` rankings with `alpha = 0.5` and top-k "
            "fixed at 3. Panels show top-k consistency, mean absolute rank shift, and Spearman "
            "rank correlation across perturbation families and perturbation strengths. Lines show "
            "median values for each family-strength condition in the pooled formal output "
            "(n = 340 comparisons per point). Error bars are omitted so that this supplement-facing "
            "figure focuses on ranking direction and relative family-level behaviour."
        ),
        output_exists=out_path.exists(),
    )


def make_phasewise_supplement(baseline_df: pd.DataFrame) -> FigureRecord:
    primary_df = baseline_df[baseline_df["subset_name"] == "primary"].copy().sort_values("run_order")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)
    metric_labels = {
        "z_internal": "Internal z",
        "z_mech": "Mech. z",
        "combined_load_v2": "CL(alpha)",
    }

    left = axes[0]
    phase_summary = (
        primary_df.groupby("subset_phase", as_index=False)[["z_internal", "z_mech", "combined_load_v2"]]
        .mean(numeric_only=True)
    )
    phase_summary["subset_phase"] = pd.Categorical(phase_summary["subset_phase"], categories=PHASE_ORDER, ordered=True)
    phase_summary = phase_summary.sort_values("subset_phase")
    for metric_name in ["z_internal", "z_mech", "combined_load_v2"]:
        left.plot(
            phase_summary["subset_phase"].astype(str),
            phase_summary[metric_name],
            marker="o",
            linewidth=2.2,
            color=PHASE_COLORS[metric_name],
            label=metric_labels[metric_name],
        )
    left.set_title("Primary-set tercile summaries", loc="left", fontweight="bold")
    left.set_xlabel("Run-order tercile")
    left.set_ylabel("Mean standardized value")
    left.legend(frameon=False, loc="best")

    right = axes[1]
    contrast_rows = []
    for metric_name in ["z_internal", "z_mech", "combined_load_v2"]:
        early = primary_df.loc[primary_df["subset_phase"] == "early", metric_name].mean()
        late = primary_df.loc[primary_df["subset_phase"] == "late", metric_name].mean()
        contrast_rows.append({"metric": metric_name, "late_minus_early": late - early})
    contrast_df = pd.DataFrame(contrast_rows)
    contrast_df["label"] = contrast_df["metric"].map(metric_labels)
    right.bar(
        contrast_df["label"],
        contrast_df["late_minus_early"],
        color=[PHASE_COLORS[name] for name in contrast_df["metric"]],
    )
    right.axhline(0.0, color="#666666", linewidth=1.0)
    right.set_title("Late minus early contrast", loc="left", fontweight="bold")
    right.set_xlabel("Metric")
    right.set_ylabel("Contrast")
    right.tick_params(axis="x", rotation=20)

    out_path = OUT_DIR / "figS02_phasewise_contrast.png"
    save_figure(fig, out_path)
    return FigureRecord(
        figure_id="figS02",
        title="Phase-wise contrast supplementary figure",
        purpose="Show early, middle, and late run-order tercile summaries plus late-minus-early contrasts, explicitly as a run-order comparison device rather than a biomechanical phase detector.",
        recommended_section="Supplementary",
        source_inputs=[relpath(FORMAL_BASELINE_CSV)],
        generating_script=FIGURE_SCRIPT,
        output_path=relpath(out_path),
        status="supplementary",
        caption_draft=(
            "Phase-wise supplementary view based on primary-set run order. The primary analytical "
            "set (n = 27) was sorted by run order and divided into early, middle, and late terciles "
            "(9 runs per tercile). The left panel reports tercile means for `z_internal`, `z_mech`, "
            "and `CL(alpha)` with `alpha = 0.5`; the right panel reports the late-minus-early "
            "contrast for the same metrics. No perturbation repeats or error bars are shown. These "
            "terciles are descriptive run-order comparison bins and should not be interpreted as "
            "biomechanical turn phases or a dedicated phase-detection model."
        ),
        output_exists=out_path.exists(),
    )


def write_manifest(records: list[FigureRecord]) -> Path:
    manifest_path = OUT_DIR / "figure_manifest.json"
    captions_path = OUT_DIR / "captions_v0.md"
    manifest = [
        {
            "figure_id": record.figure_id,
            "title": record.title,
            "purpose": record.purpose,
            "recommended_section": record.recommended_section,
            "source_inputs": record.source_inputs,
            "generating_script": record.generating_script,
            "output_path": record.output_path,
            "status": record.status,
            "caption_draft": record.caption_draft,
            "output_exists": record.output_exists,
        }
        for record in records
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    caption_lines = ["# Caption Drafts v0", ""]
    for record in records:
        caption_lines.append(f"**{record.figure_id}. {record.title}.** {record.caption_draft}")
        caption_lines.append("")
    captions_path.write_text("\n".join(caption_lines), encoding="utf-8")
    return manifest_path


def main() -> None:
    apply_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    runs_df = pd.read_csv(RUNS_FINAL_CSV)
    baseline_df = pd.read_csv(FORMAL_BASELINE_CSV)
    long_df = pd.read_csv(FORMAL_LONG_CSV)
    summary_df = pd.read_csv(FORMAL_SUMMARY_CSV)
    alpha_df = pd.read_csv(ALPHA_SUMMARY_CSV)

    records: list[FigureRecord] = []
    records.append(make_workflow_architecture())
    records.extend(make_sample_flow(runs_df))
    records.append(make_alpha_sweep(alpha_df))
    records.extend(make_core_robustness_figures(long_df, summary_df))
    records.append(make_subset_comparison(long_df))
    records.append(make_ranking_supplement(long_df))
    records.append(make_phasewise_supplement(baseline_df))

    manifest_path = write_manifest(records)
    print(f"[OK] Wrote figure assets to {OUT_DIR}")
    print(f"[OK] Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
