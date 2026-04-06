# METHODS

## Overview

SkiLoadLab is an open-source Python toolkit for modeling downhill-skiing training load, centered on a packaged demo-compatible run-level workflow for reproducible combined-load computation, alpha-sweep diagnostics, and figure generation. Public reproducibility begins from an anonymized/demo-compatible run-level table rather than from raw GPS or heart-rate exports.

This document distinguishes between:

- the maintained public analytical workflow
- the broader methodological context represented by retained upstream utilities

The maintained public analytical workflow is the installable package and formal CLI. Retained upstream utilities remain available for method development and extension, but they are not the primary public reproducibility path and are not the core CI-validated workflow.

## Maintained public analytical workflow

The maintained public workflow starts from:

- `data/example/runs_final_example.csv`

In this workflow, the run-level input table already contains the standardized components `z_internal` and `z_mech`. The maintained package CLI reproduces:

- combined-load computation
- alpha-sweep diagnostics
- figure generation

Within this maintained workflow, figure generation consumes the combined run-level table produced by the public CLI, rather than depending on a separate raw-source preprocessing stage.

The formal public entry points are:

- `skiloadlab-combine`
- `skiloadlab-alpha-sweep`
- `skiloadlab-make-figures`

For the step-by-step public protocol, see [`reproducibility.md`](reproducibility.md).

## Broader methodological context and retained upstream utilities

The repository also retains upstream utilities that support broader method development. These include:

- GPX parsing
- DEM sampling
- heuristic run segmentation
- HR-GPX time alignment in raw-source workflows

These utilities provide methodological context for how run-level inputs may be derived in broader research settings, but they are not the maintained public analytical workflow.

## Internal and external components

The public analytical workflow combines two standardized run-level components:

- `z_internal`: standardized internal-load component
- `z_mech`: standardized external/mechanical-load component

Because the maintained public workflow begins from a demo-compatible run-level table, these standardized components are expected to already be present in the input file.

## Combined load model

The combined load index is defined as:

`CL(alpha) = alpha * z_internal + (1 - alpha) * z_mech`

where:

- `z_internal` is the standardized internal-load component
- `z_mech` is the standardized external/mechanical-load component
- `alpha` controls the relative weighting of the internal component

This formulation remains intentionally interpretable:

- `alpha = 0` corresponds to a purely external/mechanical score
- `alpha = 1` corresponds to a purely internal/physiological score
- `0 < alpha < 1` yields a blended score with explicit weighting

## Alpha-sweep criterion

Rather than assuming a single fixed alpha, the maintained workflow evaluates `alpha` over `[0, 1]` to quantify the trade-off between internal and external alignment.

The alpha-sweep summary reports:

- correlation between combined load and the internal component
- correlation between combined load and the external component
- a balance-oriented score

The balance-oriented score is defined as the smaller of the two constituent correlations at a given alpha.

## Outputs of the maintained workflow

Typical outputs of the maintained public analytical workflow include:

- run-level combined-load CSV tables
- JSON summary reports
- alpha-sweep summary CSV tables
- publication-style figures in `docs/figures/`

These outputs support reproducible analysis and reporting for the public workflow.

## Current implementation constraints

- public reproducibility begins from an anonymized/demo-compatible run-level table rather than raw GPS/HR exports
- the maintained test path exercises the formal CLI
- not all upstream utilities are part of the main validated public workflow
- the retained upstream DEM sampling utility currently expects EPSG:4326 inputs
- retained upstream geospatial utilities are useful for research extension, but are not the main public reproducibility path
- time alignment between HR and GPX streams in broader upstream workflows is currently pragmatic rather than fully automated
- run segmentation in broader upstream workflows is heuristic and may require adaptation across terrain and recording contexts

## Validation boundary

Validation in the public release is software-facing: package installation, CLI execution, output generation, and automated tests. This validation boundary applies to the maintained public analytical workflow, not to every retained upstream utility in the repository.
