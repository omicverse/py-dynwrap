"""pydynwrap — pure-Python port of dynverse/dynwrap.

A trajectory data wrapper used by `dyneval::calculate_metrics` and the
dynbenchmark TI method comparison framework.

v0.1 scope: data structures + topology utilities + geodesic distances.
TI method runners (babelwhale/docker) deferred to v0.2.

Citation: Saelens et al. *A comparison of single-cell trajectory inference
methods.* Nat Biotechnol 37, 547 (2019).
"""

from __future__ import annotations

__version__ = "0.1.0"

from .trajectory import (
    Trajectory,
    wrap_data,
    add_trajectory,
    add_linear_trajectory,
    add_branch_trajectory,
    add_cluster_graph,
    add_pseudotime,
    add_grouping,
    add_dimred,
    add_expression,
    add_cell_waypoints,
    group_onto_nearest_milestones,
    group_onto_trajectory_edges,
)
from .convert import (
    convert_progressions_to_milestone_percentages,
    convert_milestone_percentages_to_progressions,
)
from .geodesic import calculate_geodesic_distances
from .topology import simplify_trajectory, classify_milestone_network
from .predicates import (
    is_wrapper_with_trajectory,
    is_wrapper_with_dimred,
    is_wrapper_with_expression,
    is_wrapper_with_waypoint_cells,
    is_wrapper_with_grouping,
)

__all__ = [
    "Trajectory",
    "wrap_data",
    "add_trajectory",
    "add_linear_trajectory",
    "add_branch_trajectory",
    "add_cluster_graph",
    "add_pseudotime",
    "add_grouping",
    "add_dimred",
    "add_expression",
    "add_cell_waypoints",
    "group_onto_nearest_milestones",
    "group_onto_trajectory_edges",
    "convert_progressions_to_milestone_percentages",
    "convert_milestone_percentages_to_progressions",
    "calculate_geodesic_distances",
    "simplify_trajectory",
    "classify_milestone_network",
    "is_wrapper_with_trajectory",
    "is_wrapper_with_dimred",
    "is_wrapper_with_expression",
    "is_wrapper_with_waypoint_cells",
    "is_wrapper_with_grouping",
    "__version__",
]
