from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
    ExternalCapitalRouteStatus,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin


class ExternalCapitalProviderRoute(BaseModel):
    # Relationships
    target_coin: Coin | None = Field(default=None)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    conversion_mode: ExternalCapitalConversionMode = Field(default=ExternalCapitalConversionMode.direct_denomination)
    external_currency: str
    external_minor_unit_exponent: int
    max_external_amount_minor: int | None = Field(default=None)
    min_external_amount_minor: int | None = Field(default=None)
    route_key: str
    status: ExternalCapitalRouteStatus = Field(default=ExternalCapitalRouteStatus.active)
