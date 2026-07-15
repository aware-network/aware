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

# Economy Ontology Dto
from aware_economy_ontology_dto.external_capital.external_capital_enums import ExternalCapitalConversionMode

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.external_capital.external_capital_provider_route import ExternalCapitalProviderRoute


class CapitalConversionQuote(BaseModel):
    # Relationships
    provider_route: ExternalCapitalProviderRoute | None = Field(default=None)
    target_coin: Coin | None = Field(default=None)

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
