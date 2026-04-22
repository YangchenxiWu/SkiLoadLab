# Carving V2 Sample Summary

This note records the current sample flow and analytical inclusion structure for the
`carving_v2` run-level dataset.

## Sample flow

- Total valid runs: `64`
- Total sessions: `4`
- Date range: `2026-02-03` to `2026-02-06`
- Strict carving runs: `7`
- Carving-like runs: `20`
- Carving-focused analytical set: `27`
  This set is defined as `strict_carving + carving_like`
- Non-carving borderline runs: `19`
- Non-carving runs: `18`
- Total excluded from the carving-focused analytical set: `37`
  This excluded group is defined as `non_carving_borderline + non_carving`

## Final primary-analysis inclusion rule

The final primary analysis includes:

- `strict_carving`
- `carving_like`

The strict high-confidence subset includes:

- `strict_carving` only

The following classes are excluded from the primary carving-focused analytical set:

- `non_carving_borderline`
- `non_carving`

`non_carving_borderline` is not treated as permanently discarded. It may still be retained for:

- supplement-facing reporting
- exploratory comparison
- future threshold refinement or relabeling review

## Paper-ready sample-flow wording

Current manuscript-ready wording:

> A total of 64 valid downhill runs from 4 sessions recorded between 2026-02-03 and 2026-02-06 were available for carving-focused analysis. Runs were classified into a high-confidence strict-carving subset (`n = 7`), a carving-like subset (`n = 20`), a non-carving-borderline subset (`n = 19`), and a non-carving subset (`n = 18`). The primary carving-focused analytical sample therefore comprised 27 runs (`strict_carving + carving_like`), whereas the 7 strict-carving runs were retained as a higher-confidence subset for sensitivity and robustness analyses. Borderline and non-carving runs were excluded from the primary carving-focused set, although borderline runs were retained for supplementary and exploratory comparison.

## Source table

These counts are based on:

- `output/carving_v2_cleaned/runs_carving_final.csv`
