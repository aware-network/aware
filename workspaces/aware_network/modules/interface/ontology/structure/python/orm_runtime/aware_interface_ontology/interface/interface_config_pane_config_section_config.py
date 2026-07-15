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
    from aware_attention_ontology.layout.layout_config_section_config import LayoutConfigSectionConfig


class InterfaceConfigPaneConfigSectionConfig(ORMModel):
    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    interface_config_pane_config_id: UUID = Field(
        description="Foreign key for InterfaceConfigPaneConfig.section_mounts"
    )
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for InterfaceConfigPaneConfigSectionConfig.layout_config_section_config"
    )

    @classmethod
    async def build_via_interface_config_pane_config(
        cls, interface_config_pane_config_id: UUID, layout_config_section_config_id: UUID
    ) -> InterfaceConfigPaneConfigSectionConfig:
        """
        Create one deterministic Interface-scoped mount binding between this InterfaceConfigPaneConfig
        pane-view adapter and one layout section.
        """

        payload = {
            "interface_config_pane_config_id": interface_config_pane_config_id,
            "layout_config_section_config_id": layout_config_section_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_interface_config_pane_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, InterfaceConfigPaneConfigSectionConfig):
            return value
        return InterfaceConfigPaneConfigSectionConfig.validate_invocation_value(value)


class InterfaceConfigPaneConfigSectionConfigBuildViaInterfaceConfigPaneConfigInput(BaseModel):
    interface_config_pane_config_id: UUID = Field(
        description="Foreign key for InterfaceConfigPaneConfig.section_mounts"
    )
    layout_config_section_config_id: UUID


class InterfaceConfigPaneConfigSectionConfigBuildViaInterfaceConfigPaneConfigOutput(BaseModel):
    value: InterfaceConfigPaneConfigSectionConfig


FUNCTIONS = {
    "InterfaceConfigPaneConfigSectionConfig": {
        "build_via_interface_config_pane_config": {
            "canonical": {
                "name": "build_via_interface_config_pane_config",
                "description": "Create one deterministic Interface-scoped mount binding between this InterfaceConfigPaneConfig pane-view adapter and one layout section.",
                "is_constructor": True,
            },
            "input": InterfaceConfigPaneConfigSectionConfigBuildViaInterfaceConfigPaneConfigInput,
            "output": InterfaceConfigPaneConfigSectionConfigBuildViaInterfaceConfigPaneConfigOutput,
        },
    },
}

__all__ = [
    "InterfaceConfigPaneConfigSectionConfig",
    "InterfaceConfigPaneConfigSectionConfigBuildViaInterfaceConfigPaneConfigInput",
    "InterfaceConfigPaneConfigSectionConfigBuildViaInterfaceConfigPaneConfigOutput",
    "FUNCTIONS",
]
