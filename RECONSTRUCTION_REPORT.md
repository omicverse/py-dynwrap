# Reconstruction Report — py-dynwrap v0.1.0

## 1. Identity

| Field | Value |
|---|---|
| Python package | `pydynwrap` (PyPI: `pydynwrap-bio`) |
| Upstream R | `dynwrap` 1.3.0 |
| Citation | Saelens et al. Nat Biotechnol 2019 |
| Algorithm class | deterministic (data wrapping + geodesic Dijkstra) |
| Threshold | max|Δ| ≤ 1e-6 |
| **Measured parity** | **0.0** byte-equivalent |
| Audit class | **A** translation-only |
| LOC | ~600 Python (vs ~6409 R) |

## 2. R function coverage

14/91 R exports ported. See README §Function map.

**In scope** (v0.1): trajectory data structures, geodesic distances,
topology classification, percentage/progression converters. This is the
minimum needed for `pydyneval::calculate_metrics`.

**Deferred** (v0.2+):
- Method runners (containerised TI methods via babelwhale/docker)
- `align_to_*` trajectory comparison
- `add_cell_graph` / `add_dimred_projection` / `project_waypoints` —
  not used by core metrics

## 3. Parity evidence

Fixture: deterministic 3-branch tent trajectory (30 cells × 4 milestones).

| Output | Class | Threshold | Measured | Pass |
|---|---|---|---|---|
| `geodesic_distances` (30×30 matrix) | deterministic | max|Δ| ≤ 1e-6 | **0.0** | ✅ |
| `milestone_percentages` | deterministic | exact match | exact | ✅ |

## 4. Acceleration

None (class A).

## 5. Code quality

- `pip install -e .` ✅
- `pytest -q` ✅ 6/6 + 1/1 parity
- 4 notebooks ✅
- README/MATH/AUDIT/DISCOVERY/this report ✅

## 6. Known limitations

1. TI method runners (babelwhale/docker) deferred — dynbenchmark
   benchmark-of-method-execution use case not yet supported.
2. `simplify_trajectory` is a no-op stub for v0.1 (passes input through).
3. Directed geodesic distances ("forward" / "reverse" mode) tested only
   indirectly via dyneval; full coverage in v0.2.

## 7. omicverse integration

`omicverse.external.pydynwrap` (planned). Required dependency for
py-dyneval (which depends on calculate_geodesic_distances).

## 8. Sign-off

| Field | Value |
|---|---|
| Author | claude-opus-4-7 via omicverse-rebuildr |
| Date | 2026-05-24 |
| Audit class | A |
