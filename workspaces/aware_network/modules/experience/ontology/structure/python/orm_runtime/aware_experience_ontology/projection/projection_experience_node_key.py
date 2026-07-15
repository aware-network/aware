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
    from aware_meta_ontology.graph.projection.object_projection_graph_node_key import ObjectProjectionGraphNodeKey


class ProjectionExperienceNodeKey(ORMModel):
    """
    ProjectionExperience node key compatibility wrapper.
    Contract:
    - Declares one deterministic ProjectionKey consumer row under ProjectionExperienceNode.
    - Canonical key schema is owned by Meta `ObjectProjectionGraphNodeKey`.
    """

    # Relationships
    object_projection_graph_node_key: ObjectProjectionGraphNodeKey | None = Field(default=None, exclude=True)

    # Foreign Keys
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.projection_experience_node_keys"
    )
    object_projection_graph_node_key_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeKey.object_projection_graph_node_key"
    )

    @classmethod
    async def build_via_projection_experience_node(
        cls, projection_experience_node_id: UUID, object_projection_graph_node_key_id: UUID
    ) -> ProjectionExperienceNodeKey:
        """Create deterministic ProjectionExperienceNodeKey compatibility edge."""

        payload = {
            "projection_experience_node_id": projection_experience_node_id,
            "object_projection_graph_node_key_id": object_projection_graph_node_key_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_node", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceNodeKey):
            return value
        return ProjectionExperienceNodeKey.validate_invocation_value(value)


class ProjectionExperienceNodeKeyBuildViaProjectionExperienceNodeInput(BaseModel):
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNode.projection_experience_node_keys"
    )
    object_projection_graph_node_key_id: UUID


class ProjectionExperienceNodeKeyBuildViaProjectionExperienceNodeOutput(BaseModel):
    value: ProjectionExperienceNodeKey


FUNCTIONS = {
    "ProjectionExperienceNodeKey": {
        "build_via_projection_experience_node": {
            "canonical": {
                "name": "build_via_projection_experience_node",
                "description": "Create deterministic ProjectionExperienceNodeKey compatibility edge.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceNodeKeyBuildViaProjectionExperienceNodeInput,
            "output": ProjectionExperienceNodeKeyBuildViaProjectionExperienceNodeOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceNodeKey",
    "ProjectionExperienceNodeKeyBuildViaProjectionExperienceNodeInput",
    "ProjectionExperienceNodeKeyBuildViaProjectionExperienceNodeOutput",
    "FUNCTIONS",
]
