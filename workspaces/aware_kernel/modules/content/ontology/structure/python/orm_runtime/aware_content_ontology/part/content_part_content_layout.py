from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Content Ontology
from aware_content_ontology.part.content_part_enums import ContentPartLayoutUnit

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_content_ontology.part.content_part_content import ContentPartContent


class ContentPartContentLayout(ORMModel):
    # Relationships
    content_part_content: ContentPartContent | None = Field(
        default=None, exclude=True, description="Association target reference to ContentPartContent"
    )

    # Attributes
    aspect_ratio: float | None = Field(default=None)
    depth_unit: ContentPartLayoutUnit | None = Field(default=None)
    depth_value: float | None = Field(default=None)
    height_unit: ContentPartLayoutUnit
    height_value: float
    is_responsive: bool = Field(default=True)
    layout_order: int = Field(default=0)
    margin_bottom: float | None = Field(default=None)
    margin_left: float | None = Field(default=None)
    margin_right: float | None = Field(default=None)
    margin_top: float | None = Field(default=None)
    max_height_unit: ContentPartLayoutUnit | None = Field(default=None)
    max_height_value: float | None = Field(default=None)
    max_width_unit: ContentPartLayoutUnit | None = Field(default=None)
    max_width_value: float | None = Field(default=None)
    min_height_unit: ContentPartLayoutUnit | None = Field(default=None)
    min_height_value: float | None = Field(default=None)
    min_width_unit: ContentPartLayoutUnit | None = Field(default=None)
    min_width_value: float | None = Field(default=None)
    opacity: float = Field(default=1.0)
    padding_bottom: float | None = Field(default=None)
    padding_left: float | None = Field(default=None)
    padding_right: float | None = Field(default=None)
    padding_top: float | None = Field(default=None)
    position_x_unit: ContentPartLayoutUnit
    position_x_value: float
    position_y_unit: ContentPartLayoutUnit
    position_y_value: float
    position_z_unit: ContentPartLayoutUnit | None = Field(default=None)
    position_z_value: float | None = Field(default=None)
    rotation_x: float | None = Field(default=None)
    rotation_y: float | None = Field(default=None)
    rotation_z: float | None = Field(default=None)
    scale_x: float | None = Field(default=None)
    scale_y: float | None = Field(default=None)
    scale_z: float | None = Field(default=None)
    width_unit: ContentPartLayoutUnit
    width_value: float

    # Foreign Keys
    content_part_content_id: UUID = Field(description="Join FK to ContentPartContent")
    content_layout_id: UUID = Field(description="Join FK to ContentLayout")

    @classmethod
    async def create_content_part_content_layout_via_content_layout(
        cls,
        content_layout_id: UUID,
        content_part_content_id: UUID,
        layout_order: int = 0,
        height_unit: ContentPartLayoutUnit = ContentPartLayoutUnit.percentage,
        height_value: float = 100.0,
        position_x_unit: ContentPartLayoutUnit = ContentPartLayoutUnit.percentage,
        position_x_value: float = 0.0,
        position_y_unit: ContentPartLayoutUnit = ContentPartLayoutUnit.percentage,
        position_y_value: float = 0.0,
        width_unit: ContentPartLayoutUnit = ContentPartLayoutUnit.percentage,
        width_value: float = 100.0,
    ) -> ContentPartContentLayout:
        """Creates a layout placement for a content part inside a content layout."""

        payload = {
            "content_layout_id": content_layout_id,
            "content_part_content_id": content_part_content_id,
            "layout_order": layout_order,
            "height_unit": height_unit,
            "height_value": height_value,
            "position_x_unit": position_x_unit,
            "position_x_value": position_x_value,
            "position_y_unit": position_y_unit,
            "position_y_value": position_y_value,
            "width_unit": width_unit,
            "width_value": width_value,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_content_part_content_layout_via_content_layout", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ContentPartContentLayout):
            return value
        return ContentPartContentLayout.validate_invocation_value(value)


class ContentPartContentLayoutCreateContentPartContentLayoutViaContentLayoutInput(BaseModel):
    content_layout_id: UUID = Field(description="Join FK to ContentLayout")
    content_part_content_id: UUID
    layout_order: int = Field(default=0)
    height_unit: ContentPartLayoutUnit = Field(default=ContentPartLayoutUnit.percentage)
    height_value: float = Field(default=100.0)
    position_x_unit: ContentPartLayoutUnit = Field(default=ContentPartLayoutUnit.percentage)
    position_x_value: float = Field(default=0.0)
    position_y_unit: ContentPartLayoutUnit = Field(default=ContentPartLayoutUnit.percentage)
    position_y_value: float = Field(default=0.0)
    width_unit: ContentPartLayoutUnit = Field(default=ContentPartLayoutUnit.percentage)
    width_value: float = Field(default=100.0)


class ContentPartContentLayoutCreateContentPartContentLayoutViaContentLayoutOutput(BaseModel):
    value: ContentPartContentLayout


FUNCTIONS = {
    "ContentPartContentLayout": {
        "create_content_part_content_layout_via_content_layout": {
            "canonical": {
                "name": "create_content_part_content_layout_via_content_layout",
                "description": "Creates a layout placement for a content part inside a content layout.",
                "is_constructor": True,
            },
            "input": ContentPartContentLayoutCreateContentPartContentLayoutViaContentLayoutInput,
            "output": ContentPartContentLayoutCreateContentPartContentLayoutViaContentLayoutOutput,
        },
    },
}

__all__ = [
    "ContentPartContentLayout",
    "ContentPartContentLayoutCreateContentPartContentLayoutViaContentLayoutInput",
    "ContentPartContentLayoutCreateContentPartContentLayoutViaContentLayoutOutput",
    "FUNCTIONS",
]
