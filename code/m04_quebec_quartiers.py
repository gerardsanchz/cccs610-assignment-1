"""Module 4, in-depth stage (conceptual option): colouring the map of Québec City's quartiers.

Each of the city's 35 official neighbourhoods is a vertex, and two neighbourhoods are joined
when they share a border longer than 1 m (two areas that meet at a single point may take the
same colour on a map). The graph is coloured with the class method (`original()` from
m04_coloring.py) and with DSatur, and an exact search finds the smallest number of colours
that works, so both counts can be compared with the true minimum.

Run: uv run --with geopandas --with networkx --with matplotlib --with pillow --with numpy python code/m04_quebec_quartiers.py
"""

import json
from itertools import combinations
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from m04_coloring import PALETTE, original

HERE = Path(__file__).resolve().parent.parent
MTM7 = "EPSG:32187"


def border_graph(quarters):
    graph = nx.Graph()
    graph.add_nodes_from(quarters["NOM"])
    for i, j in combinations(range(len(quarters)), 2):
        shared = quarters.geometry[i].intersection(quarters.geometry[j])
        if shared.length > 1:
            graph.add_edge(quarters["NOM"][i], quarters["NOM"][j])
    return graph


def colouring_with(graph, k):
    """A colouring with at most k colours, found by exhaustive backtracking, or None."""
    order = sorted(graph, key=graph.degree, reverse=True)
    col = {}

    def extend(n):
        if n == len(order):
            return True
        v = order[n]
        used = {col[u] for u in graph[v] if u in col}
        for c in range(k):
            if c not in used:
                col[v] = c
                if extend(n + 1):
                    return True
                del col[v]
        return False

    return dict(col) if extend(0) else None


def draw(quarters, cols, names, path):
    fig, axes = plt.subplots(1, len(names), figsize=(7 * len(names), 6.5), dpi=150)
    for ax, name in zip(axes, names):
        col = cols[name]
        quarters.plot(
            ax=ax,
            color=[PALETTE[col[n]] for n in quarters["NOM"]],
            edgecolor="black",
            linewidth=0.5,
        )
        ax.set_title(f"{name}: {len(set(col.values()))} colours", fontsize=13)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    quarters = gpd.read_file(HERE / "data" / "vdq-quartier.geojson").to_crs(MTM7)
    graph = border_graph(quarters)
    cols = {
        "class method": original(graph),
        "DSatur": nx.coloring.greedy_color(graph, strategy="saturation_largest_first"),
    }
    minimum = next(
        k for k in range(1, graph.number_of_nodes() + 1) if colouring_with(graph, k)
    )
    for name, col in cols.items():  # every colouring must be proper
        if any(col[u] == col[v] for u, v in graph.edges):
            raise AssertionError(f"{name} gave two neighbours the same colour")
    out = {
        "quartiers": graph.number_of_nodes(),
        "shared_borders": graph.number_of_edges(),
        "largest_group_all_touching": max(len(c) for c in nx.find_cliques(graph)),
        "colours": {name: len(set(col.values())) for name, col in cols.items()},
        "true_minimum": minimum,
    }
    draw(quarters, cols, list(cols), HERE / "figures" / "m04-quebec-quartiers.png")
    (HERE / "results" / "m04-quebec-quartiers.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
