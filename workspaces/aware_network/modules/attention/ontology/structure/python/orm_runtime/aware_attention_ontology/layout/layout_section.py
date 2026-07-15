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
    from aware_attention_ontology.section.section import Section


class LayoutSection(ORMModel):
    """Canonical section geometry/visibility entry inside a Layout."""

    # Relationships
    section: Section | None = Field(default=None, exclude=True)

    # Attributes
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)

    # Foreign Keys
    layout_id: UUID = Field(description="Foreign key for Layout.sections")
    section_id: UUID = Field(description="Foreign key for LayoutSection.section")

    async def set_geometry(self, order: int, flex: float) -> LayoutSection:
        """Updates section order/flex geometry."""

        payload = {"order": order, "flex": flex}
        result = await invoke_instance(orm_model=self, function_name="set_geometry", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, LayoutSection):
            return value
        return LayoutSection.validate_invocation_value(value)

    async def set_visibility(self, is_visible: bool) -> LayoutSection:
        """Updates whether this section is visible in the Layout."""

        payload = {"is_visible": is_visible}
        result = await invoke_instance(orm_model=self, function_name="set_visibility", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, LayoutSection):
            return value
        return LayoutSection.validate_invocation_value(value)

    @classmethod
    async def create_via_layout(
        cls, layout_id: UUID, section_id: UUID, order: int = 0, flex: float = 1.0, is_visible: bool = True
    ) -> LayoutSection:
        """Creates a deterministic LayoutSection for a Layout and Section."""

        payload = {
            "layout_id": layout_id,
            "section_id": section_id,
            "order": order,
            "flex": flex,
            "is_visible": is_visible,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_layout", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, LayoutSection):
            return value
        return LayoutSection.validate_invocation_value(value)


class LayoutSectionSetGeometryInput(BaseModel):
    order: int
    flex: float


class LayoutSectionSetGeometryOutput(BaseModel):
    value: LayoutSection


class LayoutSectionSetVisibilityInput(BaseModel):
    is_visible: bool


class LayoutSectionSetVisibilityOutput(BaseModel):
    value: LayoutSection


class LayoutSectionCreateViaLayoutInput(BaseModel):
    layout_id: UUID = Field(description="Foreign key for Layout.sections")
    section_id: UUID
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)


class LayoutSectionCreateViaLayoutOutput(BaseModel):
    value: LayoutSection


FUNCTIONS = {
    "LayoutSection": {
        "set_geometry": {
            "canonical": {
                "name": "set_geometry",
                "description": "Updates section order/flex geometry.",
                "is_constructor": False,
            },
            "input": LayoutSectionSetGeometryInput,
            "output": LayoutSectionSetGeometryOutput,
        },
        "set_visibility": {
            "canonical": {
                "name": "set_visibility",
                "description": "Updates whether this section is visible in the Layout.",
                "is_constructor": False,
            },
            "input": LayoutSectionSetVisibilityInput,
            "output": LayoutSectionSetVisibilityOutput,
        },
        "create_via_layout": {
            "canonical": {
                "name": "create_via_layout",
                "description": "Creates a deterministic LayoutSection for a Layout and Section.",
                "is_constructor": True,
            },
            "input": LayoutSectionCreateViaLayoutInput,
            "output": LayoutSectionCreateViaLayoutOutput,
        },
    },
}

__all__ = [
    "LayoutSection",
    "LayoutSectionSetGeometryInput",
    "LayoutSectionSetGeometryOutput",
    "LayoutSectionSetVisibilityInput",
    "LayoutSectionSetVisibilityOutput",
    "LayoutSectionCreateViaLayoutInput",
    "LayoutSectionCreateViaLayoutOutput",
    "FUNCTIONS",
]
