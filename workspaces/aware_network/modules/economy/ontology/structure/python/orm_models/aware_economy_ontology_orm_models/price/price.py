from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.price.price_enums import PriceType

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.price.price_schedule import PriceSchedule


class Price(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    price_schedules: list[PriceSchedule] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    name: str
    type: PriceType

    # Foreign Keys
    coin_id: UUID = Field(description="Foreign key for Price.coin")
