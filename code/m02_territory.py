"""Module 2: delivery territories, extended from the class notebook (territory.ipynb).

Basic stage (hands-on option): a rectangular town (width != height), a margin that keeps
every restaurant away from the edge, and the same margin as a minimum distance between
restaurants. The in-depth stage took the conceptual option (code/m02_quebec_clsc.py).

Run: uv run --with pillow --with seaborn python code/m02_territory.py
"""

import json
import random
from math import sqrt
from pathlib import Path
from statistics import mean, pstdev

import seaborn as sns
from PIL import Image, ImageColor, ImageDraw

HERE = Path(__file__).resolve().parent.parent
MAGNIFICATION = 6
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def distance(p1, p2):  # the notebook's Euclidean distance
    (x1, y1), (x2, y2) = p1, p2
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def place(width, height, margin, existing, rng, permitted=1000):
    """One pseudorandom lot at least `margin` from every edge and more than `margin` from
    every existing restaurant; None after `permitted` failed tries in a row."""
    for _ in range(permitted):
        pos = (
            rng.randint(margin, width - 1 - margin),
            rng.randint(margin, height - 1 - margin),
        )
        if all(distance(pos, r) > margin for r in existing):
            return pos
    return None


def territories(width, height, restaurants, ranges=None):
    """owner[y][x] = index of the restaurant that delivers to lot (x, y), or None.

    Without ranges this is the notebook's rule: the nearest restaurant. With ranges, a lot
    goes to the nearest restaurant *whose range reaches it*; when the nearest one is out of
    range but a farther one is in range, the farther one delivers.
    """
    owner = [[None] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            best, best_d = None, None
            for i, r in enumerate(restaurants):
                d = distance((x, y), r)
                if ranges is not None and d > ranges[i]:
                    continue
                if best_d is None or d < best_d:
                    best, best_d = i, d
            owner[y][x] = best
    return owner


def draw(width, height, restaurants, owner, path, ranges=None):
    colors = [
        ImageColor.getcolor(c, "RGB")
        for c in sns.color_palette("husl", len(restaurants)).as_hex()
    ]
    town = Image.new("RGB", (width, height), WHITE)
    px = town.load()
    for y in range(height):
        for x in range(width):
            if owner[y][x] is not None:
                px[x, y] = colors[owner[y][x]]
    for x, y in restaurants:
        px[x, y] = BLACK
    big = town.resize((width * MAGNIFICATION, height * MAGNIFICATION), Image.NEAREST)
    if ranges is not None:  # outline each delivery range
        pen = ImageDraw.Draw(big)
        for (x, y), r in zip(restaurants, ranges):
            cx, cy, rr = (
                (x + 0.5) * MAGNIFICATION,
                (y + 0.5) * MAGNIFICATION,
                r * MAGNIFICATION,
            )
            pen.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=BLACK, width=1)
    big.save(path)


def stats(width, height, restaurants, owner):
    areas = [0] * len(restaurants)
    edge = set()
    for y in range(height):
        for x in range(width):
            i = owner[y][x]
            areas[i] += 1
            if x in (0, width - 1) or y in (0, height - 1):
                edge.add(i)
    edge_areas = [areas[i] for i in edge]
    inner_areas = [a for i, a in enumerate(areas) if i not in edge]
    nearest = [min(distance(r, s) for s in restaurants if s != r) for r in restaurants]
    return {
        "min_area": min(areas),
        "max_area": max(areas),
        "cv_area": pstdev(areas)
        / mean(areas),  # spread of territory sizes, relative to the mean
        "edge_share": len(edge) / len(restaurants),
        "mean_edge_area": mean(edge_areas) if edge_areas else None,
        "mean_inner_area": mean(inner_areas) if inner_areas else None,
        "min_gap": min(nearest),
    }


SCENARIOS = [  # name, width, height, margin
    ("A: square 80x80, no margin (class notebook)", 80, 80, 0),
    ("B: rectangle 120x54, no margin", 120, 54, 0),
    ("C: rectangle 120x54, margin 6", 120, 54, 6),
    ("D: rectangle 120x54, margin 12", 120, 54, 12),
]
HOW_MANY = 15
REPLICAS = 20


def basic(seed):
    rows = []
    for k, (name, w, h, m) in enumerate(SCENARIOS):
        reps = []
        for rep in range(REPLICAS):
            rng = random.Random(seed + 100 * k + rep)
            rs = []
            while len(rs) < HOW_MANY:
                pos = place(w, h, m, rs, rng)
                if pos is None:
                    raise RuntimeError(
                        f"{name}: no legal lot left for restaurant {len(rs) + 1}"
                    )
                rs.append(pos)
            owner = territories(w, h, rs)
            reps.append(stats(w, h, rs, owner))
            if rep == 0:
                draw(
                    w,
                    h,
                    rs,
                    owner,
                    HERE / "figures" / f"m02-basic-{name[0].lower()}.png",
                )
        rows.append({
            "scenario": name,
            "width": w,
            "height": h,
            "margin": m,
            "replicas": REPLICAS,
            **{
                key: round(mean(r[key] for r in reps), 3)
                for key in (
                    "min_area",
                    "max_area",
                    "cv_area",
                    "edge_share",
                    "mean_edge_area",
                    "mean_inner_area",
                    "min_gap",
                )
            },
        })
    return rows


def main(seed=610):
    out = {"seed": seed, "basic": basic(seed)}
    (HERE / "results" / "m02.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
