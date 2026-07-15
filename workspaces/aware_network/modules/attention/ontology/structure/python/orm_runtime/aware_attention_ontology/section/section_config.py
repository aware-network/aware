from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class SectionConfig(ORMModel):
    """
    Declarative section configuration for Attention.
    Contract:
    - Config-level section source for layout token lowering.
    - Not a runtime instance surface.
    """

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)

    # Foreign Keys
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for LayoutConfigSectionConfig.section_config"
    )

    @classmethod
    async def build_via_layout_config_section_config(
        cls, layout_config_section_config_id: UUID, key: str, title: str, description: str | None = None
    ) -> SectionConfig:
        """Build a deterministic SectionConfig by key."""

        payload = {
            "layout_config_section_config_id": layout_config_section_config_id,
            "key": key,
            "title": title,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_layout_config_section_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SectionConfig):
            return value
        return SectionConfig.validate_invocation_value(value)


class SectionConfigBuildViaLayoutConfigSectionConfigInput(BaseModel):
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for LayoutConfigSectionConfig.section_config"
    )
    key: str
    title: str
    description: str | None = Field(default=None)


class SectionConfigBuildViaLayoutConfigSectionConfigOutput(BaseModel):
    value: SectionConfig


FUNCTIONS = {
    "SectionConfig": {
        "build_via_layout_config_section_config": {
            "canonical": {
                "name": "build_via_layout_config_section_config",
                "description": "Build a deterministic SectionConfig by key.",
                "is_constructor": True,
            },
            "input": SectionConfigBuildViaLayoutConfigSectionConfigInput,
            "output": SectionConfigBuildViaLayoutConfigSectionConfigOutput,
        },
    },
}

__all__ = [
    "SectionConfig",
    "SectionConfigBuildViaLayoutConfigSectionConfigInput",
    "SectionConfigBuildViaLayoutConfigSectionConfigOutput",
    "FUNCTIONS",
]
