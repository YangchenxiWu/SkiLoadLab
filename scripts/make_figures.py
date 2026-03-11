#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Make publication-style figures from processed SkiLoadLab outputs.

Inputs (default):
  - data/processed/runs_final.csv
  - output/alpha_sweep_summary.csv

Outputs (default):
  - output/figures/*.png
  - optional PDF if --pdf is set

Design goals:
  - Deterministic output (fixed seed)
  - Robust to missing columns: skip figure with a warning
  - Minimal dependencies: pandas, numpy, matplotlib
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def require_file(p: Path, name: str) -> None:
    if not p.exists():
        raise FileNotFoundError(f"{name} not found: {p}")


def save_fig(fig, out_png: Path, also_pdf: bool = False) -> None:
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    ok(f"Saved: {out_png.resolve()}")
    if also_pdf:
        out_pdf = out_png.with_suffix(".pdf")
        fig.savefig(out_pdf)
        ok(f"Saved: {out_pdf.resolve()}")
    plt.close(fig)


def _has_cols(df: pd.DataFrame, cols: list[str]) -> bool:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        warn(f"Missing columns, skip figure: {missing}")
        return False
    return True


def fig_run_duration_dist(df: pd.DataFrame, out_dir: Path, also_pdf: bool) -> None:
    if not _has_cols(df, ["duration_s"]):
        return
    x = pd.to_numeric(df["duration_s"], errors="coerce").dropna()
    if len(x) == 0:
        warn("duration_s has no valid values; skip duration distribution.")
        return

    fig = plt.figure()
    plt.hist(x / 60.0, bins=30)
    plt.xlabel("Run duration (min)")
    plt.ylabel("Count")
    plt.title("Run duration distribution")
    save_fig(fig, out_dir / "fig01_run_duration_hist.png", also_pdf)


def fig_vertical_drop_dist(df: pd.DataFrame, out_dir: Path, also_pdf: bool) -> None:
    # Optional but useful sanity check
    if "vertical_drop_m" not in df.columns:
        warn("vertical_drop_m not found; skip vertical drop distribution.")
        return
    x = pd.to_numeric(df["vertical_drop_m"], errors="coerce").dropna()
    if len(x) == 0:
        warn("vertical_drop_m has no valid values; skip.")
        return

    fig = plt.figure()
    plt.hist(x, bins=30)
    plt.xlabel("Vertical drop per run (m)")
    plt.ylabel("Count")
    plt.title("Vertical drop distribution")
    save_fig(fig, out_dir / "fig02_vertical_drop_hist.png", also_pdf)


def fig_internal_vs_external(df: pd.DataFrame, out_dir: Path, also_pdf: bool) -> None:
    # Prefer z_internal (continuous) + z_mech
    candidates_internal = ["z_internal", "z_internal_cont", "z_trimp", "z_trimp_disc"]
    internal_col = None
    for c in candidates_internal:
        if c in df.columns:
            internal_col = c
            break
    if internal_col is None or "z_mech" not in df.columns:
        warn("Need z_mech and one of z_internal/z_trimp; skip internal vs external scatter.")
        return

    x = pd.to_numeric(df["z_mech"], errors="coerce")
    y = pd.to_numeric(df[internal_col], errors="coerce")
    m = (~x.isna()) & (~y.isna())
    if m.sum() == 0:
        warn("No valid points for internal vs external scatter.")
        return

    fig = plt.figure()
    plt.scatter(x[m], y[m], s=18)
    plt.xlabel("External load (z_mech)")
    plt.ylabel(f"Internal load ({internal_col})")
    plt.title("Internal vs external load (z-scores)")
    save_fig(fig, out_dir / "fig03_internal_vs_external_scatter.png", also_pdf)


def fig_combined_vs_components(df: pd.DataFrame, out_dir: Path, also_pdf: bool) -> None:
    # combined_load_v2 vs z_internal and z_mech
    if "combined_load_v2" not in df.columns or "z_mech" not in df.columns:
        warn("Need combined_load_v2 and z_mech; skip combined vs components.")
        return
    candidates_internal = ["z_internal", "z_internal_cont", "z_trimp", "z_trimp_disc"]
    internal_col = None
    for c in candidates_internal:
        if c in df.columns:
            internal_col = c
            break
    if internal_col is None:
        warn("No internal z-score column found; skip combined vs components.")
        return

    c = pd.to_numeric(df["combined_load_v2"], errors="coerce")
    z_m = pd.to_numeric(df["z_mech"], errors="coerce")
    z_i = pd.to_numeric(df[internal_col], errors="coerce")

    fig = plt.figure()
    # two scatters on one figure is okay if readable; keep simple with markers
    m1 = (~c.isna()) & (~z_i.isna())
    m2 = (~c.isna()) & (~z_m.isna())
    if m1.sum() == 0 and m2.sum() == 0:
        warn("No valid points for combined vs components.")
        return

    if m1.sum() > 0:
        plt.scatter(c[m1], z_i[m1], s=18, label=f"{internal_col} vs combined")
    if m2.sum() > 0:
        plt.scatter(c[m2], z_m[m2], s=18, label="z_mech vs combined")

    plt.xlabel("combined_load_v2")
    plt.ylabel("z-score")
    plt.title("Combined load vs components")
    plt.legend()
    save_fig(fig, out_dir / "fig04_combined_vs_components.png", also_pdf)


def fig_top_runs_by_combined(df: pd.DataFrame, out_dir: Path, also_pdf: bool, top_n: int = 10) -> None:
    if "combined_load_v2" not in df.columns:
        warn("combined_load_v2 not found; skip top runs bar chart.")
        return
    if "run_id" not in df.columns:
        warn("run_id not found; skip top runs bar chart.")
        return

    tmp = df.copy()
    tmp["combined_load_v2"] = pd.to_numeric(tmp["combined_load_v2"], errors="coerce")
    tmp = tmp.dropna(subset=["combined_load_v2"])
    if len(tmp) == 0:
        warn("combined_load_v2 has no valid values; skip.")
        return

    top = tmp.sort_values("combined_load_v2", ascending=False).head(top_n)
    labels = top["run_id"].astype(str).tolist()
    vals = top["combined_load_v2"].to_numpy()

    fig = plt.figure(figsize=(8, 4))
    plt.bar(labels, vals)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("combined_load_v2 (z-score blend)")
    plt.title(f"Top {top_n} runs by combined load")
    save_fig(fig, out_dir / "fig05_top_runs_by_combined.png", also_pdf)


def fig_alpha_sweep(summary_csv: Path, out_dir: Path, also_pdf: bool) -> None:
    if not summary_csv.exists():
        warn(f"alpha sweep summary not found; skip alpha sweep figure: {summary_csv}")
        return

    df = pd.read_csv(summary_csv)
    needed_any = ["alpha"]
    if not all(c in df.columns for c in needed_any):
        warn("alpha_sweep_summary.csv missing 'alpha'; skip alpha sweep figure.")
        return

    # If you saved these columns, plot them; otherwise plot what exists
    cand_series = [
        ("corr_comb_internal", "corr(combined, z_internal)"),
        ("corr_comb_mech", "corr(combined, z_mech)"),
        ("score_balanced", "balanced score"),
    ]

    fig = plt.figure()
    x = pd.to_numeric(df["alpha"], errors="coerce")
    for col, label in cand_series:
        if col in df.columns:
            y = pd.to_numeric(df[col], errors="coerce")
            m = (~x.isna()) & (~y.isna())
            if m.sum() > 0:
                plt.plot(x[m], y[m], marker="o", linewidth=1, label=label)

    plt.xlabel("alpha (weight on internal)")
    plt.ylabel("metric")
    plt.title("Alpha sweep diagnostics")
    plt.legend()
    save_fig(fig, out_dir / "fig06_alpha_sweep.png", also_pdf)


def main():
    np.random.seed(0)

    ap = argparse.ArgumentParser(description="Generate figures from SkiLoadLab processed outputs.")
    ap.add_argument("--runs", default="data/processed/runs_final.csv", help="Input runs_final.csv")
    ap.add_argument("--alpha_summary", default="output/alpha_sweep_summary.csv", help="Input alpha_sweep_summary.csv")
    ap.add_argument("--out_dir", default="output/figures", help="Output directory for figures")
    ap.add_argument("--pdf", action="store_true", help="Also export PDF copies")
    ap.add_argument("--top_n", type=int, default=10, help="Top N runs in bar chart")
    args = ap.parse_args()

    runs_csv = Path(args.runs)
    alpha_csv = Path(args.alpha_summary)
    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)

    require_file(runs_csv, "runs_final.csv")
    df = pd.read_csv(runs_csv)

    ok(f"Loaded runs: {runs_csv} (n={len(df)})")

    fig_run_duration_dist(df, out_dir, args.pdf)
    fig_vertical_drop_dist(df, out_dir, args.pdf)
    fig_internal_vs_external(df, out_dir, args.pdf)
    fig_combined_vs_components(df, out_dir, args.pdf)
    fig_top_runs_by_combined(df, out_dir, args.pdf, top_n=args.top_n)
    fig_alpha_sweep(alpha_csv, out_dir, args.pdf)

    ok(f"All done. Figures in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
