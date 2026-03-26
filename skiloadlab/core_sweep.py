from __future__ import annotations

import argparse
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from skiloadlab.core_model import run_combined_load


def run_combined_load_safe(alpha: float, inp: Path, out_csv: Path, rep_json: Path):
    try:
        report = run_combined_load(
            inp=inp,
            outp=out_csv,
            rep=rep_json,
            alpha=alpha,
        )
        return True, report, ""
    except Exception:
        return False, None, traceback.format_exc()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Sweep alpha for combined_load_v2 and choose best alpha by balanced internal/external correlation."
    )
    ap.add_argument(
        "--in",
        dest="inp",
        default="data/example/runs_final_example.csv",
        help="Input run-level CSV for alpha sweep",
    )
    ap.add_argument(
        "--alpha_step",
        type=float,
        default=0.05,
        help="Alpha step (default 0.05)",
    )
    ap.add_argument(
        "--out_dir",
        default="output/alpha_sweep",
        help="Directory to store per-alpha CSVs",
    )
    ap.add_argument(
        "--report_dir",
        default="output/alpha_sweep",
        help="Directory to store per-alpha reports",
    )
    ap.add_argument(
        "--summary",
        default="output/alpha_sweep_summary.csv",
        help="Summary CSV path",
    )
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
    summary_path = Path(args.summary)

    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    step = float(args.alpha_step)
    if step <= 0 or step > 1:
        raise ValueError("--alpha_step must be in (0, 1].")

    n = int(round(1.0 / step))
    alphas = [round(i * step, 10) for i in range(n + 1)]
    if alphas[-1] != 1.0:
        alphas.append(1.0)

    rows = []
    for a in alphas:
        out_csv = out_dir / f"runs_combined_load_alpha{a:0.2f}.csv"
        rep_json = report_dir / f"combined_load_report_alpha{a:0.2f}.json"

        print(f"[RUN] alpha={a:0.2f}")
        ok, report, err = run_combined_load_safe(a, inp, out_csv, rep_json)

        row = {
            "alpha": a,
            "ok": ok,
            "returncode": 0 if ok else 1,
            "out_csv": str(out_csv),
            "report_json": str(rep_json),
            "internal_used": None,
            "corr_comb_internal": np.nan,
            "corr_comb_mech": np.nan,
            "score_balanced": np.nan,
            "stderr_tail": "",
            "stdout_tail": "",
        }

        if not ok:
            row["stderr_tail"] = err
            print(f"[FAIL] alpha={a:0.2f}")
            if args.stop_on_fail:
                rows.append(row)
                break
            rows.append(row)
            continue

        row["internal_used"] = report.get("internal_used_for_combined")
        row["corr_comb_internal"] = report.get("corr_comb_internal", np.nan)
        row["corr_comb_mech"] = report.get("corr_comb_mech", np.nan)

        vals = [row["corr_comb_internal"], row["corr_comb_mech"]]
        if all(pd.notna(v) for v in vals):
            row["score_balanced"] = min(vals)

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(summary_path, index=False)
    print(f"[OK] Saved summary: {summary_path}")

    valid = df[df["score_balanced"].notna()].copy()
    if len(valid) > 0:
        best = valid.sort_values("score_balanced", ascending=False).iloc[0]
        print("[BEST] by balanced score = max min(corr_internal, corr_mech)")
        print(best[["alpha", "corr_comb_internal", "corr_comb_mech", "score_balanced"]])
        print("\n[TOP 5] by score_balanced")
        print(
            valid.sort_values("score_balanced", ascending=False)
            .head(5)[["alpha", "corr_comb_internal", "corr_comb_mech", "score_balanced"]]
            .to_string(index=False)
        )
    else:
        print(
            "[WARN] No valid score_balanced rows. Check that combined_load outputs "
            "z_internal / z_mech / combined_load_v2."
        )


if __name__ == "__main__":
    main()
