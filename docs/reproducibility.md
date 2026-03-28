# Reproducibility Guide

This document describes the tested public demo workflow for reproducing the core SkiLoadLab outputs from the repository.

## Scope

The public reproducibility path is based on the demo-compatible run-level CSV:

- `data/example/runs_final_example.csv`

This workflow is intended to reproduce:

- combined-load computation
- alpha-sweep diagnostics
- publication-style figures
- the basic test suite

It does **not** require access to raw GPS trajectories, raw DEM rasters, or identifiable Polar heart-rate exports.

## Tested environment

The public demo workflow has been tested on:

- macOS (Apple Silicon / arm64)
- Python 3.13
- a virtual environment created with `python3 -m venv .venv`

## Dependencies

For the public demo workflow, dependencies are installed from:

- `requirements.txt`

The demo-compatible reproduction path primarily exercises the run-level modeling and figure-generation stack.

The broader full workflow (e.g., GPX + DEM processing) may additionally rely on geospatial dependencies such as `rasterio`, but raw DEM sampling is not required to reproduce the public demo outputs described in this document.

## Full demo reproduction recipe

### 1. Clone the repository and enter the project directory

```bash
git clone https://github.com/YangchenxiWu/SkiLoadLab.git
cd SkiLoadLab
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Note:** After activation, your shell prompt may show `(.venv)`.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the demo combined-load workflow

```bash
skiloadlab-combine \
  --in data/example/runs_final_example.csv \
  --out output/demo_runs_combined.csv \
  --report output/demo_combined_report.json \
  --alpha 0.5
```

#### Expected outputs
This step should generate:
- `output/demo_runs_combined.csv`
- `output/demo_combined_report.json`

**Terminal verification:**
- successful CSV/report writing
- the internal signal used for fusion
- correlations between combined load and the internal/external components

### 5. Run alpha-sweep diagnostics

```bash
skiloadlab-alpha-sweep
```

#### Expected outputs
This step executes the sweep and generates the following artifacts:
- `output/alpha_sweep_summary.csv`: The master summary table.
- `output/alpha_sweep/`: A directory containing per-alpha CSV and JSON reports.

**Terminal verification:**
You should see progress logs for 21 iterations (from 0.00 to 1.00), concluding with:
- A confirmation of the saved summary CSV.
- A reported best alpha identified by the balanced score (typically near 0.50).

### 6. Generate figures

```bash
skiloadlab-make-figures \
  --runs data/example/runs_final_example.csv \
  --alpha_summary output/alpha_sweep_summary.csv \
  --out docs/figures
```

#### Expected outputs
This step should generate figures in `docs/figures/`, including:
- `fig01_run_duration_hist.png`
- `fig02_vertical_drop_hist.png`
- `fig03_internal_vs_external_scatter.png`
- `fig04_combined_vs_components.png`
- `fig05_top_runs_by_combined.png`
- `fig06_alpha_sweep.png`

### 7. Run tests

```bash
pytest -q
```

#### Expected result
The test command should complete successfully without failing tests.

## Notes on public reproducibility

The public repository is intentionally organized around a demo-compatible run-level table so that the central modeling logic can be reproduced without disclosing:

- raw geolocation traces
- identifiable physiological timestamps
- private source data exports

This design supports transparent method demonstration while maintaining data minimization.

## Known limitations

- The demo workflow uses a processed run-level table rather than raw GPS/HR inputs.
- Time alignment between HR and GPX streams in the full workflow is currently pragmatic rather than fully automated.
- Run segmentation remains heuristic in the full workflow and may require adaptation across contexts.
- Figure outputs are deterministic for the public demo path, but full-session workflows may depend on upstream preprocessing choices.

## Recommended citation

If you use SkiLoadLab in research, cite the Zenodo archive:

- Concept DOI: https://doi.org/10.5281/zenodo.19108568
- Version DOI (v0.1.2): https://doi.org/10.5281/zenodo.19110471

## Cross-platform validation

The public demo workflow has been successfully tested on Windows using a Python virtual environment.

The following steps were verified:
- combined load computation (`combined_load.py`)
- alpha sweep diagnostics (`alpha_sweep.py`)
- figure generation (`make_figures.py`)
- test suite (`pytest -q`)

All steps completed without errors using the example dataset.


