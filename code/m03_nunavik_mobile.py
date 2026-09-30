"""Module 3, in-depth stage (conceptual option): mobile coverage in Nunavik, people against land.

Two official measures of the same network:
- people: the CRTC's availability table (Table 9, by census subdivision and year) gives the
  population with any mobile service ("AllMobile") and with LTE. The share is summed over
  the 14 northern villages, Québec and Canada, for 2025, the latest year;
- land: the Atlas of Canada "Wireless Data Network" layers (NRCan, LTE and 5G, 2024) are
  intersected with Nunavik's health region (region 17 of the MSSS CLSC territories, the
  same file as session 2) and with the whole province. Areas are in an equal-area
  projection. The atlas has no 3G layer, so the land share counts LTE only.

Run: uv run --with geopandas --with pandas python code/m03_nunavik_mobile.py
"""

import json
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import make_valid

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
BUILD = HERE / "build"
YEAR = 2025
VILLAGES = [
    "Akulivik",
    "Aupaluk",
    "Inukjuak",
    "Ivujivik",
    "Kangiqsualujjuaq",
    "Kangiqsujuaq",
    "Kangirsuk",
    "Kuujjuaq",
    "Kuujjuarapik",
    "Puvirnituq",
    "Quaqtaq",
    "Salluit",
    "Tasiujaq",
    "Umiujaq",
]
# Canada Albers equal-area conic, so that areas in m² are true areas
ALBERS = "+proj=aea +lat_0=40 +lon_0=-96 +lat_1=50 +lat_2=70 +datum=NAD83 +units=m"


def people():
    with zipfile.ZipFile(DATA / "crtc-mobile-broadband-availability.zip") as z:
        t = pd.read_csv(z.open("C-T9.csv"), skiprows=5, encoding="latin-1")
    t.columns = [
        "prov_id",
        "prov",
        "csd",
        "name",
        "centre",
        "reserve",
        "speed",
        "year",
        *t.columns[8:13],
        "pop",
        *t.columns[14:],
    ]
    t = t[t["year"] == YEAR]

    def share(rows):
        pop = rows.groupby("speed")["pop"].sum()
        return {
            s: round(100 * float(pop.get(s, 0) / pop["AllDemographics"]), 2)
            for s in ("AllMobile", "LTE")
        } | {"population": round(float(pop["AllDemographics"]))}

    qc = t[t["prov"] == "QC"]
    nunavik = qc[qc["name"].isin(VILLAGES)]
    found = sorted(nunavik.loc[nunavik["pop"] > 0, "name"].unique())
    if found != VILLAGES:
        raise AssertionError(f"villages found in Table 9: {found}")
    return {
        "Canada": share(t),
        "Québec": share(qc),
        "Nunavik, 14 northern villages": share(nunavik),
        "by_village": {v: share(nunavik[nunavik["name"] == v]) for v in VILLAGES},
    }


def land():
    target = BUILD / "msss-territoires-clsc-2026"
    with zipfile.ZipFile(DATA / "msss-territoires-clsc-2026.zip") as z:
        z.extractall(target)
    clsc = gpd.read_file(next(target.rglob("Territoires_CLSC_2026.shp"))).to_crs(ALBERS)
    areas = {
        "Québec": make_valid(clsc.union_all()),
        "Nunavik (health region 17)": make_valid(
            clsc[clsc["RSS_code"] == "17"].union_all()
        ),
    }
    target = BUILD / "nrcan-wireless"
    with zipfile.ZipFile(DATA / "nrcan-wireless-data-network.gdb.zip") as z:
        z.extractall(target)
    gdb = next(target.rglob("*.gdb"))
    out = {}
    for name, geom in areas.items():
        out[name] = {"area_km2": round(geom.area / 1e6)}
        for layer, tag in (("LTE_2024", "LTE"), ("_5G_2024", "5G")):
            cover = make_valid(
                gpd.read_file(gdb, layer=layer).to_crs(ALBERS).union_all()
            )
            out[name][f"{tag}_share_pct"] = round(
                100 * cover.intersection(geom).area / geom.area, 2
            )
    return out


def main():
    out = {"year_people": YEAR, "people": people(), "land_2024": land()}
    (HERE / "results" / "m03-nunavik-mobile.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
