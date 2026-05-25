# py-dynwrap — Math Notes

## 1. Bit-equivalent (E)

- **`convert_progressions_to_milestone_percentages`**: linear identity
  `pct_from = 1 - p`, `pct_to = p`, then sum + renormalise per cell. Exact.
- **`convert_milestone_percentages_to_progressions`**: pick the edge `(f,t)`
  maximising `mp[f] + mp[t]`, emit `p = mp[t] / (mp[f] + mp[t])`. Exact.
- **`calculate_geodesic_distances`**: the tent-aware Dijkstra. R uses
  igraph + reshape2; we use networkx + pandas. The graph construction is
  reproduced verbatim:
  1. Rename milestones → `MILESTONE_*` (avoid name collisions).
  2. For each divergence_region (or auto-generated extra divergences from
     ungrouped edges), compute per-cell tent percentages × tent_distances
     → cell-tent stub edges.
  3. Combine milestone_network edges + cell-tent edges, dedupe by min length.
  4. Dijkstra from each waypoint to every cell.

  Byte-equivalent against R on the canonical fixture: max|Δ| = 0.0.

## 2. Bounded ε-approximations (B)

None claimed.

## 3. Class-containment (C)

None.

## 4. Cross-implementation divergence

### 4.1 Self-loops

R `add_trajectory` accepts `allow_self_loops`; we honour it identically.

### 4.2 Empty graphs

If `milestone_network` is empty, R returns an empty matrix; we return a
zero matrix with the right shape.

## 5. Audit class

**A** — translation-only.
