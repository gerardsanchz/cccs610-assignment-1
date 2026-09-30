"""Module 3, in-depth stage (conceptual option): scalarization on the basic stage's results.

The two objectives are coverage (more is better) and the number of antennas (fewer is
better). Scalarization turns them into one score with a weight:

    score = coverage (%) - price * antennas

where `price` is how many points of coverage one antenna must bring to be worth building.
For each threshold of the basic stage (mean over its replicas), this finds the range of
prices for which that threshold has the best score. A threshold that is never best for any
price is dominated by a mix of its neighbours and gets no range. The ranges are exact:
they meet at the prices where two thresholds tie.

Run: python3 code/m03_weights.py
"""

import json
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def main():
    rows = json.loads((HERE / "results" / "m03.json").read_text())["sweeps"][
        "fixed 0.1"
    ]
    pts = [(r["threshold"], r["mean"], r["mean_coverage_pct"]) for r in rows]
    steps = [
        {
            "from": a[0],
            "to": b[0],
            "extra_antennas": round(b[1] - a[1], 1),
            "extra_coverage_pts": round(b[2] - a[2], 2),
            "pts_per_antenna": round((b[2] - a[2]) / (b[1] - a[1]), 3),
        }
        for a, b in pairwise(pts)
    ]

    # Exact range of prices for which each threshold has the best score. Against a point
    # with fewer antennas, a threshold wins while the price is below the coverage it adds per
    # extra antenna; against a point with more antennas, it wins once the price is above the
    # coverage that point adds per extra antenna. A threshold with an empty range is never best.
    def slope(a, b):
        return (b[2] - a[2]) / (b[1] - a[1])

    ranges = {}
    for p in pts:
        lo = max((slope(p, q) for q in pts if q[1] > p[1]), default=0.0)
        hi = min((slope(q, p) for q in pts if q[1] < p[1]), default=None)
        if hi is None or max(lo, 0.0) < hi:
            ranges[p[0]] = (max(lo, 0.0), hi)
    out = {
        "steps": steps,
        "best_threshold_for_price": {
            str(t): {
                "from": round(lo, 4),
                "to": None if hi is None else round(hi, 4),
            }
            for t, (lo, hi) in sorted(ranges.items(), reverse=True)
        },
    }
    (HERE / "results" / "m03-weights.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
