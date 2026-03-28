import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_make_figures_runs(tmp_path: Path):
    runs = REPO / "data/example/runs_final_example.csv"
    alpha_summary = REPO / "output/alpha_sweep_summary.csv"  # This file may not exist in advance, so the test should not depend on it
    out_dir = tmp_path / "figs"

    # Only require a successful run and at least one generated figure
    p = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/make_figures.py"),
            "--runs",
            str(runs),
            "--alpha_summary",
            str(alpha_summary),
            "--out_dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert p.returncode == 0, p.stderr + "\n" + p.stdout

    # At least one PNG figure should be generated
    pngs = list(out_dir.glob("*.png"))
    assert len(pngs) >= 1
