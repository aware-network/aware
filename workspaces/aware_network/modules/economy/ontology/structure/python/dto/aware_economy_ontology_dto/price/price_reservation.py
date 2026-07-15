from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.price.price_reservation_enums import PriceReservationStatus

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)


class PriceReservation(BaseModel):
    # Attributes
    actual_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    actual_markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    final_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    reservation_key: str
    reserved_at: datetime
    status: PriceReservationStatus = Field(default=PriceReservationStatus.reserved)
