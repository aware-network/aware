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

if TYPE_CHECKING:
    from aware_experience_ontology.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )
    from aware_experience_ontology.projection.projection_experience_node_class_identity_edge import (
        ProjectionExperienceNodeClassIdentityEdge,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class ProjectionExperienceOIGI(ORMModel):
    """
    ProjectionExperience -> ObjectInstanceGraphIdentity bridge.
    Contract:
    - Owns ProjectionExperience semantic-to-runtime identity topology.
    - Environment/Thread bind to this object; they do not own node/edge topology.
    """

    # Relationships
    node_class_identities: list[ProjectionExperienceNodeClassIdentity] = Field(default_factory=list, exclude=True)
    node_class_identity_edges: list[ProjectionExperienceNodeClassIdentityEdge] = Field(
        default_factory=list, exclude=True
    )
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_oigis"
    )
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceOIGI.object_instance_graph_identity"
    )

    async def create_node_class_identity(
        self, projection_experience_node_identity_id: UUID, class_instance_identity_id: UUID, key: str
    ) -> ProjectionExperienceNodeClassIdentity:
        """Attach one semantic ProjectionExperienceNodeIdentity -> ClassInstanceIdentity anchor."""

        payload = {
            "projection_experience_node_identity_id": projection_experience_node_identity_id,
            "class_instance_identity_id": class_instance_identity_id,
            "key": key,
        }
        result = await invoke_instance(orm_model=self, function_name="create_node_class_identity", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_node_class_identity import (
            ProjectionExperienceNodeClassIdentity,
        )

        if isinstance(value, ProjectionExperienceNodeClassIdentity):
            return value
        return ProjectionExperienceNodeClassIdentity.validate_invocation_value(value)

    async def create_node_class_identity_edge(
        self,
        parent_node_class_identity_id: UUID,
        child_node_class_identity_id: UUID,
        class_instance_relationship_identity_id: UUID,
        key: str | None = None,
    ) -> ProjectionExperienceNodeClassIdentityEdge:
        """Attach one explicit parent->child edge under this ProjectionExperienceOIGI."""

        payload = {
            "parent_node_class_identity_id": parent_node_class_identity_id,
            "child_node_class_identity_id": child_node_class_identity_id,
            "class_instance_relationship_identity_id": class_instance_relationship_identity_id,
            "key": key,
        }
        result = await invoke_instance(orm_model=self, function_name="create_node_class_identity_edge", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_node_class_identity_edge import (
            ProjectionExperienceNodeClassIdentityEdge,
        )

        if isinstance(value, ProjectionExperienceNodeClassIdentityEdge):
            return value
        return ProjectionExperienceNodeClassIdentityEdge.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience(
        cls, projection_experience_id: UUID, object_instance_graph_identity_id: UUID, key: str | None = None
    ) -> ProjectionExperienceOIGI:
        """Create deterministic ProjectionExperienceOIGI."""

        payload = {
            "projection_experience_id": projection_experience_id,
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceOIGI):
            return value
        return ProjectionExperienceOIGI.validate_invocation_value(value)


class ProjectionExperienceOIGICreateNodeClassIdentityInput(BaseModel):
    projection_experience_node_identity_id: UUID
    class_instance_identity_id: UUID
    key: str


class ProjectionExperienceOIGICreateNodeClassIdentityOutput(BaseModel):
    value: ProjectionExperienceNodeClassIdentity


class ProjectionExperienceOIGICreateNodeClassIdentityEdgeInput(BaseModel):
    parent_node_class_identity_id: UUID
    child_node_class_identity_id: UUID
    class_instance_relationship_identity_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceOIGICreateNodeClassIdentityEdgeOutput(BaseModel):
    value: ProjectionExperienceNodeClassIdentityEdge


class ProjectionExperienceOIGIBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_oigis"
    )
    object_instance_graph_identity_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceOIGIBuildViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceOIGI


FUNCTIONS = {
    "ProjectionExperienceOIGI": {
        "create_node_class_identity": {
            "canonical": {
                "name": "create_node_class_identity",
                "description": "Attach one semantic ProjectionExperienceNodeIdentity -> ClassInstanceIdentity anchor.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceOIGICreateNodeClassIdentityInput,
            "output": ProjectionExperienceOIGICreateNodeClassIdentityOutput,
        },
        "create_node_class_identity_edge": {
            "canonical": {
                "name": "create_node_class_identity_edge",
                "description": "Attach one explicit parent->child edge under this ProjectionExperienceOIGI.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceOIGICreateNodeClassIdentityEdgeInput,
            "output": ProjectionExperienceOIGICreateNodeClassIdentityEdgeOutput,
        },
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create deterministic ProjectionExperienceOIGI.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceOIGIBuildViaProjectionExperienceInput,
            "output": ProjectionExperienceOIGIBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceOIGI",
    "ProjectionExperienceOIGICreateNodeClassIdentityInput",
    "ProjectionExperienceOIGICreateNodeClassIdentityOutput",
    "ProjectionExperienceOIGICreateNodeClassIdentityEdgeInput",
    "ProjectionExperienceOIGICreateNodeClassIdentityEdgeOutput",
    "ProjectionExperienceOIGIBuildViaProjectionExperienceInput",
    "ProjectionExperienceOIGIBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
