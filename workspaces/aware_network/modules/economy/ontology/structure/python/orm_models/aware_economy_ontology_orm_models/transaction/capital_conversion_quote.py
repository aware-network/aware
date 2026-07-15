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

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.external_capital.external_capital_enums import ExternalCapitalConversionMode

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.external_capital.external_capital_provider_route import (
        ExternalCapitalProviderRoute,
    )


class CapitalConversionQuote(ORMModel):
    # Relationships
    provider_route: ExternalCapitalProviderRoute | None = Field(default=None, exclude=True)
    target_coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    captured_at: datetime
    conversion_mode: ExternalCapitalConversionMode
    expires_at: datetime | None = Field(default=None)
    external_amount_minor: int
    external_currency: str
    quote_hash: str
    quote_key: str
    source: str
    target_amount: Annotated[Decimal, DecimalWire()]

    # Foreign Keys
    provider_route_id: UUID = Field(description="Foreign key for CapitalConversionQuote.provider_route")
    target_coin_id: UUID = Field(description="Foreign key for CapitalConversionQuote.target_coin")
