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
    from aware_experience_ontology_orm_models.projection.projection_experience_view_invocation_action_config import (
        ProjectionExperienceViewInvocationActionConfig,
    )


class ProjectionExperienceViewInvocationAction(ORMModel):
    """
    View-owned provenance bridge for one concrete invocation action.
    Contract:
    - `ProjectionExperienceViewInvocationActionConfig` is view-level configuration.
    - `ExperienceInvocationAction` is the actual invocation receipt.
    - This bridge records that the invocation happened through one concrete
    `ProjectionExperienceViewInstance`.
    """

    # Relationships
    view_invocation_action_config: ProjectionExperienceViewInvocationActionConfig
    experience_invocation_action: ExperienceInvocationAction | None = Field(default=None)

    # Foreign Keys
    projection_experience_view_instance_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInstance.invocation_actions"
    )
    view_invocation_action_config_id: UUID | None = Field(
        default=None,
        description="Foreign key for ProjectionExperienceViewInvocationAction.view_invocation_action_config",
    )
    experience_invocation_action_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInvocationAction.experience_invocation_action"
    )
