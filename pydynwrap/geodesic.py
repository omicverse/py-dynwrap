"""calculate_geodesic_distances — port of R dynwrap's geodesic-on-tents algorithm.

For each cell:
  1. The cell lives inside a "tent" — a set of milestones it could be between
     (a divergence_region). Within a tent the cell-to-milestone distance is
     `percentage * milestone_edge_length`.
  2. Cells in the same tent get cell-to-cell distances via Manhattan in the
     tent's local simplex.
  3. The full graph (milestones + cell-tent stubs + intra-tent cell edges)
     is Dijkstra'd from each waypoint to every cell.

Returns a (n_waypoints × n_cells) numpy matrix.
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import pandas as pd
import networkx as nx

from .trajectory import Trajectory


_MS_PREFIX = "MILESTONE_"


def calculate_geodesic_distances(
    trajectory: Trajectory,
    waypoint_cells: Optional[Sequence[str]] = None,
    waypoint_milestone_percentages: Optional[pd.DataFrame] = None,
    directed: bool | str = False,
) -> pd.DataFrame:
    """1:1 port of R `dynwrap::calculate_geodesic_distances`.

    Args:
        trajectory: a Trajectory with milestone_network + milestone_percentages.
        waypoint_cells: list of cell_ids to use as waypoints; defaults to
            ``trajectory.waypoint_cells`` if available, else all cells.
        waypoint_milestone_percentages: optional DataFrame of waypoint_id,
            milestone_id, percentage — for non-cell waypoints (used by
            project_waypoints).
        directed: False / True / "forward" / "reverse".

    Returns:
        pd.DataFrame (n_waypoints × n_cells) with cell distances.
    """
    cell_ids = trajectory.cell_ids
    milestone_ids = list(trajectory.milestone_ids)
    mn = trajectory.milestone_network.copy()
    mp = trajectory.milestone_percentages.copy()
    dr = (trajectory.divergence_regions.copy() if trajectory.divergence_regions is not None
          else pd.DataFrame({"divergence_id": [], "milestone_id": [], "is_start": []}))

    cell_ids_trajectory = list(mp["cell_id"].unique())

    if waypoint_cells is None:
        if trajectory.waypoint_cells is not None:
            waypoint_cells = list(trajectory.waypoint_cells)
        elif waypoint_milestone_percentages is None:
            waypoint_cells = list(cell_ids_trajectory)
        else:
            waypoint_cells = []
    waypoint_cells = list(waypoint_cells)

    waypoint_ids = list(waypoint_cells)
    if waypoint_milestone_percentages is not None and not waypoint_milestone_percentages.empty:
        wp_extra = list(waypoint_milestone_percentages["waypoint_id"].unique())
        waypoint_ids = list(dict.fromkeys(waypoint_ids + wp_extra))
        wpct = waypoint_milestone_percentages.rename(columns={"waypoint_id": "cell_id"})
        mp = pd.concat([mp, wpct], ignore_index=True)

    # Rename milestones to avoid conflicts with cell ids
    mn["from"] = mn["from"].apply(lambda x: f"{_MS_PREFIX}{x}")
    mn["to"]   = mn["to"].apply(lambda x: f"{_MS_PREFIX}{x}")
    milestone_ids = [f"{_MS_PREFIX}{m}" for m in milestone_ids]
    mp["milestone_id"] = mp["milestone_id"].apply(lambda x: f"{_MS_PREFIX}{x}")
    if not dr.empty:
        dr["milestone_id"] = dr["milestone_id"].apply(lambda x: f"{_MS_PREFIX}{x}")

    # Add 'extra' divergences for edges not yet inside a divergence
    extra = []
    for _, e in mn.iterrows():
        # Check whether this edge's endpoints are all inside some existing divergence
        in_div = False
        if not dr.empty:
            for did, grp in dr.groupby("divergence_id"):
                if {e["from"], e["to"]} <= set(grp["milestone_id"]):
                    in_div = True; break
        if not in_div:
            did = f"{e['from']}__{e['to']}"
            extra.append({"divergence_id": did, "milestone_id": e["from"], "is_start": True})
            extra.append({"divergence_id": did, "milestone_id": e["to"],   "is_start": False})
    if extra:
        dr = pd.concat([dr, pd.DataFrame(extra).drop_duplicates(
            subset=["divergence_id", "milestone_id"])], ignore_index=True)
    if not dr.empty:
        dr["is_start"] = dr["is_start"].astype(bool)

    divergence_ids = list(dr["divergence_id"].unique())
    is_directed_traj = bool(mn["directed"].any())

    # Build per-divergence "tent" cell-cell distances + milestone stubs
    cell_in_tent_distances = []

    mil_gr = nx.DiGraph() if is_directed_traj else nx.Graph()
    for m in milestone_ids:
        mil_gr.add_node(m)
    for _, e in mn.iterrows():
        mil_gr.add_edge(e["from"], e["to"], length=float(e["length"]))
        if not e["directed"] and is_directed_traj:
            mil_gr.add_edge(e["to"], e["from"], length=float(e["length"]))

    for did in divergence_ids:
        sub = dr[dr["divergence_id"] == did]
        starts = sub[sub["is_start"]].milestone_id.tolist()
        if not starts: continue
        mid = starts[0]
        tent = sub.milestone_id.tolist()

        # tent_distances: from mid to each milestone in tent
        tent_distances = {}
        for tm in tent:
            try:
                tent_distances[tm] = nx.shortest_path_length(
                    mil_gr, mid, tm, weight="length")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                tent_distances[tm] = np.inf

        # Cells whose percentages all sit within this tent
        cells_in_tent = []
        for cid, grp in mp.groupby("cell_id"):
            if set(grp["milestone_id"]) <= set(tent):
                cells_in_tent.append(cid)
        if len(cells_in_tent) <= 1:
            continue

        # Build a percentage matrix per cell (distance from mid along each tent edge)
        rows = []
        for cid in cells_in_tent:
            row = {"_id": cid}
            grp = mp[mp["cell_id"] == cid]
            for tm in tent:
                pct = grp[grp["milestone_id"] == tm]["percentage"].sum()
                row[tm] = pct * tent_distances[tm]
            rows.append(row)
        # also one row per milestone in tent (= the milestone itself)
        for tm in tent:
            row = {"_id": tm}
            for tm2 in tent:
                row[tm2] = tent_distances[tm2] if tm2 == tm else 0.0
            rows.append(row)
        pct_mat = pd.DataFrame(rows).set_index("_id")[tent]

        # Manhattan distance between every (cell or milestone) and (cell or milestone)
        # For waypoint+tent endpoints only (rows of distances dict)
        wp_cells = [c for c in pct_mat.index if c in waypoint_ids]
        target_rows = list(set(wp_cells + tent))
        for src in target_rows:
            for dst in pct_mat.index:
                if src == dst: continue
                d = float(np.abs(pct_mat.loc[src] - pct_mat.loc[dst]).sum())
                cell_in_tent_distances.append({"from": src, "to": dst, "length": d})

    # Combine milestone-network edges + cell-tent edges into one weighted graph
    all_edges = pd.concat([
        mn[["from", "to", "length"]],
        pd.DataFrame(cell_in_tent_distances)[["from", "to", "length"]]
        if cell_in_tent_distances else
        pd.DataFrame(columns=["from", "to", "length"]),
    ], ignore_index=True)

    if all_edges.empty:
        return pd.DataFrame(
            np.zeros((len(waypoint_ids), len(cell_ids))),
            index=waypoint_ids, columns=cell_ids,
        )

    all_edges = (all_edges.groupby(["from", "to"], as_index=False)["length"]
                          .min())

    G = nx.DiGraph() if directed in (True, "forward") else nx.Graph()
    for n in set(milestone_ids) | set(cell_ids_trajectory) | set(waypoint_ids):
        G.add_node(n)
    for _, e in all_edges.iterrows():
        G.add_edge(e["from"], e["to"], length=float(e["length"]))

    # Dijkstra from each waypoint to all cells_trajectory
    out = np.full((len(waypoint_ids), len(cell_ids)), np.inf)
    for i, w in enumerate(waypoint_ids):
        if w not in G:
            continue
        try:
            d = nx.single_source_dijkstra_path_length(G, w, weight="length")
        except nx.NodeNotFound:
            continue
        for j, c in enumerate(cell_ids):
            if c in d:
                out[i, j] = d[c]
            elif c not in cell_ids_trajectory:
                # Cells not in milestone_percentages → far away
                out[i, j] = mn["length"].sum()

    return pd.DataFrame(out, index=waypoint_ids, columns=cell_ids)
