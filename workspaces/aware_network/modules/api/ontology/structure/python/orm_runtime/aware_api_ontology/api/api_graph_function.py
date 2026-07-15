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
    from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig


class ApiGraphFunction(ORMModel):
    # Relationships
    class_config_function_config: ClassConfigFunctionConfig | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_functions")
    class_config_function_config_id: UUID = Field(
        description="Foreign key for ApiGraphFunction.class_config_function_config"
    )

    @classmethod
    async def create_via_api_graph(
        cls, api_graph_id: UUID, class_config_function_config_id: UUID, description: str | None = None
    ) -> ApiGraphFunction:
        """Create one standalone API-owned callable graph target."""

        payload = {
            "api_graph_id": api_graph_id,
            "class_config_function_config_id": class_config_function_config_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiGraphFunction):
            return value
        return ApiGraphFunction.validate_invocation_value(value)


class ApiGraphFunctionCreateViaApiGraphInput(BaseModel):
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_functions")
    class_config_function_config_id: UUID
    description: str | None = Field(default=None)


class ApiGraphFunctionCreateViaApiGraphOutput(BaseModel):
    value: ApiGraphFunction


FUNCTIONS = {
    "ApiGraphFunction": {
        "create_via_api_graph": {
            "canonical": {
                "name": "create_via_api_graph",
                "description": "Create one standalone API-owned callable graph target.",
                "is_constructor": True,
            },
            "input": ApiGraphFunctionCreateViaApiGraphInput,
            "output": ApiGraphFunctionCreateViaApiGraphOutput,
        },
    },
}

__all__ = [
    "ApiGraphFunction",
    "ApiGraphFunctionCreateViaApiGraphInput",
    "ApiGraphFunctionCreateViaApiGraphOutput",
    "FUNCTIONS",
]
