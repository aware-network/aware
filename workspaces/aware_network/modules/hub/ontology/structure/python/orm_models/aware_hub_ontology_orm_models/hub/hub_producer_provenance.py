from __future__ import annotations

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class HubProducerProvenance(ORMModel):
    # Attributes
    build_ref: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)
    producer_key: str
    producer_kind: str
    producer_revision_id: str | None = Field(default=None)
    provenance_key: str = Field(default="default")
    source_revision_id: str | None = Field(default=None)
    source_revision_kind: str | None = Field(default=None)
