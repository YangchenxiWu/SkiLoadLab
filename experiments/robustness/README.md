# Trajectory and Elevation Robustness Framework

This directory contains the current `carving_v2` robustness framework.

## Modules

- `data_interface.py`: load the current carving-focused analytical set and expose per-run baseline inputs
- `baseline.py`: generate baseline reference outputs and save `baseline_run_metrics.csv` plus `baseline_reference.json`
- `perturbations.py`: apply single-factor perturbations and maintain `perturbation_registry.csv`
- `recompute.py`: recompute downstream run-level outputs from perturbed inputs
- `metrics.py`: compare perturbed outputs against baseline and build `robustness_metrics_long.csv`
- `summarize.py`: aggregate long-format results into `robustness_summary_table.csv`
- `plotting.py`: generate `fig_robustness_core.png`
- `runner.py`: internal orchestration layer for the experiment chain
- `cli.py`: official user-facing CLI for subset selection and explicit output-path control

## Supported perturbation types

- elevation perturbation
- position perturbation
- sampling perturbation
- temporal perturbation
- structural missingness perturbation

## Core stability outputs

- segmentation-level stability
- vertical drop error
- `CL(alpha)` deviation
- top-k consistency
- phase contrast deviation

## Segmentation stability definition

`segmentation_stability` is currently defined as run-interval IoU:

- intersection-over-union between the baseline run time interval and the perturbed recomputed run time interval
- `1.0` means the two run intervals are temporally identical
- `0.0` means the intervals have no temporal overlap

This is therefore an overlap-based boundary stability metric, not an exact-match flag.
Under temporal perturbations, values can collapse when shifted boundaries produce little or no overlap
with the baseline interval, even if the perturbed run still looks qualitatively similar.

To avoid relying on a single hard overlap-style measure, the long-format results also include:

- `matched_duration_fraction`
  baseline-duration-normalized temporal overlap fraction
- `boundary_shift_mean_s`
  mean absolute start/end boundary shift in seconds

These provide continuous supplements to the IoU-style segmentation stability measure.

## Official CLI

The official robustness CLI entry is:

```bash
python3 -m experiments.robustness.cli
```

`experiments/robustness/run_robustness.py` is only a thin compatibility wrapper around the
same CLI and should not be treated as the primary user-facing entry.

Supported subset choices:

- `primary`
- `strict`
- `both`

Key explicit path controls:

- `--output-dir`
- `--baseline-run-metrics-path`
- `--baseline-reference-path`
- `--perturbation-registry-path`
- `--recomputed-run-metrics-path`
- `--long-table-path`
- `--summary-table-path`
- `--manifest-path`
- `--figure-path`
- `--figure-primary-path`
- `--figure-strict-path`

The resulting `run_manifest.json` records the fully resolved output paths for all of the files above.

## Test run

Use the YAML config:

- `experiments/robustness/config/test_run.yaml`

Run:

```bash
python3 -m experiments.robustness.cli \
  --config experiments/robustness/config/test_run.yaml \
  --subset primary \
  --output-dir experiments/robustness/results/test_run \
  --long-table-path experiments/robustness/results/test_run/robustness_metrics_long.csv \
  --summary-table-path experiments/robustness/results/test_run/robustness_summary_table.csv \
  --manifest-path experiments/robustness/results/test_run/run_manifest.json \
  --figure-path experiments/robustness/results/test_run/fig_robustness_core.png \
  --figure-primary-path experiments/robustness/results/test_run/fig_robustness_core_primary.png \
  --figure-strict-path experiments/robustness/results/test_run/fig_robustness_core_strict.png
```

## Formal run

Use:

```bash
python3 -m experiments.robustness.cli \
  --config experiments/robustness/config/formal_run.yaml \
  --subset both \
  --output-dir experiments/robustness/results/formal_run \
  --baseline-run-metrics-path experiments/robustness/results/formal_run/baseline_run_metrics.csv \
  --baseline-reference-path experiments/robustness/results/formal_run/baseline_reference.json \
  --perturbation-registry-path experiments/robustness/results/formal_run/perturbation_registry.csv \
  --recomputed-run-metrics-path experiments/robustness/results/formal_run/recomputed_run_metrics.csv \
  --long-table-path experiments/robustness/results/formal_run/robustness_metrics_long.csv \
  --summary-table-path experiments/robustness/results/formal_run/robustness_summary_table.csv \
  --manifest-path experiments/robustness/results/formal_run/run_manifest.json \
  --figure-path experiments/robustness/results/formal_run/fig_robustness_core.png \
  --figure-primary-path experiments/robustness/results/formal_run/fig_robustness_core_primary.png \
  --figure-strict-path experiments/robustness/results/formal_run/fig_robustness_core_strict.png
```

Current formal outputs are written to:

- `experiments/robustness/results/formal_run/`
- `experiments/robustness/results/formal_run/fig_robustness_core.png`
- `experiments/robustness/results/formal_run/fig_robustness_core_primary.png`
- `experiments/robustness/results/formal_run/fig_robustness_core_strict.png`
- `experiments/robustness/results/formal_run/robustness_metrics_long.csv`
- `experiments/robustness/results/formal_run/robustness_summary_table.csv`
- `experiments/robustness/results/formal_run/run_manifest.json`

The test run is intentionally a structured engineering check rather than a manuscript-ready robustness
experiment. It is designed to make the outputs interpretable enough for framework validation while
remaining small enough to run quickly.
