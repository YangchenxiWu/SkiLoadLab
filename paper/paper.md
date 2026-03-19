# SkiLoadLab: Reproducible training-load modeling for downhill skiing (Polar HR + GPX + DEM)

## Summary
SkiLoadLab is a research-oriented, reproducible pipeline for modeling downhill-skiing training load by fusing internal (heart-rate–based) and external (terrain- and speed-derived) proxies. The toolkit supports GPX parsing, DEM elevation sampling, downhill run segmentation, and Polar HR ↔ GPX time alignment, producing run-level tables, JSON reports, and publication-ready figures (PNG/PDF). A transparent combined-load index is computed as an alpha-weighted fusion of standardized internal/external signals, and an alpha-sweep utility supports interpretability-driven selection of internal/external balance. The repository includes an anonymized demo table that reproduces the figure set and alpha-sweep logic without distributing raw GPS/HR time series.

## Statement of need
Quantifying training load in outdoor/downhill skiing is challenging because internal load (physiological response) and external load (terrain exposure and mechanical demands) are captured by heterogeneous devices with different clocks, sampling rates, and data models. In practice, researchers and coaches frequently rely on ad-hoc spreadsheet workflows or opaque consumer dashboards, which limits transparency and reproducibility: preprocessing choices (e.g., time alignment, segmentation rules, and normalization) are rarely documented and difficult to audit.

SkiLoadLab addresses this gap by providing a scriptable, testable research pipeline with explicit inputs/outputs and reproducible figure generation. It is intended for method development and research reporting where traceability and repeatability are prioritized over consumer-product features. The demo mode enables sharing and peer verification of the modeling logic without exposing identifiable raw trajectory or HR streams.

## Functionality

### Inputs
**Demo mode (no raw GPS/HR required):**
- Run-level table containing standardized signals `z_internal` and `z_mech` plus minimal metadata (e.g., duration and vertical drop).
- The repository ships an anonymized example dataset derived from a cross-training skiing session of a professional fencer, enabling a realistic worked example without exposing raw device exports.

**Full mode (end-to-end):**
- GPX track (GPS trajectory and timestamps)
- DEM (GeoTIFF) for elevation sampling
- Polar heart-rate export (often relative time)

### Pipeline
1. **GPX parsing**: read track points and timestamps.
2. **DEM elevation sampling**: sample elevation values from a GeoTIFF DEM at track coordinates.
3. **Run segmentation**: partition a continuous session into downhill runs vs lift/transitions using explicit heuristics.
4. **HR ↔ GPX time alignment**: align Polar HR (relative-time stream) to the GPX timeline, handling practical timebase differences and small drift.
5. **Internal load estimation**: compute heart-rate–based metrics (e.g., Edwards TRIMP and/or continuous HR impulse variants).
6. **External load proxies**: compute practical proxies such as vertical drop and speed-derived mechanical intensity.
7. **Combined load index**: compute an interpretable fusion of standardized components:
   \[
   CL(\alpha)=\alpha\cdot z_{internal} + (1-\alpha)\cdot z_{mech}
   \]
8. **Alpha sweep**: sweep \(\alpha \in [0,1]\) and select values that balance coupling to internal/external components, reporting diagnostic correlations.
9. **Figure generation**: generate publication-ready figures (PNG/PDF) for method reporting and sensitivity checks.

### Outputs
- **CSV tables** (run-level): metrics, standardized components, and combined load.
- **JSON reports**: parameter values, summary diagnostics, and reproducibility metadata.
- **Figures (PNG/PDF)**: distributions, component relationships, and alpha-sweep behavior.

## Quality control
- **Unit/integration tests** via `pytest` cover core scripts and I/O contracts.
- **Continuous integration (CI)** via GitHub Actions runs the test suite on each push, reducing regressions and improving reviewer confidence.

## Impact
SkiLoadLab reduces friction in research-grade training-load modeling by replacing manual, error-prone spreadsheet processing with a single command-line workflow that deterministically reproduces derived variables and figures. On an Apple Silicon laptop (macOS; Python 3.x), the demo end-to-end pipeline (combined-load computation plus figure generation) completed in a **median of 1.2768 s** over **3 repeats** (see `paper/bench/benchmark_demo.md`). Runtime will vary with hardware, file I/O, and full-mode inputs (e.g., DEM sampling on long GPX tracks), but the benchmark demonstrates that the core demo workflow is effectively instantaneous for iterative method development.

## Availability
- Source code (GitHub): https://github.com/YangchenxiWu/SkiLoadLab  
- License: MIT  
- Archived on Zenodo:  
  - Concept DOI (all versions): https://doi.org/10.5281/zenodo.19108568  
  - Version DOI (v0.1.2): https://doi.org/10.5281/zenodo.19110471  

## Future work
Future versions will explore incorporating subjective effort signals (e.g., RPE) for tuning \(\alpha\) under uncertainty, potentially using Bayesian optimization. Additional planned directions include more robust drift modeling for time alignment, configurable segmentation strategies for diverse skiing conditions, and multi-athlete benchmarking datasets.

## References
(Keep short; add 3–8 references total.)
- Edwards TRIMP / internal load background
- Conceptual papers on internal vs external load
- If you cite a specific DEM dataset/source, include its citation
