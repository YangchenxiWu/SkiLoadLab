# Methods (outline) — SkiLoadLab

## One-sentence summary
SkiLoadLab implements a reproducible pipeline that fuses Polar heart-rate signals (internal load) with GPX+DEM-derived external load proxies, and derives a combined training-load index via an interpretable alpha-weighted fusion with an alpha sweep that balances internal/external contributions.

---

## 1. Scope and design
- **Purpose:** research-oriented software + method for downhill-skiing training-load modeling (not a consumer product).
- **Operating modes:**
  - **Full mode:** GPX track + DEM elevation sampling + Polar HR stream.
  - **Demo mode:** anonymized run-level summary table (no raw GPS/HR) to reproduce alpha sweep logic and publication-style figures.
- **Primary outputs:**
  - Run-level CSV with internal/external metrics, standardized components, and `combined_load_v2`.
  - Figure set (histograms, scatter, combined-vs-components, alpha sweep).

---

## 2. Inputs and preprocessing

### 2.1 GPX track parsing
- GPX is parsed into a time-stamped position series (lat/lon/time; speed if available/derived).
- The GPX time axis is treated as the reference timeline for downstream alignment.

### 2.2 DEM elevation sampling (Copernicus DEM GeoTIFF)
- Elevation is sampled from a Copernicus DEM GeoTIFF at each GPX location.
- Coordinates are reprojected as needed from geographic coordinates to the DEM CRS.
- A per-point elevation time series is constructed to support descent-related proxies.

### 2.3 Polar HR stream ingestion
- Polar HR is ingested as a time series (often relative time).
- The HR stream is aligned to GPX time (e.g., via start-time anchoring and/or interpolation).
- Basic cleaning is applied (invalid samples removed; missingness tracked).

---

## 3. Run segmentation (downhill runs vs lift/transitions)
- Objective: identify downhill “runs” within a continuous skiing session.
- A rule-based segmentation is applied using features such as:
  - speed profile,
  - elevation change / gradient,
  - stop/transition heuristics.
- Output: run boundaries and `run_id` used for run-level aggregation.

---

## 4. Internal load computation

### 4.1 Edwards TRIMP (zone-weighted)
- Edwards TRIMP is computed as the sum of time spent in HR zones multiplied by zone weights.
- HR zones are defined relative to an athlete-specific reference (e.g., HRmax).

### 4.2 Continuous HR impulse (alternative / fallback)
- A continuous impulse proxy is computed (e.g., integral of HR above rest / HRR-like impulse).
- The pipeline records which internal metric is used for the combined-load fusion:
  - `internal_used_for_combined` ∈ {continuous impulse metric, Edwards TRIMP}.

---

## 5. External load proxies

### 5.1 Vertical drop
- Per-run vertical drop is computed from the elevation series.
- This proxy captures descent magnitude and is a practical external load signal for downhill skiing.

### 5.2 Speed-derived mechanical intensity
- A per-run speed-derived intensity proxy is computed (e.g., mean or percentile speed and/or custom transformation).
- This proxy represents speed-related mechanical demand.

(External metrics are **proxies** and not direct biomechanical ground-truth.)

---

## 6. Standardization (z-scoring)
- Heterogeneous metrics are standardized to comparable scale:
  - `z_internal` = z-score of selected internal load across runs (within a session/table).
  - `z_mech` = z-score of selected external/mechanical proxy across runs (within a session/table).
- Standardization is required before linear fusion.

---

## 7. Combined load index and alpha sweep

### 7.1 Combined-load definition
- The combined index is defined as:
  - `combined_load_v2 = alpha * z_internal + (1 - alpha) * z_mech`
- `alpha ∈ [0, 1]` controls the internal/external contribution:
  - alpha=1: internal-dominant
  - alpha=0: external-dominant

### 7.2 Alpha sweep objective (interpretability-driven balance)
- Alpha is swept on a grid (default step=0.05).
- For each alpha, compute correlations:
  - corr(combined, z_internal)
  - corr(combined, z_mech)
- **Balanced score** (current implementation):
  - `score_balanced = min(|corr(combined, z_internal)|, |corr(combined, z_mech)|)`
- The “best” alpha maximizes `score_balanced`, prioritizing interpretability and balanced coupling to both components.

(This is a heuristic selection rule, not a ground-truth fitted estimator.)

---

## 8. Outputs

### 8.1 Run-level table
Typical columns include:
- `run_id`, `duration_s`, `vertical_drop_m`
- standardized components: `z_internal`, `z_mech`
- internal proxy summary: `z_trimp` (when available)
- combined index: `combined_load_v2`

### 8.2 Reports and figures
- JSON report records alpha, internal metric choice, correlations, and summary statistics.
- Figures include:
  - duration histogram
  - vertical drop histogram
  - internal vs external scatter
  - combined vs components
  - top runs by combined
  - alpha sweep visualization

---

## 9. Reproducibility and testing
- Deterministic scripts and fixed I/O contracts.
- Demo dataset enables figure reproduction without raw GPS/HR sharing.
- Unit tests cover core scripts; GitHub Actions runs CI to validate reproducibility.

---

## 10. Limitations
- Demonstration is compatible with N=1 data; the paper emphasizes **method + software** rather than population-level inference.
- External load proxies are simplified and do not replace force/power measurement.
- Run segmentation uses heuristic rules and may be terrain/device dependent.
- Alpha selection is heuristic and should be interpreted as an **interpretability-driven balance**, not validated optimality.
