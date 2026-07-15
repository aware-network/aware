from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.transaction.transaction_external_enums import TransactionExternalStatus

if TYPE_CHECKING:
    from aware_economy_ontology_dto.external_capital.external_capital_provider_config import (
        ExternalCapitalProviderConfig,
    )
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.transaction.capital_conversion_quote import CapitalConversionQuote
    from aware_economy_ontology_dto.transaction.transaction import Transaction
    from aware_economy_ontology_dto.transaction.transaction_intent import TransactionIntent


class TransactionExternal(BaseModel):
    # Relationships
    capital_conversion_quote: CapitalConversionQuote | None = Field(default=None)
    provider_config: ExternalCapitalProviderConfig | None = Field(default=None)
    provider_finance_entity: FinanceEntity | None = Field(default=None)
    transaction: Transaction | None = Field(default=None)
    transaction_intent: TransactionIntent | None = Field(default=None)

    # Attributes
    external_amount_minor: int
    external_created_at: datetime
    external_currency: str
    idempotency_key: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    provider_event_id: str
    provider_key: str
    provider_payload_hash: str
    provider_public_reference: str
    quote_hash: str
    status: TransactionExternalStatus = Field(default=TransactionExternalStatus.processed)
