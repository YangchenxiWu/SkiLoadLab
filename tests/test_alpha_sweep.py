import subprocess
import sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]

def test_alpha_sweep_runs(tmp_path: Path):
    inp = REPO / "data/example/runs_with_hr_example.csv"
    out_dir = tmp_path / "alpha_sweep"
    rep_dir = tmp_path / "reports"
    summary = tmp_path / "alpha_sweep_summary.csv"

    p = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/alpha_sweep.py"),
            "--in", str(inp),
            "--alpha_step", "0.5",
            "--out_dir", str(out_dir),
            "--report_dir", str(rep_dir),
            "--summary", str(summary),
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert p.returncode == 0, p.stderr + "\n" + p.stdout
    assert summary.exists()

    df = pd.read_csv(summary)
    # 0.0, 0.5, 1.0 => 至少 3 行
    assert len(df) >= 3
    for col in ["score_balanced", "corr_comb_internal", "corr_comb_mech"]:
        assert col in df.columns
