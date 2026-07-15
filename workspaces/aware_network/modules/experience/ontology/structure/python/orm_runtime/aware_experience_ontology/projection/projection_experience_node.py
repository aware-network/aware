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
    from aware_experience_ontology.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_experience_ontology.projection.projection_experience_node_key import ProjectionExperienceNodeKey
    from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ProjectionExperienceNode(ORMModel):
    """
    ProjectionExperience node contract edge.
    Contract:
    - Anchors one ProjectionExperience to one structural projection node.
    - Owns human-stable identity names for that node.
    - Consumes canonical resolver key schema from Meta `ObjectProjectionGraphNodeKey`.
    """

    # Relationships
    object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    projection_experience_node_identities: list[ProjectionExperienceNodeIdentity] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_node_keys: list[ProjectionExperienceNodeKey] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_nodes"
    )
    object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.object_projection_graph_node"
    )

    async def create_identity(self, key: str) -> ProjectionExperienceNodeIdentity:
        """Attach one human-stable identity under this ProjectionExperienceNode."""

        payload = {"key": key}
        result = await invoke_instance(orm_model=self, function_name="create_identity", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_node_identity import (
            ProjectionExperienceNodeIdentity,
        )

        if isinstance(value, ProjectionExperienceNodeIdentity):
            return value
        return ProjectionExperienceNodeIdentity.validate_invocation_value(value)

    async def add_key(self, object_projection_graph_node_key_id: UUID) -> ProjectionExperienceNodeKey:
        """Attach one canonical ProjectionKey consumer row under this ProjectionExperienceNode."""

        payload = {"object_projection_graph_node_key_id": object_projection_graph_node_key_id}
        result = await invoke_instance(orm_model=self, function_name="add_key", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_node_key import ProjectionExperienceNodeKey

        if isinstance(value, ProjectionExperienceNodeKey):
            return value
        return ProjectionExperienceNodeKey.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience(
        cls, projection_experience_id: UUID, object_projection_graph_node_id: UUID, key: str
    ) -> ProjectionExperienceNode:
        """Create deterministic ProjectionExperienceNode association edge."""

        payload = {
            "projection_experience_id": projection_experience_id,
            "object_projection_graph_node_id": object_projection_graph_node_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceNode):
            return value
        return ProjectionExperienceNode.validate_invocation_value(value)


class ProjectionExperienceNodeCreateIdentityInput(BaseModel):
    key: str


class ProjectionExperienceNodeCreateIdentityOutput(BaseModel):
    value: ProjectionExperienceNodeIdentity


class ProjectionExperienceNodeAddKeyInput(BaseModel):
    object_projection_graph_node_key_id: UUID


class ProjectionExperienceNodeAddKeyOutput(BaseModel):
    value: ProjectionExperienceNodeKey


class ProjectionExperienceNodeBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_nodes"
    )
    object_projection_graph_node_id: UUID
    key: str


class ProjectionExperienceNodeBuildViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceNode


FUNCTIONS = {
    "ProjectionExperienceNode": {
        "create_identity": {
            "canonical": {
                "name": "create_identity",
                "description": "Attach one human-stable identity under this ProjectionExperienceNode.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceNodeCreateIdentityInput,
            "output": ProjectionExperienceNodeCreateIdentityOutput,
        },
        "add_key": {
            "canonical": {
                "name": "add_key",
                "description": "Attach one canonical ProjectionKey consumer row under this ProjectionExperienceNode.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceNodeAddKeyInput,
            "output": ProjectionExperienceNodeAddKeyOutput,
        },
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create deterministic ProjectionExperienceNode association edge.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceNodeBuildViaProjectionExperienceInput,
            "output": ProjectionExperienceNodeBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceNode",
    "ProjectionExperienceNodeCreateIdentityInput",
    "ProjectionExperienceNodeCreateIdentityOutput",
    "ProjectionExperienceNodeAddKeyInput",
    "ProjectionExperienceNodeAddKeyOutput",
    "ProjectionExperienceNodeBuildViaProjectionExperienceInput",
    "ProjectionExperienceNodeBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
