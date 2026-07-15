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
from aware_economy_ontology.transaction.provider_lifecycle_receipt_enums import (
    ProviderLifecycleEventKind,
    ProviderLifecycleStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.transaction.transaction import Transaction
    from aware_economy_ontology.transaction.transaction_external import TransactionExternal
    from aware_economy_ontology.wallet.wallet import Wallet
    from aware_economy_ontology.wallet.wallet_public import WalletPublic


class ProviderLifecycleReceipt(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    provider_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    transaction: Transaction | None = Field(default=None, exclude=True)
    transaction_external: TransactionExternal | None = Field(default=None, exclude=True)
    wallet: Wallet | None = Field(default=None, exclude=True)
    wallet_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    wallet_public: WalletPublic | None = Field(default=None, exclude=True)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    event_kind: ProviderLifecycleEventKind
    external_created_at: datetime
    idempotency_key: str
    metadata_json: JsonObject | None = Field(default=None)
    new_available_balance: Annotated[Decimal, DecimalWire()]
    new_balance: Annotated[Decimal, DecimalWire()]
    new_held_balance: Annotated[Decimal, DecimalWire()]
    previous_available_balance: Annotated[Decimal, DecimalWire()]
    previous_balance: Annotated[Decimal, DecimalWire()]
    previous_held_balance: Annotated[Decimal, DecimalWire()]
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    provider_event_id: str
    provider_lifecycle_effect_key: str
    provider_lifecycle_object_id: str
    provider_payment_reference: str
    provider_key: str
    provider_payload_hash: str
    status: ProviderLifecycleStatus

    # Foreign Keys
    coin_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.coin")
    provider_finance_entity_id: UUID = Field(
        description="Foreign key for ProviderLifecycleReceipt.provider_finance_entity"
    )
    transaction_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.transaction")
    transaction_external_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.transaction_external")
    wallet_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.wallet")
    wallet_finance_entity_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.wallet_finance_entity")
    wallet_public_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.wallet_public")

    @classmethod
    async def record(
        cls,
        provider_finance_entity_id: UUID,
        provider_key: str,
        provider_lifecycle_object_id: str,
        provider_lifecycle_effect_key: str,
        provider_event_id: str,
        wallet_finance_entity_id: UUID,
        wallet_id: UUID,
        wallet_public_id: UUID,
        coin_id: UUID,
        amount: Annotated[Decimal, DecimalWire()],
        event_kind: ProviderLifecycleEventKind,
        status: ProviderLifecycleStatus,
        idempotency_key: str,
        previous_balance: Annotated[Decimal, DecimalWire()],
        new_balance: Annotated[Decimal, DecimalWire()],
        previous_held_balance: Annotated[Decimal, DecimalWire()],
        new_held_balance: Annotated[Decimal, DecimalWire()],
        previous_available_balance: Annotated[Decimal, DecimalWire()],
        new_available_balance: Annotated[Decimal, DecimalWire()],
        provider_payment_reference: str,
        provider_payload_hash: str,
        external_created_at: datetime,
        transaction_id: UUID,
        transaction_external_id: UUID,
        metadata_json: JsonObject | None = None,
    ) -> ProviderLifecycleReceipt:
        """
        Records a provider lifecycle event as Aware Economy receipt truth.

        Receipt: one provider lifecycle object/effect stage correlated to the
        original external-ingress transaction. Provider evidence never selects
        Aware wallet coordinates; Economy derives them from committed funding
        truth and remains the only WalletBalance mutation authority.
        """

        payload = {
            "provider_finance_entity_id": provider_finance_entity_id,
            "provider_key": provider_key,
            "provider_lifecycle_object_id": provider_lifecycle_object_id,
            "provider_lifecycle_effect_key": provider_lifecycle_effect_key,
            "provider_event_id": provider_event_id,
            "wallet_finance_entity_id": wallet_finance_entity_id,
            "wallet_id": wallet_id,
            "wallet_public_id": wallet_public_id,
            "coin_id": coin_id,
            "amount": amount,
            "event_kind": event_kind,
            "status": status,
            "idempotency_key": idempotency_key,
            "previous_balance": previous_balance,
            "new_balance": new_balance,
            "previous_held_balance": previous_held_balance,
            "new_held_balance": new_held_balance,
            "previous_available_balance": previous_available_balance,
            "new_available_balance": new_available_balance,
            "provider_payment_reference": provider_payment_reference,
            "provider_payload_hash": provider_payload_hash,
            "external_created_at": external_created_at,
            "transaction_id": transaction_id,
            "transaction_external_id": transaction_external_id,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="record", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProviderLifecycleReceipt):
            return value
        return ProviderLifecycleReceipt.validate_invocation_value(value)


class ProviderLifecycleReceiptRecordInput(BaseModel):
    provider_finance_entity_id: UUID
    provider_key: str
    provider_lifecycle_object_id: str
    provider_lifecycle_effect_key: str
    provider_event_id: str
    wallet_finance_entity_id: UUID
    wallet_id: UUID
    wallet_public_id: UUID
    coin_id: UUID
    amount: Annotated[Decimal, DecimalWire()]
    event_kind: ProviderLifecycleEventKind
    status: ProviderLifecycleStatus
    idempotency_key: str
    previous_balance: Annotated[Decimal, DecimalWire()]
    new_balance: Annotated[Decimal, DecimalWire()]
    previous_held_balance: Annotated[Decimal, DecimalWire()]
    new_held_balance: Annotated[Decimal, DecimalWire()]
    previous_available_balance: Annotated[Decimal, DecimalWire()]
    new_available_balance: Annotated[Decimal, DecimalWire()]
    provider_payment_reference: str
    provider_payload_hash: str
    external_created_at: datetime
    transaction_id: UUID
    transaction_external_id: UUID
    metadata_json: JsonObject | None = Field(default=None)


class ProviderLifecycleReceiptRecordOutput(BaseModel):
    value: ProviderLifecycleReceipt


FUNCTIONS = {
    "ProviderLifecycleReceipt": {
        "record": {
            "canonical": {
                "name": "record",
                "description": "Records a provider lifecycle event as Aware Economy receipt truth.\n\nReceipt: one provider lifecycle object/effect stage correlated to the\noriginal external-ingress transaction. Provider evidence never selects\nAware wallet coordinates; Economy derives them from committed funding\ntruth and remains the only WalletBalance mutation authority.",
                "is_constructor": True,
            },
            "input": ProviderLifecycleReceiptRecordInput,
            "output": ProviderLifecycleReceiptRecordOutput,
        },
    },
}

__all__ = [
    "ProviderLifecycleReceipt",
    "ProviderLifecycleReceiptRecordInput",
    "ProviderLifecycleReceiptRecordOutput",
    "FUNCTIONS",
]
