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
    from aware_attention_ontology.section.section_config import SectionConfig


class LayoutConfigSectionConfig(ORMModel):
    """Canonical section configuration entry inside a LayoutConfig."""

    # Relationships
    section_config: SectionConfig | None = Field(default=None, exclude=True)

    # Attributes
    section_key: str
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)

    # Foreign Keys
    layout_config_id: UUID = Field(description="Foreign key for LayoutConfig.section_configs")

    async def set_geometry(self, order: int, flex: float) -> LayoutConfigSectionConfig:
        """Update section config order/flex geometry."""

        payload = {"order": order, "flex": flex}
        result = await invoke_instance(orm_model=self, function_name="set_geometry", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, LayoutConfigSectionConfig):
            return value
        return LayoutConfigSectionConfig.validate_invocation_value(value)

    async def set_visibility(self, is_visible: bool) -> LayoutConfigSectionConfig:
        """Update whether this section config is visible in the LayoutConfig."""

        payload = {"is_visible": is_visible}
        result = await invoke_instance(orm_model=self, function_name="set_visibility", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, LayoutConfigSectionConfig):
            return value
        return LayoutConfigSectionConfig.validate_invocation_value(value)

    @classmethod
    async def create_via_layout_config(
        cls,
        layout_config_id: UUID,
        section_key: str,
        title: str,
        description: str | None = None,
        order: int = 0,
        flex: float = 1.0,
        is_visible: bool = True,
    ) -> LayoutConfigSectionConfig:
        """Build a deterministic LayoutConfigSectionConfig for a LayoutConfig and SectionConfig."""

        payload = {
            "layout_config_id": layout_config_id,
            "section_key": section_key,
            "title": title,
            "description": description,
            "order": order,
            "flex": flex,
            "is_visible": is_visible,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_layout_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, LayoutConfigSectionConfig):
            return value
        return LayoutConfigSectionConfig.validate_invocation_value(value)


class LayoutConfigSectionConfigSetGeometryInput(BaseModel):
    order: int
    flex: float


class LayoutConfigSectionConfigSetGeometryOutput(BaseModel):
    value: LayoutConfigSectionConfig


class LayoutConfigSectionConfigSetVisibilityInput(BaseModel):
    is_visible: bool


class LayoutConfigSectionConfigSetVisibilityOutput(BaseModel):
    value: LayoutConfigSectionConfig


class LayoutConfigSectionConfigCreateViaLayoutConfigInput(BaseModel):
    layout_config_id: UUID = Field(description="Foreign key for LayoutConfig.section_configs")
    section_key: str
    title: str
    description: str | None = Field(default=None)
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)


class LayoutConfigSectionConfigCreateViaLayoutConfigOutput(BaseModel):
    value: LayoutConfigSectionConfig


FUNCTIONS = {
    "LayoutConfigSectionConfig": {
        "set_geometry": {
            "canonical": {
                "name": "set_geometry",
                "description": "Update section config order/flex geometry.",
                "is_constructor": False,
            },
            "input": LayoutConfigSectionConfigSetGeometryInput,
            "output": LayoutConfigSectionConfigSetGeometryOutput,
        },
        "set_visibility": {
            "canonical": {
                "name": "set_visibility",
                "description": "Update whether this section config is visible in the LayoutConfig.",
                "is_constructor": False,
            },
            "input": LayoutConfigSectionConfigSetVisibilityInput,
            "output": LayoutConfigSectionConfigSetVisibilityOutput,
        },
        "create_via_layout_config": {
            "canonical": {
                "name": "create_via_layout_config",
                "description": "Build a deterministic LayoutConfigSectionConfig for a LayoutConfig and SectionConfig.",
                "is_constructor": True,
            },
            "input": LayoutConfigSectionConfigCreateViaLayoutConfigInput,
            "output": LayoutConfigSectionConfigCreateViaLayoutConfigOutput,
        },
    },
}

__all__ = [
    "LayoutConfigSectionConfig",
    "LayoutConfigSectionConfigSetGeometryInput",
    "LayoutConfigSectionConfigSetGeometryOutput",
    "LayoutConfigSectionConfigSetVisibilityInput",
    "LayoutConfigSectionConfigSetVisibilityOutput",
    "LayoutConfigSectionConfigCreateViaLayoutConfigInput",
    "LayoutConfigSectionConfigCreateViaLayoutConfigOutput",
    "FUNCTIONS",
]
