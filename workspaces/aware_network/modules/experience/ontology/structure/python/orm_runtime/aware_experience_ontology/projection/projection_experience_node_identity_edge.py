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
    from aware_experience_ontology.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )


class ProjectionExperienceNodeIdentityEdge(ORMModel):
    """
    Semantic parent->child edge between two ProjectionExperienceNodeIdentity anchors.
    Contract:
    - Topology contract for node identities, independent from runtime class-instance edges.
    - Later materialization can instantiate this into ProjectionExperienceNodeClassIdentityEdge.
    """

    # Relationships
    child_projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(
        default=None, exclude=True
    )
    parent_projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_node_identity_edges"
    )
    child_projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeIdentityEdge.child_projection_experience_node_identity"
    )
    parent_projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceNodeIdentityEdge.parent_projection_experience_node_identity"
    )

    @classmethod
    async def build_via_projection_experience_graph(
        cls,
        projection_experience_graph_id: UUID,
        parent_projection_experience_node_identity_id: UUID,
        child_projection_experience_node_identity_id: UUID,
        key: str | None = None,
    ) -> ProjectionExperienceNodeIdentityEdge:
        """Create deterministic ProjectionExperienceNodeIdentityEdge."""

        payload = {
            "projection_experience_graph_id": projection_experience_graph_id,
            "parent_projection_experience_node_identity_id": parent_projection_experience_node_identity_id,
            "child_projection_experience_node_identity_id": child_projection_experience_node_identity_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceNodeIdentityEdge):
            return value
        return ProjectionExperienceNodeIdentityEdge.validate_invocation_value(value)


class ProjectionExperienceNodeIdentityEdgeBuildViaProjectionExperienceGraphInput(BaseModel):
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_node_identity_edges"
    )
    parent_projection_experience_node_identity_id: UUID
    child_projection_experience_node_identity_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceNodeIdentityEdgeBuildViaProjectionExperienceGraphOutput(BaseModel):
    value: ProjectionExperienceNodeIdentityEdge


FUNCTIONS = {
    "ProjectionExperienceNodeIdentityEdge": {
        "build_via_projection_experience_graph": {
            "canonical": {
                "name": "build_via_projection_experience_graph",
                "description": "Create deterministic ProjectionExperienceNodeIdentityEdge.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceNodeIdentityEdgeBuildViaProjectionExperienceGraphInput,
            "output": ProjectionExperienceNodeIdentityEdgeBuildViaProjectionExperienceGraphOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceNodeIdentityEdge",
    "ProjectionExperienceNodeIdentityEdgeBuildViaProjectionExperienceGraphInput",
    "ProjectionExperienceNodeIdentityEdgeBuildViaProjectionExperienceGraphOutput",
    "FUNCTIONS",
]
