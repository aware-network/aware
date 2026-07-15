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
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph


class ApiGraphProjection(ORMModel):
    # Relationships
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_projections")
    object_projection_graph_id: UUID = Field(description="Foreign key for ApiGraphProjection.object_projection_graph")

    @classmethod
    async def create_via_api_graph(
        cls, api_graph_id: UUID, object_projection_graph_id: UUID, description: str | None = None
    ) -> ApiGraphProjection:
        """Create deterministic graph-scoped projection bridge."""

        payload = {
            "api_graph_id": api_graph_id,
            "object_projection_graph_id": object_projection_graph_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiGraphProjection):
            return value
        return ApiGraphProjection.validate_invocation_value(value)


class ApiGraphProjectionCreateViaApiGraphInput(BaseModel):
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_projections")
    object_projection_graph_id: UUID
    description: str | None = Field(default=None)


class ApiGraphProjectionCreateViaApiGraphOutput(BaseModel):
    value: ApiGraphProjection


FUNCTIONS = {
    "ApiGraphProjection": {
        "create_via_api_graph": {
            "canonical": {
                "name": "create_via_api_graph",
                "description": "Create deterministic graph-scoped projection bridge.",
                "is_constructor": True,
            },
            "input": ApiGraphProjectionCreateViaApiGraphInput,
            "output": ApiGraphProjectionCreateViaApiGraphOutput,
        },
    },
}

__all__ = [
    "ApiGraphProjection",
    "ApiGraphProjectionCreateViaApiGraphInput",
    "ApiGraphProjectionCreateViaApiGraphOutput",
    "FUNCTIONS",
]
