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
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.external_capital.external_capital_enums import ExternalCapitalConversionMode
from aware_economy_ontology.transaction.transaction_intent_enums import TransactionIntentStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.external_capital.external_capital_provider_config import ExternalCapitalProviderConfig
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.transaction.capital_conversion_quote import CapitalConversionQuote
    from aware_economy_ontology.transaction.transaction_intent_external_expiration import (
        TransactionIntentExternalExpiration,
    )
    from aware_economy_ontology.wallet.wallet import Wallet
    from aware_economy_ontology.wallet.wallet_public import WalletPublic


class TransactionIntent(ORMModel):
    # Relationships
    capital_conversion_quote: CapitalConversionQuote | None = Field(default=None, exclude=True)
    coin: Coin | None = Field(default=None, exclude=True)
    external_expirations: list[TransactionIntentExternalExpiration] = Field(default_factory=list, exclude=True)
    provider_config: ExternalCapitalProviderConfig | None = Field(default=None, exclude=True)
    recipient_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    recipient_wallet: Wallet | None = Field(default=None, exclude=True)
    recipient_wallet_public: WalletPublic | None = Field(default=None, exclude=True)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    created_at: datetime
    funding_intent_key: str
    idempotency_key: str
    metadata_json: JsonObject | None = Field(default=None)
    provider_key: str
    status: TransactionIntentStatus = Field(default=TransactionIntentStatus.created)
    updated_at: datetime | None = Field(default=None)

    # Foreign Keys
    capital_conversion_quote_id: UUID | None = Field(
        default=None, description="Foreign key for TransactionIntent.capital_conversion_quote"
    )
    coin_id: UUID = Field(description="Foreign key for TransactionIntent.coin")
    provider_config_id: UUID = Field(description="Foreign key for TransactionIntent.provider_config")
    recipient_finance_entity_id: UUID = Field(description="Foreign key for TransactionIntent.recipient_finance_entity")
    recipient_wallet_id: UUID = Field(description="Foreign key for TransactionIntent.recipient_wallet")
    recipient_wallet_public_id: UUID = Field(description="Foreign key for TransactionIntent.recipient_wallet_public")

    @classmethod
    async def create(
        cls,
        provider_config_id: UUID,
        recipient_finance_entity_id: UUID,
        recipient_wallet_id: UUID,
        recipient_wallet_public_id: UUID,
        funding_intent_key: str,
        coin_id: UUID,
        amount: Annotated[Decimal, DecimalWire()],
        provider_key: str,
        idempotency_key: str,
        provider_route_id: UUID,
        external_currency: str,
        external_minor_unit_exponent: int,
        conversion_mode: ExternalCapitalConversionMode,
        created_at: datetime,
        quote_expires_at: datetime | None = None,
        metadata_json: JsonObject | None = None,
    ) -> TransactionIntent:
        """
        Records an Aware-owned wallet funding intent and its accepted capital quote atomically.

        Receipt: TransactionIntent(status=created) with one immutable CapitalConversionQuote.
        """

        payload = {
            "provider_config_id": provider_config_id,
            "recipient_finance_entity_id": recipient_finance_entity_id,
            "recipient_wallet_id": recipient_wallet_id,
            "recipient_wallet_public_id": recipient_wallet_public_id,
            "funding_intent_key": funding_intent_key,
            "coin_id": coin_id,
            "amount": amount,
            "provider_key": provider_key,
            "idempotency_key": idempotency_key,
            "provider_route_id": provider_route_id,
            "external_currency": external_currency,
            "external_minor_unit_exponent": external_minor_unit_exponent,
            "conversion_mode": conversion_mode,
            "created_at": created_at,
            "quote_expires_at": quote_expires_at,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, TransactionIntent):
            return value
        return TransactionIntent.validate_invocation_value(value)

    async def mark_pending(self, occurred_at: datetime) -> TransactionIntent:
        """Marks that the external-capital continuation was created."""

        payload = {"occurred_at": occurred_at}
        result = await invoke_instance(orm_model=self, function_name="mark_pending", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, TransactionIntent):
            return value
        return TransactionIntent.validate_invocation_value(value)

    async def confirm(self, occurred_at: datetime) -> TransactionIntent:
        """Confirms the intent after verified external-capital ingress."""

        payload = {"occurred_at": occurred_at}
        result = await invoke_instance(orm_model=self, function_name="confirm", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, TransactionIntent):
            return value
        return TransactionIntent.validate_invocation_value(value)

    async def cancel(self, occurred_at: datetime) -> TransactionIntent:
        """Cancels the intent after verified terminal no-credit evidence."""

        payload = {"occurred_at": occurred_at}
        result = await invoke_instance(orm_model=self, function_name="cancel", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, TransactionIntent):
            return value
        return TransactionIntent.validate_invocation_value(value)

    async def cancel_from_external_evidence(
        self,
        provider_config_id: UUID,
        capital_conversion_quote_id: UUID,
        provider_key: str,
        provider_event_id: str,
        idempotency_key: str,
        quote_hash: str,
        provider_public_reference: str,
        provider_payload_hash: str,
        external_created_at: datetime,
    ) -> TransactionIntentExternalExpiration:
        """
        Records verified provider expiration evidence and cancels this intent atomically.

        Receipt: contained TransactionIntentExternalExpiration; no Transaction
        or Wallet application is created.
        """

        payload = {
            "provider_config_id": provider_config_id,
            "capital_conversion_quote_id": capital_conversion_quote_id,
            "provider_key": provider_key,
            "provider_event_id": provider_event_id,
            "idempotency_key": idempotency_key,
            "quote_hash": quote_hash,
            "provider_public_reference": provider_public_reference,
            "provider_payload_hash": provider_payload_hash,
            "external_created_at": external_created_at,
        }
        result = await invoke_instance(orm_model=self, function_name="cancel_from_external_evidence", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.transaction.transaction_intent_external_expiration import (
            TransactionIntentExternalExpiration,
        )

        if isinstance(value, TransactionIntentExternalExpiration):
            return value
        return TransactionIntentExternalExpiration.validate_invocation_value(value)


class TransactionIntentCreateInput(BaseModel):
    provider_config_id: UUID
    recipient_finance_entity_id: UUID
    recipient_wallet_id: UUID
    recipient_wallet_public_id: UUID
    funding_intent_key: str
    coin_id: UUID
    amount: Annotated[Decimal, DecimalWire()]
    provider_key: str
    idempotency_key: str
    provider_route_id: UUID
    external_currency: str
    external_minor_unit_exponent: int
    conversion_mode: ExternalCapitalConversionMode
    created_at: datetime
    quote_expires_at: datetime | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default=None)


class TransactionIntentCreateOutput(BaseModel):
    value: TransactionIntent


class TransactionIntentMarkPendingInput(BaseModel):
    occurred_at: datetime


class TransactionIntentMarkPendingOutput(BaseModel):
    value: TransactionIntent


class TransactionIntentConfirmInput(BaseModel):
    occurred_at: datetime


class TransactionIntentConfirmOutput(BaseModel):
    value: TransactionIntent


class TransactionIntentCancelInput(BaseModel):
    occurred_at: datetime


class TransactionIntentCancelOutput(BaseModel):
    value: TransactionIntent


class TransactionIntentCancelFromExternalEvidenceInput(BaseModel):
    provider_config_id: UUID
    capital_conversion_quote_id: UUID
    provider_key: str
    provider_event_id: str
    idempotency_key: str
    quote_hash: str
    provider_public_reference: str
    provider_payload_hash: str
    external_created_at: datetime


class TransactionIntentCancelFromExternalEvidenceOutput(BaseModel):
    value: TransactionIntentExternalExpiration


FUNCTIONS = {
    "TransactionIntent": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Records an Aware-owned wallet funding intent and its accepted capital quote atomically.\n\nReceipt: TransactionIntent(status=created) with one immutable CapitalConversionQuote.",
                "is_constructor": True,
            },
            "input": TransactionIntentCreateInput,
            "output": TransactionIntentCreateOutput,
        },
        "mark_pending": {
            "canonical": {
                "name": "mark_pending",
                "description": "Marks that the external-capital continuation was created.",
                "is_constructor": False,
            },
            "input": TransactionIntentMarkPendingInput,
            "output": TransactionIntentMarkPendingOutput,
        },
        "confirm": {
            "canonical": {
                "name": "confirm",
                "description": "Confirms the intent after verified external-capital ingress.",
                "is_constructor": False,
            },
            "input": TransactionIntentConfirmInput,
            "output": TransactionIntentConfirmOutput,
        },
        "cancel": {
            "canonical": {
                "name": "cancel",
                "description": "Cancels the intent after verified terminal no-credit evidence.",
                "is_constructor": False,
            },
            "input": TransactionIntentCancelInput,
            "output": TransactionIntentCancelOutput,
        },
        "cancel_from_external_evidence": {
            "canonical": {
                "name": "cancel_from_external_evidence",
                "description": "Records verified provider expiration evidence and cancels this intent atomically.\n\nReceipt: contained TransactionIntentExternalExpiration; no Transaction\nor Wallet application is created.",
                "is_constructor": False,
            },
            "input": TransactionIntentCancelFromExternalEvidenceInput,
            "output": TransactionIntentCancelFromExternalEvidenceOutput,
        },
    },
}

__all__ = [
    "TransactionIntent",
    "TransactionIntentCreateInput",
    "TransactionIntentCreateOutput",
    "TransactionIntentMarkPendingInput",
    "TransactionIntentMarkPendingOutput",
    "TransactionIntentConfirmInput",
    "TransactionIntentConfirmOutput",
    "TransactionIntentCancelInput",
    "TransactionIntentCancelOutput",
    "TransactionIntentCancelFromExternalEvidenceInput",
    "TransactionIntentCancelFromExternalEvidenceOutput",
    "FUNCTIONS",
]
