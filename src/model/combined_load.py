#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def zscore(x: pd.Series) -> pd.Series:
    x = pd.to_numeric(x, errors="coerce")
    mu = x.mean(skipna=True)
    sd = x.std(skipna=True)
    if not np.isfinite(sd) or sd == 0:
        return x * np.nan
    return (x - mu) / sd


def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def corr_safe(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    m = a.notna() & b.notna()
    if m.sum() < 3:
        return float("nan")
    return float(np.corrcoef(a[m], b[m])[0, 1])


def main():
    ap = argparse.ArgumentParser(
        description="Compute combined training load by blending internal/external components."
    )
    ap.add_argument("--in", dest="inp", required=True, help="Input CSV")
    ap.add_argument("--out", required=True, help="Output CSV")
    ap.add_argument("--report", required=True, help="Output report JSON")
    ap.add_argument("--alpha", type=float, default=0.5, help="Weight for internal component (0..1)")
    args = ap.parse_args()

    alpha = float(args.alpha)
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("--alpha must be within [0, 1].")

    inp = Path(args.inp)
    outp = Path(args.out)
    rep = Path(args.report)

    df = pd.read_csv(inp)

    # ------------------------------------------------------------
    # Mode B (demo/minimal): has z_mech + z_internal already
    # Columns you told me:
    # run_id,duration_s,vertical_drop_m,z_mech,z_internal,z_trimp,combined_load_v2
    # ------------------------------------------------------------
    if ("z_mech" in df.columns) and ("z_internal" in df.columns):
        df["z_mech"] = pd.to_numeric(df["z_mech"], errors="coerce")
        df["z_internal"] = pd.to_numeric(df["z_internal"], errors="coerce")

        df["combined_load_v2"] = alpha * df["z_internal"] + (1.0 - alpha) * df["z_mech"]

        # For alpha-sweep "balance internal/external":
        # corr(combined, z_internal) and corr(combined, z_mech)
        corr_comb_internal = corr_safe(df["combined_load_v2"], df["z_internal"])
        corr_comb_mech = corr_safe(df["combined_load_v2"], df["z_mech"])

        ensure_parent(outp)
        ensure_parent(rep)
        df.to_csv(outp, index=False)

        report = {
            "input": str(inp),
            "output_csv": str(outp),
            "output_report": str(rep),
            "n_runs": int(len(df)),
            "alpha": alpha,
            "mode": "demo_z_blend",
            "internal_used_for_combined": "z_internal",
            "external_used_for_combined": "z_mech",
            "corr_comb_internal": corr_comb_internal,
            "corr_comb_mech": corr_comb_mech,
            "summary": {
                "combined_load_v2_mean": float(
                    pd.to_numeric(df["combined_load_v2"], errors="coerce").mean(skipna=True)
                ),
            },
        }
        rep.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"[OK] Saved: {outp.resolve()}")
        print(f"[OK] Report: {rep.resolve()}")
        print("[INFO] internal_used_for_combined = z_internal")
        print(f"[INFO] corr(combined, z_internal) = {corr_comb_internal}")
        print(f"[INFO] corr(combined, z_mech) = {corr_comb_mech}")

        # small preview
        cols = [
            c for c in ["run_id", "z_internal", "z_mech", "combined_load_v2"] if c in df.columns
        ]
        print("\n=== Preview (first 5) ===")
        print(df[cols].head().to_string(index=False))
        return

    # ------------------------------------------------------------
    # Mode A (full pipeline): fallback (your original expected columns)
    # Keep this strict so full pipeline remains honest.
    # ------------------------------------------------------------
    required = {"run_id", "duration_s", "vertical_drop_m"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {inp}: {sorted(missing)}")

    # If you want, you can extend here to recompute mech/internal proxies from raw columns.
    # For now, make it explicit to avoid silent wrong results.
    raise ValueError(
        "Input CSV does not contain (z_mech, z_internal), and full-pipeline recomputation "
        "is not implemented in this version. Provide z_mech & z_internal, or extend Mode A."
    )


if __name__ == "__main__":
    main()
