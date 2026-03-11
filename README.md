# SkiLoadLab — Training Load Modeling for Downhill Skiing (Polar + GPX + DEM)

A reproducible mini research pipeline that:
1) parses GPX track,
2) samples elevation from Copernicus DEM GeoTIFF,
3) segments downhill ski runs,
4) fuses Polar HR (relative time) with GPX time,
5) computes internal load (Edwards TRIMP + continuous HR impulse),
6) computes external load proxies (vertical drop, speed-based),
7) produces a combined load index with alpha sweep for balancing internal/external contributions,
8) generates publication-style figures.

## Project structure
- `src/` core pipeline code
- `scripts/` utility scripts (figures, alpha sweep, etc.)
- `data/example/` small anonymized example CSVs for demo
- `output/figures/` figures generated locally (ignored by git)

## Quickstart (demo with example data)
```bash
# 1) generate figures from example runs file (no raw GPS/HR needed)
python3 scripts/make_figures.py --runs data/example/runs_final_example.csv --pdf

