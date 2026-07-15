from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.transaction.transaction_external_enums import TransactionExternalStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_economy_ontology.external_capital.external_capital_provider_config import ExternalCapitalProviderConfig
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.transaction.capital_conversion_quote import CapitalConversionQuote
    from aware_economy_ontology.transaction.transaction import Transaction
    from aware_economy_ontology.transaction.transaction_intent import TransactionIntent


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

    @classmethod
    async def record(
        cls,
        transaction_id: UUID,
        transaction_intent_id: UUID,
        provider_config_id: UUID,
        capital_conversion_quote_id: UUID,
        provider_finance_entity_id: UUID,
        provider_key: str,
        provider_event_id: str,
        idempotency_key: str,
        quote_hash: str,
        external_amount_minor: int,
        external_currency: str,
        provider_public_reference: str,
        provider_payload_hash: str,
        external_created_at: datetime,
    ) -> TransactionExternal:
        """
        Records fully correlated external-capital provenance for one ingress transaction.

        Receipt: TransactionExternal(status=processed) linked to the Transaction.
        """

        payload = {
            "transaction_id": transaction_id,
            "transaction_intent_id": transaction_intent_id,
            "provider_config_id": provider_config_id,
            "capital_conversion_quote_id": capital_conversion_quote_id,
            "provider_finance_entity_id": provider_finance_entity_id,
            "provider_key": provider_key,
            "provider_event_id": provider_event_id,
            "idempotency_key": idempotency_key,
            "quote_hash": quote_hash,
            "external_amount_minor": external_amount_minor,
            "external_currency": external_currency,
            "provider_public_reference": provider_public_reference,
            "provider_payload_hash": provider_payload_hash,
            "external_created_at": external_created_at,
        }
        result = await invoke_constructor(orm_class=cls, function_name="record", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, TransactionExternal):
            return value
        return TransactionExternal.validate_invocation_value(value)


class TransactionExternalRecordInput(BaseModel):
    transaction_id: UUID
    transaction_intent_id: UUID
    provider_config_id: UUID
    capital_conversion_quote_id: UUID
    provider_finance_entity_id: UUID
    provider_key: str
    provider_event_id: str
    idempotency_key: str
    quote_hash: str
    external_amount_minor: int
    external_currency: str
    provider_public_reference: str
    provider_payload_hash: str
    external_created_at: datetime


class TransactionExternalRecordOutput(BaseModel):
    value: TransactionExternal


FUNCTIONS = {
    "TransactionExternal": {
        "record": {
            "canonical": {
                "name": "record",
                "description": "Records fully correlated external-capital provenance for one ingress transaction.\n\nReceipt: TransactionExternal(status=processed) linked to the Transaction.",
                "is_constructor": True,
            },
            "input": TransactionExternalRecordInput,
            "output": TransactionExternalRecordOutput,
        },
    },
}

__all__ = [
    "TransactionExternal",
    "TransactionExternalRecordInput",
    "TransactionExternalRecordOutput",
    "FUNCTIONS",
]
