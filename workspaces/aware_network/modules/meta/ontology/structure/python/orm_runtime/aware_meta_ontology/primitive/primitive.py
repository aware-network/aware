from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import Json

if TYPE_CHECKING:
    from aware_meta_ontology.primitive.primitive_change import PrimitiveChange
    from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig


class Primitive(ORMModel):
    # Relationships
    primitive_changes: list[PrimitiveChange] = Field(default_factory=list, exclude=True)
    primitive_config: PrimitiveConfig | None = Field(default=None, exclude=True)

    # Attributes
    value: Json

    # Foreign Keys
    primitive_config_id: UUID = Field(description="Foreign key for Primitive.primitive_config")


FUNCTIONS = {
    "Primitive": {},
}

__all__ = [
    "Primitive",
    "FUNCTIONS",
]
