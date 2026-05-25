# py-dynwrap

A **Python port of [dynverse/dynwrap](https://github.com/dynverse/dynwrap)** (Saelens et al. *Nat Biotechnol* 2019) — the trajectory data wrapper used by the dynbenchmark / dyneval comparison framework.

- Pure NumPy/SciPy/NetworkX/pandas — no R, no rpy2, no docker
- **byte-equivalent geodesic distances** vs R (max|Δ| = 0.0 on canonical fixture)
- v0.1 scope: data structures + topology utilities + geodesic distances — the minimum needed for `pydyneval::calculate_metrics`

## Install

```bash
pip install pydynwrap-bio
```

## Quick-start

```python
import pydynwrap as dw
import pandas as pd, numpy as np

# Build a 3-branch bifurcation trajectory
ds = dw.wrap_data(cell_ids=[f"c{i}" for i in range(30)])
ds = dw.add_branch_trajectory(
    ds,
    pseudotime=np.tile(np.linspace(0,1,10), 3),
    branch=np.repeat(["A","B","C"], 10),
)

# Geodesic distance matrix (every cell vs every cell)
gd = dw.calculate_geodesic_distances(ds, directed=False)
```

## Function map

| Python | R `dynwrap::` | Status |
|---|---|---|
| `wrap_data` | `wrap_data` | ✅ |
| `add_trajectory` | `add_trajectory` | ✅ |
| `add_linear_trajectory` | `add_linear_trajectory` | ✅ |
| `add_branch_trajectory` | `add_branch_trajectory` | ✅ |
| `add_cluster_graph` | `add_cluster_graph` | ✅ |
| `add_pseudotime` / `add_grouping` / `add_dimred` / `add_expression` | same | ✅ |
| `add_cell_waypoints` | `add_cell_waypoints` | ✅ |
| `convert_progressions_to_milestone_percentages` | same | ✅ |
| `convert_milestone_percentages_to_progressions` | same | ✅ |
| `calculate_geodesic_distances` | same | ✅ (byte-equivalent) |
| `classify_milestone_network` | same | ✅ |
| `simplify_trajectory` | same | ⏳ v0.2 (stub) |
| `is_wrapper_with_trajectory` etc. predicates | same | ✅ |
| Method runners (`infer_trajectory`, ti_* containers) | — | ⛔ v0.3+ (need babelwhale/docker) |
| `align_to_*` cross-trajectory comparison | — | ⏳ v0.2 |

**Coverage**: 14/91 R exports — the core data-wrapping API. Method-running (the dynbenchmark TI runners) is the remaining 60+ exports, deferred per Phase 0.5 scoping.

## Citation

> Saelens, W. et al. *A comparison of single-cell trajectory inference methods.* Nat Biotechnol 37, 547–554 (2019).

## License

MIT (matches upstream dynwrap MIT).
