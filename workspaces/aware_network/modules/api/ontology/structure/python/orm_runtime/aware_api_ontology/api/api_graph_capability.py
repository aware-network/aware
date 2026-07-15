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
    from aware_api_ontology.api.api_capability import ApiCapability
    from aware_api_ontology.api.api_graph_capability_function import ApiGraphCapabilityFunction


class ApiGraphCapability(ORMModel):
    # Relationships
    api_capability: ApiCapability | None = Field(default=None, exclude=True)
    api_graph_capability_functions: list[ApiGraphCapabilityFunction] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_capabilities")
    api_capability_id: UUID = Field(description="Foreign key for ApiGraphCapability.api_capability")

    async def create_function(
        self, name: str, api_graph_function_id: UUID, description: str | None = None
    ) -> ApiGraphCapabilityFunction:
        """Create one named graph-scoped capability function binding to one ApiGraphFunction."""

        payload = {"name": name, "api_graph_function_id": api_graph_function_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_function", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_graph_capability_function import ApiGraphCapabilityFunction

        if isinstance(value, ApiGraphCapabilityFunction):
            return value
        return ApiGraphCapabilityFunction.validate_invocation_value(value)

    @classmethod
    async def create_via_api_graph(
        cls, api_graph_id: UUID, api_capability_id: UUID, description: str | None = None
    ) -> ApiGraphCapability:
        """Create one graph-scoped binding for one declared ApiCapability."""

        payload = {"api_graph_id": api_graph_id, "api_capability_id": api_capability_id, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiGraphCapability):
            return value
        return ApiGraphCapability.validate_invocation_value(value)


class ApiGraphCapabilityCreateFunctionInput(BaseModel):
    name: str
    api_graph_function_id: UUID
    description: str | None = Field(default=None)


class ApiGraphCapabilityCreateFunctionOutput(BaseModel):
    value: ApiGraphCapabilityFunction


class ApiGraphCapabilityCreateViaApiGraphInput(BaseModel):
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_capabilities")
    api_capability_id: UUID
    description: str | None = Field(default=None)


class ApiGraphCapabilityCreateViaApiGraphOutput(BaseModel):
    value: ApiGraphCapability


FUNCTIONS = {
    "ApiGraphCapability": {
        "create_function": {
            "canonical": {
                "name": "create_function",
                "description": "Create one named graph-scoped capability function binding to one ApiGraphFunction.",
                "is_constructor": False,
            },
            "input": ApiGraphCapabilityCreateFunctionInput,
            "output": ApiGraphCapabilityCreateFunctionOutput,
        },
        "create_via_api_graph": {
            "canonical": {
                "name": "create_via_api_graph",
                "description": "Create one graph-scoped binding for one declared ApiCapability.",
                "is_constructor": True,
            },
            "input": ApiGraphCapabilityCreateViaApiGraphInput,
            "output": ApiGraphCapabilityCreateViaApiGraphOutput,
        },
    },
}

__all__ = [
    "ApiGraphCapability",
    "ApiGraphCapabilityCreateFunctionInput",
    "ApiGraphCapabilityCreateFunctionOutput",
    "ApiGraphCapabilityCreateViaApiGraphInput",
    "ApiGraphCapabilityCreateViaApiGraphOutput",
    "FUNCTIONS",
]
