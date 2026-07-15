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
    from aware_economy_ontology_dto.price.pricing_policy import PricingPolicy
    from aware_economy_ontology_dto.price.rate_snapshot import RateSnapshot


class PriceSchedule(BaseModel):
    # Relationships
    pricing_policy: PricingPolicy | None = Field(default=None)
    rate_snapshots: list[RateSnapshot] = Field(default_factory=list)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    effective_from: datetime
    effective_until: datetime | None = Field(default=None)
    fixed_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    name: str
    version: int = Field(default=1)
