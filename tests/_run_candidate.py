"""Run pydynwrap on the same fixture and dump."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
_PORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PORT))
import pydynwrap as dw


def main():
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(exist_ok=True, parents=True)

    cell_ids = [f"cell_{i+1}" for i in range(30)]
    milestone_network = pd.DataFrame({
        "from": ["A","A","A"], "to": ["B","C","D"],
        "length": [1.0]*3, "directed": [True]*3,
    })
    n_each = 10
    pct = np.linspace(0.05, 0.95, n_each)
    rows = []
    for j, b in enumerate(["B","C","D"]):
        for i in range(n_each):
            rows.append({"cell_id": f"cell_{j*10+i+1}", "from":"A", "to":b,
                          "percentage": pct[i]})
    progressions = pd.DataFrame(rows)
    ds = dw.wrap_data(cell_ids=cell_ids, id="fixture")
    ds = dw.add_trajectory(ds, milestone_ids=["A","B","C","D"],
                            milestone_network=milestone_network,
                            progressions=progressions)
    gd = dw.calculate_geodesic_distances(ds, directed=False)

    out = {
        "cell_ids": ds.cell_ids,
        "milestone_ids": ds.milestone_ids,
        "milestone_network": ds.milestone_network.to_dict(orient="records"),
        "progressions": ds.progressions.to_dict(orient="records"),
        "milestone_percentages": ds.milestone_percentages.to_dict(orient="records"),
        "geodesic_distances": gd.values.tolist(),
        "geodesic_row_names": list(gd.index),
        "geodesic_col_names": list(gd.columns),
    }
    (out_dir/"candidate.json").write_text(json.dumps(out))
    print("Py candidate done")


if __name__ == "__main__":
    main()
