"""Smoke tests for pydynwrap."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
_PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PORT))
import pydynwrap as dw


def test_import():
    assert dw.__version__ == "0.1.0"


def test_wrap_data():
    t = dw.wrap_data(["a", "b", "c"])
    assert t.cell_ids == ["a", "b", "c"]
    assert len(t.cell_info) == 3
    assert "cell_id" in t.cell_info.columns


def test_add_linear_trajectory():
    t = dw.wrap_data(["c1","c2","c3","c4","c5"])
    t = dw.add_linear_trajectory(t, [0.0, 0.25, 0.5, 0.75, 1.0])
    assert dw.is_wrapper_with_trajectory(t)
    assert set(t.milestone_ids) == {"milestone_begin", "milestone_end"}
    assert len(t.progressions) == 5
    assert t.pseudotime is not None


def test_add_branch_trajectory():
    n = 30
    cell_ids = [f"c{i}" for i in range(n)]
    pt = np.tile(np.linspace(0,1,10), 3)
    br = np.repeat(["A","B","C"], 10)
    t = dw.wrap_data(cell_ids)
    t = dw.add_branch_trajectory(t, pt, br)
    assert len(t.milestone_ids) == 4   # root + 3 branch ends
    assert len(t.progressions) == n


def test_geodesic_distances_linear():
    """Linear trajectory: cell distance ≈ |pt_a - pt_b|."""
    n = 6
    pt = np.linspace(0, 1, n)
    t = dw.wrap_data([f"c{i}" for i in range(n)])
    t = dw.add_linear_trajectory(t, pt)
    gd = dw.calculate_geodesic_distances(t, directed=False)
    # c0 → c5 should be 1.0 (the edge length)
    assert abs(gd.loc["c0", "c5"] - 1.0) < 1e-6
    # c0 → c0 = 0
    assert gd.loc["c0", "c0"] == 0.0


def test_classify_milestone_network():
    mn_linear = pd.DataFrame({"from":["A"],"to":["B"],"length":[1.0],"directed":[True]})
    assert dw.classify_milestone_network(mn_linear)["network_type"] == "linear"
    mn_bif = pd.DataFrame({"from":["A","A","A"],"to":["B","C","D"],
                           "length":[1.0]*3,"directed":[True]*3})
    info = dw.classify_milestone_network(mn_bif)
    assert info["network_type"] in ("bifurcation", "multifurcation")
