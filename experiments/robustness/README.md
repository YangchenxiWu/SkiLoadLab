# Robustness Experiment Scaffold

This directory is reserved for carving_v2 robustness experiments. Current scope:

- elevation noise injection
- position jitter
- downsampling
- timestamp offset
- short missing segments

Target outcomes to compare later:

- segmentation stability
- vertical drop estimation
- `CL(alpha)`
- top-k set consistency
- phase-wise contrast

Use `run_robustness.py` with `config_template.json` as the starting point.
