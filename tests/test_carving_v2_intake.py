from pathlib import Path

import pandas as pd

from skiloadlab.carving_v2.dataset_workflow import compare_with_v1_schema, initialize_carving_run_level_table
from skiloadlab.intake.polar_intake import organize_polar_exports


def test_polar_intake_manifest(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / ".gitkeep").write_text("", encoding="utf-8")
    (raw_dir / "Session One.gpx").write_text("<gpx />", encoding="utf-8")
    (raw_dir / "Session One.csv").write_text("timestamp,hr\n", encoding="utf-8")
    (raw_dir / "Session One_hrv.csv").write_text("timestamp,rr\n", encoding="utf-8")
    (raw_dir / "Session One.fit").write_bytes(b"FIT")

    records = organize_polar_exports(raw_dir=raw_dir)

    assert len(records) == 4
    assert (raw_dir / "intake_manifest.csv").exists()
    assert (raw_dir / "intake_manifest.json").exists()
    assert (raw_dir / "sessions" / "session_one" / "original" / "Session One.gpx").exists()
    assert any(record.detected_type == "HRV CSV" for record in records)


def test_carving_v2_schema_scaffold():
    source = initialize_carving_run_level_table(
        pd.DataFrame(
            {
                "vertical_drop_m": [100.0, 120.0],
                "duration_s": [45.0, 48.0],
                "z_internal": [0.2, 0.4],
                "z_mech": [0.1, 0.5],
            }
        )
    )
    comparison = compare_with_v1_schema(source)

    assert "carving_inclusion" in source.columns
    assert "repeated_run_block" in source.columns
    assert "status" in comparison.columns
