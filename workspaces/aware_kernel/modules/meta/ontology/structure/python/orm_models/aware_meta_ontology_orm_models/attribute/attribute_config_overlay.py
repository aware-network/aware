from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class AttributeConfigOverlay(ORMModel):
    """Per-language overrides for AttributeConfig entities."""

    # Relationships
    attribute_config: AttributeConfig | None = Field(
        default=None, exclude=True, description="Association target reference to AttributeConfig"
    )

    # Attributes
    rendered_name: str | None = Field(default=None)
    wire_name: str | None = Field(default=None)

    # Foreign Keys
    attribute_config_id: UUID = Field(description="Join FK to AttributeConfig")
    object_config_graph_overlay_id: UUID = Field(description="Join FK to ObjectConfigGraphOverlay")
