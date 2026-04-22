# Run Table Schema

This document describes the current columns in `output/carving_v2_cleaned/run_level_aligned.csv`.

| field_name | unit | meaning | missing_value_rule | used_in_main_analysis |
| --- | --- | --- | --- | --- |
| `session_label` | none | Stable identifier for the source session | Must not be missing | `yes` |
| `subject_id` | none | Subject / athlete name carried from the Polar export | Missing only if source export omitted athlete name | `no` |
| `sport` | none | Sport label from Polar export | Missing only if source export omitted sport | `no` |
| `run_id` | none | Run identifier within session, generated from segmentation order | Must not be missing | `yes` |
| `start_time_utc` | UTC timestamp | Segmented run start time from GPX after alignment workflow | Must not be missing | `no` |
| `end_time_utc` | UTC timestamp | Segmented run end time from GPX after alignment workflow | Must not be missing | `no` |
| `duration_s` | seconds | Run duration from segmented GPX track | Must not be missing | `yes` |
| `vertical_drop_m` | meters | Elevation drop across the run, using DEM-sampled elevation | Must not be missing | `yes` |
| `speed_mean_ms` | m/s | Mean horizontal speed during the run | Must not be missing | `no` |
| `speed_p95_ms` | m/s | 95th percentile horizontal speed during the run | Must not be missing | `no` |
| `vvert_mean_ms` | m/s | Mean vertical speed during the run; more negative indicates stronger descent | Must not be missing | `no` |
| `n_hr_samples` | samples | Number of HR samples aligned inside the run interval | `0` allowed if alignment exists but no usable HR points fall inside the run | `yes` |
| `hr_mean_bpm` | bpm | Mean heart rate during the run interval | Leave empty if `n_hr_samples = 0` | `no` |
| `hr_max_bpm` | bpm | Maximum heart rate during the run interval | Leave empty if `n_hr_samples = 0` | `no` |
| `hr_min_bpm` | bpm | Minimum heart rate during the run interval | Leave empty if `n_hr_samples = 0` | `no` |
| `impulse_hr_above_rest_bpms` | bpm·s | Integrated heart-rate impulse above session rest HR: `sum(max(HR - HR_rest, 0) * dt)` within the run | Leave empty if `n_hr_samples = 0` or rest HR missing | `yes` |
| `edwards_trimp` | TRIMP points | Edwards TRIMP computed from HR zone dwell time within the run | Leave empty if `n_hr_samples = 0` or session max HR missing | `yes` |
| `hr_rest_bpm` | bpm | Session rest HR from the Polar summary row (`HR sit`) | Leave empty if source export missing `HR sit` | `no` |
| `hr_max_session_bpm` | bpm | Session max HR reference from the Polar summary row (`HR max`) | Leave empty if source export missing `HR max` | `no` |
| `anchor_delta_s` | seconds | Offset applied when anchoring relative-time HR CSV to absolute-time GPX timestamps | Must not be missing for aligned sessions | `yes` |

## Main analysis fields

Current default main-analysis candidates from this table are:

- `session_label`
- `run_id`
- `duration_s`
- `vertical_drop_m`
- `n_hr_samples`
- `impulse_hr_above_rest_bpms`
- `edwards_trimp`
- `anchor_delta_s`

## Future fields not yet added

These are expected later but are not yet present in the current run-level table:

- `carving_inclusion`
- `carving_inclusion_reason`
- `repeated_run_block`
- standardized fields such as `z_internal`, `z_mech`, and `combined_load_v2`

## Labeling table extension

The companion labeling table `output/carving_v2_cleaned/run_level_labeling.csv` extends the current
run-level table with four manual-review columns:

| field_name | unit | meaning | missing_value_rule | used_in_main_analysis |
| --- | --- | --- | --- | --- |
| `carving_label` | none | Manual run label: `carving`, `uncertain`, or `non_carving` | Leave empty before review; must be filled after labeling | `yes` |
| `included_main_analysis` | none | Whether the run is included in the primary analysis set | Leave empty before review; after labeling this should be `yes` only for `carving` | `yes` |
| `exclusion_reason` | none | Reason the run is not included in the primary analysis | Leave empty when `included_main_analysis = yes`; otherwise should be filled | `yes` |
| `label_notes` | none | Free-text notes from the reviewer about trajectory pattern or uncertainty | Optional | `no` |
