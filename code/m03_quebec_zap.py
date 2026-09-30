"""Module 3, in-depth stage (conceptual option): where Québec City put its free Wi-Fi.

The ZAP hotspots are the city's own antennas. This counts them by borough (the file's
ARRONDISSEMENT field) and by neighbourhood (spatial join with the 35 quartiers), and
measures, for each type of building in the city's footprint file, the share within 50 m
and 100 m of a hotspot. The 50 m and 100 m discs are assumed ranges, not a radio model.

Run: uv run --with geopandas python code/m03_quebec_zap.py
"""

import json
import zipfile
from pathlib import Path

import geopandas as gpd

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
MTM7 = "EPSG:32187"
RADII = (50, 100)


def main():
    zap = gpd.read_file(DATA / "vdq-zap.geojson").to_crs(MTM7)
    quarters = gpd.read_file(DATA / "vdq-quartier.geojson").to_crs(MTM7)
    target = HERE / "build" / "vdq-batiments"
    with zipfile.ZipFile(DATA / "vdq-batiments.zip") as z:
        z.extractall(target)
    b = gpd.read_file(next(target.rglob("*.shp"))).to_crs(MTM7)
    b = b.set_geometry(b.representative_point())
    b = b[b.within(quarters.union_all())]
    per_q = gpd.sjoin(zap, quarters[["NOM", "geometry"]], predicate="within")
    counts_q = per_q["NOM"].value_counts()
    bq = gpd.sjoin(b, quarters[["NOM", "geometry"]], predicate="within")["NOM"]
    near = {}
    for r in RADII:
        zone = zap.buffer(r).union_all()
        inside = b.within(zone)
        near[r] = {
            t: round(100 * float(inside[b["TYPE_BATIM"] == t].mean()), 2)
            for t in sorted(b["TYPE_BATIM"].dropna().unique())
        }
        near[r]["all"] = round(100 * float(inside.mean()), 2)
    out = {
        "hotspots": len(zap),
        "by_borough": {
            k: int(v) for k, v in zap["ARRONDISSEMENT"].value_counts().items()
        },
        "by_quartier": {
            q: {"hotspots": int(counts_q.get(q, 0)), "buildings": int(n)}
            for q, n in bq.value_counts().items()
        },
        "top3_quartier_share_pct": round(100 * counts_q.head(3).sum() / len(zap), 1),
        "buildings_by_type": {
            k: int(v) for k, v in b["TYPE_BATIM"].value_counts().items()
        },
        "share_within_m_pct": {str(r): v for r, v in near.items()},
    }
    (HERE / "results" / "m03-quebec-zap.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
