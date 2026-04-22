# Carving V2 Dataset Log

This log tracks the currently imported `carving_v2` sessions that have already been converted into
run-level rows under `output/carving_v2_cleaned/`.

## Session log

| session_label | source | date | device files | current_processing_status | abnormality_or_issue |
| --- | --- | --- | --- | --- | --- |
| `polar_session_2026-02-03_09-55-13` | Polar export imported into `data/carving_v2/raw/` | `2026-02-03` | `polar_session_2026-02-03_09-55-13.csv`, `polar_session_2026-02-03_09-55-13.gpx` | Intake complete; DEM elevation sampled; run segmentation complete; HR-GPX alignment complete; `14` run-level rows written | No obvious alignment failure. Anchor delta `2.023s` |
| `polar_session_2026-02-04_09-57-46` | Polar export imported into `data/carving_v2/raw/` | `2026-02-04` | `polar_session_2026-02-04_09-57-46.csv`, `polar_session_2026-02-04_09-57-46.gpx` | Intake complete; DEM elevation sampled; run segmentation complete; HR-GPX alignment complete; `13` run-level rows written | Alignment offset larger than other sessions but still usable. Anchor delta `134.643s`; review later |
| `polar_session_2026-02-05_10-21-15` | Polar export imported into `data/carving_v2/raw/` | `2026-02-05` | `polar_session_2026-02-05_10-21-15.csv`, `polar_session_2026-02-05_10-21-15.gpx` | Intake complete; DEM elevation sampled; run segmentation complete; HR-GPX alignment complete; `16` run-level rows written | No obvious alignment failure. Anchor delta `1.370s` |
| `polar_session_2026-02-06_10-17-06` | Polar export imported into `data/carving_v2/raw/` | `2026-02-06` | `polar_session_2026-02-06_10-17-06.csv`, `polar_session_2026-02-06_10-17-06.gpx` | Intake complete; DEM elevation sampled; run segmentation complete; HR-GPX alignment complete; `21` run-level rows written | No obvious alignment failure. Anchor delta `2.376s` |

## Notes

- Session-level run counts currently sum to `64`.
- Source device/export type is Polar, with one relative-time HR CSV and one absolute-time GPX file per session.
- GPX altitude from the Polar export is not usable as-is because exported `<ele>` values are `0.0`; elevation is therefore sampled from `data/external/dem/dem.tif`.
- Current processing outputs live under `output/carving_v2_cleaned/`.
- Carving inclusion labels are not finalized yet and should be added after the carving definition is locked.
- Manual carving review should follow the 5-step workflow documented in `docs/next_version/qc_rules.md`.

## Pointers

- Intake manifest: `data/carving_v2/raw/intake_manifest.csv` and `data/carving_v2/raw/intake_manifest.json`
- Session anchor metadata: `output/carving_v2_cleaned/run_level_anchors.json`
- Current run-level table: `output/carving_v2_cleaned/run_level_aligned.csv`
