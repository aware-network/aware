from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# History Ontology Dto
from aware_history_ontology_dto.change.change_enums import ChangeType

if TYPE_CHECKING:
    from aware_history_ontology_dto.change.change_delta import ChangeDelta


class Change(BaseModel):
    # Relationships
    change_deltas: list[ChangeDelta] = Field(default_factory=list)

    # Attributes
    key: str
    created_at: datetime
    type: ChangeType
