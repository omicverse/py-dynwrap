"""Converters between progressions and milestone_percentages."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


def convert_progressions_to_milestone_percentages(
    cell_ids: Sequence[str],
    milestone_ids: Sequence[str],
    progressions: pd.DataFrame,
    milestone_network: pd.DataFrame,
) -> pd.DataFrame:
    """For each (cell, edge), split the percentage between the edge's endpoints.

    A cell with progression p% from A→B contributes (1-p) to milestone A and p
    to milestone B.

    Returns DataFrame cell_id × milestone_id × percentage.
    """
    rows = []
    for _, r in progressions.iterrows():
        rows.append({"cell_id": r["cell_id"], "milestone_id": r["from"],
                     "percentage": 1 - r["percentage"]})
        rows.append({"cell_id": r["cell_id"], "milestone_id": r["to"],
                     "percentage":     r["percentage"]})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame({"cell_id": [], "milestone_id": [], "percentage": []})
    # Aggregate by (cell, milestone) and renormalise to sum=1 per cell
    df = df.groupby(["cell_id", "milestone_id"], as_index=False)["percentage"].sum()
    sums = df.groupby("cell_id")["percentage"].transform("sum").replace(0, 1.0)
    df["percentage"] = df["percentage"] / sums
    df = df[df["percentage"] > 1e-10].reset_index(drop=True)
    return df


def convert_milestone_percentages_to_progressions(
    cell_ids: Sequence[str],
    milestone_ids: Sequence[str],
    milestone_percentages: pd.DataFrame,
    milestone_network: pd.DataFrame,
) -> pd.DataFrame:
    """For each cell, pick the edge whose endpoints account for the most of its
    weight and emit a progression along it."""
    if milestone_percentages.empty:
        return pd.DataFrame({"cell_id": [], "from": [], "to": [], "percentage": []})

    pct_by_cell = (milestone_percentages
                   .groupby("cell_id")[["milestone_id", "percentage"]]
                   .apply(lambda d: dict(zip(d["milestone_id"], d["percentage"]))))

    rows = []
    for cid, mp in pct_by_cell.items():
        # Best edge: maximises pct(from) + pct(to)
        best_score = -1.0; best_edge = None
        for _, e in milestone_network.iterrows():
            score = mp.get(e["from"], 0.0) + mp.get(e["to"], 0.0)
            if score > best_score:
                best_score = score
                best_edge = (e["from"], e["to"])
        if best_edge is None:
            continue
        f, t = best_edge
        pf, pt = mp.get(f, 0.0), mp.get(t, 0.0)
        denom = pf + pt
        prog = pt / denom if denom > 0 else 0.5
        rows.append({"cell_id": cid, "from": f, "to": t, "percentage": prog})
    return pd.DataFrame(rows)
