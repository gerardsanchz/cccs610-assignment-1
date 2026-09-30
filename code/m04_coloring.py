"""Module 4: graph colouring of the antenna graph, extended from coloring.ipynb.

The graph is built as in class: antennas placed by the Module 3 loop (threshold 0.7,
100 attempts, the notebook's own crop), radius 0.1, and an edge between two antennas
whose ranges overlap (distance < 2 * 0.1).

`original()` is the class algorithm: take one colour at a time and give it to every
still-uncoloured vertex, in descending-degree order, that has no neighbour with it.
The palette is unbounded here, so the count is never cut short at the notebook's 7.

Basic stage: one graph, DSatur (and the other networkx strategies) against the original.

Run: uv run --with pillow --with numpy --with networkx --with matplotlib python code/m04_coloring.py
"""

import json
import random
from math import sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import m03_antennas
import matplotlib.pyplot as plt
import networkx as nx

HERE = Path(__file__).resolve().parent.parent
AR = 0.1
PALETTE = [
    "cyan",
    "orange",
    "lime",
    "violet",
    "yellow",
    "wheat",
    "hotpink",
    "tomato",
    "deepskyblue",
    "gold",
    "orchid",
    "lightgreen",
]


def antenna_graph(seed):
    rng = random.Random(seed)
    antennas = []
    m03_antennas.place(0.7, [AR], rng, in_image_only=False, record=antennas)
    graph = nx.Graph()
    for i, (x, y, _) in enumerate(antennas):
        graph.add_node(i, pos=(x, y))
    for i, (x1, y1, _) in enumerate(antennas):
        for j, (x2, y2, _) in enumerate(antennas):
            if i < j and sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) < 2 * AR:
                graph.add_edge(i, j)
    return graph


def original(graph):
    """The notebook's colour-by-colour greedy, returning {vertex: colour index}."""
    degrees = sorted(
        ((v, graph.degree(v)) for v in graph.nodes), key=lambda pair: -pair[1]
    )
    assignment = {v: None for v in graph.nodes}
    current = 0
    while None in assignment.values():
        for vertex, _ in degrees:
            if assignment[vertex] is None and current not in {
                assignment[n] for n in graph.neighbors(vertex)
            }:
                assignment[vertex] = current
        current += 1
    return assignment


STRATEGIES = [
    "largest_first",
    "smallest_last",
    "saturation_largest_first",
    "independent_set",
    "connected_sequential_bfs",
    "random_sequential",
]


def colourings(graph, seed):
    out = {"original (class)": original(graph)}
    for s in STRATEGIES:
        strategy = s
        if s == "random_sequential":  # seeded, so a re-run gives the same order
            rng = random.Random(seed)
            strategy = lambda G, colors, rng=rng: (
                nx.coloring.strategy_random_sequential(G, colors, seed=rng)
            )
        out[s] = nx.coloring.greedy_color(graph, strategy=strategy)
    for name, col in out.items():  # every colouring must be proper
        bad = [(u, v) for u, v in graph.edges if col[u] == col[v]]
        if bad:
            raise AssertionError(f"{name} gave neighbours {bad[0]} the same colour")
    return out


def count(col):
    return len(set(col.values()))


def draw(graph, cols, names, path):
    fig, axes = plt.subplots(1, len(names), figsize=(6 * len(names), 6), dpi=130)
    pos = nx.get_node_attributes(graph, "pos")
    for ax, name in zip(axes, names):
        col = cols[name]
        nx.draw(
            graph,
            pos,
            ax=ax,
            node_size=160,
            node_color=[PALETTE[col[v] % len(PALETTE)] for v in graph.nodes],
            edgecolors="black",
            linewidths=0.5,
            width=0.6,
        )
        nx.draw_networkx_labels(graph, pos, ax=ax, font_size=6)
        ax.set_title(f"{name}: {count(col)} colours", fontsize=13)
        ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main(seed=610):
    g = antenna_graph(seed)
    cols = colourings(g, seed)
    basic = {
        "vertices": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "max_degree": max(d for _, d in g.degree()),
        "colours": {k: count(v) for k, v in cols.items()},
        "original_equals_largest_first": cols["original (class)"]
        == cols["largest_first"],
    }
    draw(
        g,
        cols,
        ["original (class)", "saturation_largest_first"],
        HERE / "figures" / "m04-basic.png",
    )

    out = {"seed": seed, "basic": basic}
    (HERE / "results" / "m04.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(basic))


if __name__ == "__main__":
    main()
