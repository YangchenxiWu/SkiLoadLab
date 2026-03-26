from __future__ import annotations

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


def run_combined_load(inp: Path, outp: Path, rep: Path, alpha: float) -> dict:
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha must be within [0, 1].")

    df = pd.read_csv(inp)

    # Demo / public run-level mode
    if ("z_mech" in df.columns) and ("z_internal" in df.columns):
        df["z_mech"] = pd.to_numeric(df["z_mech"], errors="coerce")
        df["z_internal"] = pd.to_numeric(df["z_internal"], errors="coerce")

        df["combined_load_v2"] = alpha * df["z_internal"] + (1.0 - alpha) * df["z_mech"]

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
            "corr_comb_internal": corr_comb_internal,
            "corr_comb_mech": corr_comb_mech,
        }

        with rep.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    raise ValueError(
        "Input CSV does not contain the required columns for demo mode. "
        "Expected at least: z_internal, z_mech."
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Compute combined training load by blending internal/external components."
    )
    ap.add_argument("--in", dest="inp", required=True, help="Input CSV")
    ap.add_argument("--out", required=True, help="Output CSV")
    ap.add_argument("--report", required=True, help="Output report JSON")
    ap.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Weight for internal component (0..1)",
    )
    args = ap.parse_args()

    report = run_combined_load(
        inp=Path(args.inp),
        outp=Path(args.out),
        rep=Path(args.report),
        alpha=float(args.alpha),
    )

    print(f"[OK] Saved: {report['output_csv']}")
    print(f"[OK] Report: {report['output_report']}")
    print(f"internal_used_for_combined = {report['internal_used_for_combined']}")
    print(f"corr(combined, z_internal) = {report['corr_comb_internal']}")
    print(f"corr(combined, z_mech) = {report['corr_comb_mech']}")


if __name__ == "__main__":
    main()
