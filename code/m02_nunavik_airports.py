"""Module 2, in-depth stage: which Nunavik airports a "large and medium airports" map keeps.

Jason Davies' World Airports Voronoi draws one cell per large or medium airport with
scheduled service in OurAirports. This lists the Québec airports north of the 55th
parallel (Nunavik) with scheduled service, and how OurAirports classifies each one today.
The data is the OurAirports airports.csv downloaded on 2026-09-29; the classification in
2015, when the map was made, may differ.

Run: uv run --with pandas python code/m02_nunavik_airports.py
"""

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent


def main():
    a = pd.read_csv(HERE / "data" / "ourairports-airports.zip", low_memory=False)
    north = a[
        (a["iso_region"] == "CA-QC")
        & (a["latitude_deg"] > 55)
        & (a["scheduled_service"] == "yes")
    ].sort_values("municipality")
    kept = north["type"].isin(["large_airport", "medium_airport"])
    out = {
        "scheduled_airports": len(north),
        "large_or_medium": int(kept.sum()),
        "kept": sorted(north.loc[kept, "municipality"]),
        "left_out": sorted(north.loc[~kept, "municipality"]),
        "worldwide_large_or_medium_scheduled": int(
            (
                a["type"].isin(["large_airport", "medium_airport"])
                & (a["scheduled_service"] == "yes")
            ).sum()
        ),
    }
    (HERE / "results" / "m02-nunavik-airports.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
