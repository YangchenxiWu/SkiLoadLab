# Carving V2 Dataset Log

Use this log together with the generated intake manifest. One row should represent one imported
source file or one clearly defined session artifact.

| source_file_name | date | modality | session_label | carving_inclusion_yes_no | quality_or_issue_notes |
| --- | --- | --- | --- | --- | --- |
| TODO_fill_after_import | YYYY-MM-DD | GPX / CSV / FIT / HRV CSV / ZIP | TODO_session_label | TODO | TODO |

## Field notes

- `source_file_name`: original exported filename from Polar Flow or local export package
- `date`: session date when known from filename, metadata, or manual verification
- `modality`: one of `GPX`, `CSV`, `FIT`, `HRV CSV`, or `ZIP`
- `session_label`: stable session identifier used in `data/carving_v2/raw/sessions/`
- `carving_inclusion_yes_no`: `yes`, `no`, or `review`
- `quality_or_issue_notes`: timestamp gaps, elevation drift, HR dropout, duplicate files, etc.

## TODO

- Append rows after each import batch.
- Cross-check this table against `data/carving_v2/raw/intake_manifest.csv`.
