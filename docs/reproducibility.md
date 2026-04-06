# Public Reproducibility Protocol

This document is the authoritative public reproducibility protocol for SkiLoadLab. The maintained public reproducibility path is the installable package and formal CLI, centered on a demo-compatible run-level workflow rather than on raw GPS, DEM, or heart-rate preprocessing.

## Scope of the public reproducibility path

Public reproducibility is centered on the packaged demo workflow.

It covers:

- combined-load computation
- alpha-sweep diagnostics
- figure generation
- software-facing validation of package installation, CLI execution, output generation, and automated tests

It does not require:

- raw GPS trajectories
- raw DEM rasters
- identifiable Polar heart-rate exports

Retained upstream utilities for GPX parsing, DEM sampling, and heuristic run segmentation remain available for extension and method development, but they are not the primary public reproducibility path and are not the core CI-validated workflow.

## 1. Reproducibility starts from this file

Public reproducibility begins from the anonymized/demo-compatible run-level table:

- `data/example/runs_final_example.csv`

This table is the maintained input to the public analytical workflow. In the package-based workflow, the standardized components `z_internal` and `z_mech` are already present in this run-level input.

## 2. Exact CLI commands

### Environment setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/YangchenxiWu/SkiLoadLab.git
cd SkiLoadLab
python3 -m venv .venv
source .venv/bin/activate
```

Install the package:

```bash
python3 -m pip install -e .
```

For development tools and optional geospatial dependencies, use:

```bash
python3 -m pip install -e '.[dev,geo]'
```

### Maintained public analytical workflow

Run the public workflow in this order:

```bash
skiloadlab-combine \
  --in data/example/runs_final_example.csv \
  --out output/demo_runs_combined.csv \
  --report output/demo_combined_report.json \
  --alpha 0.5
```

```bash
skiloadlab-alpha-sweep
```

```bash
skiloadlab-make-figures \
  --runs output/demo_runs_combined.csv \
  --alpha_summary output/alpha_sweep_summary.csv \
  --out_dir docs/figures
```

Run the validated software test path with:

```bash
pytest -q
```

## 3. Expected outputs

The maintained public workflow generates:

- `output/demo_runs_combined.csv`
- `output/demo_combined_report.json`
- `output/alpha_sweep_summary.csv`
- per-alpha CSV and JSON reports in `output/alpha_sweep/`
- figures in `docs/figures/`

In the maintained public workflow, figure generation consumes the combined run-level table produced by `skiloadlab-combine`, together with the alpha-sweep summary produced by `skiloadlab-alpha-sweep`.

Expected figure outputs include:

- `docs/figures/fig01_run_duration_hist.png`
- `docs/figures/fig02_vertical_drop_hist.png`
- `docs/figures/fig03_internal_vs_external_scatter.png`
- `docs/figures/fig04_combined_vs_components.png`
- `docs/figures/fig05_top_runs_by_combined.png`
- `docs/figures/fig06_alpha_sweep.png`

## 4. What is validated in tests and CI

The maintained test path exercises the formal CLI and package installation path.

Validated public workflow coverage includes:

- package installation in a Python virtual environment
- `skiloadlab-combine`
- `skiloadlab-alpha-sweep`
- `skiloadlab-make-figures`
- automated tests via `pytest -q`

Validation is software-facing. It covers package installation, CLI execution, output generation, and automated tests. It does not imply that all upstream utilities are part of the main validated public workflow.

## 5. What is out of scope for the public reproducibility path

The following are retained upstream utilities or broader methodological context, not the maintained public reproducibility path:

- GPX parsing
- DEM sampling
- heuristic run segmentation
- HR-GPX time alignment from raw exports
- raw-sensor preprocessing from full-session inputs

These components remain useful for method development and extension, but they are not the primary public reproducibility path and are not the core CI-validated path.

## Current implementation constraints

- reproducibility begins from an anonymized/demo-compatible run-level table rather than raw GPS/HR exports
- the maintained implementation expects `z_internal` and `z_mech` in the run-level input table
- the balance-oriented score is defined as the smaller of the two constituent correlations at a given alpha
- the retained upstream DEM sampling utility currently expects EPSG:4326 inputs
- retained upstream geospatial utilities are useful for research extension, but are not the main public reproducibility path
- time alignment between HR and GPX streams in broader upstream workflows is currently pragmatic rather than fully automated
- run segmentation in broader upstream workflows is heuristic and may require adaptation across contexts

## Tested environment

The public workflow has been tested on:

- macOS (Apple Silicon / arm64)
- Windows (Python virtual environment)
- Python 3.13

## Citation

If you use SkiLoadLab in research, cite the Zenodo archive:

- Concept DOI: https://doi.org/10.5281/zenodo.19108568
- Version DOI (v0.1.2): https://doi.org/10.5281/zenodo.19110471
