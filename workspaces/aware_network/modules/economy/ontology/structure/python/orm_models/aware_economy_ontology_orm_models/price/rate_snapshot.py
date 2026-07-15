from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.price.price_reservation import PriceReservation


class RateSnapshot(ORMModel):
    # Relationships
    price_reservations: list[PriceReservation] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    captured_at: datetime
    cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    quoted_amount: Annotated[Decimal, DecimalWire()]
    snapshot_key: str

    # Foreign Keys
    price_schedule_id: UUID = Field(description="Foreign key for PriceSchedule.rate_snapshots")
