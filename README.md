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
