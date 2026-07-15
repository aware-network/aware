from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
    from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
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

    @classmethod
    async def build(
        cls,
        projection_experience_view_instance_id: UUID,
        view_invocation_action_config_id: UUID,
        experience_invocation_action_id: UUID,
    ) -> ProjectionExperienceViewInvocationAction:
        """
        Create one deterministic view provenance bridge under a view instance.

        Contract:
        - `projection_experience_view_instance_id` is explicit provenance for the concrete view instance.
        - `view_invocation_action_config` proves the action was exposed by the view.
        - `experience_invocation_action` carries the actual invocation receipt.
        """

        payload = {
            "projection_experience_view_instance_id": projection_experience_view_instance_id,
            "view_invocation_action_config_id": view_invocation_action_config_id,
            "experience_invocation_action_id": experience_invocation_action_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceViewInvocationAction):
            return value
        return ProjectionExperienceViewInvocationAction.validate_invocation_value(value)


class ProjectionExperienceViewInvocationActionBuildInput(BaseModel):
    projection_experience_view_instance_id: UUID
    view_invocation_action_config_id: UUID
    experience_invocation_action_id: UUID


class ProjectionExperienceViewInvocationActionBuildOutput(BaseModel):
    value: ProjectionExperienceViewInvocationAction


FUNCTIONS = {
    "ProjectionExperienceViewInvocationAction": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic view provenance bridge under a view instance.\n\nContract:\n- `projection_experience_view_instance_id` is explicit provenance for the concrete view instance.\n- `view_invocation_action_config` proves the action was exposed by the view.\n- `experience_invocation_action` carries the actual invocation receipt.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceViewInvocationActionBuildInput,
            "output": ProjectionExperienceViewInvocationActionBuildOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceViewInvocationAction",
    "ProjectionExperienceViewInvocationActionBuildInput",
    "ProjectionExperienceViewInvocationActionBuildOutput",
    "FUNCTIONS",
]
