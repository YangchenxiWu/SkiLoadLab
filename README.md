# SkiLoadLab: Reproducible Training Load Modeling for Downhill Skiing

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19108568.svg)](https://doi.org/10.5281/zenodo.19108568)

SkiLoadLab is a reproducible run-level load fusion toolkit for alpine/downhill skiing. It combines internal and external load proxies through an interpretable alpha-weighted framework, with optional upstream GPX/DEM/HR processing components for full-session workflows.

The public repository is centered on a demo-compatible run-level workflow for transparent method development, reproducible reporting, and publication-style figure generation.

## Key features

- Reproducible run-level internal/external load fusion with interpretable alpha weighting
- Demo-compatible workflow for public reproducibility without exposing raw GPS/HR exports
- Alpha-sweep diagnostics for sensitivity analysis and balance-point selection
- Publication-style figure generation for reporting and manuscript preparation
- Installable Python package with CLI entry points
- GitHub Actions CI and Zenodo-archived releases for testing, citation, and versioning

## Repository structure

- `skiloadlab/` - installable package containing the core implementation and CLI entry points
- `src/` - legacy-compatible shim entry points and earlier module layout
- `scripts/` - legacy-compatible runnable shims for workflow compatibility
- `data/` - demo/example inputs
- `docs/` - figures and methods-facing notes
- `paper/` - manuscript/preprint materials
- `tests/` - test suite

The installable package lives in `skiloadlab/`. The `src/` and `scripts/` paths are retained as legacy-compatible entry points, while the public workflow is documented through the package CLI.


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

### 2. Run the demo combined-load workflow

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
  --runs data/example/runs_final_example.csv \
  --alpha_summary output/alpha_sweep_summary.csv \
  --out docs/figures
```

This step generates figures such as:
- `docs/figures/fig03_internal_vs_external_scatter.png`
- `docs/figures/fig06_alpha_sweep.png`

### 5. Run tests

```bash
pytest -q
```

For a step-by-step demo reproduction guide, see [`docs/reproducibility.md`](docs/reproducibility.md).


## Core model

The combined load index is defined as:

`CL(alpha) = alpha * z_internal + (1 - alpha) * z_mech`

where:

- `z_internal` represents standardized internal load
- `z_mech` represents standardized external/mechanical load
- `alpha` controls the relative weighting of the internal component

The alpha-sweep workflow evaluates `alpha` over `[0, 1]` to quantify the trade-off between internal and external alignment rather than assuming a single fixed default.

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

## Current assumptions and limitations

- The demo workflow operates on a run-level table rather than raw GPS/HR exports.
- Time alignment between Polar HR and GPX logs currently relies on pragmatic timestamp anchoring rather than fully automated drift correction.
- Run segmentation in the full workflow is heuristic and may require adaptation across terrain, snow conditions, and skier profile.
- The repository is intended for research transparency and reproducibility, not as a consumer-facing scoring product.

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


