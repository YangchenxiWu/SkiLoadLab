# Carving V2 Plan

## Project goal

Upgrade the current demonstration-focused run-level fusion workflow into a carving-focused,
larger-sample, robustness-enhanced sports-engineering workflow for a stronger next-version
paper, while preserving the current submitted/preprint path untouched.

## Priority 1

- Build a reproducible intake path for Polar exports under `data/carving_v2/raw/`.
- Establish a carving-only dataset workflow with stable field naming and run-level tables.
- Add robustness experiment scaffolds for trajectory/elevation perturbations.
- Add interpretable HR short-gap dropout handling baselines.

## Priority 2

- Integrate larger-sample sessions with traceable manifest logging.
- Compare carving_v2 run-level schema against the current v1 schema.
- Add reusable preprocessing comparison scaffolds shared across HR and trajectory signals.
- Draft manuscript figures and methods placeholders for the next-version paper.

## Priority 3

- Expand robustness summaries to phase-wise contrast and top-k consistency reporting.
- Add optional preprocessing comparisons in the future manuscript workflow.
- Prepare transfer/submission packaging notes once the carving_v2 dataset is populated.

## Explicit non-priority

- No medical-risk detection module.
- No disease detection, diagnosis, or clinical decision support features.
- No claims beyond engineering workflow setup until real carving_v2 data are imported.

## Immediate TODOs

- Populate `data/carving_v2/raw/` with tomorrow's Polar exports.
- Decide session labels for imported files if filenames are ambiguous.
- Implement final carving inclusion rules after reviewing actual exported signals.
