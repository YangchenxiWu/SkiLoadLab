#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def zscore(x: pd.Series) -> pd.Series:
    """NaN-safe z-score."""
    x = pd.to_numeric(x, errors="coerce")
    mu = x.mean(skipna=True)
    sd = x.std(skipna=True)
    if not np.isfinite(sd) or sd == 0:
        return x * np.nan
    return (x - mu) / sd


def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Compute mechanical proxies + combined load (internal + external) from runs_with_hr.csv"
    )
    ap.add_argument("--in", dest="inp", default="data/processed/runs_with_hr.csv", help="Input CSV")
    ap.add_argument("--out", default="data/processed/runs_combined_load.csv", help="Output CSV")
    ap.add_argument("--report", default="output/combined_load_report.json", help="Report JSON")
    ap.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Weight for internal load in combined load (0..1). combined = alpha*z_internal + (1-alpha)*z_mech",
    )
    args = ap.parse_args()

    inp = Path(args.inp)
    outp = Path(args.out)
    rep = Path(args.report)

    if not inp.exists():
        raise FileNotFoundError(f"Input not found: {inp}")

    alpha = float(args.alpha)
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("--alpha must be within [0, 1].")

    ensure_parent(outp)
    ensure_parent(rep)

    df = pd.read_csv(inp)

    # ---- Required columns (from your pipeline) ----
    required = {"run_id", "duration_s", "vertical_drop_m", "speed_mean_ms", "edwards_trimp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {inp}: {sorted(missing)}")

    # ---- Mechanical proxies (external load proxies) ----
    df["mech_drop"] = pd.to_numeric(df["vertical_drop_m"], errors="coerce")
    df["mech_intensity"] = df["mech_drop"] * pd.to_numeric(df["speed_mean_ms"], errors="coerce")
    df["mech_volume"] = df["mech_drop"] * pd.to_numeric(df["duration_s"], errors="coerce")

    # ---- Internal load: keep Edwards TRIMP (discrete) + prefer continuous if present ----
    internal_cont_name = None
    z_internal_cont = None

    if "impulse_hr_s" in df.columns:
        internal_cont_name = "impulse_hr_s"
        df["internal_cont_name"] = internal_cont_name
        df["internal_cont"] = pd.to_numeric(df["impulse_hr_s"], errors="coerce")
        z_internal_cont = zscore(df["internal_cont"])
    elif "impulse_hr_above_rest_bpms" in df.columns:
        internal_cont_name = "impulse_hr_above_rest_bpms"
        df["internal_cont_name"] = internal_cont_name
        df["internal_cont"] = pd.to_numeric(df["impulse_hr_above_rest_bpms"], errors="coerce")
        z_internal_cont = zscore(df["internal_cont"])
    else:
        df["internal_cont_name"] = ""
        df["internal_cont"] = np.nan

    z_trimp = zscore(df["edwards_trimp"])
    z_mech = zscore(df["mech_intensity"])

    # expose z versions explicitly
    df["z_trimp"] = z_trimp
    df["z_mech"] = z_mech

    # choose internal: continuous if available else TRIMP
    if z_internal_cont is not None and z_internal_cont.notna().any():
        df["z_internal"] = z_internal_cont
        internal_used = internal_cont_name
        df["z_internal_cont"] = z_internal_cont
    else:
        df["z_internal"] = z_trimp
        internal_used = "edwards_trimp"
        df["z_internal_cont"] = np.nan

    # ---- Final combined load ----
    df["combined_load_v2"] = alpha * df["z_internal"] + (1.0 - alpha) * df["z_mech"]

    # Save CSV
    df.to_csv(outp, index=False)

    # Simple correlations (diagnostics)
    corr_tm = float(df[["edwards_trimp", "mech_intensity"]].corr().iloc[0, 1])
    corr_td = float(df[["edwards_trimp", "mech_drop"]].corr().iloc[0, 1])

    report = {
        "input": str(inp),
        "output_csv": str(outp),
        "output_report": str(rep),
        "n_runs": int(len(df)),
        "alpha": alpha,
        "internal_used_for_combined": internal_used,
        "corr_trimp_mech_intensity": corr_tm,
        "corr_trimp_drop": corr_td,
        "summary": {
            "trimp_total": float(pd.to_numeric(df["edwards_trimp"], errors="coerce").sum(skipna=True)),
            "vertical_drop_total_m": float(pd.to_numeric(df["mech_drop"], errors="coerce").sum(skipna=True)),
            "combined_load_v2_mean": float(pd.to_numeric(df["combined_load_v2"], errors="coerce").mean(skipna=True)),
        },
    }
    rep.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Saved: {outp.resolve()}")
    print(f"[OK] Report: {rep.resolve()}")
    print(f"[INFO] internal_used_for_combined = {internal_used}")
    print(f"[INFO] corr(TRIMP, mech_intensity) = {corr_tm}")
    print(f"[INFO] corr(TRIMP, drop) = {corr_td}")

    # Preview
    preview_cols = ["run_id", "edwards_trimp", "mech_intensity", "combined_load_v2"]
    preview_cols = [c for c in preview_cols if c in df.columns]
    print("\n=== Preview (run_id, edwards_trimp, mech_intensity, combined_load_v2) ===")
    print(df[preview_cols].head().to_string(index=False))


if __name__ == "__main__":
    main()
