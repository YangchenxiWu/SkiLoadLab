import subprocess
import sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]

def test_combined_load_runs(tmp_path: Path):
    inp = REPO / "data/example/runs_with_hr_example.csv"
    out_csv = tmp_path / "runs_combined.csv"
    out_json = tmp_path / "report.json"

    p = subprocess.run(
        [
            sys.executable,
            str(REPO / "src/model/combined_load.py"),
            "--in", str(inp),
            "--out", str(out_csv),
            "--report", str(out_json),
            "--alpha", "0.5",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert p.returncode == 0, p.stderr + "\n" + p.stdout
    assert out_csv.exists()
    df = pd.read_csv(out_csv)
    for col in ["combined_load_v2", "z_internal", "z_mech"]:
        assert col in df.columns
