from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.external_capital.external_capital_provider_config import (
        ExternalCapitalProviderConfig,
    )
    from aware_economy_ontology_dto.transaction.capital_conversion_quote import CapitalConversionQuote


class TransactionIntentExternalExpiration(BaseModel):
    # Relationships
    capital_conversion_quote: CapitalConversionQuote | None = Field(default=None)
    provider_config: ExternalCapitalProviderConfig | None = Field(default=None)

    # Attributes
    external_created_at: datetime
    idempotency_key: str
    provider_event_id: str
    provider_key: str
    provider_payload_hash: str
    provider_public_reference: str
    quote_hash: str
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
