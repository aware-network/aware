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
    from aware_interface_ontology.interface.window_config import WindowConfig


class InterfaceConfigWindowConfig(ORMModel):
    # Relationships
    window_config: WindowConfig | None = Field(default=None)

    # Foreign Keys
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interface_config_window_configs")
    window_config_id: UUID = Field(description="Foreign key for InterfaceConfigWindowConfig.window_config")

    @classmethod
    async def build_via_interface_config(
        cls, interface_config_id: UUID, window_config_id: UUID
    ) -> InterfaceConfigWindowConfig:
        """
        Create one deterministic InterfaceConfig↔WindowConfig composition join.

        Contract:
        - `WindowConfig` stays standalone Interface-side window namespace identity.
        - `InterfaceConfigWindowConfig` is the explicit composition rail for one interface package/config.
        - Pane placement remains section-scoped through pane/view/section agreements, not through this join.
        """

        payload = {"interface_config_id": interface_config_id, "window_config_id": window_config_id}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceConfigWindowConfig):
            return value
        return InterfaceConfigWindowConfig.validate_invocation_value(value)


class InterfaceConfigWindowConfigBuildViaInterfaceConfigInput(BaseModel):
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interface_config_window_configs")
    window_config_id: UUID


class InterfaceConfigWindowConfigBuildViaInterfaceConfigOutput(BaseModel):
    value: InterfaceConfigWindowConfig


FUNCTIONS = {
    "InterfaceConfigWindowConfig": {
        "build_via_interface_config": {
            "canonical": {
                "name": "build_via_interface_config",
                "description": "Create one deterministic InterfaceConfig↔WindowConfig composition join.\n\nContract:\n- `WindowConfig` stays standalone Interface-side window namespace identity.\n- `InterfaceConfigWindowConfig` is the explicit composition rail for one interface package/config.\n- Pane placement remains section-scoped through pane/view/section agreements, not through this join.",
                "is_constructor": True,
            },
            "input": InterfaceConfigWindowConfigBuildViaInterfaceConfigInput,
            "output": InterfaceConfigWindowConfigBuildViaInterfaceConfigOutput,
        },
    },
}

__all__ = [
    "InterfaceConfigWindowConfig",
    "InterfaceConfigWindowConfigBuildViaInterfaceConfigInput",
    "InterfaceConfigWindowConfigBuildViaInterfaceConfigOutput",
    "FUNCTIONS",
]
