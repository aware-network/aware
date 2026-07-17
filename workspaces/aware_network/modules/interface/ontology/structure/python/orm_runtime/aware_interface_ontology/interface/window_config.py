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
    from aware_interface_ontology.interface.window_config_layout_config import WindowConfigLayoutConfig


class WindowConfig(ORMModel):
    # Relationships
    layout_configs: list[WindowConfigLayoutConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, key: str, description: str | None = None) -> WindowConfig:
        """
        Create one deterministic Interface-side window configuration.

        Contract:
        - `WindowConfig` is the authored/config namespace that names one interface window.
        - It composes attention-owned layouts through explicit joins.
        - It does not own pane semantics.
        """

        payload = {"key": key, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WindowConfig):
            return value
        return WindowConfig.validate_invocation_value(value)

    async def attach_layout_config(
        self, layout_config_id: UUID, description: str | None = None
    ) -> WindowConfigLayoutConfig:
        """Attach one attention-owned LayoutConfig to this Interface-side window configuration."""

        payload = {"layout_config_id": layout_config_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="attach_layout_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_interface_ontology.interface.window_config_layout_config import WindowConfigLayoutConfig

        if isinstance(value, WindowConfigLayoutConfig):
            return value
        return WindowConfigLayoutConfig.validate_invocation_value(value)


class WindowConfigBuildInput(BaseModel):
    key: str
    description: str | None = Field(default=None)


class WindowConfigBuildOutput(BaseModel):
    value: WindowConfig


class WindowConfigAttachLayoutConfigInput(BaseModel):
    layout_config_id: UUID
    description: str | None = Field(default=None)


class WindowConfigAttachLayoutConfigOutput(BaseModel):
    value: WindowConfigLayoutConfig


FUNCTIONS = {
    "WindowConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one deterministic Interface-side window configuration.\n\nContract:\n- `WindowConfig` is the authored/config namespace that names one interface window.\n- It composes attention-owned layouts through explicit joins.\n- It does not own pane semantics.",
                "is_constructor": True,
            },
            "input": WindowConfigBuildInput,
            "output": WindowConfigBuildOutput,
        },
        "attach_layout_config": {
            "canonical": {
                "name": "attach_layout_config",
                "description": "Attach one attention-owned LayoutConfig to this Interface-side window configuration.",
                "is_constructor": False,
            },
            "input": WindowConfigAttachLayoutConfigInput,
            "output": WindowConfigAttachLayoutConfigOutput,
        },
    },
}

__all__ = [
    "WindowConfig",
    "WindowConfigBuildInput",
    "WindowConfigBuildOutput",
    "WindowConfigAttachLayoutConfigInput",
    "WindowConfigAttachLayoutConfigOutput",
    "FUNCTIONS",
]
