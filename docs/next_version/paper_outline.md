# Carving V2 Paper Outline

## Introduction

- Motivate carving-focused alpine skiing load analysis at the run level.
- Position the work as an engineering robustness and reproducibility upgrade over the current
  demonstration-focused workflow.
- Avoid unsupported claims until larger-sample carving_v2 data are processed.

## Methods

- Data intake and provenance logging for Polar exports.
- Carving-only session and run inclusion workflow.
- Run-level feature table generation with harmonized field naming.
- Comparison against the current v1 run-level schema.

## Robustness analysis

- Elevation noise injection.
- Position jitter.
- Downsampling.
- Timestamp offset.
- Short missing trajectory/elevation segments.
- Metrics of interest: segmentation stability, vertical drop estimation, `CL(alpha)`,
  top-k set consistency, and phase-wise contrast.

## HR dropout handling

- Short-gap detection.
- No-correction baseline.
- Linear interpolation baseline.
- Smoothing plus interpolation baseline.
- Optional Kalman-style method placeholder kept secondary to interpretable baselines.

## Results

- Larger-sample carving_v2 descriptive summary.
- Robustness sensitivity findings.
- HR dropout comparison findings.
- Updated carving_v2 alpha-sweep behavior.

## Discussion

- Implications for reproducible sports-engineering workflow design.
- Limits of heuristic carving inclusion and sensor-quality assumptions.
- Next steps for broader validation and submission strategy.

## Future figures

1. Workflow architecture diagram for intake, processing, fusion, and experiments.
2. Trajectory/elevation robustness figure showing perturbation effects.
3. HR dropout handling comparison figure across baseline correction methods.
4. Updated alpha-sweep figure for `carving_v2`.

## TODO

- Replace outline bullets with manuscript-ready subsection text after real data import.
- Add concrete sample-size reporting once the carving_v2 dataset is assembled.
