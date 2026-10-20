"""Thin Goal composition; Workspace retains the original publisher and receipts.

Only repository publication is available here. Projection, qualified Goal
reading and Project membership are deliberately separate unfinished effects.
"""

from .goal_planning_initial_plan import _PLANS, GoalPlanningPostimagePreparation
from .goal_planning_initial_source import _PREPARATIONS


def plan_initial_planning_goal_publication(postimage):
    if type(postimage) is not GoalPlanningPostimagePreparation:
        raise ValueError("original_goal_postimage_source_required")
    retained = _PLANS.get(postimage)
    if retained is None:
        raise ValueError("original_goal_postimage_source_required")
    workspace = _PREPARATIONS[retained[1]][1]
    return workspace.plan_initial_goal(postimage)
