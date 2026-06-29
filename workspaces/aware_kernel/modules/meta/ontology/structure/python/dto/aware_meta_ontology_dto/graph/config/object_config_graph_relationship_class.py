from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class ObjectConfigGraphRelationshipClass(BaseModel):
    """One concrete cross-OCG relationship to reference a ClassConfig"""

    # Relationships
    class_config: ClassConfig | None = Field(default=None)
