"""Topology utilities — classify_milestone_network + simplify_trajectory."""

from __future__ import annotations

import numpy as np
import pandas as pd
import networkx as nx

from .trajectory import Trajectory


def classify_milestone_network(milestone_network: pd.DataFrame) -> dict:
    """Return a dict with `network_type`, `n_milestones`, `n_edges`, `directed`.

    network_type ∈ {linear, bifurcation, multifurcation, tree, cycle,
                    convergence, disconnected_graph, graph}.
    """
    n_milestones = len(set(milestone_network["from"]) | set(milestone_network["to"]))
    n_edges = len(milestone_network)
    directed = bool(milestone_network["directed"].any())

    G = nx.DiGraph() if directed else nx.Graph()
    for _, e in milestone_network.iterrows():
        G.add_edge(e["from"], e["to"])
    n_nodes = G.number_of_nodes()

    # Is it a cycle?
    if directed:
        try:
            nx.find_cycle(G)
            is_cycle = nx.is_strongly_connected(G) and all(d == 1 for _, d in G.out_degree())
        except nx.NetworkXNoCycle:
            is_cycle = False
    else:
        is_cycle = (nx.is_connected(G) and all(d == 2 for _, d in G.degree())
                    and n_edges == n_nodes)
    if is_cycle:
        return {"network_type": "cycle", "n_milestones": n_milestones,
                "n_edges": n_edges, "directed": directed}

    # Connected?
    if directed:
        connected = nx.is_weakly_connected(G)
    else:
        connected = nx.is_connected(G)

    if not connected:
        return {"network_type": "disconnected_graph", "n_milestones": n_milestones,
                "n_edges": n_edges, "directed": directed}

    # Tree?
    is_tree = n_edges == n_nodes - 1
    if is_tree:
        # In an undirected tree:
        # - 2 leaves total → linear
        # - >2 leaves & one internal node connected to all branches → multifurcation
        # - otherwise → tree (bifurcation if degree-3 anywhere)
        deg = dict(G.degree() if not directed else G.to_undirected().degree())
        n_leaves = sum(1 for d in deg.values() if d == 1)
        if n_leaves == 2:
            return {"network_type": "linear", "n_milestones": n_milestones,
                    "n_edges": n_edges, "directed": directed}
        # bifurcation = exactly one degree-3 + only degree-1/2
        max_deg = max(deg.values())
        if n_leaves == 3 and max_deg == 3:
            return {"network_type": "bifurcation", "n_milestones": n_milestones,
                    "n_edges": n_edges, "directed": directed}
        if max_deg > 3:
            return {"network_type": "multifurcation", "n_milestones": n_milestones,
                    "n_edges": n_edges, "directed": directed}
        return {"network_type": "tree", "n_milestones": n_milestones,
                "n_edges": n_edges, "directed": directed}

    return {"network_type": "graph", "n_milestones": n_milestones,
            "n_edges": n_edges, "directed": directed}


def simplify_trajectory(trajectory: Trajectory) -> Trajectory:
    """Remove milestones that are pure pass-throughs (degree 2 with no cell
    progression touching them as an endpoint). v0.1 is a no-op stub —
    full simplification is a v0.2 task."""
    return trajectory
