import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_make_figures_runs(tmp_path: Path):
    runs = REPO / "data/example/runs_final_example.csv"
    alpha_summary = REPO / "output/alpha_sweep_summary.csv"  # 可能不存在，所以这里不依赖它
    out_dir = tmp_path / "figs"

    # 只要求不报错 + 至少生成一张图
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

    # 至少有一张 png
    pngs = list(out_dir.glob("*.png"))
    assert len(pngs) >= 1
