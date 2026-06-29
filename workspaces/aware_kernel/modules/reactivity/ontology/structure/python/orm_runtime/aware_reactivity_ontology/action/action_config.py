from __future__ import annotations

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


class ActionConfig(ORMModel):
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

    @classmethod
    async def create(
        cls,
        name: str,
        description: str,
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
        - `action_schema` is deprecated compatibility metadata only.
        - New typed action contracts resolve through Experience invocation
          bindings and Meta `InlineValueInstance` payload evidence.
        """

        payload = {
            "name": name,
            "description": description,
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
                "description": "Create a canonical action policy root.\n\nContract:\n- `action_schema` is deprecated compatibility metadata only.\n- New typed action contracts resolve through Experience invocation\n  bindings and Meta `InlineValueInstance` payload evidence.",
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
