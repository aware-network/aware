from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology.enum.enum_config import EnumConfig


class EnumConfigOverlay(ORMModel):
    """Per-language overrides for EnumConfig entities"""

    # Relationships
    enum_config: EnumConfig | None = Field(
        default=None, exclude=True, description="Association target reference to EnumConfig"
    )

    # Attributes
    rendered_name: str | None = Field(default=None)

    # Foreign Keys
    enum_config_id: UUID = Field(description="Join FK to EnumConfig")
    object_config_graph_overlay_id: UUID = Field(description="Join FK to ObjectConfigGraphOverlay")


FUNCTIONS = {
    "EnumConfigOverlay": {},
}

__all__ = [
    "EnumConfigOverlay",
    "FUNCTIONS",
]
