"""Module 3: antenna placement, extended from the class notebook (antennas.ipynb).

The placement loop is the notebook's last one: a random candidate inside the margin is
accepted when the proportion of its bounding box already covered is below `threshold`,
and the loop stops when no black pixel is left or after `permitted` rejections in a row.
Two changes. Speed: `coverage()` and `holes()` count pixels with numpy instead of a Python
loop over 360,000 pixels, which gives the same numbers far faster. Correctness: the local
coverage of a candidate is measured over the part of its box inside the town (see
`local_coverage`); the notebook's crop, kept as `in_image_only=False`, never stops at a
threshold of 0.9 or more.

Basic stage (hands-on option): vary the allowed overlap (threshold) and count antennas,
5 replicas each. The in-depth stage took the conceptual option (code/m03_weights.py).

Run: uv run --with pillow --with numpy python code/m03_antennas.py
"""

import json
import random
from pathlib import Path
from statistics import mean

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
SIZE = 600
GROUND = (0, 0, 0)
RANGE = (255, 255, 0)


def coverage(image):  # proportion of NON-background pixels, as in the notebook
    return float((np.asarray(image)[:, :, 0] != GROUND[0]).mean())


def holes(image):  # is any background pixel left?
    return bool((np.asarray(image)[:, :, 0] == GROUND[0]).any())


def local_coverage(aux, bb, in_image_only):
    """Proportion of the bounding box already covered.

    The notebook's `aux.crop(bb)` pads the part of the box that falls outside the town
    with black, which reads as uncovered. That is `in_image_only=False`. It makes an
    antenna near the edge look useful however covered its in-town part already is.
    """
    if not in_image_only:
        return coverage(aux.crop(bb))
    left, top, right, bottom = (round(v) for v in bb)
    left, top, right, bottom = (
        max(left, 0),
        max(top, 0),
        min(right, SIZE),
        min(bottom, SIZE),
    )
    return coverage(aux.crop((left, top, right, bottom)))


def place(
    threshold,
    radii,
    rng,
    permitted=100,
    fixed=0.1,
    draw_path=None,
    in_image_only=True,
    cap=3000,
    record=None,
):
    """radii: the options each antenna's radius is drawn from ([0.1] = the notebook).

    cap stops a run that would otherwise never end (see local_coverage); a capped run
    is reported as such rather than hidden. record, if given, receives the antennas.
    """
    margin = fixed / 2  # the notebook's margin, from the original radius
    span = 1 - 2 * margin
    aux = Image.new("RGB", (SIZE, SIZE), GROUND)
    cov = ImageDraw.Draw(aux)
    antennas = []  # (x, y, radius)
    attempts = permitted
    while holes(aux):
        x, y = margin + span * rng.random(), margin + span * rng.random()
        r = rng.choice(radii)
        col, row, unit = SIZE * x, SIZE * y, SIZE * r
        bb = (row - unit, col - unit, row + unit, col + unit)
        present = local_coverage(aux, bb, in_image_only)
        if present < threshold:
            attempts = permitted
            antennas.append((x, y, r))
            cov.ellipse(bb, fill=RANGE)
            if len(antennas) >= cap:
                break
        else:
            attempts -= 1
            if attempts == 0:
                break
    if record is not None:
        record.extend(antennas)
    if draw_path is not None:
        town = aux.copy()
        pen = ImageDraw.Draw(town)
        for x, y, r in antennas:
            col, row, unit = SIZE * x, SIZE * y, SIZE * r
            pen.ellipse(
                (row - unit, col - unit, row + unit, col + unit),
                outline=(200, 0, 0),
                width=2,
            )
            pen.rectangle((row - 4, col - 4, row + 4, col + 4), fill=(255, 255, 255))
        town.save(draw_path)
    return {
        "antennas": len(antennas),
        "coverage_pct": round(100 * coverage(aux), 2),
        "complete": not holes(aux),
        "capped": len(antennas) >= cap,
        "mean_radius": round(mean(r for _, _, r in antennas), 4),
    }


FIGURES = {("fixed", 0.7)}  # the run the report shows
THRESHOLDS = [0.3, 0.5, 0.7, 0.8, 0.9, 0.95]
REPLICAS = 5
RADIUS_SETS = {"fixed 0.1": [0.1]}  # the notebook's fixed radius


def sweep(radii, seed, tag, in_image_only=True):
    rows = []
    for k, t in enumerate(THRESHOLDS):
        reps = [
            place(
                t,
                radii,
                random.Random(seed + 10 * k + i),
                in_image_only=in_image_only,
                draw_path=(HERE / "figures" / f"m03-{tag}-t{int(t * 100)}.png")
                if i == 0 and (tag, t) in FIGURES
                else None,
            )
            for i in range(REPLICAS)
        ]
        counts = [r["antennas"] for r in reps]
        rows.append({
            "threshold": t,
            "radii": radii,
            "replicas": REPLICAS,
            "counts": counts,
            "min": min(counts),
            "mean": round(mean(counts), 1),
            "max": max(counts),
            "mean_coverage_pct": round(mean(r["coverage_pct"] for r in reps), 2),
            "complete_runs": sum(r["complete"] for r in reps),
            "capped_runs": sum(r["capped"] for r in reps),
            "mean_radius_used": round(mean(r["mean_radius"] for r in reps), 4),
        })
    return rows


def main(seed=610):
    out = {"seed": seed, "size": SIZE, "permitted": 100, "margin": 0.05, "sweeps": {}}
    for j, (name, radii) in enumerate(RADIUS_SETS.items()):
        tag = (
            "fixed"
            if len(radii) == 1
            else "mixed" + "".join(str(int(r * 100)) for r in radii)
        )
        # same seeds for every radius set, so the comparison differs only by the radii
        out["sweeps"][name] = sweep(radii, seed, tag)
        for row in out["sweeps"][name]:
            print(
                f"{name:20s} t={row['threshold']:.2f} antennas {row['min']}-{row['mean']}-{row['max']}"
                f" coverage {row['mean_coverage_pct']}% complete {row['complete_runs']}/{REPLICAS}"
            )
    (HERE / "results" / "m03.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
