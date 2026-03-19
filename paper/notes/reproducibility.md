# Reproducibility

## Demo dataset
This repository includes an anonymized **run-level demo table** that contains no raw GPS or heart-rate time series. It is sufficient to reproduce:
- alpha sweep logic
- publication-style figures

Demo CSV:
- `data/example/runs_final_example.csv`

## Quick verification commands (demo mode)

### 1) Compute combined load (demo table)
```bash
python3 src/model/combined_load.py \
  --in data/example/runs_final_example.csv \
  --out /tmp/demo_out.csv \
  --report /tmp/demo_report.json \
  --alpha 0.5
