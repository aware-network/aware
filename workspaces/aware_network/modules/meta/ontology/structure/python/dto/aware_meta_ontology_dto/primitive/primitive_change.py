from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.change.change import Change


class PrimitiveChange(BaseModel):
    # Relationships
    change: Change | None = Field(default=None)
