import subprocess
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def test_compare_analysis_runs(tmp_path: Path):
    runs = REPO / "data/example/runs_final_example.csv"
    out_dir = tmp_path / "comparison_analysis"

    p = subprocess.run(
        [
            "python3",
            "-m",
            "skiloadlab.core_compare",
            "--runs",
            str(runs),
            "--out_dir",
            str(out_dir),
            "--top_n",
            "3",
            "--case_count",
            "3",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert p.returncode == 0, p.stderr + "\n" + p.stdout

    corr_path = out_dir / "correlation_matrix.csv"
    ranking_path = out_dir / "ranking_stability.csv"
    phase_path = out_dir / "session_phase_summary.csv"
    drift_path = out_dir / "late_session_drift.csv"
    cases_csv_path = out_dir / "interpretive_cases.csv"
    cases_md_path = out_dir / "interpretive_cases.md"

    for path in [corr_path, ranking_path, phase_path, drift_path, cases_csv_path, cases_md_path]:
        assert path.exists(), path.name

    corr = pd.read_csv(corr_path)
    assert "metric" in corr.columns
    assert "combined_load_v2" in corr.columns
    assert "z_internal" in corr.columns

    ranking = pd.read_csv(ranking_path)
    for col in ["metric_a", "metric_b", "spearman_rho", "top_k_set_consistency"]:
        assert col in ranking.columns
    assert len(ranking) > 0

    phase = pd.read_csv(phase_path)
    assert set(["early", "mid", "late"]).issubset(set(phase["session_phase"]))

    drift = pd.read_csv(drift_path)
    assert len(drift) > 0
    assert set(["metric", "drift_method", "late_session_drift"]).issubset(set(drift.columns))
    assert set(drift["drift_method"]) == {"late_tercile_mean_minus_early_tercile_mean"}
    assert set(drift["run_order_basis"]) == {"input_row_order"}
    assert set(drift["phase_definition"]) == {"contiguous_session_terciles"}
    assert "z_trimp" in set(drift["metric"])
    assert "vertical_drop_m" in set(drift["metric"])
    assert "combined_load_v2" in set(drift["metric"])

    cases = pd.read_csv(cases_csv_path)
    assert 2 <= len(cases) <= 3
    assert "case_type" in cases.columns
    assert "run_label" in cases.columns
    assert cases["run_label"].is_unique

    cases_md = cases_md_path.read_text(encoding="utf-8")
    assert "# Interpretive Cases" in cases_md
