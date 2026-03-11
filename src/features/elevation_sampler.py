#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


NODATA_SENTINELS = {-32768.0, -9999.0, -3.4028235e38}


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_track_csv(track_csv: Path) -> pd.DataFrame:
    if not track_csv.exists():
        raise FileNotFoundError(f"Track CSV not found: {track_csv.resolve()}")

    df = pd.read_csv(track_csv)

    # Basic schema check
    required = {"lat", "lon"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Track CSV missing columns: {sorted(missing)}. Found: {list(df.columns)}")

    # Optional time
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")

    # Force numeric
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    after = len(df)

    if after == 0:
        raise ValueError("No valid lat/lon rows after cleaning.")
    if after != before:
        print(f"[WARN] Dropped {before - after} rows with invalid lat/lon.")

    # Sanity bounds for lat/lon (helps catch swapped columns)
    if (df["lat"].abs().max() > 90) or (df["lon"].abs().max() > 180):
        raise ValueError(
            "Lat/Lon values look invalid. "
            "Check if columns are swapped or the file is not WGS84 lat/lon."
        )

    return df


def _print_bounds_warning(df: pd.DataFrame, src) -> None:
    bounds = src.bounds  # left, bottom, right, top
    lon_min, lon_max = float(df["lon"].min()), float(df["lon"].max())
    lat_min, lat_max = float(df["lat"].min()), float(df["lat"].max())

    outside = (
        (lon_max < bounds.left)
        or (lon_min > bounds.right)
        or (lat_max < bounds.bottom)
        or (lat_min > bounds.top)
    )
    if outside:
        print("[WARN] Track bbox appears outside DEM bounds (expect many NaNs).")
        print(f"       Track lon[{lon_min:.6f},{lon_max:.6f}] lat[{lat_min:.6f},{lat_max:.6f}]")
        print(
            f"       DEM   lon[{bounds.left:.6f},{bounds.right:.6f}] "
            f"lat[{bounds.bottom:.6f},{bounds.top:.6f}]"
        )


def sample_elevation_from_dem(df: pd.DataFrame, dem_tif: Path, band: int = 1) -> pd.DataFrame:
    if not dem_tif.exists():
        raise FileNotFoundError(f"DEM file not found: {dem_tif.resolve()}")

    with rasterio.open(dem_tif) as src:
        if src.crs is None:
            raise ValueError("DEM has no CRS. Cannot interpret coordinates safely.")
        epsg = src.crs.to_epsg()
        if epsg != 4326:
            raise ValueError(
                f"DEM CRS is {src.crs} (EPSG:{epsg}). This script expects EPSG:4326 (lon/lat). "
                "If you really need non-4326 DEMs, we can add reprojection."
            )

        _print_bounds_warning(df, src)

        nodata = src.nodata

        # rasterio.sample expects (x, y) = (lon, lat) for EPSG:4326
        coords = zip(df["lon"].to_numpy(), df["lat"].to_numpy())
        samples = src.sample(coords, indexes=band)

        elev = np.fromiter(
            (s[0] if (s is not None and len(s)) else np.nan for s in samples),
            dtype="float64",
            count=len(df),
        )

    # Handle nodata from metadata
    if nodata is not None:
        elev = np.where(elev == nodata, np.nan, elev)

    # Handle common sentinel nodata values
    for v in NODATA_SENTINELS:
        elev = np.where(elev == v, np.nan, elev)

    # Guard unrealistic elevations (helps catch corrupted / wrong sampling)
    elev = np.where((elev < -500) | (elev > 9000), np.nan, elev)

    out = df.copy()
    out["elev_m"] = elev

    nan_count = int(np.isnan(out["elev_m"]).sum())
    print(f"[OK] Sampled elevation for {len(out)} points. NaN elevations: {nan_count}")

    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample elevation (meters) from a DEM GeoTIFF for GPX track points (lat/lon)."
    )
    parser.add_argument(
        "--track",
        type=str,
        default="data/processed/track.csv",
        help="Input CSV with columns: lat, lon (optional: time)",
    )
    parser.add_argument(
        "--dem",
        type=str,
        default="data/external/dem/dem.tif",
        help="DEM GeoTIFF path (expects EPSG:4326).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="data/processed/track_elevation.csv",
        help="Output CSV path.",
    )
    args = parser.parse_args()

    track_csv = Path(args.track)
    dem_tif = Path(args.dem)
    out_csv = Path(args.out)

    df = load_track_csv(track_csv)
    out = sample_elevation_from_dem(df, dem_tif, band=1)

    ensure_parent_dir(out_csv)
    out.to_csv(out_csv, index=False)

    valid = out["elev_m"].dropna()
    if len(valid) > 0:
        print(
            "[SUMMARY] elev_m: "
            f"min={valid.min():.1f}, mean={valid.mean():.1f}, max={valid.max():.1f}"
        )
    else:
        print("[SUMMARY] elev_m: no valid elevations (all NaN). Check DEM coverage/CRS.")

    print(f"[OK] Saved: {out_csv.resolve()}")


if __name__ == "__main__":
    main()
