from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class NetworkNodeConfig(ORMModel):
    # Attributes
    name: str
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, name: str, description: str | None = None) -> NetworkNodeConfig:
        """
        Create the canonical Network-owned semantic config root for a Node package.

        Notes:
        - `NetworkNodeConfig` is keyed by semantic node package identity, not by bootstrap secrets.
        - This root stays minimal and node-owned.
        - Workspace/deploy own hosted composition and runtime-target selection above this rail.
        """

        payload = {"name": name, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodeConfig):
            return value
        return NetworkNodeConfig.validate_invocation_value(value)


class NetworkNodeConfigBuildInput(BaseModel):
    name: str
    description: str | None = Field(default=None)


class NetworkNodeConfigBuildOutput(BaseModel):
    value: NetworkNodeConfig


FUNCTIONS = {
    "NetworkNodeConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical Network-owned semantic config root for a Node package.\n\nNotes:\n- `NetworkNodeConfig` is keyed by semantic node package identity, not by bootstrap secrets.\n- This root stays minimal and node-owned.\n- Workspace/deploy own hosted composition and runtime-target selection above this rail.",
                "is_constructor": True,
            },
            "input": NetworkNodeConfigBuildInput,
            "output": NetworkNodeConfigBuildOutput,
        },
    },
}

__all__ = [
    "NetworkNodeConfig",
    "NetworkNodeConfigBuildInput",
    "NetworkNodeConfigBuildOutput",
    "FUNCTIONS",
]
