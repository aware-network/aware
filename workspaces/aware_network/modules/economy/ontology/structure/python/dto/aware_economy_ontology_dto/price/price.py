from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.price.price_enums import PriceType

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.price.price_schedule import PriceSchedule


class Price(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    price_schedules: list[PriceSchedule] = Field(default_factory=list)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    name: str
    type: PriceType
