from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_METRIC_CANDIDATES = [
    "combined_load_v2",
    "z_internal",
    "z_mech",
    "z_trimp",
    "vertical_drop_m",
    "duration_s",
    "speed_mean_ms",
    "speed_p95_ms",
    "edwards_trimp",
    "impulse_hr_above_rest_bpms",
]


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def require_file(path: Path, name: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")


def load_runs(path: Path) -> pd.DataFrame:
    require_file(path, "runs CSV")
    df = pd.read_csv(path)
    if len(df) == 0:
        raise ValueError(f"Input runs CSV is empty: {path}")
    return df


def detect_metric_columns(df: pd.DataFrame) -> list[str]:
    metrics: list[str] = []
    seen: set[str] = set()
    candidates = list(DEFAULT_METRIC_CANDIDATES) + list(df.columns)

    for col in candidates:
        if col in seen or col not in df.columns:
            continue
        seen.add(col)
        vals = pd.to_numeric(df[col], errors="coerce")
        if vals.notna().sum() >= 3:
            metrics.append(col)

    if len(metrics) < 2:
        raise ValueError(
            "Need at least two numeric run-level metrics with >= 3 valid values for comparison."
        )

    return metrics


def correlation_matrix(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=metrics, columns=metrics, dtype=float)
    for left in metrics:
        x = pd.to_numeric(df[left], errors="coerce")
        for right in metrics:
            y = pd.to_numeric(df[right], errors="coerce")
            mask = x.notna() & y.notna()
            if mask.sum() < 3:
                out.loc[left, right] = np.nan
            else:
                out.loc[left, right] = float(x[mask].corr(y[mask], method="pearson"))
    out.index.name = "metric"
    return out


def _spearman_corr(x: pd.Series, y: pd.Series) -> float:
    xr = x.rank(method="average")
    yr = y.rank(method="average")
    return float(xr.corr(yr, method="pearson"))


def _kendall_tau(x: pd.Series, y: pd.Series) -> float:
    n = len(x)
    if n < 2:
        return float("nan")

    concordant = 0
    discordant = 0
    ties_x = 0
    ties_y = 0

    xv = x.to_numpy(dtype=float)
    yv = y.to_numpy(dtype=float)
    for i in range(n - 1):
        dx = xv[i + 1 :] - xv[i]
        dy = yv[i + 1 :] - yv[i]

        sx = np.sign(dx)
        sy = np.sign(dy)

        concordant += int(np.sum((sx * sy) > 0))
        discordant += int(np.sum((sx * sy) < 0))
        ties_x += int(np.sum((sx == 0) & (sy != 0)))
        ties_y += int(np.sum((sy == 0) & (sx != 0)))

    denom = np.sqrt((concordant + discordant + ties_x) * (concordant + discordant + ties_y))
    if denom == 0:
        return float("nan")
    return float((concordant - discordant) / denom)


def _top_k_set_consistency(df: pd.DataFrame, left: str, right: str, top_n: int) -> float:
    cols = [left, right]
    tmp = df[cols].copy()
    for col in cols:
        tmp[col] = pd.to_numeric(tmp[col], errors="coerce")
    tmp = tmp.dropna(subset=cols)
    if len(tmp) == 0:
        return float("nan")

    n = min(int(top_n), len(tmp))
    left_top = set(tmp.nlargest(n, left).index.tolist())
    right_top = set(tmp.nlargest(n, right).index.tolist())
    if n == 0:
        return float("nan")
    return float(len(left_top & right_top) / n)


def ranking_stability(df: pd.DataFrame, metrics: list[str], top_n: int) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for i, left in enumerate(metrics):
        x = pd.to_numeric(df[left], errors="coerce")
        for right in metrics[i + 1 :]:
            y = pd.to_numeric(df[right], errors="coerce")
            mask = x.notna() & y.notna()
            row: dict[str, float | int | str] = {
                "metric_a": left,
                "metric_b": right,
                "n_overlap_runs": int(mask.sum()),
                "spearman_rho": np.nan,
                "kendall_tau": np.nan,
                "top_n": int(top_n),
                "top_k_set_consistency": np.nan,
            }
            if mask.sum() >= 3:
                row["spearman_rho"] = _spearman_corr(x[mask], y[mask])
                row["kendall_tau"] = _kendall_tau(x[mask], y[mask])
            row["top_k_set_consistency"] = _top_k_set_consistency(df, left, right, top_n=top_n)
            rows.append(row)

    out = pd.DataFrame(rows)
    if len(out) > 0 and "spearman_rho" in out.columns:
        out = out.sort_values(
            by=["spearman_rho", "top_k_set_consistency"],
            ascending=False,
            na_position="last",
        ).reset_index(drop=True)
    return out


def _session_phase_labels(n: int) -> pd.Series:
    if n <= 0:
        return pd.Series(dtype=object)
    labels = pd.Series(index=range(n), dtype=object)
    thirds = np.array_split(np.arange(n), 3)
    names = ["early", "mid", "late"]
    for name, idx in zip(names, thirds):
        labels.iloc[idx] = name
    return labels


def session_phase_summary(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    ordered = df.copy()
    ordered["session_index"] = np.arange(1, len(ordered) + 1)
    ordered["session_phase"] = _session_phase_labels(len(ordered)).values

    rows: list[dict[str, float | int | str]] = []
    phase_order = ["early", "mid", "late"]
    for metric in metrics:
        vals = pd.to_numeric(ordered[metric], errors="coerce")
        for phase in phase_order:
            phase_vals = vals[ordered["session_phase"] == phase].dropna()
            rows.append(
                {
                    "metric": metric,
                    "session_phase": phase,
                    "n_runs": int(len(phase_vals)),
                    "mean": float(phase_vals.mean()) if len(phase_vals) else np.nan,
                    "median": float(phase_vals.median()) if len(phase_vals) else np.nan,
                    "std": float(phase_vals.std()) if len(phase_vals) > 1 else np.nan,
                    "min": float(phase_vals.min()) if len(phase_vals) else np.nan,
                    "max": float(phase_vals.max()) if len(phase_vals) else np.nan,
                }
            )

    return pd.DataFrame(rows)


def phase_contrast_summary(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    ordered = df.copy()
    ordered["session_index"] = np.arange(1, len(ordered) + 1)
    ordered["session_phase"] = _session_phase_labels(len(ordered)).values

    rows: list[dict[str, float | int | str]] = []
    for metric in metrics:
        vals = pd.to_numeric(ordered[metric], errors="coerce")
        early_vals = vals[ordered["session_phase"] == "early"].dropna()
        mid_vals = vals[ordered["session_phase"] == "mid"].dropna()
        late_vals = vals[ordered["session_phase"] == "late"].dropna()

        early_mean = float(early_vals.mean()) if len(early_vals) else np.nan
        mid_mean = float(mid_vals.mean()) if len(mid_vals) else np.nan
        late_mean = float(late_vals.mean()) if len(late_vals) else np.nan
        contrast_value = (
            float(late_mean - early_mean)
            if pd.notna(late_mean) and pd.notna(early_mean)
            else np.nan
        )

        rows.append(
            {
                "metric": metric,
                "contrast_method": "late_tercile_mean_minus_early_tercile_mean",
                "run_order_basis": "input_row_order",
                "phase_definition": "contiguous_session_terciles",
                "n_total": int(vals.notna().sum()),
                "n_early": int(len(early_vals)),
                "n_mid": int(len(mid_vals)),
                "n_late": int(len(late_vals)),
                "early_mean": early_mean,
                "mid_mean": mid_mean,
                "late_mean": late_mean,
                "late_minus_early_contrast": contrast_value,
            }
        )

    return pd.DataFrame(rows)


def _choose_case_metrics(metrics: list[str]) -> tuple[str | None, str | None]:
    internal = "z_internal" if "z_internal" in metrics else None
    if internal is None and "z_trimp" in metrics:
        internal = "z_trimp"

    mech = "z_mech" if "z_mech" in metrics else None
    if mech is None and "vertical_drop_m" in metrics:
        mech = "vertical_drop_m"

    return internal, mech


def interpretive_cases(df: pd.DataFrame, metrics: list[str], case_count: int) -> pd.DataFrame:
    tmp = df.copy()
    tmp["session_index"] = np.arange(1, len(tmp) + 1)
    tmp["session_phase"] = _session_phase_labels(len(tmp)).values
    run_labels = tmp["run_id"].astype(str) if "run_id" in tmp.columns else tmp.index.astype(str)
    tmp["run_label"] = run_labels

    cases: list[dict[str, object]] = []
    used_runs: set[str] = set()
    internal, mech = _choose_case_metrics(metrics)

    def _first_unused_run(df_sorted: pd.DataFrame):
        for _, row in df_sorted.iterrows():
            run_label = str(row["run_label"])
            if run_label not in used_runs:
                used_runs.add(run_label)
                return row
        return None

    if internal is not None and mech is not None:
        tmp["_internal"] = pd.to_numeric(tmp[internal], errors="coerce")
        tmp["_mech"] = pd.to_numeric(tmp[mech], errors="coerce")
        tmp["_delta_internal_minus_mech"] = tmp["_internal"] - tmp["_mech"]

        high_internal = tmp.dropna(subset=["_delta_internal_minus_mech"]).sort_values(
            "_delta_internal_minus_mech", ascending=False
        )
        high_mech = tmp.dropna(subset=["_delta_internal_minus_mech"]).sort_values(
            "_delta_internal_minus_mech", ascending=True
        )
        if len(high_internal) > 0:
            row = _first_unused_run(high_internal)
            if row is not None:
                cases.append(
                    {
                        "case_id": "case_01",
                        "case_type": "internal_dominant",
                        "run_label": row["run_label"],
                        "session_index": int(row["session_index"]),
                        "session_phase": row["session_phase"],
                        "summary": f"{internal} is higher than {mech} more than any other run.",
                        "primary_metric": internal,
                        "secondary_metric": mech,
                        "primary_value": float(row["_internal"]),
                        "secondary_value": float(row["_mech"]),
                        "difference": float(row["_delta_internal_minus_mech"]),
                    }
                )
        if len(high_mech) > 0:
            row = _first_unused_run(high_mech)
            if row is not None:
                cases.append(
                    {
                        "case_id": "case_02",
                        "case_type": "mechanical_dominant",
                        "run_label": row["run_label"],
                        "session_index": int(row["session_index"]),
                        "session_phase": row["session_phase"],
                        "summary": f"{mech} is higher than {internal} more than any other run.",
                        "primary_metric": mech,
                        "secondary_metric": internal,
                        "primary_value": float(row["_mech"]),
                        "secondary_value": float(row["_internal"]),
                        "difference": float(-row["_delta_internal_minus_mech"]),
                    }
                )

    combined = "combined_load_v2" if "combined_load_v2" in metrics else None
    if combined is not None:
        tmp["_combined"] = pd.to_numeric(tmp[combined], errors="coerce")
        top_combined = tmp.dropna(subset=["_combined"]).sort_values("_combined", ascending=False)
        if len(top_combined) > 0:
            row = _first_unused_run(top_combined)
            if row is not None:
                cases.append(
                    {
                        "case_id": "case_03",
                        "case_type": "highest_combined",
                        "run_label": row["run_label"],
                        "session_index": int(row["session_index"]),
                        "session_phase": row["session_phase"],
                        "summary": f"{combined} is the highest blended load in the session.",
                        "primary_metric": combined,
                        "secondary_metric": internal or mech or combined,
                        "primary_value": float(row["_combined"]),
                        "secondary_value": (
                            float(pd.to_numeric(row[internal], errors="coerce")) if internal else np.nan
                        ),
                        "difference": np.nan,
                    }
                )

    if len(cases) == 0:
        raise ValueError("Could not derive interpretive cases from the available metrics.")

    return pd.DataFrame(cases).head(case_count)


def write_cases_markdown(cases: pd.DataFrame, out_path: Path) -> None:
    lines = ["# Interpretive Cases", ""]
    for _, row in cases.iterrows():
        lines.append(f"## {row['case_id']}: {row['case_type']}")
        lines.append(
            f"- Run: `{row['run_label']}` (session index {int(row['session_index'])}, {row['session_phase']})"
        )
        lines.append(f"- Summary: {row['summary']}")
        lines.append(
            f"- Primary metric: `{row['primary_metric']}` = {row['primary_value']:.4f}"
        )
        secondary_value = row["secondary_value"]
        if pd.notna(secondary_value):
            lines.append(
                f"- Secondary metric: `{row['secondary_metric']}` = {float(secondary_value):.4f}"
            )
        difference = row["difference"]
        if pd.notna(difference):
            lines.append(f"- Difference: {float(difference):.4f}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    ok(f"Saved: {out_path.resolve()}")


def run_comparison_analysis(
    runs_csv: Path,
    out_dir: Path,
    top_n: int = 5,
    case_count: int = 3,
) -> dict[str, object]:
    ensure_dir(out_dir)

    df = load_runs(runs_csv)
    metrics = detect_metric_columns(df)

    corr = correlation_matrix(df, metrics)
    corr_path = out_dir / "correlation_matrix.csv"
    corr.to_csv(corr_path)
    ok(f"Saved: {corr_path.resolve()}")

    ranking = ranking_stability(df, metrics, top_n=top_n)
    ranking_path = out_dir / "ranking_stability.csv"
    ranking.to_csv(ranking_path, index=False)
    ok(f"Saved: {ranking_path.resolve()}")

    phases = session_phase_summary(df, metrics)
    phase_path = out_dir / "session_phase_summary.csv"
    phases.to_csv(phase_path, index=False)
    ok(f"Saved: {phase_path.resolve()}")

    contrast = phase_contrast_summary(df, metrics)
    contrast_path = out_dir / "phase_contrast_summary.csv"
    contrast.to_csv(contrast_path, index=False)
    ok(f"Saved: {contrast_path.resolve()}")

    cases = interpretive_cases(df, metrics, case_count=case_count)
    cases_csv_path = out_dir / "interpretive_cases.csv"
    cases.to_csv(cases_csv_path, index=False)
    ok(f"Saved: {cases_csv_path.resolve()}")

    cases_md_path = out_dir / "interpretive_cases.md"
    write_cases_markdown(cases, cases_md_path)

    report = {
        "input_runs_csv": str(runs_csv),
        "out_dir": str(out_dir),
        "metrics_compared": metrics,
        "n_runs": int(len(df)),
        "correlation_matrix_csv": str(corr_path),
        "ranking_stability_csv": str(ranking_path),
        "session_phase_summary_csv": str(phase_path),
        "phase_contrast_summary_csv": str(contrast_path),
        "interpretive_cases_csv": str(cases_csv_path),
        "interpretive_cases_md": str(cases_md_path),
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Generate run-level comparison analysis outputs including correlation matrix, "
            "ranking stability, session-phase stratification, phase contrasts, "
            "and interpretive cases."
        )
    )
    ap.add_argument(
        "--runs",
        default="data/example/runs_final_example.csv",
        help="Input run-level CSV",
    )
    ap.add_argument(
        "--out_dir",
        default="output/comparison_analysis",
        help="Output directory for comparison-analysis artifacts",
    )
    ap.add_argument(
        "--top_n",
        type=int,
        default=5,
        help="Top-N cutoff for coarse high-load overlap / top-k set consistency",
    )
    ap.add_argument(
        "--case_count",
        type=int,
        default=3,
        help="Number of interpretive cases to export",
    )
    args = ap.parse_args()

    report = run_comparison_analysis(
        runs_csv=Path(args.runs),
        out_dir=Path(args.out_dir),
        top_n=int(args.top_n),
        case_count=int(args.case_count),
    )

    ok(f"Compared metrics: {', '.join(report['metrics_compared'])}")
    ok(f"Completed comparison analysis for {report['n_runs']} runs")


if __name__ == "__main__":
    main()
