"""Core data-wrapper + trajectory constructors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np
import pandas as pd


@dataclass
class Trajectory:
    """A dynwrap-style trajectory wrapper.

    Mirrors the R `dynwrap` list-based wrapper. All trajectory fields are
    optional until the corresponding ``add_*`` function is called.

    Attributes:
        id: opaque string identifier.
        cell_ids: list of cell names.
        cell_info: DataFrame with one row per cell, ``cell_id`` column required.
        feature_ids: list of feature/gene names.
        feature_info: DataFrame with one row per feature.
        milestone_ids: list of milestone names.
        milestone_network: DataFrame ``from, to, length, directed`` describing
            edges between milestones.
        progressions: DataFrame ``cell_id, from, to, percentage`` — fractional
            position of each cell along an edge.
        milestone_percentages: DataFrame ``cell_id, milestone_id, percentage``
            — equivalent to progressions but per-milestone closeness.
        divergence_regions: DataFrame ``divergence_id, milestone_id, is_start``
            for tents (e.g. a bifurcation).
        pseudotime: dict cell_id → float, optional.
        grouping: dict cell_id → group_label, optional.
        dimred: (n_cells × d) ndarray, optional.
        counts / expression: raw / normalised expression matrices, optional.
        waypoint_cells: list of cell ids used as waypoints for downstream metrics.
    """

    id: str
    cell_ids: list[str]
    cell_info: pd.DataFrame
    feature_ids: Optional[list[str]] = None
    feature_info: Optional[pd.DataFrame] = None
    # Trajectory
    milestone_ids: Optional[list[str]] = None
    milestone_network: Optional[pd.DataFrame] = None
    progressions: Optional[pd.DataFrame] = None
    milestone_percentages: Optional[pd.DataFrame] = None
    divergence_regions: Optional[pd.DataFrame] = None
    # Auxiliary
    pseudotime: Optional[pd.Series] = None
    grouping: Optional[pd.Series] = None
    dimred: Optional[np.ndarray] = None
    counts: Optional[np.ndarray] = None
    expression: Optional[np.ndarray] = None
    waypoint_cells: Optional[list[str]] = None
    extra: dict = field(default_factory=dict)


# ----- wrap_data ---------------------------------------------------------- #


def _random_id(prefix: str = "data_wrapper") -> str:
    import time, random
    return f"{prefix}_{int(time.time() * 1000)}_{random.randint(0, 99999)}"


def wrap_data(
    cell_ids: Sequence[str],
    *,
    id: Optional[str] = None,
    cell_info: Optional[pd.DataFrame] = None,
    feature_ids: Optional[Sequence[str]] = None,
    feature_info: Optional[pd.DataFrame] = None,
    **extra,
) -> Trajectory:
    """1:1 port of R ``dynwrap::wrap_data``."""
    cell_ids = list(cell_ids)
    if len(set(cell_ids)) != len(cell_ids):
        raise ValueError("cell_ids contain duplicates.")
    if id is None:
        id = _random_id()
    if cell_info is None:
        cell_info = pd.DataFrame({"cell_id": cell_ids})
    else:
        cell_info = cell_info.copy()
        if "cell_id" not in cell_info.columns:
            cell_info.insert(0, "cell_id", cell_ids)
    return Trajectory(
        id=id,
        cell_ids=cell_ids,
        cell_info=cell_info,
        feature_ids=list(feature_ids) if feature_ids is not None else None,
        feature_info=feature_info,
        extra=dict(extra),
    )


# ----- add_trajectory ----------------------------------------------------- #


def add_trajectory(
    traj: Trajectory,
    milestone_ids: Sequence[str],
    milestone_network: pd.DataFrame,
    *,
    progressions: Optional[pd.DataFrame] = None,
    milestone_percentages: Optional[pd.DataFrame] = None,
    divergence_regions: Optional[pd.DataFrame] = None,
    allow_self_loops: bool = False,
) -> Trajectory:
    """1:1 port of R ``dynwrap::add_trajectory``.

    Either ``progressions`` or ``milestone_percentages`` must be provided;
    the other is derived.
    """
    milestone_ids = list(milestone_ids)
    mn = milestone_network.copy()
    for col in ("from", "to", "length"):
        if col not in mn.columns:
            raise ValueError(f"milestone_network missing column '{col}'.")
    if "directed" not in mn.columns:
        mn["directed"] = False
    if not allow_self_loops:
        mn = mn[mn["from"] != mn["to"]].reset_index(drop=True)

    # Derive the missing one
    if progressions is None and milestone_percentages is None:
        raise ValueError("Provide progressions or milestone_percentages.")
    if progressions is None:
        from .convert import convert_milestone_percentages_to_progressions
        progressions = convert_milestone_percentages_to_progressions(
            traj.cell_ids, milestone_ids, milestone_percentages, mn
        )
    if milestone_percentages is None:
        from .convert import convert_progressions_to_milestone_percentages
        milestone_percentages = convert_progressions_to_milestone_percentages(
            traj.cell_ids, milestone_ids, progressions, mn
        )

    if divergence_regions is None:
        divergence_regions = pd.DataFrame(
            {"divergence_id": [], "milestone_id": [], "is_start": []}
        )

    traj.milestone_ids = milestone_ids
    traj.milestone_network = mn
    traj.progressions = progressions
    traj.milestone_percentages = milestone_percentages
    traj.divergence_regions = divergence_regions
    return traj


# ----- add_linear_trajectory ---------------------------------------------- #


def add_linear_trajectory(
    traj: Trajectory,
    pseudotime: pd.Series | np.ndarray | dict,
    *,
    milestone_id_start: str = "milestone_begin",
    milestone_id_end: str = "milestone_end",
) -> Trajectory:
    """Create a 1-edge trajectory from a per-cell pseudotime vector."""
    if isinstance(pseudotime, dict):
        pt = pd.Series(pseudotime).reindex(traj.cell_ids)
    elif isinstance(pseudotime, pd.Series):
        pt = pseudotime.reindex(traj.cell_ids)
    else:
        pt = pd.Series(np.asarray(pseudotime, dtype=np.float64), index=traj.cell_ids)

    pt = pt.fillna(0.0)
    lo, hi = float(pt.min()), float(pt.max())
    rng = hi - lo if hi > lo else 1.0
    pct = (pt - lo) / rng

    milestone_network = pd.DataFrame({
        "from": [milestone_id_start], "to": [milestone_id_end],
        "length": [1.0], "directed": [True],
    })
    progressions = pd.DataFrame({
        "cell_id": traj.cell_ids,
        "from": [milestone_id_start] * len(traj.cell_ids),
        "to":   [milestone_id_end]   * len(traj.cell_ids),
        "percentage": pct.values,
    })
    traj = add_trajectory(
        traj,
        milestone_ids=[milestone_id_start, milestone_id_end],
        milestone_network=milestone_network,
        progressions=progressions,
    )
    add_pseudotime(traj, pt)
    return traj


# ----- add_branch_trajectory ---------------------------------------------- #


def add_branch_trajectory(
    traj: Trajectory,
    pseudotime: pd.Series | np.ndarray | dict,
    branch: pd.Series | np.ndarray | list | dict,
    *,
    root: Optional[str] = None,
) -> Trajectory:
    """Create a trajectory from per-cell (pseudotime, branch) pairs.

    The branch labels define lineages — for each branch we add an edge
    from a shared root milestone to a per-branch end milestone, and
    cell percentages run from 0 (at root) → 1 (at branch end).
    """
    if isinstance(pseudotime, dict):
        pt = pd.Series(pseudotime).reindex(traj.cell_ids)
    elif isinstance(pseudotime, pd.Series):
        pt = pseudotime.reindex(traj.cell_ids)
    else:
        pt = pd.Series(np.asarray(pseudotime, dtype=np.float64), index=traj.cell_ids)
    if isinstance(branch, dict):
        br = pd.Series(branch).reindex(traj.cell_ids)
    elif isinstance(branch, pd.Series):
        br = branch.reindex(traj.cell_ids)
    else:
        br = pd.Series(np.asarray(branch), index=traj.cell_ids)
    pt = pt.fillna(0.0); br = br.fillna("L1")

    branches = sorted(br.unique())
    if root is None:
        root = "milestone_root"
    milestone_ids = [root] + [f"milestone_{b}" for b in branches]
    mn = pd.DataFrame({
        "from": [root] * len(branches),
        "to":   [f"milestone_{b}" for b in branches],
        "length": [1.0] * len(branches),
        "directed": [True] * len(branches),
    })
    # Scale pseudotime within each branch to [0,1]
    pct_rows = []
    for b in branches:
        mask = br == b
        pt_b = pt[mask]
        lo, hi = float(pt_b.min()), float(pt_b.max())
        rng = (hi - lo) if hi > lo else 1.0
        pct = (pt_b - lo) / rng
        for cid, p in pct.items():
            pct_rows.append({"cell_id": cid, "from": root, "to": f"milestone_{b}", "percentage": p})
    progressions = pd.DataFrame(pct_rows)

    traj = add_trajectory(
        traj, milestone_ids=milestone_ids, milestone_network=mn, progressions=progressions
    )
    add_pseudotime(traj, pt)
    add_grouping(traj, br)
    return traj


def add_cluster_graph(
    traj: Trajectory,
    *,
    milestone_ids: Sequence[str],
    milestone_network: pd.DataFrame,
    grouping: pd.Series | dict,
) -> Trajectory:
    """Trajectory where each cell sits at a milestone (no in-edge progression).
    Used by clustering-style TI methods (PAGA, etc.)."""
    if isinstance(grouping, dict):
        gr = pd.Series(grouping).reindex(traj.cell_ids)
    else:
        gr = grouping.reindex(traj.cell_ids)
    rows = [{"cell_id": cid, "milestone_id": str(g), "percentage": 1.0}
            for cid, g in gr.items() if pd.notna(g)]
    mp = pd.DataFrame(rows)
    traj = add_trajectory(
        traj, milestone_ids=list(milestone_ids),
        milestone_network=milestone_network, milestone_percentages=mp
    )
    add_grouping(traj, gr)
    return traj


# ----- aux setters -------------------------------------------------------- #


def add_pseudotime(traj: Trajectory, pseudotime) -> Trajectory:
    if isinstance(pseudotime, dict):
        pt = pd.Series(pseudotime).reindex(traj.cell_ids)
    elif isinstance(pseudotime, pd.Series):
        pt = pseudotime.reindex(traj.cell_ids)
    else:
        pt = pd.Series(np.asarray(pseudotime, dtype=np.float64), index=traj.cell_ids)
    traj.pseudotime = pt
    return traj


def add_grouping(traj: Trajectory, grouping) -> Trajectory:
    if isinstance(grouping, dict):
        gr = pd.Series(grouping).reindex(traj.cell_ids)
    elif isinstance(grouping, pd.Series):
        gr = grouping.reindex(traj.cell_ids)
    else:
        gr = pd.Series(np.asarray(grouping), index=traj.cell_ids)
    traj.grouping = gr
    return traj


def add_dimred(traj: Trajectory, dimred: np.ndarray) -> Trajectory:
    arr = np.asarray(dimred, dtype=np.float64)
    if arr.shape[0] != len(traj.cell_ids):
        raise ValueError(
            f"dimred has {arr.shape[0]} rows but traj has {len(traj.cell_ids)} cells"
        )
    traj.dimred = arr
    return traj


def add_expression(
    traj: Trajectory,
    counts: np.ndarray,
    expression: Optional[np.ndarray] = None,
    feature_ids: Optional[Sequence[str]] = None,
) -> Trajectory:
    counts = np.asarray(counts, dtype=np.float64)
    traj.counts = counts
    traj.expression = (counts if expression is None
                       else np.asarray(expression, dtype=np.float64))
    if feature_ids is not None:
        traj.feature_ids = list(feature_ids)
    elif traj.feature_ids is None:
        traj.feature_ids = [f"gene_{i}" for i in range(counts.shape[1])]
    return traj


def group_onto_nearest_milestones(traj: Trajectory) -> pd.Series:
    """For each cell, return the milestone with the highest milestone_percentage.

    Mirrors R `dynwrap::group_onto_nearest_milestones`.
    """
    if traj.milestone_percentages is None:
        raise ValueError("trajectory has no milestone_percentages")
    mp = traj.milestone_percentages
    idx = mp.groupby("cell_id")["percentage"].idxmax()
    nearest = mp.loc[idx].set_index("cell_id")["milestone_id"]
    return nearest.reindex(traj.cell_ids)


def group_onto_trajectory_edges(traj: Trajectory) -> pd.Series:
    """For each cell, return its edge as a string "from___to".

    Mirrors R `dynwrap::group_onto_trajectory_edges`.
    """
    if traj.progressions is None:
        raise ValueError("trajectory has no progressions")
    p = traj.progressions.copy()
    # If a cell appears on multiple edges, take the one with highest percentage
    idx = p.groupby("cell_id")["percentage"].idxmax()
    sub = p.loc[idx].set_index("cell_id")
    edges = sub["from"].astype(str) + "___" + sub["to"].astype(str)
    return edges.reindex(traj.cell_ids)


def add_cell_waypoints(traj: Trajectory, n_waypoints: int = 100,
                       seed: int = 42) -> Trajectory:
    """Pick n_waypoints cells evenly-spaced along the trajectory (random if no pt)."""
    n_cells = len(traj.cell_ids)
    n = min(n_waypoints, n_cells)
    rng = np.random.RandomState(seed)
    if traj.pseudotime is not None:
        pt = traj.pseudotime.fillna(0.0).values
        # quantile-based sampling
        ranks = pt.argsort().argsort()
        quants = np.linspace(0, n_cells - 1, n).astype(int)
        target_ranks = quants
        idx = np.argsort(np.abs(ranks[:, None] - target_ranks[None, :]), axis=0)[0]
        idx = np.unique(idx)[:n]
    else:
        idx = rng.choice(n_cells, n, replace=False)
    traj.waypoint_cells = [traj.cell_ids[i] for i in idx]
    return traj
