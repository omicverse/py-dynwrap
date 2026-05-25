# Discovery — py-dynwrap

## 1. Is the target already ported?

`gh repo view omicverse/py-dynwrap` → **not found at port start**.

## 2. R dependency audit + py-mirror reuse

R upstream `DESCRIPTION` lists: `igraph`, `Matrix`, `dplyr`, `purrr`, `tibble`, `glue`, `assertthat`, `processx`, `crayon`, `babelwhale`.

| R dep | Py mirror | Status |
|---|---|---|
| igraph | `networkx` | ✅ direct sub |
| Matrix | `scipy.sparse` | ✅ direct sub |
| dplyr/purrr/tibble | `pandas` | ✅ |
| processx, babelwhale | (containerised TI method runners) | ⛔ skipped — out of scope for v0.1 (we only need the trajectory wrapper + metrics path) |

## 3. v0.1 scope

dynwrap has **91 exports / 6409 R LOC**. Per rebuildr Phase 0.5 scoping, v0.1 ports the **trajectory-data wrapper + topology utilities + geodesic distances** — the minimum needed for `dyneval::calculate_metrics` to work.

**In scope (v0.1)**:
- Data wrappers: `wrap_data`, `add_trajectory`, `add_pseudotime`, `add_grouping`, `add_dimred`, `add_expression`
- Converters: `convert_progressions_to_milestone_percentages`, `convert_milestone_percentages_to_progressions`
- Topology utilities: `simplify_trajectory`, `classify_milestone_network`
- Geodesic distances: `calculate_geodesic_distances` (the critical input to cor_dist + position_predict metrics)
- Waypoints: `add_cell_waypoints`, `select_waypoint_cells`
- Predicates: `is_wrapper_with_trajectory`, `is_wrapper_with_dimred`, etc.

**Deferred (v0.2+)**:
- TI method runners (containerised execution via babelwhale/docker)
- Method discovery / definition
- Trajectory-comparison helpers (`align_to_*`, `mix_trajectories`)
- Cell-graph wrappers

## 4. Decision

**Proceed with full port** — algorithm class is data-structure/utility (not numeric inference). Parity gate: byte-equivalence on `calculate_geodesic_distances` (a single deterministic shortest-path Floyd-Warshall on the milestone graph).
