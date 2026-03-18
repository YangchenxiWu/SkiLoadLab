import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def parse_gpx(gpx_file):
    tree = ET.parse(gpx_file)
    root = tree.getroot()

    namespace = {"default": "http://www.topografix.com/GPX/1/1"}

    points = []

    for trkpt in root.findall(".//default:trkpt", namespace):
        lat = float(trkpt.attrib["lat"])
        lon = float(trkpt.attrib["lon"])

        time_elem = trkpt.find("default:time", namespace)
        time = time_elem.text if time_elem is not None else None

        points.append({"time": time, "lat": lat, "lon": lon})

    return pd.DataFrame(points)


def main():

    gpx_path = Path("data/raw/ski_session.gpx")
    output_path = Path("data/processed/track.csv")

    if not gpx_path.exists():
        raise FileNotFoundError(f"GPX file not found: {gpx_path}")

    df = parse_gpx(gpx_path)

    if "time" in df.columns and not df["time"].isnull().all():
        df["time"] = pd.to_datetime(df["time"])
        df = df.drop_duplicates(subset="time")

    df.to_csv(output_path, index=False)

    print("Track points:", len(df))
    print("Saved to:", output_path)


if __name__ == "__main__":
    main()
