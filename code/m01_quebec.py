"""Module 1, in-depth stage (conceptual option): Québec City's built form across scales.

Three equal square windows (512 m a side), one per construction era. Limoilou and Sainte-Foy
are centred on the median building of an official neighbourhood (Ville de Québec, "Quartiers":
Vieux-Limoilou, Plateau). Haute-Ville is centred inside the walls instead: its official
neighbourhood also holds Cap-Blanc and the parliament hill, so its median building falls
outside the walled city. The centre sits east of the three western gates, which Nominatim
places at longitude -71.2113 to -71.2131 (Porte Saint-Louis, Porte Kent, Porte Saint-Jean).

Two measures per window, on the city's building footprints ("Empreintes des bâtiments"):
- box counting, the method of session 1: the share of boxes of side s that touch a building,
  for s from 4 m to 128 m; the slope of log N(s) against log(1/s) is the dimension D;
- step-by-step dilation, the method Tannier and Pumain use for Basle: every building grows
  by d metres and the clusters that merge are counted, for d from 0 to 64 m.

Run: uv run --with geopandas --with pillow --with numpy python code/m01_quebec.py
"""

import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, box

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
SIDE = 512  # metres
PIXEL = 1  # metre per pixel when rasterizing
SIZES = [4, 8, 16, 32, 64, 128]  # box sides in metres
DILATIONS = [0, 2, 4, 8, 16, 32, 64]  # metres
MTM7 = "EPSG:32187"  # NAD83 / MTM zone 7, the metric grid used in Québec City
HAUTE_VILLE_CENTRE = (-71.2075, 46.8123)  # lon, lat: inside the walls
AREAS = {
    "Haute-Ville": HAUTE_VILLE_CENTRE,
    "Limoilou": "Vieux-Limoilou",
    "Sainte-Foy": sys.argv[1] if len(sys.argv) > 1 else "Plateau",
}


def load():
    with zipfile.ZipFile(DATA / "vdq-batiments.zip") as z:
        z.extractall(HERE / "build" / "vdq-batiments")
    shp = next((HERE / "build" / "vdq-batiments").rglob("*.shp"))
    buildings = gpd.read_file(shp).to_crs(MTM7)
    quarters = gpd.read_file(DATA / "vdq-quartier.geojson").to_crs(MTM7)
    return buildings, quarters


def window(buildings, quarters, where):
    """The square of side SIDE centred on a (lon, lat) point, or on the median building of the
    named neighbourhood."""
    if isinstance(where, tuple):
        pt = gpd.GeoSeries([Point(*where)], crs="EPSG:4326").to_crs(MTM7)[0]
        cx, cy = pt.x, pt.y
    else:
        poly = quarters.loc[quarters["NOM"] == where].geometry.union_all()
        inside = buildings[buildings.representative_point().within(poly)]
        c = inside.geometry.centroid
        cx, cy = float(np.median(c.x)), float(np.median(c.y))
    sq = box(cx - SIDE / 2, cy - SIDE / 2, cx + SIDE / 2, cy + SIDE / 2)
    return sq, buildings[buildings.intersects(sq)].clip(sq)


def raster(sq, shapes):
    """1-metre raster of the window: True where a building stands."""
    x0, y0, _, _ = sq.bounds
    n = SIDE // PIXEL
    img = Image.new("1", (n, n), 0)
    pen = ImageDraw.Draw(img)
    for geom in shapes.geometry:
        for part in getattr(geom, "geoms", [geom]):
            if part.geom_type != "Polygon":
                continue
            pts = [
                ((x - x0) / PIXEL, n - (y - y0) / PIXEL)
                for x, y in part.exterior.coords
            ]
            pen.polygon(pts, fill=1)
    return np.array(img, dtype=bool)


def box_count(grid):
    counts = []
    for s in SIZES:
        k = s // PIXEL
        m = grid.shape[0] // k
        blocks = grid[: m * k, : m * k].reshape(m, k, m, k).any(axis=(1, 3))
        counts.append(int(blocks.sum()))
    slope = np.polyfit(np.log(1 / np.array(SIZES)), np.log(counts), 1)[0]
    return counts, round(float(slope), 3)


def dilation(shapes):
    out = []
    for d in DILATIONS:
        merged = (
            shapes.geometry.buffer(d).union_all() if d else shapes.geometry.union_all()
        )
        out.append(len(getattr(merged, "geoms", [merged])))
    return out


def draw(grid, path, label):
    """The map, with its label above and a 100 m scale bar below, each on a white band so
    that no text sits on the black buildings."""
    band = 44
    square = Image.fromarray(np.where(grid, 0, 255).astype(np.uint8)).convert("RGB")
    square = square.resize((768, 768), Image.LANCZOS)
    img = Image.new("RGB", (768, 768 + 2 * band), "white")
    img.paste(square, (0, band))
    pen = ImageDraw.Draw(img)
    pen.rectangle((0, band, 767, band + 767), outline=(0, 0, 0), width=2)
    font = ImageFont.load_default(26)
    pen.text((4, band // 2), label, fill=(0, 0, 0), font=font, anchor="lm")
    bar = 768 * 100 / SIDE  # a 100 m scale bar
    y = band + 768 + band // 2
    pen.rectangle((4, y - 5, 4 + bar, y + 5), fill=(0, 0, 0))
    pen.text((4 + bar + 12, y), "100 m", fill=(0, 0, 0), font=font, anchor="lm")
    img.save(path)


def main():
    buildings, quarters = load()
    out = {
        "window_m": SIDE,
        "box_sizes_m": SIZES,
        "dilations_m": DILATIONS,
        "areas": {},
    }
    for tag, where in AREAS.items():
        sq, shapes = window(buildings, quarters, where)
        grid = raster(sq, shapes)
        counts, dim = box_count(grid)
        out["areas"][tag] = {
            "centre": "inside the walls (lon, lat) " + str(where)
            if isinstance(where, tuple)
            else "median building of " + where,
            "buildings": len(shapes),
            "built_share_pct": round(100 * float(grid.mean()), 1),
            "boxes_touched": counts,
            "box_dimension": dim,
            "clusters_after_dilation": dilation(shapes),
        }
        draw(
            grid,
            HERE / "figures" / f"m01-quebec-{tag.lower()}.png",
            f"{tag}, 512 m x 512 m",
        )
    maps = [
        Image.open(HERE / "figures" / f"m01-quebec-{tag.lower()}.png") for tag in AREAS
    ]
    strip = Image.new(
        "RGB",
        (sum(m.width for m in maps) + 16 * (len(maps) - 1), maps[0].height),
        "white",
    )
    for i, m in enumerate(maps):
        strip.paste(m, (i * (m.width + 16), 0))
    strip.save(HERE / "figures" / "m01-quebec.png")
    (HERE / "results" / "m01-quebec.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
