from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.price.price_reservation_enums import PriceReservationStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)


class PriceReservation(ORMModel):
    # Attributes
    actual_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    actual_markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    final_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    reservation_key: str
    reserved_at: datetime
    status: PriceReservationStatus = Field(default=PriceReservationStatus.reserved)

    # Foreign Keys
    rate_snapshot_id: UUID = Field(description="Foreign key for RateSnapshot.price_reservations")
