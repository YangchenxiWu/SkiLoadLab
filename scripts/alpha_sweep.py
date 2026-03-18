#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def run_combined_load(
    alpha: float, inp: Path, out_csv: Path, rep_json: Path
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        "src/model/combined_load.py",
        "--in",
        str(inp),
        "--out",
        str(out_csv),
        "--report",
        str(rep_json),
        "--alpha",
        str(alpha),
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def safe_corr(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    m = a.notna() & b.notna()
    if int(m.sum()) < 3:
        return float("nan")
    return float(a[m].corr(b[m]))


def main():
    ap = argparse.ArgumentParser(
        description="Sweep alpha for combined_load_v2 and choose best alpha by balanced internal/external correlation."
    )
    ap.add_argument(
        "--in", dest="inp", default="data/processed/runs_with_hr.csv", help="Input runs_with_hr.csv"
    )
    ap.add_argument("--alpha_step", type=float, default=0.05, help="Alpha step (default 0.05)")
    ap.add_argument(
        "--out_dir", default="data/processed/alpha_sweep", help="Directory to store per-alpha CSVs"
    )
    ap.add_argument(
        "--report_dir", default="output/alpha_sweep", help="Directory to store per-alpha reports"
    )
    ap.add_argument("--summary", default="output/alpha_sweep_summary.csv", help="Summary CSV path")
    ap.add_argument(
        "--stop_on_fail",
        action="store_true",
        help="Stop sweep immediately if any run fails (default: continue).",
    )
    args = ap.parse_args()

    inp = Path(args.inp)
    if not inp.exists():
        raise FileNotFoundError(f"Input not found: {inp}")

    out_dir = Path(args.out_dir)
    report_dir = Path(args.report_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    step = float(args.alpha_step)
    if step <= 0 or step > 1:
        raise ValueError("--alpha_step must be in (0, 1].")

    # alpha grid: 0..1 inclusive
    n = int(round(1.0 / step))
    alphas = [round(i * step, 10) for i in range(n + 1)]
    if alphas[-1] != 1.0:
        alphas.append(1.0)

    rows = []
    for a in alphas:
        out_csv = out_dir / f"runs_combined_load_alpha{a:0.2f}.csv"
        rep_json = report_dir / f"combined_load_report_alpha{a:0.2f}.json"

        print(f"[RUN] alpha={a:0.2f}")
        p = run_combined_load(a, inp, out_csv, rep_json)

        row = {
            "alpha": a,
            "ok": (p.returncode == 0),
            "returncode": int(p.returncode),
            "out_csv": str(out_csv),
            "report_json": str(rep_json),
            "internal_used": None,
            # correlations we care about
            "corr_comb_internal": np.nan,
            "corr_comb_mech": np.nan,
            "score_balanced": np.nan,
            # optional debug tails
            "stderr_tail": "",
            "stdout_tail": "",
        }

        # parse internal_used from stdout if present
        for line in (p.stdout or "").splitlines():
            if "internal_used_for_combined" in line:
                row["internal_used"] = line.split("=", 1)[-1].strip()

        if not row["ok"]:
            row["stderr_tail"] = "\n".join((p.stderr or "").splitlines()[-20:])
            row["stdout_tail"] = "\n".join((p.stdout or "").splitlines()[-20:])
            print(f"[FAIL] alpha={a:0.2f} returncode={p.returncode}")
            if row["stderr_tail"]:
                print(row["stderr_tail"])
            if args.stop_on_fail:
                rows.append(row)
                break
            rows.append(row)
            continue

        if not out_csv.exists():
            row["ok"] = False
            row["returncode"] = 999
            row["stderr_tail"] = "combined_load.py succeeded but out_csv not found."
            print(f"[FAIL] alpha={a:0.2f} out_csv missing: {out_csv}")
            if args.stop_on_fail:
                rows.append(row)
                break
            rows.append(row)
            continue

        df = pd.read_csv(out_csv)

        required = {"combined_load_v2", "z_internal", "z_mech"}
        missing = required - set(df.columns)
        if missing:
            row["ok"] = False
            row["returncode"] = 998
            row["stderr_tail"] = f"Missing columns in out_csv: {sorted(missing)}"
            print(f"[FAIL] alpha={a:0.2f} missing columns: {sorted(missing)}")
            if args.stop_on_fail:
                rows.append(row)
                break
            rows.append(row)
            continue

        r_int = safe_corr(df["combined_load_v2"], df["z_internal"])
        r_mech = safe_corr(df["combined_load_v2"], df["z_mech"])
        row["corr_comb_internal"] = r_int
        row["corr_comb_mech"] = r_mech

        if np.isfinite(r_int) and np.isfinite(r_mech):
            row["score_balanced"] = float(min(abs(r_int), abs(r_mech)))

        rows.append(row)

    # write summary
    out_df = pd.DataFrame(rows)
    summary = Path(args.summary)
    summary.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(summary, index=False)
    print(f"[OK] Saved summary: {summary.resolve()}")

    ok_df = out_df[out_df["ok"] == True].copy()
    ok_df = ok_df[np.isfinite(ok_df["score_balanced"])].copy()

    if len(ok_df) == 0:
        print(
            "[WARN] No valid score_balanced rows. Check that combined_load.py outputs z_internal/z_mech/combined_load_v2."
        )
        return

    best = ok_df.loc[ok_df["score_balanced"].idxmax()]
    print(
        "\n[BEST] by balanced score = max min(|corr(combined,z_internal)|, |corr(combined,z_mech)|)"
    )
    print(
        best[
            [
                "alpha",
                "internal_used",
                "corr_comb_internal",
                "corr_comb_mech",
                "score_balanced",
            ]
        ].to_string()
    )

    # optional: top-5
    top5 = ok_df.sort_values("score_balanced", ascending=False).head(5)
    print("\n[TOP 5] by score_balanced")
    print(
        top5[
            [
                "alpha",
                "internal_used",
                "corr_comb_internal",
                "corr_comb_mech",
                "score_balanced",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
