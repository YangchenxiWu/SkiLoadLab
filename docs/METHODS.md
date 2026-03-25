# METHODS

## Overview

SkiLoadLab is a reproducible research workflow for modeling downhill-skiing training load by combining internal and external load proxies within an interpretable alpha-weighted fusion framework. The repository is designed for method development, reproducible reporting, and publication-style figure generation rather than consumer-facing scoring.

## Public demo workflow vs full workflow

The repository supports two related workflows:

- **Public demo workflow:** based on the run-level table `data/example/runs_final_example.csv`
- **Full workflow:** based on GPX tracks, Polar heart-rate exports, and DEM-based elevation sampling

The public demo path is intended to reproduce the central modeling logic without exposing raw geolocation traces or identifiable physiological timestamps.

## Data sources

In the full workflow, SkiLoadLab combines three source types:

- **GPX trajectory data** for run structure and movement context
- **Polar HR exports** for physiological/internal load proxies
- **DEM rasters** for terrain-aware elevation sampling

In the public repository, these raw sources are abstracted into a demo-compatible run-level table to support transparent method demonstration and reproducibility.

## GPX parsing and DEM elevation sampling

The full workflow parses GPX tracks into structured movement segments and samples elevation from DEM rasters. This provides terrain-aware descriptors such as vertical drop and related downhill-run context variables.

The public demo workflow does not require raw DEM sampling, but the broader pipeline may rely on geospatial dependencies such as `rasterio` for this part of the workflow.

## Run segmentation

A continuous skiing session is partitioned into run-level units representing downhill runs versus lift/transition phases. In the current repository, run segmentation is heuristic and rule-based. This is sufficient for reproducible method development, but thresholds and logic may require adaptation across terrain, snow conditions, skier profile, and recording conditions.

## HR-GPX time alignment

A practical challenge in the full workflow is alignment between Polar HR data and GPX-derived run structure. The current workflow uses pragmatic timestamp-based anchoring rather than fully automated drift correction. This design keeps the pipeline transparent and reproducible, while leaving room for future refinement using more robust temporal matching strategies.

## Internal load proxies

Internal load is represented using heart-rate-derived physiological information. Conceptually, this aligns with TRIMP-style or HR-impulse interpretations of training response. In the public demo workflow, the internal component is already represented at the run level and standardized before fusion.

## External load proxies

External load is represented using terrain- and movement-derived variables, including vertical drop and related speed/mechanical context. In the public demo workflow, the external/mechanical component is likewise represented at the run level and standardized before fusion.

## Normalization

SkiLoadLab combines internal and external load only after expressing them on comparable standardized scales. The current implementation uses z-score normalization for the internal and external components before alpha-weighted fusion.

## Combined load model

The combined load index is defined as:

`CL(alpha) = alpha * z_internal + (1 - alpha) * z_mech`

where:

- `z_internal` is the standardized internal-load component
- `z_mech` is the standardized external/mechanical-load component
- `alpha` controls the relative weighting of the internal component

This formulation is intentionally interpretable:

- `alpha = 0` corresponds to a purely external/mechanical score
- `alpha = 1` corresponds to a purely internal/physiological score
- `0 < alpha < 1` yields a blended score with explicit weighting

## Alpha sweep criterion

Rather than assuming a single fixed alpha a priori, SkiLoadLab evaluates `alpha` over the interval `[0, 1]`. For each alpha, the workflow quantifies how strongly the resulting combined load aligns with the internal and external components.

The alpha-sweep summary reports:

- correlation between combined load and the internal component
- correlation between combined load and the external component
- a balanced score used to identify an interpretable compromise alpha

The current balanced criterion emphasizes symmetry between internal and external alignment rather than maximizing only one side. In practical terms, the workflow prefers an alpha that maintains strong correspondence with both components instead of overfitting to either the physiological or mechanical signal alone.

## Outputs

Typical outputs include:

- run-level combined-load CSV tables
- JSON summary reports
- alpha-sweep summary CSV tables
- publication-style figures in `docs/figures/`

These outputs support both reproducible analysis and manuscript/preprint preparation.

## Current assumptions and limitations

Several methodological boundaries should be noted:

- the public demo workflow is based on a processed run-level table rather than raw GPS/HR inputs
- run segmentation is heuristic and context-dependent
- HR-GPX alignment is currently pragmatic rather than fully automated
- full-session behavior may depend on upstream preprocessing choices
- the repository prioritizes transparent and reproducible method development over black-box optimization

## Reproducibility

For a step-by-step public demo reproduction recipe, see [`docs/reproducibility.md`](reproducibility.md).
