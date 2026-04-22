# QC Rules

This document records the current quality-control rules for `carving_v2` session alignment and
run-level inclusion.

## Alignment failure

Treat a session as alignment failure when any of the following is true:

- The Polar CSV summary start time cannot be parsed into a valid local datetime.
- The GPX track has no valid timestamps.
- A plausible UTC offset cannot be inferred from CSV local start time versus GPX timestamps.
- The anchor delta is so large that the session is no longer credible as the same recording block.
- Run intervals fall largely outside the anchored HR stream, causing most runs to have no HR points.

Current practical threshold proposal:

- `anchor_delta_s > 300` should be treated as alignment failure by default.
- `60 < anchor_delta_s <= 300` should be treated as review-needed, not automatic failure.
- `anchor_delta_s <= 60` is acceptable unless other evidence contradicts it.

## HR coverage too low

Treat HR coverage as too low when any of the following is true:

- A run has `n_hr_samples = 0`.
- A run has fewer than `0.5 * duration_s` usable HR samples in a nominal 1 Hz export.
- A session has fewer than `80%` of runs with at least one aligned HR sample.
- A session shows repeated long HR gaps that materially reduce run-level internal-load estimates.

Current practical threshold proposal:

- Run-level warning: `n_hr_samples < max(30, 0.5 * duration_s)`.
- Session-level warning: fewer than `80%` of runs pass the run-level HR coverage rule.

## Needs exclusion

Exclude a run or session when any of the following is true:

- Alignment failure is confirmed.
- DEM sampling fails or produces unusable elevation for most of the session.
- Segmentation output is clearly non-skiing or obviously broken on manual review.
- HR coverage is too low and the run cannot support internal-load computation.
- Source files are duplicated, corrupted, or not traceable to a single session.

For now, exclusion should be recorded with a concrete reason rather than silently dropping rows.

## Carving uncertain

## Carving labeling workflow

### Step 1: candidate screening

From the run-level table, first screen for runs that are complete, valid, and downhill-type runs.

Candidate screening should remove runs that are clearly unsuitable for carving review, including:

- invalid or missing core run metrics
- failed HR-GPX alignment when internal-load fields are required downstream
- obviously broken segmentation
- runs that are not meaningfully downhill

### Step 2: trajectory-informed review

For each candidate run, review the GPX trajectory together with derived trajectory features.

The review should focus on:

- whether the run is dominated by continuous arc-shaped turns
- whether there is obvious irregular skidding, abrupt stopping, or long traversing
- whether the run shows relatively good speed maintenance
- whether the run shows relatively low excess-dissipation proxies

### Step 3: assign label

Each reviewed run must receive exactly one of the following labels:

- `carving`
- `uncertain`
- `non_carving`

### Step 4: primary analysis

The primary analysis includes only runs labeled `carving`.

### Step 5: sensitivity analysis

Sensitivity analysis should be rerun on:

- `carving + uncertain`

The goal is to check whether the main results remain stable when uncertain runs are included.

## Label-to-analysis mapping

Use the labeling columns in `run_level_labeling.csv` as follows:

- `carving_label`: one of `carving`, `uncertain`, or `non_carving`
- `included_main_analysis`: `yes` only for `carving`; otherwise `no`
- `exclusion_reason`: required when `included_main_analysis = no`
- `label_notes`: optional free-text notes from trajectory review
