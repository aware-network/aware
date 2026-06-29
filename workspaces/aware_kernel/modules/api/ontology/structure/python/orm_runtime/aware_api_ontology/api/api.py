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
    from aware_api_ontology.api.api_graph import ApiGraph


class Api(ORMModel):
    # Relationships
    api_graphs: list[ApiGraph] = Field(default_factory=list, exclude=True)
    api_capabilities: list[ApiCapability] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    @classmethod
    async def create(cls, name: str, description: str | None = None) -> Api:
        """Create deterministic public/vendor API identity."""

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Api):
            return value
        return Api.validate_invocation_value(value)

    async def create_api_graph(self, object_config_graph_id: UUID, description: str | None = None) -> ApiGraph:
        """Create one API graph bridge under this Api."""

        payload = {"object_config_graph_id": object_config_graph_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_api_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_graph import ApiGraph

        if isinstance(value, ApiGraph):
            return value
        return ApiGraph.validate_invocation_value(value)

    async def create_capability(self, name: str, description: str | None = None) -> ApiCapability:
        """Create one named reusable API capability contract under this Api identity."""

        payload = {"name": name, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_capability", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability import ApiCapability

        if isinstance(value, ApiCapability):
            return value
        return ApiCapability.validate_invocation_value(value)


class ApiCreateInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class ApiCreateOutput(BaseModel):
    value: Api


class ApiCreateApiGraphInput(BaseModel):
    object_config_graph_id: UUID
    description: str | None = Field(default=None)


class ApiCreateApiGraphOutput(BaseModel):
    value: ApiGraph


class ApiCreateCapabilityInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class ApiCreateCapabilityOutput(BaseModel):
    value: ApiCapability


FUNCTIONS = {
    "Api": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create deterministic public/vendor API identity.",
                "is_constructor": True,
            },
            "input": ApiCreateInput,
            "output": ApiCreateOutput,
        },
        "create_api_graph": {
            "canonical": {
                "name": "create_api_graph",
                "description": "Create one API graph bridge under this Api.",
                "is_constructor": False,
            },
            "input": ApiCreateApiGraphInput,
            "output": ApiCreateApiGraphOutput,
        },
        "create_capability": {
            "canonical": {
                "name": "create_capability",
                "description": "Create one named reusable API capability contract under this Api identity.",
                "is_constructor": False,
            },
            "input": ApiCreateCapabilityInput,
            "output": ApiCreateCapabilityOutput,
        },
    },
}

__all__ = [
    "Api",
    "ApiCreateInput",
    "ApiCreateOutput",
    "ApiCreateApiGraphInput",
    "ApiCreateApiGraphOutput",
    "ApiCreateCapabilityInput",
    "ApiCreateCapabilityOutput",
    "FUNCTIONS",
]
