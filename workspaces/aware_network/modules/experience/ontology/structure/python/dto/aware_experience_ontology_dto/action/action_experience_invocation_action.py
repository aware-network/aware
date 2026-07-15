from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.invocation.experience_invocation_action import ExperienceInvocationAction


class ActionExperienceInvocationAction(BaseModel):
    """
    ActionExperience-owned provenance bridge for one invocation action.
    Contract:
    - Parent `ActionExperienceInvocation` scope is provided only by
    `ActionExperienceInvocation::invocation_actions` traversal.
    - `ExperienceInvocationAction` is the actual generic invocation receipt.
    - This bridge records that the dispatch happened through one
    ActionExperience invocation binding without making the binding a receipt
    identity owner.
    """

    # Relationships
    experience_invocation_action: ExperienceInvocationAction | None = Field(default=None)
