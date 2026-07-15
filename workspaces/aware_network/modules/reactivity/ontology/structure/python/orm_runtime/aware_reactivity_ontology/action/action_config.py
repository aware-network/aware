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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint


class ActionConfig(ORMModel):
    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)

    # Attributes
    action_schema: JsonObject = Field(
        default_factory=JsonObject,
        description="Deprecated compatibility schema mirror.\nSchema authority belongs to Meta ClassConfig and API endpoint\nrequest/response/stream contracts. New action rail code must resolve\ntyped contracts through Experience bindings and `InlineValueInstance`\npayload evidence, not this JSON attribute.",
    )
    action_type: str
    allowed_roles: list[str] = Field(default_factory=list)
    description: str
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    name: str
    require_authentication: bool = Field(default=True)

    # Foreign Keys
    api_capability_endpoint_id: UUID = Field(description="Foreign key for ActionConfig.api_capability_endpoint")

    @classmethod
    async def create(
        cls,
        name: str,
        description: str,
        api_capability_endpoint_id: UUID,
        action_type: str,
        is_enabled: bool = True,
        is_system: bool = False,
        require_authentication: bool = True,
        allowed_roles: list[str] = [],
        action_schema: JsonObject = {},
    ) -> ActionConfig:
        """
        Create a canonical action policy root.

        Contract:
        - `api_capability_endpoint` is the required 1:1 API contract anchor
          for this action. Experience may activate/refine this contract by
          scenario or role, but must not redirect it to another endpoint.
        - `action_schema` is deprecated compatibility metadata only.
        - Request value truth is created once at `ApiCall.request_model`;
          Reactivity carries decision/lifecycle evidence only.
        """

        payload = {
            "name": name,
            "description": description,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "action_type": action_type,
            "is_enabled": is_enabled,
            "is_system": is_system,
            "require_authentication": require_authentication,
            "allowed_roles": allowed_roles,
            "action_schema": action_schema,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActionConfig):
            return value
        return ActionConfig.validate_invocation_value(value)


class ActionConfigCreateInput(BaseModel):
    name: str
    description: str
    api_capability_endpoint_id: UUID
    action_type: str
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    require_authentication: bool = Field(default=True)
    allowed_roles: list[str] = Field(default_factory=list)
    action_schema: JsonObject = Field(default_factory=JsonObject)


class ActionConfigCreateOutput(BaseModel):
    value: ActionConfig


FUNCTIONS = {
    "ActionConfig": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Create a canonical action policy root.\n\nContract:\n- `api_capability_endpoint` is the required 1:1 API contract anchor\n  for this action. Experience may activate/refine this contract by\n  scenario or role, but must not redirect it to another endpoint.\n- `action_schema` is deprecated compatibility metadata only.\n- Request value truth is created once at `ApiCall.request_model`;\n  Reactivity carries decision/lifecycle evidence only.",
                "is_constructor": True,
            },
            "input": ActionConfigCreateInput,
            "output": ActionConfigCreateOutput,
        },
    },
}

__all__ = [
    "ActionConfig",
    "ActionConfigCreateInput",
    "ActionConfigCreateOutput",
    "FUNCTIONS",
]
