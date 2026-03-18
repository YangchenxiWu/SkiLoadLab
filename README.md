# SkiLoadLab — Training Load Modeling for Downhill Skiing (Polar HR + GPX + DEM)

![CI](https://github.com/YangchenxiWu/SkiLoadLab/actions/workflows/ci.yml/badge.svg)

A reproducible mini research pipeline that:
1) parses GPX track  
2) samples elevation from Copernicus DEM GeoTIFF  
3) segments downhill ski runs  
4) fuses Polar HR (relative time) with GPX time  
5) computes internal load (Edwards TRIMP + continuous HR impulse)  
6) computes external load proxies (vertical drop, speed-based)  
7) produces a combined load index with **alpha sweep** to balance internal/external contributions  
8) generates publication-style figures

---

## Project structure

- `src/` core pipeline code  
- `scripts/` utility scripts (alpha sweep, figures, etc.)  
- `data/example/` small anonymized example CSVs for demo  
- `output/` local outputs (ignored by git)  
- `docs/figures/` key figures committed for quick preview

---

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional (tests)
