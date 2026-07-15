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
    from aware_attention_ontology.layout.layout_config import LayoutConfig


class WindowConfigLayoutConfig(ORMModel):
    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    is_default: bool = Field(default=False)

    # Foreign Keys
    window_config_id: UUID = Field(description="Foreign key for WindowConfig.layout_configs")
    layout_config_id: UUID = Field(description="Foreign key for WindowConfigLayoutConfig.layout_config")

    async def set_attachment_config(
        self, description: str | None = None, is_default: bool = False
    ) -> WindowConfigLayoutConfig:
        """Update the WindowConfig-scoped layout attachment on the join itself."""

        payload = {"description": description, "is_default": is_default}
        result = await invoke_instance(orm_model=self, function_name="set_attachment_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WindowConfigLayoutConfig):
            return value
        return WindowConfigLayoutConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_window_config(
        cls, window_config_id: UUID, layout_config_id: UUID, description: str | None = None, is_default: bool = False
    ) -> WindowConfigLayoutConfig:
        """Create one deterministic WindowConfig↔LayoutConfig bridge."""

        payload = {
            "window_config_id": window_config_id,
            "layout_config_id": layout_config_id,
            "description": description,
            "is_default": is_default,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_window_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WindowConfigLayoutConfig):
            return value
        return WindowConfigLayoutConfig.validate_invocation_value(value)


class WindowConfigLayoutConfigSetAttachmentConfigInput(BaseModel):
    description: str | None = Field(default=None)
    is_default: bool = Field(default=False)


class WindowConfigLayoutConfigSetAttachmentConfigOutput(BaseModel):
    value: WindowConfigLayoutConfig


class WindowConfigLayoutConfigBuildViaWindowConfigInput(BaseModel):
    window_config_id: UUID = Field(description="Foreign key for WindowConfig.layout_configs")
    layout_config_id: UUID
    description: str | None = Field(default=None)
    is_default: bool = Field(default=False)


class WindowConfigLayoutConfigBuildViaWindowConfigOutput(BaseModel):
    value: WindowConfigLayoutConfig


FUNCTIONS = {
    "WindowConfigLayoutConfig": {
        "set_attachment_config": {
            "canonical": {
                "name": "set_attachment_config",
                "description": "Update the WindowConfig-scoped layout attachment on the join itself.",
                "is_constructor": False,
            },
            "input": WindowConfigLayoutConfigSetAttachmentConfigInput,
            "output": WindowConfigLayoutConfigSetAttachmentConfigOutput,
        },
        "build_via_window_config": {
            "canonical": {
                "name": "build_via_window_config",
                "description": "Create one deterministic WindowConfig↔LayoutConfig bridge.",
                "is_constructor": True,
            },
            "input": WindowConfigLayoutConfigBuildViaWindowConfigInput,
            "output": WindowConfigLayoutConfigBuildViaWindowConfigOutput,
        },
    },
}

__all__ = [
    "WindowConfigLayoutConfig",
    "WindowConfigLayoutConfigSetAttachmentConfigInput",
    "WindowConfigLayoutConfigSetAttachmentConfigOutput",
    "WindowConfigLayoutConfigBuildViaWindowConfigInput",
    "WindowConfigLayoutConfigBuildViaWindowConfigOutput",
    "FUNCTIONS",
]
