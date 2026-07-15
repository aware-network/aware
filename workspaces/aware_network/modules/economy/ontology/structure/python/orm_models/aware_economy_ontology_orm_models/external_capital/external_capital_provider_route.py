from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
    ExternalCapitalRouteStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin


class ExternalCapitalProviderRoute(ORMModel):
    # Relationships
    target_coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    conversion_mode: ExternalCapitalConversionMode = Field(default=ExternalCapitalConversionMode.direct_denomination)
    external_currency: str
    external_minor_unit_exponent: int
    max_external_amount_minor: int | None = Field(default=None)
    min_external_amount_minor: int | None = Field(default=None)
    route_key: str
    status: ExternalCapitalRouteStatus = Field(default=ExternalCapitalRouteStatus.active)

    # Foreign Keys
    external_capital_provider_config_id: UUID = Field(
        description="Foreign key for ExternalCapitalProviderConfig.routes"
    )
    target_coin_id: UUID = Field(description="Foreign key for ExternalCapitalProviderRoute.target_coin")
