"""Module 2, in-depth stage (conceptual option): Québec City's CLSCs as pizza restaurants.

The class rule gives every lot to the nearest restaurant. Here the restaurants are the CLSC
points of service of the Capitale-Nationale region: installations that hold a CLSC mission
(column CLSC = "Oui" in the health ministry's M02 file) and are named a CLSC or a
multiservice centre. That drops the youth-protection, youth-drop-in and birthing sites that
also carry the mission code; the JSON lists them. Sites outside the city stay in, because
residents cross municipal lines: the Laurentien territory's CLSC is in L'Ancienne-Lorette,
an enclave the city surrounds. The town is the Ville de Québec (the union of its 35
official neighbourhoods), and the lots are the city's buildings. The nearest-site cells (a Voronoi diagram) are compared
with the official CLSC territories the ministry draws.

Two measures:
- agreement: the share of buildings whose nearest site belongs to the building's own
  official CLSC territory;
- distance: per official territory, the median and 90th-percentile straight-line distance
  from a building to its nearest site, in metres.

Run: uv run --with geopandas --with matplotlib python code/m02_quebec_clsc.py
"""

import json
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from shapely.geometry import box
from shapely.ops import voronoi_diagram

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
BUILD = HERE / "build"
MTM7 = "EPSG:32187"  # NAD83 / MTM zone 7, the metric grid used in Québec City


def shapefile(archive, name):
    target = BUILD / archive.removesuffix(".zip")
    with zipfile.ZipFile(DATA / archive) as z:
        z.extractall(target)
    return gpd.read_file(next(target.rglob(name))).to_crs(MTM7)


def load():
    city = gpd.read_file(DATA / "vdq-quartier.geojson").to_crs(MTM7).union_all()
    sites = shapefile("msss-installations.zip", "Installations.shp")
    sites = sites[(sites["CLSC"] == "Oui") & (sites["RSS_CODE"] == "03")]
    public = sites["INSTAL_NOM"].str.contains("CLSC") | sites[
        "INSTAL_NOM"
    ].str.startswith("CENTRE MULTISERVICES")
    excluded = sorted(sites.loc[~public, "INSTAL_NOM"])
    sites = sites[public].reset_index(drop=True)
    territories = shapefile(
        "msss-territoires-clsc-2026.zip", "Territoires_CLSC_2026.shp"
    )
    territories = territories[territories.intersects(city)].copy()
    territories["geometry"] = territories.intersection(city)
    territories = territories[territories.area > 1e5].reset_index(
        drop=True
    )  # > 0.1 km²
    buildings = shapefile("vdq-batiments.zip", "*.shp")
    buildings = gpd.GeoDataFrame(geometry=buildings.representative_point(), crs=MTM7)
    buildings = buildings[
        buildings.within(city)
    ]  # the file also covers the agglomeration
    return city, sites, excluded, territories, buildings


def cells(sites, city):
    """The Voronoi cell of every site, clipped to the city, in the order of `sites`."""
    raw = gpd.GeoSeries(
        list(
            voronoi_diagram(
                sites.union_all(), envelope=sites.union_all().union(city).envelope
            ).geoms
        ),
        crs=MTM7,
    )
    order = [int(np.argmax(raw.contains(p))) for p in sites.geometry]
    return gpd.GeoDataFrame(
        sites[["INSTAL_NOM", "CLSC_NOM"]], geometry=raw.iloc[order].values, crs=MTM7
    ).assign(geometry=lambda d: d.intersection(city))


def measure(sites, territories, buildings):
    b = gpd.sjoin(buildings, territories[["CLSC_nom", "geometry"]], predicate="within")
    b = b.drop(columns="index_right")
    b = gpd.sjoin_nearest(b, sites[["CLSC_NOM", "geometry"]], distance_col="d")
    b = b[~b.index.duplicated()]  # a tie between two sites keeps the first
    agree = float((b["CLSC_nom"] == b["CLSC_NOM"]).mean())
    per = {}
    for name, g in b.groupby("CLSC_nom"):
        per[name] = {
            "buildings": len(g),
            "sites_of_territory": int((sites["CLSC_NOM"] == name).sum()),
            "nearest_site_in_own_territory_pct": round(
                100 * float((g["CLSC_NOM"] == name).mean()), 1
            ),
            "median_m": round(float(g["d"].median())),
            "p90_m": round(float(g["d"].quantile(0.9))),
            "nearest_site_territory": {
                k: int(v) for k, v in g["CLSC_NOM"].value_counts().items()
            },
        }
    return {
        "buildings": len(b),
        "nearest_site_in_own_territory_pct": round(100 * agree, 1),
        "median_m": round(float(b["d"].median())),
        "p90_m": round(float(b["d"].quantile(0.9))),
        "territories": per,
    }


CENTRE = (
    -71.262,
    46.788,
    -71.195,
    46.842,
)  # lon/lat box of the zoom: Haute-Ville, Basse-Ville, Limoilou


def panel(ax, city, sites, vor, territories, colour, bounds, bar_km):
    vor.plot(
        ax=ax,
        color=[colour[n] for n in vor["CLSC_NOM"]],
        alpha=0.55,
        edgecolor="white",
        linewidth=1,
    )
    territories.boundary.plot(ax=ax, color="black", linewidth=1.6)
    gpd.GeoSeries([city], crs=MTM7).boundary.plot(ax=ax, color="grey", linewidth=0.6)
    x0, y0, x1, y1 = bounds
    shown = sites.cx[x0:x1, y0:y1]
    shown.plot(ax=ax, color="black", markersize=14, zorder=3)
    for i, p in shown.geometry.items():
        ax.annotate(
            str(i + 1),
            (p.x, p.y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=9,
        )
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    step = (x1 - x0) / 25
    ax.plot(
        [x0 + step, x0 + step + bar_km * 1000],
        [y0 + step, y0 + step],
        color="black",
        linewidth=3,
    )
    ax.text(x0 + step, y0 + 1.6 * step, f"{bar_km} km", fontsize=9)
    ax.set_axis_off()


def draw(city, sites, vor, territories, path):
    names = sorted(territories["CLSC_nom"])
    colour = dict(zip(names, plt.get_cmap("tab10").colors))
    zoom = gpd.GeoSeries(box(*CENTRE), crs="EPSG:4326").to_crs(MTM7).total_bounds
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(15, 7.5), dpi=150, width_ratios=[1.25, 1]
    )
    panel(left, city, sites, vor, territories, colour, city.bounds, 5)
    panel(right, city, sites, vor, territories, colour, zoom, 1)
    x0, y0, x1, y1 = zoom
    left.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color="red", linewidth=1.2)
    handles = [Patch(color=colour[n], alpha=0.55, label=n) for n in names]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=9, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path)


def main():
    city, sites, excluded, territories, buildings = load()
    vor = cells(sites, city)
    reach = ~vor.is_empty & (vor.area > 0)
    sites, vor = sites[reach].reset_index(drop=True), vor[reach].reset_index(drop=True)
    out = {
        "sites": [
            {
                "n": i,
                "name": r.INSTAL_NOM,
                "address": r.ADRESSE,
                "municipality": r.MUN_NOM,
                "clsc": r.CLSC_NOM,
            }
            for i, r in enumerate(sites.itertuples(), start=1)
        ],
        "excluded_same_mission_code": excluded,
        "official_territories": sorted(territories["CLSC_nom"]),
        **measure(sites, territories, buildings),
    }
    draw(city, sites, vor, territories, HERE / "figures" / "m02-quebec-clsc.png")
    (HERE / "results" / "m02-quebec-clsc.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
