from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

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
    from aware_attention_ontology.layout.layout_config_section_config import LayoutConfigSectionConfig


class LayoutConfig(ORMModel):
    """
    Declarative layout configuration for Attention.
    Contract:
    - Config-level topology source for layout token lowering.
    - Not a runtime instance surface.
    """

    # Relationships
    section_configs: list[LayoutConfigSectionConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)

    @classmethod
    async def build(cls, key: str, title: str, description: str | None = None) -> LayoutConfig:
        """Build a deterministic LayoutConfig by key."""

        payload = {"key": key, "title": title, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, LayoutConfig):
            return value
        return LayoutConfig.validate_invocation_value(value)

    async def add_section_config(
        self,
        section_key: str,
        title: str,
        description: str | None = None,
        order: int = 0,
        flex: float = 1.0,
        is_visible: bool = True,
    ) -> LayoutConfigSectionConfig:
        """Add a SectionConfig binding to this LayoutConfig."""

        payload = {
            "section_key": section_key,
            "title": title,
            "description": description,
            "order": order,
            "flex": flex,
            "is_visible": is_visible,
        }
        result = await invoke_instance(orm_model=self, function_name="add_section_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_attention_ontology.layout.layout_config_section_config import LayoutConfigSectionConfig

        if isinstance(value, LayoutConfigSectionConfig):
            return value
        return LayoutConfigSectionConfig.validate_invocation_value(value)


class LayoutConfigBuildInput(BaseModel):
    key: str
    title: str
    description: str | None = Field(default=None)


class LayoutConfigBuildOutput(BaseModel):
    value: LayoutConfig


class LayoutConfigAddSectionConfigInput(BaseModel):
    section_key: str
    title: str
    description: str | None = Field(default=None)
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)


class LayoutConfigAddSectionConfigOutput(BaseModel):
    value: LayoutConfigSectionConfig


FUNCTIONS = {
    "LayoutConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Build a deterministic LayoutConfig by key.",
                "is_constructor": True,
            },
            "input": LayoutConfigBuildInput,
            "output": LayoutConfigBuildOutput,
        },
        "add_section_config": {
            "canonical": {
                "name": "add_section_config",
                "description": "Add a SectionConfig binding to this LayoutConfig.",
                "is_constructor": False,
            },
            "input": LayoutConfigAddSectionConfigInput,
            "output": LayoutConfigAddSectionConfigOutput,
        },
    },
}

__all__ = [
    "LayoutConfig",
    "LayoutConfigBuildInput",
    "LayoutConfigBuildOutput",
    "LayoutConfigAddSectionConfigInput",
    "LayoutConfigAddSectionConfigOutput",
    "FUNCTIONS",
]
