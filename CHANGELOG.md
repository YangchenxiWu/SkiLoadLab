# Changelog

## v0.1.2-post
### Fixed
- Fixed `scripts/alpha_sweep.py` default input path.
- Alpha-sweep diagnostics now run successfully with the demo dataset.
- Regenerated `docs/figures/fig06_alpha_sweep.png` after resolving failed per-alpha runs and NaN summary outputs.

### Added
- Windows smoke test validation for the public demo workflow
  - combined load computation
  - alpha sweep diagnostics
  - figure generation
  - test suite (pytest)
