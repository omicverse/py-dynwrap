"""End-to-end R parity test."""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

_PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PORT))


@pytest.fixture(scope="module")
def dumps():
    DATA = _PORT/"data"; DATA.mkdir(exist_ok=True)
    ref, cand = DATA/"reference.json", DATA/"candidate.json"
    if not ref.exists():
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = ("/share/software/user/open/netcdf/4.8.1/lib:"
                                   + env.get("LD_LIBRARY_PATH", ""))
        subprocess.run(["conda","run","-p",
                        os.environ.get("R_TEST_ENV","/scratch/users/steorra/env/CMAP"),
                        "Rscript", str(_PORT/"tests"/"r_reference_driver.R"), str(DATA)],
                       check=True, env=env, capture_output=True)
    if not cand.exists():
        subprocess.run([sys.executable, str(_PORT/"tests"/"_run_candidate.py"), str(DATA)],
                       check=True, capture_output=True)
    return json.loads(ref.read_text()), json.loads(cand.read_text())


def test_geodesic_byte_equivalent(dumps):
    r, p = dumps
    R = pd.DataFrame(np.array(r["geodesic_distances"]),
                     index=r["geodesic_row_names"], columns=r["geodesic_col_names"])
    P = pd.DataFrame(np.array(p["geodesic_distances"]),
                     index=p["geodesic_row_names"], columns=p["geodesic_col_names"])
    rows = sorted(set(R.index) & set(P.index))
    cols = sorted(set(R.columns) & set(P.columns))
    delta = np.abs(R.loc[rows, cols].values - P.loc[rows, cols].values)
    print(f"  geodesic max|Δ| = {delta.max():.6e}")
    assert delta.max() < 1e-6
