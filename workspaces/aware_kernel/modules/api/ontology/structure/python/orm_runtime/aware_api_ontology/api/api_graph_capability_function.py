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
    from aware_api_ontology.api.api_graph_function import ApiGraphFunction


class ApiGraphCapabilityFunction(ORMModel):
    # Relationships
    api_graph_function: ApiGraphFunction | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_capability_id: UUID = Field(
        description="Foreign key for ApiGraphCapability.api_graph_capability_functions"
    )
    api_graph_function_id: UUID = Field(description="Foreign key for ApiGraphCapabilityFunction.api_graph_function")

    @classmethod
    async def create_via_api_graph_capability(
        cls, api_graph_capability_id: UUID, name: str, api_graph_function_id: UUID, description: str | None = None
    ) -> ApiGraphCapabilityFunction:
        """Create one named graph-scoped capability function bound to one ApiGraphFunction."""

        payload = {
            "api_graph_capability_id": api_graph_capability_id,
            "name": name,
            "api_graph_function_id": api_graph_function_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_api_graph_capability", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiGraphCapabilityFunction):
            return value
        return ApiGraphCapabilityFunction.validate_invocation_value(value)


class ApiGraphCapabilityFunctionCreateViaApiGraphCapabilityInput(BaseModel):
    api_graph_capability_id: UUID = Field(
        description="Foreign key for ApiGraphCapability.api_graph_capability_functions"
    )
    name: str
    api_graph_function_id: UUID
    description: str | None = Field(default=None)


class ApiGraphCapabilityFunctionCreateViaApiGraphCapabilityOutput(BaseModel):
    value: ApiGraphCapabilityFunction


FUNCTIONS = {
    "ApiGraphCapabilityFunction": {
        "create_via_api_graph_capability": {
            "canonical": {
                "name": "create_via_api_graph_capability",
                "description": "Create one named graph-scoped capability function bound to one ApiGraphFunction.",
                "is_constructor": True,
            },
            "input": ApiGraphCapabilityFunctionCreateViaApiGraphCapabilityInput,
            "output": ApiGraphCapabilityFunctionCreateViaApiGraphCapabilityOutput,
        },
    },
}

__all__ = [
    "ApiGraphCapabilityFunction",
    "ApiGraphCapabilityFunctionCreateViaApiGraphCapabilityInput",
    "ApiGraphCapabilityFunctionCreateViaApiGraphCapabilityOutput",
    "FUNCTIONS",
]
