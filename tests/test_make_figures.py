import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_make_figures_runs(tmp_path: Path):
    runs = REPO / "data/example/runs_final_example.csv"
    combined_runs = tmp_path / "runs_combined.csv"
    combined_report = tmp_path / "report.json"
    alpha_summary = tmp_path / "alpha_sweep_summary.csv"
    alpha_dir = tmp_path / "alpha_sweep"
    report_dir = tmp_path / "reports"
    out_dir = tmp_path / "figs"

    combine = subprocess.run(
        [
            "skiloadlab-combine",
            "--in",
            str(runs),
            "--out",
            str(combined_runs),
            "--report",
            str(combined_report),
            "--alpha",
            "0.5",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert combine.returncode == 0, combine.stderr + "\n" + combine.stdout
    assert combined_runs.exists()

    sweep = subprocess.run(
        [
            "skiloadlab-alpha-sweep",
            "--in",
            str(runs),
            "--alpha_step",
            "0.5",
            "--out_dir",
            str(alpha_dir),
            "--report_dir",
            str(report_dir),
            "--summary",
            str(alpha_summary),
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert sweep.returncode == 0, sweep.stderr + "\n" + sweep.stdout
    assert alpha_summary.exists()

    p = subprocess.run(
        [
            "skiloadlab-make-figures",
            "--runs",
            str(combined_runs),
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

    expected_pngs = [
        "fig01_run_duration_hist.png",
        "fig02_vertical_drop_hist.png",
        "fig03_internal_vs_external_scatter.png",
        "fig04_combined_vs_components.png",
        "fig05_top_runs_by_combined.png",
        "fig06_alpha_sweep.png",
    ]
    for name in expected_pngs:
        assert (out_dir / name).exists(), name
