# Limitations and future work

## Limitations
1. **N=1 / case-study context**
   - The current repository is designed as a method + software contribution. It does not claim population-level generalization or statistical inference.
2. **External load proxies**
   - Vertical drop and speed-derived intensity are practical proxies but are not direct measurements of mechanical work, force, or power.
3. **Heuristic segmentation**
   - Downhill run segmentation is rule-based and may vary across terrain, devices, and recording conditions.
4. **Heuristic alpha selection**
   - Alpha sweep optimizes an interpretability-driven balance criterion, not validated predictive optimality against an external ground truth.

## Future work
- Validate proxies against richer sensing (IMU, GNSS quality, pressure insoles, force platforms where available).
- Extend segmentation with probabilistic or learning-based classifiers with labeled data.
- Evaluate alpha selection against task-specific criteria (e.g., fatigue outcomes, recovery markers, performance measures).
- Add multi-athlete datasets and standardized benchmarking protocols for skiing workload estimation.
