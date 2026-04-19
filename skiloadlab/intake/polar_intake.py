from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile


SUPPORTED_SUFFIXES = {
    ".gpx": "GPX",
    ".csv": "CSV",
    ".fit": "FIT",
    ".zip": "ZIP",
}


@dataclass
class IntakeRecord:
    source_file_name: str
    source_path: str
    detected_type: str
    session_label: str
    copied_to: str
    extracted_dir: str
    zip_member_count: int
    notes: str


def _normalize_session_label(name: str) -> str:
    label = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return label or "session_unknown"


def _detect_type(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".csv" and "hrv" in path.stem.lower():
        return "HRV CSV", "hrv_csv"
    if suffix in SUPPORTED_SUFFIXES:
        return SUPPORTED_SUFFIXES[suffix], SUPPORTED_SUFFIXES[suffix].lower().replace(" ", "_")
    return "UNKNOWN", "unknown"


def _iter_source_files(raw_dir: Path) -> Iterable[Path]:
    for path in sorted(raw_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.name in {"intake_manifest.csv", "intake_manifest.json"}:
            continue
        yield path


def _write_manifest(records: list[IntakeRecord], csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(IntakeRecord.__dataclass_fields__.keys())
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump([asdict(record) for record in records], handle, indent=2)


def organize_polar_exports(
    raw_dir: Path,
    sessions_dir: Path | None = None,
    manifest_csv: Path | None = None,
    manifest_json: Path | None = None,
) -> list[IntakeRecord]:
    raw_dir = raw_dir.resolve()
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    sessions_dir = (sessions_dir or raw_dir / "sessions").resolve()
    manifest_csv = (manifest_csv or raw_dir / "intake_manifest.csv").resolve()
    manifest_json = (manifest_json or raw_dir / "intake_manifest.json").resolve()

    sessions_dir.mkdir(parents=True, exist_ok=True)
    records: list[IntakeRecord] = []

    for source_path in _iter_source_files(raw_dir):
        detected_type, type_slug = _detect_type(source_path)
        session_label = _normalize_session_label(source_path.stem)
        session_dir = sessions_dir / session_label
        original_dir = session_dir / "original"
        extracted_dir = session_dir / "extracted"
        original_dir.mkdir(parents=True, exist_ok=True)

        copied_path = original_dir / source_path.name
        shutil.copy2(source_path, copied_path)

        zip_member_count = 0
        notes = ""
        if detected_type == "ZIP":
            extracted_dir.mkdir(parents=True, exist_ok=True)
            with ZipFile(source_path) as archive:
                archive.extractall(extracted_dir)
                zip_member_count = len(archive.namelist())
            notes = "Zip package extracted for later manual review."
        elif detected_type == "UNKNOWN":
            notes = "Unsupported suffix kept for traceability; manual review required."
        elif type_slug == "csv":
            notes = "Generic CSV detected; confirm whether this is a session summary or stream export."

        records.append(
            IntakeRecord(
                source_file_name=source_path.name,
                source_path=str(source_path),
                detected_type=detected_type,
                session_label=session_label,
                copied_to=str(copied_path),
                extracted_dir=str(extracted_dir if extracted_dir.exists() else ""),
                zip_member_count=zip_member_count,
                notes=notes,
            )
        )

    _write_manifest(records, manifest_csv, manifest_json)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Organize Polar export files into a carving_v2 session structure."
    )
    parser.add_argument(
        "--raw_dir",
        default="data/carving_v2/raw",
        help="Directory containing exported Polar files to intake.",
    )
    parser.add_argument(
        "--sessions_dir",
        default=None,
        help="Optional output directory for organized sessions. Defaults to <raw_dir>/sessions.",
    )
    parser.add_argument(
        "--manifest_csv",
        default=None,
        help="Optional manifest CSV path. Defaults to <raw_dir>/intake_manifest.csv.",
    )
    parser.add_argument(
        "--manifest_json",
        default=None,
        help="Optional manifest JSON path. Defaults to <raw_dir>/intake_manifest.json.",
    )
    args = parser.parse_args()

    records = organize_polar_exports(
        raw_dir=Path(args.raw_dir),
        sessions_dir=Path(args.sessions_dir) if args.sessions_dir else None,
        manifest_csv=Path(args.manifest_csv) if args.manifest_csv else None,
        manifest_json=Path(args.manifest_json) if args.manifest_json else None,
    )

    print(f"[OK] Organized {len(records)} files")
    print(f"[OK] Manifest CSV: {(Path(args.manifest_csv) if args.manifest_csv else Path(args.raw_dir) / 'intake_manifest.csv').resolve()}")
    print(f"[OK] Manifest JSON: {(Path(args.manifest_json) if args.manifest_json else Path(args.raw_dir) / 'intake_manifest.json').resolve()}")


if __name__ == "__main__":
    main()
