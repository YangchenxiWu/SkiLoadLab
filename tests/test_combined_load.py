import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def test_combined_load_runs(tmp_path: Path):
    inp = REPO / "data/example/runs_final_example.csv"
    out_csv = tmp_path / "runs_combined.csv"
    out_json = tmp_path / "report.json"

    p = subprocess.run(
        [
            "skiloadlab-combine",
            "--in",
            str(inp),
            "--out",
            str(out_csv),
            "--report",
            str(out_json),
            "--alpha",
            "0.5",
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

    expected = 0.5 * pd.to_numeric(df["z_internal"], errors="coerce") + 0.5 * pd.to_numeric(
        df["z_mech"], errors="coerce"
    )
    np.testing.assert_allclose(df["combined_load_v2"], expected, rtol=0, atol=1e-12)
