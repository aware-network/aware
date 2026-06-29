from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Content Ontology Orm Models
from aware_content_ontology_orm_models.part.content_part_enums import ContentPartLayoutUnit

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_content import ContentPartContent


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
