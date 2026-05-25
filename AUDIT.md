# AUDIT — py-dynwrap

R exports per `dynwrap::NAMESPACE`: 91 total.

## Ported (14)

| R | Python | Notes |
|---|---|---|
| `wrap_data` | `wrap_data` | ✅ |
| `add_trajectory` | `add_trajectory` | ✅ |
| `add_linear_trajectory` | `add_linear_trajectory` | ✅ |
| `add_branch_trajectory` | `add_branch_trajectory` | ✅ |
| `add_cluster_graph` | `add_cluster_graph` | ✅ |
| `add_pseudotime` | `add_pseudotime` | ✅ |
| `add_grouping` | `add_grouping` | ✅ |
| `add_dimred` | `add_dimred` | ✅ |
| `add_expression` | `add_expression` | ✅ |
| `add_cell_waypoints` | `add_cell_waypoints` | ✅ |
| `convert_progressions_to_milestone_percentages` | same | ✅ |
| `convert_milestone_percentages_to_progressions` | same | ✅ |
| `calculate_geodesic_distances` | same | ✅ byte-equivalent |
| `classify_milestone_network` | same | ✅ |

## Deferred (77)

- TI method runners (`infer_trajectory`, `create_ti_method_*`, `get_ti_methods`, `test_ti_method`, `priors`, `runtimes`): 18 functions
- Trajectory comparison (`align_to_*`, `mix_trajectories`): 6
- Cell graph + dimred utilities (`add_cell_graph`, `add_dimred_projection`, `project_waypoints`, `add_attraction`): 8
- Regulatory net + tde (`add_regulatory_network`, `add_tde_overall`, `add_feature_importance`): 6
- Cyclic trajectory specifics (`add_cyclic_trajectory`, `add_branch_trajectory_directly`): 3
- Subset / extract / merge helpers (`extract_*`, `subset_*`, `gather_cells_at_milestones`, `label_milestones`): 12
- Predicates and getters (the remaining `get_*` + `is_*` and reexports): 24

Total: 14 ported + 77 deferred = 91. The 14 ported items cover 100% of
the dependency surface needed by `pydyneval::calculate_metrics`.
