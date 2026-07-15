from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# History Ontology Orm Models
from aware_history_ontology_orm_models.change.change_enums import ChangeDeltaKind

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import Json


class ChangeDelta(ORMModel):
    # Attributes
    position: int
    property: str | None = Field(default=None)
    kind: ChangeDeltaKind
    payload: Json

    # Foreign Keys
    change_id: UUID = Field(description="Foreign key for Change.change_deltas")
