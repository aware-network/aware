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
    from aware_experience_ontology.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )
    from aware_experience_ontology.projection.projection_experience_graph_identity_edge import (
        ProjectionExperienceGraphIdentityEdge,
    )
    from aware_experience_ontology.projection.projection_experience_node_identity_edge import (
        ProjectionExperienceNodeIdentityEdge,
    )


class ProjectionExperienceGraph(ORMModel):
    """
    ProjectionExperience graph topology contract.
    Contract:
    - Owns deterministic topology composition over ProjectionExperienceNodeIdentity.
    - API/profile/value bindings are intentionally out of scope.
    """

    # Relationships
    projection_experience_graph_identities: list[ProjectionExperienceGraphIdentity] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_graph_identity_edges: list[ProjectionExperienceGraphIdentityEdge] = Field(
        default_factory=list, exclude=True
    )
    projection_experience_node_identity_edges: list[ProjectionExperienceNodeIdentityEdge] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    name: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_graphs"
    )

    async def create_identity(
        self, projection_experience_node_identity_id: UUID, key: str, is_root: bool = False
    ) -> ProjectionExperienceGraphIdentity:
        """Attach one graph occurrence identity bound to one ProjectionExperienceNodeIdentity."""

        payload = {
            "projection_experience_node_identity_id": projection_experience_node_identity_id,
            "key": key,
            "is_root": is_root,
        }
        result = await invoke_instance(orm_model=self, function_name="create_identity", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_graph_identity import (
            ProjectionExperienceGraphIdentity,
        )

        if isinstance(value, ProjectionExperienceGraphIdentity):
            return value
        return ProjectionExperienceGraphIdentity.validate_invocation_value(value)

    async def create_node_identity_edge(
        self,
        parent_projection_experience_node_identity_id: UUID,
        child_projection_experience_node_identity_id: UUID,
        key: str | None = None,
    ) -> ProjectionExperienceNodeIdentityEdge:
        """Attach one semantic parent->child node identity edge contract."""

        payload = {
            "parent_projection_experience_node_identity_id": parent_projection_experience_node_identity_id,
            "child_projection_experience_node_identity_id": child_projection_experience_node_identity_id,
            "key": key,
        }
        result = await invoke_instance(orm_model=self, function_name="create_node_identity_edge", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_node_identity_edge import (
            ProjectionExperienceNodeIdentityEdge,
        )

        if isinstance(value, ProjectionExperienceNodeIdentityEdge):
            return value
        return ProjectionExperienceNodeIdentityEdge.validate_invocation_value(value)

    async def create_graph_identity_edge(
        self,
        parent_projection_experience_graph_identity_id: UUID,
        child_projection_experience_graph_identity_id: UUID,
        projection_experience_node_identity_edge_id: UUID,
        key: str | None = None,
    ) -> ProjectionExperienceGraphIdentityEdge:
        """Attach one graph occurrence edge bound to one semantic node identity edge contract."""

        payload = {
            "parent_projection_experience_graph_identity_id": parent_projection_experience_graph_identity_id,
            "child_projection_experience_graph_identity_id": child_projection_experience_graph_identity_id,
            "projection_experience_node_identity_edge_id": projection_experience_node_identity_edge_id,
            "key": key,
        }
        result = await invoke_instance(orm_model=self, function_name="create_graph_identity_edge", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_graph_identity_edge import (
            ProjectionExperienceGraphIdentityEdge,
        )

        if isinstance(value, ProjectionExperienceGraphIdentityEdge):
            return value
        return ProjectionExperienceGraphIdentityEdge.validate_invocation_value(value)

    @classmethod
    async def create_via_projection_experience(
        cls, projection_experience_id: UUID, name: str
    ) -> ProjectionExperienceGraph:
        """Create deterministic ProjectionExperienceGraph under one ProjectionExperience."""

        payload = {"projection_experience_id": projection_experience_id, "name": name}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceGraph):
            return value
        return ProjectionExperienceGraph.validate_invocation_value(value)


class ProjectionExperienceGraphCreateIdentityInput(BaseModel):
    projection_experience_node_identity_id: UUID
    key: str
    is_root: bool = Field(default=False)


class ProjectionExperienceGraphCreateIdentityOutput(BaseModel):
    value: ProjectionExperienceGraphIdentity


class ProjectionExperienceGraphCreateNodeIdentityEdgeInput(BaseModel):
    parent_projection_experience_node_identity_id: UUID
    child_projection_experience_node_identity_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceGraphCreateNodeIdentityEdgeOutput(BaseModel):
    value: ProjectionExperienceNodeIdentityEdge


class ProjectionExperienceGraphCreateGraphIdentityEdgeInput(BaseModel):
    parent_projection_experience_graph_identity_id: UUID
    child_projection_experience_graph_identity_id: UUID
    projection_experience_node_identity_edge_id: UUID
    key: str | None = Field(default=None)


class ProjectionExperienceGraphCreateGraphIdentityEdgeOutput(BaseModel):
    value: ProjectionExperienceGraphIdentityEdge


class ProjectionExperienceGraphCreateViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_graphs"
    )
    name: str


class ProjectionExperienceGraphCreateViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceGraph


FUNCTIONS = {
    "ProjectionExperienceGraph": {
        "create_identity": {
            "canonical": {
                "name": "create_identity",
                "description": "Attach one graph occurrence identity bound to one ProjectionExperienceNodeIdentity.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceGraphCreateIdentityInput,
            "output": ProjectionExperienceGraphCreateIdentityOutput,
        },
        "create_node_identity_edge": {
            "canonical": {
                "name": "create_node_identity_edge",
                "description": "Attach one semantic parent->child node identity edge contract.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceGraphCreateNodeIdentityEdgeInput,
            "output": ProjectionExperienceGraphCreateNodeIdentityEdgeOutput,
        },
        "create_graph_identity_edge": {
            "canonical": {
                "name": "create_graph_identity_edge",
                "description": "Attach one graph occurrence edge bound to one semantic node identity edge contract.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceGraphCreateGraphIdentityEdgeInput,
            "output": ProjectionExperienceGraphCreateGraphIdentityEdgeOutput,
        },
        "create_via_projection_experience": {
            "canonical": {
                "name": "create_via_projection_experience",
                "description": "Create deterministic ProjectionExperienceGraph under one ProjectionExperience.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceGraphCreateViaProjectionExperienceInput,
            "output": ProjectionExperienceGraphCreateViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceGraph",
    "ProjectionExperienceGraphCreateIdentityInput",
    "ProjectionExperienceGraphCreateIdentityOutput",
    "ProjectionExperienceGraphCreateNodeIdentityEdgeInput",
    "ProjectionExperienceGraphCreateNodeIdentityEdgeOutput",
    "ProjectionExperienceGraphCreateGraphIdentityEdgeInput",
    "ProjectionExperienceGraphCreateGraphIdentityEdgeOutput",
    "ProjectionExperienceGraphCreateViaProjectionExperienceInput",
    "ProjectionExperienceGraphCreateViaProjectionExperienceOutput",
    "FUNCTIONS",
]
