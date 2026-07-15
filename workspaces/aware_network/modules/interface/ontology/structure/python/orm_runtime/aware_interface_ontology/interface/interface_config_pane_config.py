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
    from aware_interface_ontology.interface.interface_config_pane_config_section_config import (
        InterfaceConfigPaneConfigSectionConfig,
    )
    from aware_interface_ontology.interface.pane_config import PaneConfig


class InterfaceConfigPaneConfig(ORMModel):
    # Relationships
    pane_config: PaneConfig | None = Field(default=None)
    section_mounts: list[InterfaceConfigPaneConfigSectionConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    narrative_key: str | None = Field(default=None)

    # Foreign Keys
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interface_config_pane_configs")
    pane_config_id: UUID = Field(description="Foreign key for InterfaceConfigPaneConfig.pane_config")

    async def add_section_mount(self, layout_config_section_config_id: UUID) -> InterfaceConfigPaneConfigSectionConfig:
        """Attach one Interface-scoped section mount for one standalone PaneConfig pane-view adapter."""

        payload = {"layout_config_section_config_id": layout_config_section_config_id}
        result = await invoke_instance(orm_model=self, function_name="add_section_mount", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.interface_config_pane_config_section_config import (
            InterfaceConfigPaneConfigSectionConfig,
        )

        if isinstance(value, InterfaceConfigPaneConfigSectionConfig):
            return value
        return InterfaceConfigPaneConfigSectionConfig.validate_invocation_value(value)

    async def set_narrative_key(self, narrative_key: str | None = None) -> InterfaceConfigPaneConfig:
        """
        Update the Interface-scoped pane narrative key on the join itself.

        InterfaceConfig must call this public method instead of mutating an
        existing join directly, preserving runtime mutation-boundary ownership.
        """

        payload = {"narrative_key": narrative_key}
        result = await invoke_instance(orm_model=self, function_name="set_narrative_key", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceConfigPaneConfig):
            return value
        return InterfaceConfigPaneConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_interface_config(
        cls, interface_config_id: UUID, pane_config_id: UUID, narrative_key: str | None = None
    ) -> InterfaceConfigPaneConfig:
        """
        Create one deterministic InterfaceConfig↔PaneConfig composition join.

        Contract:
        - `PaneConfig` stays standalone semantic pane identity.
        - `InterfaceConfigPaneConfig` is the explicit composition rail for one interface package/config.
        - Interface-scoped mount policy belongs under this join, not under the standalone pane semantic
        rail.
        """

        payload = {
            "interface_config_id": interface_config_id,
            "pane_config_id": pane_config_id,
            "narrative_key": narrative_key,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_interface_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceConfigPaneConfig):
            return value
        return InterfaceConfigPaneConfig.validate_invocation_value(value)


class InterfaceConfigPaneConfigAddSectionMountInput(BaseModel):
    layout_config_section_config_id: UUID


class InterfaceConfigPaneConfigAddSectionMountOutput(BaseModel):
    value: InterfaceConfigPaneConfigSectionConfig


class InterfaceConfigPaneConfigSetNarrativeKeyInput(BaseModel):
    narrative_key: str | None = Field(default=None)


class InterfaceConfigPaneConfigSetNarrativeKeyOutput(BaseModel):
    value: InterfaceConfigPaneConfig


class InterfaceConfigPaneConfigBuildViaInterfaceConfigInput(BaseModel):
    interface_config_id: UUID = Field(description="Foreign key for InterfaceConfig.interface_config_pane_configs")
    pane_config_id: UUID
    narrative_key: str | None = Field(default=None)


class InterfaceConfigPaneConfigBuildViaInterfaceConfigOutput(BaseModel):
    value: InterfaceConfigPaneConfig


FUNCTIONS = {
    "InterfaceConfigPaneConfig": {
        "add_section_mount": {
            "canonical": {
                "name": "add_section_mount",
                "description": "Attach one Interface-scoped section mount for one standalone PaneConfig pane-view adapter.",
                "is_constructor": False,
            },
            "input": InterfaceConfigPaneConfigAddSectionMountInput,
            "output": InterfaceConfigPaneConfigAddSectionMountOutput,
        },
        "set_narrative_key": {
            "canonical": {
                "name": "set_narrative_key",
                "description": "Update the Interface-scoped pane narrative key on the join itself.\n\nInterfaceConfig must call this public method instead of mutating an\nexisting join directly, preserving runtime mutation-boundary ownership.",
                "is_constructor": False,
            },
            "input": InterfaceConfigPaneConfigSetNarrativeKeyInput,
            "output": InterfaceConfigPaneConfigSetNarrativeKeyOutput,
        },
        "build_via_interface_config": {
            "canonical": {
                "name": "build_via_interface_config",
                "description": "Create one deterministic InterfaceConfig↔PaneConfig composition join.\n\nContract:\n- `PaneConfig` stays standalone semantic pane identity.\n- `InterfaceConfigPaneConfig` is the explicit composition rail for one interface package/config.\n- Interface-scoped mount policy belongs under this join, not under the standalone pane semantic rail.",
                "is_constructor": True,
            },
            "input": InterfaceConfigPaneConfigBuildViaInterfaceConfigInput,
            "output": InterfaceConfigPaneConfigBuildViaInterfaceConfigOutput,
        },
    },
}

__all__ = [
    "InterfaceConfigPaneConfig",
    "InterfaceConfigPaneConfigAddSectionMountInput",
    "InterfaceConfigPaneConfigAddSectionMountOutput",
    "InterfaceConfigPaneConfigSetNarrativeKeyInput",
    "InterfaceConfigPaneConfigSetNarrativeKeyOutput",
    "InterfaceConfigPaneConfigBuildViaInterfaceConfigInput",
    "InterfaceConfigPaneConfigBuildViaInterfaceConfigOutput",
    "FUNCTIONS",
]
