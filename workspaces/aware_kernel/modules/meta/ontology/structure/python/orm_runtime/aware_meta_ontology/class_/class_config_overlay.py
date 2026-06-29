from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig


class ClassConfigOverlay(ORMModel):
    """Per-language overrides for ClassConfig entities."""

    # Relationships
    class_config: ClassConfig | None = Field(
        default=None, exclude=True, description="Association target reference to ClassConfig"
    )

    # Attributes
    rendered_name: str | None = Field(default=None)
    lang_flags: JsonObject | None = Field(default=None)

    # Foreign Keys
    class_config_id: UUID = Field(description="Join FK to ClassConfig")
    object_config_graph_overlay_id: UUID = Field(description="Join FK to ObjectConfigGraphOverlay")


FUNCTIONS = {
    "ClassConfigOverlay": {},
}

__all__ = [
    "ClassConfigOverlay",
    "FUNCTIONS",
]
