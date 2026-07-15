from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action import ExperienceInvocationAction


class ActionExperienceInvocationAction(ORMModel):
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

    # Foreign Keys
    action_experience_invocation_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocation.invocation_actions"
    )
    experience_invocation_action_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocationAction.experience_invocation_action"
    )
