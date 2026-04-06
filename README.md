# SkiLoadLab: Reproducible Training Load Modeling for Alpine Skiing

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19108568.svg)](https://doi.org/10.5281/zenodo.19108568)

SkiLoadLab is an open-source Python toolkit for alpine/downhill skiing, centered on a packaged demo-compatible run-level workflow for reproducible combined-load computation, alpha-sweep diagnostics, and figure generation. Public reproducibility begins from an anonymized/demo-compatible run-level table rather than from raw GPS or heart-rate exports.

The primary public reproducibility path is the installable package and formal CLI. Retained upstream utilities for GPX parsing, DEM sampling, and heuristic run segmentation remain available for extension and method development, but they are not the primary public reproducibility path and are not the core CI-validated workflow.

## What SkiLoadLab publicly provides

- installable Python package
- CLI for `skiloadlab-combine`, `skiloadlab-alpha-sweep`, and `skiloadlab-make-figures`
- demo-compatible run-level dataset
- reproducible outputs: CSV, JSON, and figures
- tests and CI for the public workflow

## What is retained but not the primary public reproducibility path

- GPX parsing
- DEM sampling
- heuristic run segmentation

## Key features

- Reproducible run-level internal/external load fusion with interpretable alpha weighting
- Demo-compatible workflow for public reproducibility without exposing raw GPS/HR exports
- Alpha-sweep diagnostics for sensitivity analysis and balance-oriented reporting
- Publication-style figure generation for reporting and manuscript preparation
- Installable Python package with CLI entry points
- GitHub Actions CI and Zenodo-archived releases for testing, citation, and versioning

## Repository structure

- `skiloadlab/` - installable package containing the maintained public demo workflow and CLI entry points
- `src/` - research and legacy utilities, including upstream GPX/DEM/segmentation scripts retained for broader method development
- `scripts/` - backward-compatible workflow shims retained for earlier script-based usage
- `data/` - demo/example inputs
- `docs/` - figures and methods-facing notes
- `paper/` - manuscript/preprint materials
- `tests/` - test suite

The maintained public reproducibility path lives in `skiloadlab/`. The `scripts/` directory is retained for backward-compatible entry points, while `src/` also contains upstream research utilities that provide broader GPX/DEM/segmentation context but are not the primary public demo workflow documented below.

## Scope of the public release

- public reproducibility is centered on the packaged demo workflow
- upstream utilities remain available for extension and method development
- not all upstream steps are currently part of the validated public CI path


## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YangchenxiWu/SkiLoadLab.git
cd SkiLoadLab
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python3 -m pip install -e .
```

For development tools and optional geospatial dependencies, use:

```bash
python3 -m pip install -e '.[dev,geo]'
```

## Quickstart

### 1. Install the package in editable mode

```bash
python3 -m pip install -e .
```

For development tools and optional geospatial dependencies, use:
```bash
python3 -m pip install -e '.[dev,geo]'
```

### 2. Run combined-load computation

```bash
skiloadlab-combine \
  --in data/example/runs_final_example.csv \
  --out output/demo_runs_combined.csv \
  --report output/demo_combined_report.json \
  --alpha 0.5
```

### 3. Run alpha-sweep diagnostics

```bash
skiloadlab-alpha-sweep
```

This step generates:
- `output/alpha_sweep_summary.csv`
- per-alpha CSV/report files in `output/alpha_sweep/`

### 4. Generate publication-style figures

```bash
skiloadlab-make-figures \
  --runs output/demo_runs_combined.csv \
  --alpha_summary output/alpha_sweep_summary.csv \
  --out_dir docs/figures
```

This step generates figures such as:
- `docs/figures/fig03_internal_vs_external_scatter.png`
- `docs/figures/fig06_alpha_sweep.png`

In the maintained public workflow, figure generation consumes the combined run-level table produced by `skiloadlab-combine`, together with the alpha-sweep summary produced by `skiloadlab-alpha-sweep`.

For a step-by-step demo reproduction guide, see [`docs/reproducibility.md`](docs/reproducibility.md).


## Core model

The combined load index is defined as:

`CL(alpha) = alpha * z_internal + (1 - alpha) * z_mech`

where:

- `z_internal` represents standardized internal load
- `z_mech` represents standardized external/mechanical load
- `alpha` controls the relative weighting of the internal component

The alpha-sweep workflow evaluates `alpha` over `[0, 1]` to quantify the trade-off between internal and external alignment rather than assuming a single fixed default.

The balance-oriented score is defined as the smaller of the two constituent correlations at a given alpha.

In the public demo workflow, `z_internal` and `z_mech` are expected to already be present in the run-level input table. The package CLI therefore reproduces the fusion, alpha-sweep, and figure-generation stages of the workflow from a demo-compatible dataset, while retained upstream utilities remain available separately for research use.

The public workflow is exposed through the installable SkiLoadLab package and its command-line interface.

## Outputs

Typical outputs include:

- run-level combined-load CSV tables
- JSON summary reports
- alpha-sweep summary tables
- publication-style figures in `docs/figures/`

Key generated figures include:

- `docs/figures/fig03_internal_vs_external_scatter.png`
- `docs/figures/fig06_alpha_sweep.png`
![Alpha sweep diagnostics](docs/figures/fig06_alpha_sweep.png)

*Alpha-sweep diagnostics showing the trade-off between internal alignment, external alignment, and the balanced score across* `alpha` *values from 0 to 1.*

## Reproducibility note

The repository is designed around a demo-compatible run-level CSV (`data/example/runs_final_example.csv`) so that the core combined-load workflow, alpha-sweep diagnostics, and figure generation can be reproduced without access to raw geolocation or identifiable physiological timestamps.

The recommended public entry points are the package CLI commands documented above.

## Current implementation constraints

- reproducibility begins from an anonymized/demo-compatible run-level table rather than raw GPS/HR exports
- the maintained test path exercises the formal CLI: `skiloadlab-combine`, `skiloadlab-alpha-sweep`, and `skiloadlab-make-figures`
- validation is software-facing: package installation, CLI execution, output generation, and automated tests
- not all upstream utilities are part of the main validated public workflow
- the retained upstream DEM sampling utility currently expects EPSG:4326 inputs
- retained upstream geospatial utilities are useful for research extension, but are not the main public reproducibility path
- Time alignment between Polar HR and GPX logs currently relies on pragmatic timestamp anchoring rather than fully automated drift correction.
- Run segmentation in the broader research workflow is heuristic and may require adaptation across terrain, snow conditions, and skier profile.
- The repository is intended for research transparency and reproducibility, not as a consumer-facing scoring product.

## Validation

Run the public test path with:

```bash
pytest -q
```

## Citation

If you use SkiLoadLab in research, please cite the Zenodo archive. Please prefer the versioned DOI when citing a specific archived software release.

- Concept DOI: https://doi.org/10.5281/zenodo.19108568
- Version DOI (v0.1.2): https://doi.org/10.5281/zenodo.19110471

See also:

- `CITATION.cff`
- `CHANGELOG.md`

## License
MIT License

## Platform support

The public demo workflow has been tested on:
- macOS (Apple Silicon)
- Windows (Python + virtual environment)

All core steps (combined load, alpha sweep, figure generation, and test suite) run successfully with the example dataset.
