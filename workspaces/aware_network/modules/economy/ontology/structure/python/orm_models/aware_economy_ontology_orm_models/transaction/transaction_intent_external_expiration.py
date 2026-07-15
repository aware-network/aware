from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.external_capital.external_capital_provider_config import (
        ExternalCapitalProviderConfig,
    )
    from aware_economy_ontology_orm_models.transaction.capital_conversion_quote import CapitalConversionQuote


class TransactionIntentExternalExpiration(ORMModel):
    # Relationships
    capital_conversion_quote: CapitalConversionQuote | None = Field(default=None, exclude=True)
    provider_config: ExternalCapitalProviderConfig | None = Field(default=None, exclude=True)

    # Attributes
    external_created_at: datetime
    idempotency_key: str
    provider_event_id: str
    provider_key: str
    provider_payload_hash: str
    provider_public_reference: str
    quote_hash: str
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign Keys
    transaction_intent_id: UUID = Field(description="Foreign key for TransactionIntent.external_expirations")
    capital_conversion_quote_id: UUID = Field(
        description="Foreign key for TransactionIntentExternalExpiration.capital_conversion_quote"
    )
    provider_config_id: UUID = Field(description="Foreign key for TransactionIntentExternalExpiration.provider_config")
