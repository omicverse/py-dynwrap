#!/usr/bin/env Rscript
# R reference: build a known bifurcation trajectory + dump it as JSON.
# Then dump the calculate_geodesic_distances matrix (the v0.1 parity target).
suppressPackageStartupMessages({
  library(dynwrap); library(jsonlite); library(dplyr); library(tibble)
})
args <- commandArgs(trailingOnly = TRUE)
out_dir <- args[1]
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

# A deterministic 3-branch tent trajectory
set.seed(42)
cell_ids <- paste0("cell_", 1:30)
milestone_network <- tribble(
  ~from, ~to, ~length, ~directed,
  "A",   "B", 1.0,     TRUE,
  "A",   "C", 1.0,     TRUE,
  "A",   "D", 1.0,     TRUE,
)
# Equally distributed cells along A→B, A→C, A→D
n_each <- 10
progressions <- bind_rows(
  tibble(cell_id = paste0("cell_",  1:10), from = "A", to = "B",
         percentage = seq(0.05, 0.95, length.out = n_each)),
  tibble(cell_id = paste0("cell_", 11:20), from = "A", to = "C",
         percentage = seq(0.05, 0.95, length.out = n_each)),
  tibble(cell_id = paste0("cell_", 21:30), from = "A", to = "D",
         percentage = seq(0.05, 0.95, length.out = n_each)),
)
ds <- wrap_data(id = "fixture", cell_ids = cell_ids)
ds <- add_trajectory(ds, milestone_ids = c("A","B","C","D"),
                     milestone_network = milestone_network,
                     progressions = progressions)

# Geodesic distance matrix with no waypoints (= all cells)
gd <- calculate_geodesic_distances(ds, directed = FALSE)
gd_mat <- as.matrix(gd)
rownames(gd_mat) <- rownames(gd); colnames(gd_mat) <- colnames(gd)

# Dump
write_json(list(
  cell_ids = ds$cell_ids,
  milestone_ids = ds$milestone_ids,
  milestone_network = ds$milestone_network,
  progressions = ds$progressions,
  milestone_percentages = ds$milestone_percentages,
  geodesic_distances = gd_mat,
  geodesic_row_names = rownames(gd_mat),
  geodesic_col_names = colnames(gd_mat)
), file.path(out_dir, "reference.json"), auto_unbox = TRUE, digits = 10)
cat("R reference done\n")
