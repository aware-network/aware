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
    from aware_api_ontology.api.api_graph_capability import ApiGraphCapability
    from aware_api_ontology.api.api_graph_function import ApiGraphFunction
    from aware_api_ontology.api.api_graph_projection import ApiGraphProjection
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


class ApiGraph(ORMModel):
    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None, exclude=True)
    api_graph_functions: list[ApiGraphFunction] = Field(default_factory=list, exclude=True)
    api_graph_projections: list[ApiGraphProjection] = Field(default_factory=list, exclude=True)
    api_graph_capabilities: list[ApiGraphCapability] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_id: UUID = Field(description="Foreign key for Api.api_graphs")
    object_config_graph_id: UUID = Field(description="Foreign key for ApiGraph.object_config_graph")

    async def create_graph_function(
        self, class_config_function_config_id: UUID, description: str | None = None
    ) -> ApiGraphFunction:
        """Create one standalone API graph callable target under this ApiGraph."""

        payload = {"class_config_function_config_id": class_config_function_config_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_graph_function", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_graph_function import ApiGraphFunction

        if isinstance(value, ApiGraphFunction):
            return value
        return ApiGraphFunction.validate_invocation_value(value)

    async def create_graph_projection(
        self, object_projection_graph_id: UUID, description: str | None = None
    ) -> ApiGraphProjection:
        """Create one graph-scoped projection mapping bridge under this ApiGraph."""

        payload = {"object_projection_graph_id": object_projection_graph_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_graph_projection", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_graph_projection import ApiGraphProjection

        if isinstance(value, ApiGraphProjection):
            return value
        return ApiGraphProjection.validate_invocation_value(value)

    async def create_graph_capability(
        self, api_capability_id: UUID, description: str | None = None
    ) -> ApiGraphCapability:
        """Bind one declared ApiCapability to this ApiGraph."""

        payload = {"api_capability_id": api_capability_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_graph_capability", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_graph_capability import ApiGraphCapability

        if isinstance(value, ApiGraphCapability):
            return value
        return ApiGraphCapability.validate_invocation_value(value)

    @classmethod
    async def create_via_api(
        cls, api_id: UUID, object_config_graph_id: UUID, description: str | None = None
    ) -> ApiGraph:
        """Create one deterministic API graph bridge to one target ObjectConfigGraph."""

        payload = {"api_id": api_id, "object_config_graph_id": object_config_graph_id, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiGraph):
            return value
        return ApiGraph.validate_invocation_value(value)


class ApiGraphCreateGraphFunctionInput(BaseModel):
    class_config_function_config_id: UUID
    description: str | None = Field(default=None)


class ApiGraphCreateGraphFunctionOutput(BaseModel):
    value: ApiGraphFunction


class ApiGraphCreateGraphProjectionInput(BaseModel):
    object_projection_graph_id: UUID
    description: str | None = Field(default=None)


class ApiGraphCreateGraphProjectionOutput(BaseModel):
    value: ApiGraphProjection


class ApiGraphCreateGraphCapabilityInput(BaseModel):
    api_capability_id: UUID
    description: str | None = Field(default=None)


class ApiGraphCreateGraphCapabilityOutput(BaseModel):
    value: ApiGraphCapability


class ApiGraphCreateViaApiInput(BaseModel):
    api_id: UUID = Field(description="Foreign key for Api.api_graphs")
    object_config_graph_id: UUID
    description: str | None = Field(default=None)


class ApiGraphCreateViaApiOutput(BaseModel):
    value: ApiGraph


FUNCTIONS = {
    "ApiGraph": {
        "create_graph_function": {
            "canonical": {
                "name": "create_graph_function",
                "description": "Create one standalone API graph callable target under this ApiGraph.",
                "is_constructor": False,
            },
            "input": ApiGraphCreateGraphFunctionInput,
            "output": ApiGraphCreateGraphFunctionOutput,
        },
        "create_graph_projection": {
            "canonical": {
                "name": "create_graph_projection",
                "description": "Create one graph-scoped projection mapping bridge under this ApiGraph.",
                "is_constructor": False,
            },
            "input": ApiGraphCreateGraphProjectionInput,
            "output": ApiGraphCreateGraphProjectionOutput,
        },
        "create_graph_capability": {
            "canonical": {
                "name": "create_graph_capability",
                "description": "Bind one declared ApiCapability to this ApiGraph.",
                "is_constructor": False,
            },
            "input": ApiGraphCreateGraphCapabilityInput,
            "output": ApiGraphCreateGraphCapabilityOutput,
        },
        "create_via_api": {
            "canonical": {
                "name": "create_via_api",
                "description": "Create one deterministic API graph bridge to one target ObjectConfigGraph.",
                "is_constructor": True,
            },
            "input": ApiGraphCreateViaApiInput,
            "output": ApiGraphCreateViaApiOutput,
        },
    },
}

__all__ = [
    "ApiGraph",
    "ApiGraphCreateGraphFunctionInput",
    "ApiGraphCreateGraphFunctionOutput",
    "ApiGraphCreateGraphProjectionInput",
    "ApiGraphCreateGraphProjectionOutput",
    "ApiGraphCreateGraphCapabilityInput",
    "ApiGraphCreateGraphCapabilityOutput",
    "ApiGraphCreateViaApiInput",
    "ApiGraphCreateViaApiOutput",
    "FUNCTIONS",
]
