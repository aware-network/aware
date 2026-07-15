from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.price.price_reservation import PriceReservation


class RateSnapshot(BaseModel):
    # Relationships
    price_reservations: list[PriceReservation] = Field(default_factory=list)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    captured_at: datetime
    cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    quoted_amount: Annotated[Decimal, DecimalWire()]
    snapshot_key: str
