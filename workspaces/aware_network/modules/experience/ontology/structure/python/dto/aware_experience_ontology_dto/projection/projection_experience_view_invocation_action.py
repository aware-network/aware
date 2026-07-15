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
    from aware_experience_ontology_dto.projection.projection_experience_view_invocation_action_config import (
        ProjectionExperienceViewInvocationActionConfig,
    )


class ProjectionExperienceViewInvocationAction(BaseModel):
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
