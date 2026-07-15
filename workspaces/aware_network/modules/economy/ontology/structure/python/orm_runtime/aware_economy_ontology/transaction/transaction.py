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
from aware_economy_ontology.transaction.transaction_enums import (
    TransactionKind,
    TransactionStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.wallet.wallet_public import WalletPublic


class Transaction(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    source_wallet_public: WalletPublic | None = Field(default=None, exclude=True)
    target_wallet_public: WalletPublic | None = Field(default=None, exclude=True)

    # Attributes
    capital_origin_id: UUID
    coin_amount: Annotated[Decimal, DecimalWire()]
    confirmed_at: datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    gas_price: Annotated[Decimal, DecimalWire()]
    idempotency_key: str | None = Field(default=None)
    kind: TransactionKind = Field(default=TransactionKind.transfer)
    nonce: int
    receiver_signature: str | None = Field(default=None)
    sender_signature: str | None = Field(default=None)
    source_previous_coin_balance: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    status: TransactionStatus = Field(default=TransactionStatus.created)
    target_previous_coin_balance: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    transaction_hash: str

    # Foreign Keys
    coin_id: UUID = Field(description="Foreign key for Transaction.coin")
    source_wallet_public_id: UUID | None = Field(
        default=None, description="Foreign key for Transaction.source_wallet_public"
    )
    target_wallet_public_id: UUID = Field(description="Foreign key for Transaction.target_wallet_public")

    @classmethod
    async def create(
        cls,
        source_wallet_public_id: UUID,
        capital_origin_id: UUID,
        target_wallet_public_id: UUID,
        coin_id: UUID,
        coin_amount: Annotated[Decimal, DecimalWire()],
        nonce: int,
        description: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transaction:
        """
        Creates a new transaction record.

        Receipt: Transaction(status=created) with hash/signature/nonce set by handler.
        Transaction is a root Economy transfer receipt; higher-level lanes may
        reference it but do not own its identity.
        """

        payload = {
            "source_wallet_public_id": source_wallet_public_id,
            "capital_origin_id": capital_origin_id,
            "target_wallet_public_id": target_wallet_public_id,
            "coin_id": coin_id,
            "coin_amount": coin_amount,
            "nonce": nonce,
            "description": description,
            "idempotency_key": idempotency_key,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Transaction):
            return value
        return Transaction.validate_invocation_value(value)

    @classmethod
    async def create_external_ingress(
        cls,
        capital_origin_id: UUID,
        target_wallet_public_id: UUID,
        coin_id: UUID,
        coin_amount: Annotated[Decimal, DecimalWire()],
        nonce: int,
        description: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transaction:
        """
        Creates an external-capital ingress receipt with no source WalletPublic.

        Receipt: Transaction(kind=external_ingress, status=created) with target,
        amount, and deterministic provider-evidence nonce.
        """

        payload = {
            "capital_origin_id": capital_origin_id,
            "target_wallet_public_id": target_wallet_public_id,
            "coin_id": coin_id,
            "coin_amount": coin_amount,
            "nonce": nonce,
            "description": description,
            "idempotency_key": idempotency_key,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_external_ingress", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Transaction):
            return value
        return Transaction.validate_invocation_value(value)


class TransactionCreateInput(BaseModel):
    source_wallet_public_id: UUID
    capital_origin_id: UUID
    target_wallet_public_id: UUID
    coin_id: UUID
    coin_amount: Annotated[Decimal, DecimalWire()]
    nonce: int
    description: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)


class TransactionCreateOutput(BaseModel):
    value: Transaction


class TransactionCreateExternalIngressInput(BaseModel):
    capital_origin_id: UUID
    target_wallet_public_id: UUID
    coin_id: UUID
    coin_amount: Annotated[Decimal, DecimalWire()]
    nonce: int
    description: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)


class TransactionCreateExternalIngressOutput(BaseModel):
    value: Transaction


FUNCTIONS = {
    "Transaction": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Creates a new transaction record.\n\nReceipt: Transaction(status=created) with hash/signature/nonce set by handler.\nTransaction is a root Economy transfer receipt; higher-level lanes may\nreference it but do not own its identity.",
                "is_constructor": True,
            },
            "input": TransactionCreateInput,
            "output": TransactionCreateOutput,
        },
        "create_external_ingress": {
            "canonical": {
                "name": "create_external_ingress",
                "description": "Creates an external-capital ingress receipt with no source WalletPublic.\n\nReceipt: Transaction(kind=external_ingress, status=created) with target,\namount, and deterministic provider-evidence nonce.",
                "is_constructor": True,
            },
            "input": TransactionCreateExternalIngressInput,
            "output": TransactionCreateExternalIngressOutput,
        },
    },
}

__all__ = [
    "Transaction",
    "TransactionCreateInput",
    "TransactionCreateOutput",
    "TransactionCreateExternalIngressInput",
    "TransactionCreateExternalIngressOutput",
    "FUNCTIONS",
]
