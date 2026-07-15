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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience_node_class_identity_key_binding import (
        ProjectionExperienceNodeClassIdentityKeyBinding,
    )
    from aware_experience_ontology.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity


class ProjectionExperienceNodeClassIdentity(ORMModel):
    """
    Shared semantic node identity -> runtime class identity bridge.
    Contract:
    - Bridges one ProjectionExperienceNodeIdentity to one Meta ClassInstanceIdentity.
    - Traversal context is expressed via ProjectionExperienceNodeClassIdentityEdge.
    - Key bindings live under this edge as mapping data.
    """

    # Relationships
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)
    class_instance_identity: ClassInstanceIdentity | None = Field(default=None, exclude=True)
    key_bindings: list[ProjectionExperienceNodeClassIdentityKeyBinding] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str

    # Foreign Keys
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.node_class_identities"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentity.projection_experience_node_identity"
    )
    class_instance_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentity.class_instance_identity"
    )

    async def add_key_binding(
        self, projection_experience_node_key_id: UUID, value: JsonObject | None = None
    ) -> ProjectionExperienceNodeClassIdentityKeyBinding:
        """Attach one ProjectionKey resolution payload row under this projection node-class identity bridge."""

        payload = {"projection_experience_node_key_id": projection_experience_node_key_id, "value": value}
        result = await invoke_instance(orm_model=self, function_name="add_key_binding", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_node_class_identity_key_binding import (
            ProjectionExperienceNodeClassIdentityKeyBinding,
        )

        if isinstance(value, ProjectionExperienceNodeClassIdentityKeyBinding):
            return value
        return ProjectionExperienceNodeClassIdentityKeyBinding.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience_oigi(
        cls,
        projection_experience_oigi_id: UUID,
        projection_experience_node_identity_id: UUID,
        class_instance_identity_id: UUID,
        key: str,
    ) -> ProjectionExperienceNodeClassIdentity:
        """Create deterministic ProjectionExperienceNodeClassIdentity."""

        payload = {
            "projection_experience_oigi_id": projection_experience_oigi_id,
            "projection_experience_node_identity_id": projection_experience_node_identity_id,
            "class_instance_identity_id": class_instance_identity_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_oigi", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceNodeClassIdentity):
            return value
        return ProjectionExperienceNodeClassIdentity.validate_invocation_value(value)


class ProjectionExperienceNodeClassIdentityAddKeyBindingInput(BaseModel):
    projection_experience_node_key_id: UUID
    value: JsonObject | None = Field(default=None)


class ProjectionExperienceNodeClassIdentityAddKeyBindingOutput(BaseModel):
    value: ProjectionExperienceNodeClassIdentityKeyBinding


class ProjectionExperienceNodeClassIdentityBuildViaProjectionExperienceOigiInput(BaseModel):
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.node_class_identities"
    )
    projection_experience_node_identity_id: UUID
    class_instance_identity_id: UUID
    key: str


class ProjectionExperienceNodeClassIdentityBuildViaProjectionExperienceOigiOutput(BaseModel):
    value: ProjectionExperienceNodeClassIdentity


FUNCTIONS = {
    "ProjectionExperienceNodeClassIdentity": {
        "add_key_binding": {
            "canonical": {
                "name": "add_key_binding",
                "description": "Attach one ProjectionKey resolution payload row under this projection node-class identity bridge.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceNodeClassIdentityAddKeyBindingInput,
            "output": ProjectionExperienceNodeClassIdentityAddKeyBindingOutput,
        },
        "build_via_projection_experience_oigi": {
            "canonical": {
                "name": "build_via_projection_experience_oigi",
                "description": "Create deterministic ProjectionExperienceNodeClassIdentity.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceNodeClassIdentityBuildViaProjectionExperienceOigiInput,
            "output": ProjectionExperienceNodeClassIdentityBuildViaProjectionExperienceOigiOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceNodeClassIdentity",
    "ProjectionExperienceNodeClassIdentityAddKeyBindingInput",
    "ProjectionExperienceNodeClassIdentityAddKeyBindingOutput",
    "ProjectionExperienceNodeClassIdentityBuildViaProjectionExperienceOigiInput",
    "ProjectionExperienceNodeClassIdentityBuildViaProjectionExperienceOigiOutput",
    "FUNCTIONS",
]
