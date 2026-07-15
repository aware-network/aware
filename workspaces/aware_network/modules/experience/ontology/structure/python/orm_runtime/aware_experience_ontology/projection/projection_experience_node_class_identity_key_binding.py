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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience_node_key import ProjectionExperienceNodeKey


class ProjectionExperienceNodeClassIdentityKeyBinding(ORMModel):
    """
    ProjectionKey payload row under ProjectionExperienceNodeClassIdentity.
    Contract:
    - Binds one consumed ProjectionExperienceNodeKey to one concrete payload used for resolution proof.
    """

    # Relationships
    projection_experience_node_key: ProjectionExperienceNodeKey | None = Field(default=None, exclude=True)

    # Attributes
    value: JsonObject | None = Field(default=None)

    # Foreign Keys
    projection_experience_node_class_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentity.key_bindings"
    )
    projection_experience_node_key_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityKeyBinding.projection_experience_node_key"
    )

    @classmethod
    async def build_via_projection_experience_node_class_identity(
        cls,
        projection_experience_node_class_identity_id: UUID,
        projection_experience_node_key_id: UUID,
        value: JsonObject | None = None,
    ) -> ProjectionExperienceNodeClassIdentityKeyBinding:
        """Create deterministic ProjectionExperienceNodeClassIdentityKeyBinding."""

        payload = {
            "projection_experience_node_class_identity_id": projection_experience_node_class_identity_id,
            "projection_experience_node_key_id": projection_experience_node_key_id,
            "value": value,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_node_class_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceNodeClassIdentityKeyBinding):
            return value
        return ProjectionExperienceNodeClassIdentityKeyBinding.validate_invocation_value(value)


class ProjectionExperienceNodeClassIdentityKeyBindingBuildViaProjectionExperienceNodeClassIdentityInput(BaseModel):
    projection_experience_node_class_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentity.key_bindings"
    )
    projection_experience_node_key_id: UUID
    value: JsonObject | None = Field(default=None)


class ProjectionExperienceNodeClassIdentityKeyBindingBuildViaProjectionExperienceNodeClassIdentityOutput(BaseModel):
    value: ProjectionExperienceNodeClassIdentityKeyBinding


FUNCTIONS = {
    "ProjectionExperienceNodeClassIdentityKeyBinding": {
        "build_via_projection_experience_node_class_identity": {
            "canonical": {
                "name": "build_via_projection_experience_node_class_identity",
                "description": "Create deterministic ProjectionExperienceNodeClassIdentityKeyBinding.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceNodeClassIdentityKeyBindingBuildViaProjectionExperienceNodeClassIdentityInput,
            "output": ProjectionExperienceNodeClassIdentityKeyBindingBuildViaProjectionExperienceNodeClassIdentityOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceNodeClassIdentityKeyBinding",
    "ProjectionExperienceNodeClassIdentityKeyBindingBuildViaProjectionExperienceNodeClassIdentityInput",
    "ProjectionExperienceNodeClassIdentityKeyBindingBuildViaProjectionExperienceNodeClassIdentityOutput",
    "FUNCTIONS",
]
