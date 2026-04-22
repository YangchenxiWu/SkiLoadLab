# Carving Operationalization

This note converts the current project-side carving rules into manuscript-ready methods language.

## Theoretical definition

In this workflow, a carving-focused descent is conceptualized as a downhill run whose trajectory is
predominantly governed by continuous, smooth, and repeated arc-shaped turns, with limited evidence
of prolonged traverse, marked stop-and-go behavior, or disorganized direction changes. The working
 concept is therefore not restricted to idealized textbook carving alone; rather, it targets runs
 whose overall movement structure remains more consistent with carving-focused skiing than with
 mixed, traversing, braking-dominant, or otherwise non-carving descent patterns.

## Operational definition

Operationally, carving classification was performed at the run level after GPX-based segmentation
 and heart-rate alignment had already been completed. Each valid run was first retained within the
 all-valid-run pool, and then assigned to one of four final classes:

- `strict_carving`
- `carving_like`
- `non_carving_borderline`
- `non_carving`

The `strict_carving` class represents a high-specificity subset of runs with clearly dominant,
 continuous, and repeated arc-shaped turn structure and minimal evidence of prolonged traverse,
 abrupt stopping, or disorganized redirection. The `carving_like` class represents runs that still
 appear predominantly arc-turn-dominant and downhill-continuous, but may contain limited local
 imperfection such as mild skidding, partial mixing, or isolated non-ideal segments. The
 `non_carving` class represents runs with clearly weak turn structure, substantial traverse,
 stop-dominant behavior, incomplete downhill continuity, or movement patterns inconsistent with a
 carving-focused descent. The `non_carving_borderline` class captures runs that do not meet the
 carving-focused analytical threshold, but are not treated as definitively unusable for all future
 secondary analyses.

## Labeling and review procedure

The labeling procedure followed a staged operational workflow.

First, a candidate screening step retained complete, valid, downhill-type runs from the run-level
 table. Second, each run was evaluated using trajectory-informed derived features extracted from the
 segmented GPX trace. The most important second-pass fields were:

- `median_turn_amp_deg`
- `large_turn_block_frac`
- `turn_switches`
- `turns_per_min`
- `mean_abs_heading_delta_deg`
- `drop_per_hdist`

These features were used as operational proxies for whether the run was dominated by repeated
 arc-shaped turning, whether turning structure occupied a large fraction of the descent, whether the
 skier maintained continuous direction alternation, and whether the overall path remained consistent
 with a carving-focused downhill pattern rather than with prolonged traverse or technically mixed
 descent behavior.

The initial high-specificity pass identified a small subset of runs that were clearly closest to a
 pure carving pattern. Rather than treating those runs as the only carving class, that subset was
 preserved as `strict_carving`. Runs initially deemed uncertain were then subjected to a second-pass
 redistribution step. In that second pass, uncertain runs were promoted to `carving_like` when they
 satisfied at least 4 of 6 predefined threshold conditions across the six key trajectory features
 listed above; otherwise they were assigned to `non_carving_borderline`. Runs already classified as
 clearly non-carving remained in `non_carving`.

## Primary analysis set

The primary carving-focused analytical set includes:

- `strict_carving`
- `carving_like`

Thus, the primary analytical sample is intentionally broader than the strict high-specificity
 subset, because it is designed to capture runs that are operationally suitable for carving-focused
 engineering analysis rather than only runs that approximate near-pure carving behavior.

## Strict-subset sensitivity analysis

The `strict_carving` subset is retained as a higher-confidence sensitivity and robustness subset.
This allows the main analyses to be repeated on a narrower but more specific sample in order to
 evaluate whether the main carving-focused findings remain directionally stable when the analytical
 set is restricted to the most confident carving runs.

## Current dataset instantiation

In the current dataset snapshot, the final run-level carving classes are:

- `strict_carving`: `7`
- `carving_like`: `20`
- `non_carving_borderline`: `19`
- `non_carving`: `18`

Accordingly, the primary carving-focused analytical set contains `27` runs, and the strict
 high-confidence subset contains `7` runs.
