# SkiLoadLab: Reproducible Training Load Modeling for Downhill Skiing (Polar HR + GPX + DEM)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19108568.svg)](https://doi.org/10.5281/zenodo.19108568)

SkiLoadLab is a research-oriented, reproducible pipeline for modeling downhill-skiing training load by combining internal load proxies (heart-rate-derived) and external load proxies (terrain- and speed-derived). The repository supports both a full workflow (GPX + Polar HR + DEM) and a demo-compatible run-level workflow designed for transparent method development, figure generation, and reproducible reporting.

## Key features

- Combined internal/external load modeling with interpretable alpha-weighted fusion
- Demo-compatible run-level workflow for reproducibility without exposing raw GPS/HR exports
- Alpha-sweep diagnostics for sensitivity analysis
- Publication-style figure generation
- Unit/integration tests with GitHub Actions CI
- Zenodo-archived release for citation and versioning

## Repository structure

- `src/` - core modeling modules
- `scripts/` - runnable utilities (alpha sweep, figure generation, benchmarking)
- `data/` - demo/example inputs
- `docs/` - figures and methods-facing notes
- `paper/` - manuscript/preprint materials
- `tests/` - test suite

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
pip install -r requirements.txt
```

## Quickstart

### 1. Run the demo combined-load workflow

```bash
python3 src/model/combined_load.py \
  --in data/example/runs_final_example.csv \
  --out output/demo_runs_combined.csv \
  --report output/demo_combined_report.json \
  --alpha 0.5
```

### 2. Run alpha-sweep diagnostics

```bash
python3 scripts/alpha_sweep.py
```

This step generates:
- `output/alpha_sweep_summary.csv`
- per-alpha CSV/report files in `output/alpha_sweep/`

### 3. Generate publication-style figures

```bash
python3 scripts/make_figures.py \
  --runs data/example/runs_final_example.csv \
  --alpha_summary output/alpha_sweep_summary.csv \
  --out docs/figures
```

This step generates figures such as:
- `docs/figures/fig03_internal_vs_external_scatter.png`
- `docs/figures/fig06_alpha_sweep.png`

### 4. Run tests

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

## Outputs

Typical outputs include:

- run-level combined-load CSV tables
- JSON summary reports
- alpha-sweep summary tables
- publication-style figures in `docs/figures/`

Key generated figures include:

- `docs/figures/fig03_internal_vs_external_scatter.png`
- `docs/figures/fig06_alpha_sweep.png`

## Reproducibility note

The repository is designed around a demo-compatible run-level CSV (`data/example/runs_final_example.csv`) so that the core combined-load workflow, alpha-sweep diagnostics, and figure generation can be reproduced without access to raw geolocation or identifiable physiological timestamps.

## Current assumptions and limitations

- The demo workflow operates on a run-level table rather than raw GPS/HR exports.
- Time alignment between Polar HR and GPX logs currently relies on pragmatic timestamp anchoring rather than fully automated drift correction.
- Run segmentation in the full workflow is heuristic and may require adaptation across terrain, snow conditions, and skier profile.
- The repository is intended for research transparency and reproducibility, not as a consumer-facing scoring product.

## Citation

If you use SkiLoadLab in research, please cite the Zenodo archive:

- Concept DOI: https://doi.org/10.5281/zenodo.19108568
- Version DOI (v0.1.2): https://doi.org/10.5281/zenodo.19110471

See also:

- `CITATION.cff`
- `CHANGELOG.md`

## License
MIT License




