from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class ClassConfigOverlay(BaseModel):
    """Per-language overrides for ClassConfig entities."""

    # Relationships
    class_config: ClassConfig | None = Field(default=None, description="Association target reference to ClassConfig")

    # Attributes
    rendered_name: str | None = Field(default=None)
    lang_flags: JsonObject | None = Field(default=None)
