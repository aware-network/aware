from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# History Ontology Dto
from aware_history_ontology_dto.change.change_enums import ChangeDeltaKind

# Types
from aware_types import Json


class ChangeDelta(BaseModel):
    # Attributes
    position: int
    property: str | None = Field(default=None)
    kind: ChangeDeltaKind
    payload: Json
