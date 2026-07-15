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
    from aware_experience_ontology.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )
    from aware_experience_ontology.projection.projection_experience_node_identity_edge import (
        ProjectionExperienceNodeIdentityEdge,
    )


class ProjectionExperienceGraphIdentityEdge(ORMModel):
    """
    Graph occurrence parent->child edge under ProjectionExperienceGraph.
    Contract:
    - Encodes graph occurrence traversal using parent/child ProjectionExperienceGraphIdentity.
    - Requires a semantic ProjectionExperienceNodeIdentityEdge contract boundary.
    """

    # Relationships
    child_projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(
        default=None, exclude=True
    )
    parent_projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(
        default=None, exclude=True
    )
    projection_experience_node_identity_edge: ProjectionExperienceNodeIdentityEdge | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_graph_identity_edges"
    )
    child_projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityEdge.child_projection_experience_graph_identity"
    )
    parent_projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityEdge.parent_projection_experience_graph_identity"
    )
    projection_experience_node_identity_edge_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraphIdentityEdge.projection_experience_node_identity_edge"
    )

    @classmethod
    async def build_via_projection_experience_graph(
        cls,
        projection_experience_graph_id: UUID,
        parent_projection_experience_graph_identity_id: UUID,
        child_projection_experience_graph_identity_id: UUID,
        projection_experience_node_identity_edge_id: UUID,
        key: str | None = None,
    ) -> ProjectionExperienceGraphIdentityEdge:
        """Create deterministic ProjectionExperienceGraphIdentityEdge."""

        payload = {
            "projection_experience_graph_id": projection_experience_graph_id,
            "parent_projection_experience_graph_identity_id": parent_projection_experience_graph_identity_id,
            "child_projection_experience_graph_identity_id": child_projection_experience_graph_identity_id,
            "projection_experience_node_identity_edge_id": projection_experience_node_identity_edge_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceGraphIdentityEdge):
            return value
        return ProjectionExperienceGraphIdentityEdge.validate_invocation_value(value)


class ProjectionExperienceGraphIdentityEdgeBuildViaProjectionExperienceGraphInput(BaseModel):
    projection_experience_graph_id: UUID = Field(
        description="Foreign key for ProjectionExperienceGraph.projection_experience_graph_identity_edges"
    )
    parent_projection_experience_graph_identity_id: UUID
    child_projection_experience_graph_identity_id: UUID
    projection_experience_node_identity_edge_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceGraphIdentityEdgeBuildViaProjectionExperienceGraphOutput(BaseModel):
    value: ProjectionExperienceGraphIdentityEdge


FUNCTIONS = {
    "ProjectionExperienceGraphIdentityEdge": {
        "build_via_projection_experience_graph": {
            "canonical": {
                "name": "build_via_projection_experience_graph",
                "description": "Create deterministic ProjectionExperienceGraphIdentityEdge.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceGraphIdentityEdgeBuildViaProjectionExperienceGraphInput,
            "output": ProjectionExperienceGraphIdentityEdgeBuildViaProjectionExperienceGraphOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceGraphIdentityEdge",
    "ProjectionExperienceGraphIdentityEdgeBuildViaProjectionExperienceGraphInput",
    "ProjectionExperienceGraphIdentityEdgeBuildViaProjectionExperienceGraphOutput",
    "FUNCTIONS",
]
