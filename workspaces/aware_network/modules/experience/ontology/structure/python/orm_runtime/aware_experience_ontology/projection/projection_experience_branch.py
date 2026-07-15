from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class ProjectionExperienceBranch(ORMModel):
    # Attributes
    name: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_branches"
    )

    @classmethod
    async def create_via_projection_experience(
        cls, projection_experience_id: UUID, name: str
    ) -> ProjectionExperienceBranch:
        """
        Construct a deterministic ProjectionExperienceBranch under a ProjectionExperience.

        Contract:
        - `ProjectionExperienceBranch.id` is deterministic for `(projection_experience_id, name)`.
        - Constructor is idempotent for repeated calls with the same pair.
        """

        payload = {"projection_experience_id": projection_experience_id, "name": name}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceBranch):
            return value
        return ProjectionExperienceBranch.validate_invocation_value(value)


class ProjectionExperienceBranchCreateViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_branches"
    )
    name: str


class ProjectionExperienceBranchCreateViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceBranch


FUNCTIONS = {
    "ProjectionExperienceBranch": {
        "create_via_projection_experience": {
            "canonical": {
                "name": "create_via_projection_experience",
                "description": "Construct a deterministic ProjectionExperienceBranch under a ProjectionExperience.\n\nContract:\n- `ProjectionExperienceBranch.id` is deterministic for `(projection_experience_id, name)`.\n- Constructor is idempotent for repeated calls with the same pair.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceBranchCreateViaProjectionExperienceInput,
            "output": ProjectionExperienceBranchCreateViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceBranch",
    "ProjectionExperienceBranchCreateViaProjectionExperienceInput",
    "ProjectionExperienceBranchCreateViaProjectionExperienceOutput",
    "FUNCTIONS",
]
