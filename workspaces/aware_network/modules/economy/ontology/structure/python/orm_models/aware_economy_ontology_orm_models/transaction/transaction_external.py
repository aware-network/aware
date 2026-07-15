from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.transaction.transaction_external_enums import TransactionExternalStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.external_capital.external_capital_provider_config import (
        ExternalCapitalProviderConfig,
    )
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.transaction.capital_conversion_quote import CapitalConversionQuote
    from aware_economy_ontology_orm_models.transaction.transaction import Transaction
    from aware_economy_ontology_orm_models.transaction.transaction_intent import TransactionIntent


class TransactionExternal(ORMModel):
    # Relationships
    capital_conversion_quote: CapitalConversionQuote | None = Field(default=None, exclude=True)
    provider_config: ExternalCapitalProviderConfig | None = Field(default=None, exclude=True)
    provider_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    transaction: Transaction | None = Field(default=None, exclude=True)
    transaction_intent: TransactionIntent | None = Field(default=None, exclude=True)

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

    # Foreign Keys
    capital_conversion_quote_id: UUID = Field(
        description="Foreign key for TransactionExternal.capital_conversion_quote"
    )
    provider_config_id: UUID = Field(description="Foreign key for TransactionExternal.provider_config")
    provider_finance_entity_id: UUID = Field(description="Foreign key for TransactionExternal.provider_finance_entity")
    transaction_id: UUID = Field(description="Foreign key for TransactionExternal.transaction")
    transaction_intent_id: UUID = Field(description="Foreign key for TransactionExternal.transaction_intent")
