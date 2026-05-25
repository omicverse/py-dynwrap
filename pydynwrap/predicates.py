"""Predicate functions matching R `dynwrap::is_wrapper_with_*`."""
from __future__ import annotations

from .trajectory import Trajectory


def is_wrapper_with_trajectory(obj) -> bool:
    return (isinstance(obj, Trajectory)
            and obj.milestone_ids is not None
            and obj.milestone_network is not None
            and obj.milestone_percentages is not None)


def is_wrapper_with_dimred(obj) -> bool:
    return isinstance(obj, Trajectory) and obj.dimred is not None


def is_wrapper_with_expression(obj) -> bool:
    return isinstance(obj, Trajectory) and obj.counts is not None


def is_wrapper_with_waypoint_cells(obj) -> bool:
    return (isinstance(obj, Trajectory) and obj.waypoint_cells is not None
            and len(obj.waypoint_cells) > 0)


def is_wrapper_with_grouping(obj) -> bool:
    return isinstance(obj, Trajectory) and obj.grouping is not None
