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
    from aware_economy_ontology_orm_models.price.pricing_policy import PricingPolicy
    from aware_economy_ontology_orm_models.price.rate_snapshot import RateSnapshot


class PriceSchedule(ORMModel):
    # Relationships
    pricing_policy: PricingPolicy | None = Field(default=None, exclude=True)
    rate_snapshots: list[RateSnapshot] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    effective_from: datetime
    effective_until: datetime | None = Field(default=None)
    fixed_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    name: str
    version: int = Field(default=1)

    # Foreign Keys
    price_id: UUID = Field(description="Foreign key for Price.price_schedules")
    pricing_policy_id: UUID = Field(description="Foreign key for PriceSchedule.pricing_policy")
