# SkiLoadLab: Reproducible training-load modeling for downhill skiing (Polar HR + GPX + DEM)

## Summary
SkiLoadLab is a research-oriented, reproducible pipeline for modeling downhill-skiing training load by fusing internal (heart-rate-based) and external (terrain- and speed-derived) proxies. The toolkit supports GPX parsing, DEM elevation sampling, downhill-run segmentation, and generation of publication-ready figures (PNG/PDF) from either a full sensor workflow or an anonymized demo table. SkiLoadLab targets transparent method development and reproducible reporting in outdoor sports contexts where consumer platforms often hide data-processing steps. The repository includes tests (pytest) and continuous integration (GitHub Actions) to reduce regressions and improve reviewer confidence.

## Statement of need
Quantifying training load in outdoor/downhill skiing is challenging because internal load (physiological response) and external load (terrain exposure and mechanical demands) are captured by heterogeneous devices with different clocks, sampling rates, and data formats. Unlike controlled laboratory tasks, skiing sessions are affected by lift transitions, GNSS uncertainty, and terrain-driven intensity fluctuations, which complicate reproducible processing. Meanwhile, consumer tools often provide opaque “scores” without transparent assumptions or traceable intermediate variables, limiting methodological comparison and research reuse.

SkiLoadLab fills this gap by providing a scriptable, testable research pipeline with explicit inputs/outputs and reproducible figure generation. It is designed for method development, sensitivity analysis, and research reporting where traceability and repeatability are priorities.

## Functionality

### Inputs
**Demo mode (no raw GPS/HR required):**
- A run-level table containing standardized signals `z_internal` and `z_mech` plus minimal metadata (e.g., run duration and vertical drop).
- The repository ships an anonymized demo table derived from a professional fencer’s cross-training skiing session, enabling a realistic worked example without exposing raw device exports.

**Full mode (end-to-end):**
- GPX track (GNSS trajectory and timestamps)
- DEM GeoTIFF (for elevation sampling)
- Polar heart-rate export (often relative time)

### Pipeline
1. **GPX parsing:** read track points and timestamps.
2. **DEM elevation sampling:** sample elevation values from a GeoTIFF DEM at track coordinates.  
   *Implementation note:* Elevation sampling is implemented via rasterio (v1.5.0) on Copernicus DEM GeoTIFF tiles.
3. **Run segmentation (heuristic):** partition a continuous session into downhill runs vs. lift/transitions using explicit heuristics.  
   *Boundary/assumption:* Run segmentation is executed via a slope-threshold heuristic. By default, downhill runs are identified by a minimum elevation drop of 20 meters and a minimum duration of 30 seconds. These parameters are exposed as user-configurable settings (e.g., command-line arguments) to adapt to varying terrain and skill levels.
4. **HR ↔ GPX time alignment:** align Polar HR timeline to GPX timeline, handling practical timebase differences and small drift.  
   *Boundary/assumption:* Time alignment between the relative-time Polar HR stream and absolute-time GPX logs assumes a synchronized start or a constant temporal offset. While linear drift is currently minimized via timestamp anchoring, future iterations will implement cross-correlation of heart-rate kinetics and mechanical intensity for automated drift correction.
5. **Internal load estimation:** compute heart-rate-based metrics (Edwards TRIMP and/or continuous HR impulse variants).
6. **External load proxies:** compute practical proxies such as vertical drop and speed-derived mechanical intensity.
7. **Combined load index (interpretable fusion):**
   \[
   CL(\alpha)=\alpha \cdot z_{\mathrm{internal}} + (1-\alpha)\cdot z_{\mathrm{mech}}
   \]
8. **Alpha sweep (sensitivity framework):** sweep \(\alpha \in [0,1]\) and report diagnostic correlations, allowing researchers to explore sensitivity between physiological response and mechanical exposure rather than “choosing a single best value”.  
   *Interpretation:* The alpha-sweep utility (α∈[0,1]) provides a sensitivity-analysis framework rather than a fixed optimization. It enables researchers to quantify coupling strength between internal physiological strain and external mechanical work, facilitating an interpretability-driven selection of the fusion weight α.
9. **Figure generation:** generate publication-ready figures (PNG/PDF) for method reporting and sensitivity checks.

### Outputs
- **CSV tables:** run-level metrics, standardized components, and combined load.
- **JSON reports:** parameter values, summary diagnostics, and reproducibility metadata.
- **Figures (PNG/PDF):** distributions, component relationships, and alpha-sweep behavior.

## Quality control
- **Unit/integration tests:** `pytest` covers core scripts and I/O contracts.
- **Continuous integration (CI):** GitHub Actions runs the test suite on each push.

## Impact
SkiLoadLab reduces friction in research-grade training-load modeling by replacing manual, error-prone spreadsheet processing with a single command-line workflow that deterministically reproduces derived variables and figures. On an Apple Silicon macOS system (arm64) with Python 3.13.1, the demo pipeline (combined-load computation + figure generation) demonstrated a median wall-clock execution time of **1.2768 s (n=3)** using the repository’s reproducible benchmark script.

## Availability
- Source code (GitHub): https://github.com/YangchenxiWu/SkiLoadLab
- License: MIT
- Archived on Zenodo:
  - **Concept DOI (all versions):** https://doi.org/10.5281/zenodo.19108568
  - **Version DOI (v0.1.2):** https://doi.org/10.5281/zenodo.19110471

**Data privacy note (GDPR):** To adhere to data-privacy standards, the repository provides an anonymized run-level demo table. Raw trajectories containing precise geo-locations and identifiable physiological timestamps are intentionally excluded from the public release.

## Future work
Future versions will explore incorporating subjective effort signals (e.g., RPE) for tuning \(\alpha\) under uncertainty, potentially using Bayesian optimization. Additional planned directions include more robust drift modeling for time alignment and improved configurability/validation for run segmentation heuristics.

## References
Impellizzeri, F. M., Marcora, S. M., & Coutts, A. J. (2019). Internal and external training load: 15 years on. *International Journal of Sports Physiology and Performance*, 14(2), 270–273. https://doi.org/10.1123/ijspp.2018-0935

Halperin, I., Vigotsky, A. D., Foster, C., & Pyne, D. B. (2018). Strengthening the practice of exercise and sport-science research. *International Journal of Sports Physiology and Performance*, 13(3), 384–388. https://doi.org/10.1123/ijspp.2017-0322

Gilgien, M., Spörri, J., Chardonnens, J., Kröll, J., & Müller, E. (2013). Determination of external load in alpine skiing using GNSS. *European Journal of Sport Science*, 13(6), 582–592. https://doi.org/10.1080/17461391.2013.765934

Supej, M., & Holmberg, H.-C. (2019). Recent approaches to GNSS measurements in alpine skiing: Accuracy requirements and challenges for research and applied science. *Frontiers in Physiology*, 10, 1188. https://doi.org/10.3389/fphys.2019.01188

Harris, C. R., Millman, K. J., van der Walt, S. J., et al. (2020). Array programming with NumPy. *Nature*, 585, 357–362. https://doi.org/10.1038/s41586-020-2649-2

McKinney, W. (2010). Data structures for statistical computing in Python. In *Proceedings of the 9th Python in Science Conference (SciPy 2010)* (pp. 56–61). https://doi.org/10.25080/Majora-92bf1922-00a

Rasterio Developers. (2026). *rasterio: Fast and direct raster I/O for use with NumPy* (Version 1.5.0) [Computer software]. https://rasterio.readthedocs.io/

Edwards, S. (1993). *The Heart Rate Monitor Book*. Polar Electro Oy.
