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
    from aware_experience_ontology.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )
    from aware_meta_ontology.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity


class ProjectionExperienceNodeClassIdentityEdge(ORMModel):
    """
    Environment-scoped binding edge for semantic node-class anchors.
    Contract:
    - Explicitly encodes parent -> child chain between two node-class anchors.
    - ClassInstanceRelationshipIdentity is required and is the only traversal truth.
    """

    # Relationships
    child_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None, exclude=True)
    parent_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None, exclude=True)
    class_instance_relationship_identity: ClassInstanceRelationshipIdentity | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.node_class_identity_edges"
    )
    child_node_class_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityEdge.child_node_class_identity"
    )
    parent_node_class_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityEdge.parent_node_class_identity"
    )
    class_instance_relationship_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeClassIdentityEdge.class_instance_relationship_identity"
    )

    @classmethod
    async def build_via_projection_experience_oigi(
        cls,
        projection_experience_oigi_id: UUID,
        parent_node_class_identity_id: UUID,
        child_node_class_identity_id: UUID,
        class_instance_relationship_identity_id: UUID,
        key: str | None = None,
    ) -> ProjectionExperienceNodeClassIdentityEdge:
        """Create deterministic ProjectionExperienceNodeClassIdentityEdge."""

        payload = {
            "projection_experience_oigi_id": projection_experience_oigi_id,
            "parent_node_class_identity_id": parent_node_class_identity_id,
            "child_node_class_identity_id": child_node_class_identity_id,
            "class_instance_relationship_identity_id": class_instance_relationship_identity_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_oigi", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceNodeClassIdentityEdge):
            return value
        return ProjectionExperienceNodeClassIdentityEdge.validate_invocation_value(value)


class ProjectionExperienceNodeClassIdentityEdgeBuildViaProjectionExperienceOigiInput(BaseModel):
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.node_class_identity_edges"
    )
    parent_node_class_identity_id: UUID
    child_node_class_identity_id: UUID
    class_instance_relationship_identity_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceNodeClassIdentityEdgeBuildViaProjectionExperienceOigiOutput(BaseModel):
    value: ProjectionExperienceNodeClassIdentityEdge


FUNCTIONS = {
    "ProjectionExperienceNodeClassIdentityEdge": {
        "build_via_projection_experience_oigi": {
            "canonical": {
                "name": "build_via_projection_experience_oigi",
                "description": "Create deterministic ProjectionExperienceNodeClassIdentityEdge.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceNodeClassIdentityEdgeBuildViaProjectionExperienceOigiInput,
            "output": ProjectionExperienceNodeClassIdentityEdgeBuildViaProjectionExperienceOigiOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceNodeClassIdentityEdge",
    "ProjectionExperienceNodeClassIdentityEdgeBuildViaProjectionExperienceOigiInput",
    "ProjectionExperienceNodeClassIdentityEdgeBuildViaProjectionExperienceOigiOutput",
    "FUNCTIONS",
]
