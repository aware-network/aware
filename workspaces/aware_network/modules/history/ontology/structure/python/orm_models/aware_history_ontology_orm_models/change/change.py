from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# History Ontology Orm Models
from aware_history_ontology_orm_models.change.change_enums import ChangeType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.change.change_delta import ChangeDelta


class Change(ORMModel):
    # Relationships
    change_deltas: list[ChangeDelta] = Field(default_factory=list)

    # Attributes
    key: str
    created_at: datetime
    type: ChangeType
