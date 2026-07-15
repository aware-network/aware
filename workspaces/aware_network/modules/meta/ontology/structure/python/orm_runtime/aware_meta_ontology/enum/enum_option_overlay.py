from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology.enum.enum_option import EnumOption


class EnumOptionOverlay(ORMModel):
    """Per-language overrides for EnumOption entities"""

    # Relationships
    enum_option: EnumOption | None = Field(
        default=None, exclude=True, description="Association target reference to EnumOption"
    )

    # Attributes
    rendered_name: str | None = Field(default=None)
    wire_name: str | None = Field(default=None)

    # Foreign Keys
    enum_option_id: UUID = Field(description="Join FK to EnumOption")
    object_config_graph_overlay_id: UUID = Field(description="Join FK to ObjectConfigGraphOverlay")


FUNCTIONS = {
    "EnumOptionOverlay": {},
}

__all__ = [
    "EnumOptionOverlay",
    "FUNCTIONS",
]
