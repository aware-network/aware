from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.transaction.transaction import Transaction

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from decimal import Decimal
from hashlib import sha256

# Economy Ontology
from aware_economy_ontology.stable_ids import stable_transaction_id
from aware_economy_ontology.transaction.transaction_enums import (
    TransactionKind,
    TransactionStatus,
)

# Economy Runtime
from aware_economy.transaction_balance_context import (
    resolve_known_transaction_previous_balances,
)
from aware_economy.capital_amount import (
    amount_equal,
    canonical_amount_text,
    positive_amount,
)

# Orm
from aware_orm.session.current_session_ctx import current_session

# --- AWARE: USER_IMPORTS END


async def create(
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

    # --- AWARE: LOGIC START create
    coin_amount = positive_amount(
        coin_amount,
        field_name="transaction coin_amount",
    )
    if capital_origin_id != source_wallet_public_id:
        raise ValueError("transaction.create requires capital_origin_id to equal source_wallet_public_id")
    if nonce <= 0:
        raise ValueError("transaction.create requires nonce > 0")

    transaction_id = stable_transaction_id(
        capital_origin_id=capital_origin_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        nonce=nonce,
    )
    session = current_session()
    existing = session.imap_get(Transaction, transaction_id) if session is not None else None
    if existing is not None:
        if str(existing.source_wallet_public_id) != str(source_wallet_public_id):
            raise ValueError("transaction.create existing source_wallet_public_id mismatch")
        if existing.capital_origin_id != capital_origin_id:
            raise ValueError("transaction.create existing capital_origin_id mismatch")
        if existing.kind != TransactionKind.transfer:
            raise ValueError("transaction.create existing transaction kind mismatch")
        if str(existing.target_wallet_public_id) != str(target_wallet_public_id):
            raise ValueError("transaction.create existing target_wallet_public_id mismatch")
        if str(existing.coin_id) != str(coin_id):
            raise ValueError("transaction.create existing coin_id mismatch")
        if int(existing.nonce) != int(nonce):
            raise ValueError("transaction.create existing nonce mismatch")
        if not amount_equal(existing.coin_amount, coin_amount):
            raise ValueError("transaction.create existing coin_amount mismatch")
        return existing

    amount_key = canonical_amount_text(
        coin_amount,
        field_name="transaction coin_amount",
    )
    hash_payload = (
        f"{source_wallet_public_id}:{target_wallet_public_id}:{coin_id}:{amount_key}:{nonce}:{description or ''}"
    )
    transaction_hash = sha256(hash_payload.encode()).hexdigest()
    sender_signature = sha256(f"tx:{transaction_hash}:sender:{source_wallet_public_id}".encode()).hexdigest()

    source_previous_coin_balance, target_previous_coin_balance = resolve_known_transaction_previous_balances(
        source_wallet_public_id=source_wallet_public_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
    )

    if source_previous_coin_balance is not None and source_previous_coin_balance < coin_amount:
        raise ValueError("transaction.create insufficient known source wallet balance for requested transfer amount")

    return Transaction(
        id=transaction_id,
        source_wallet_public_id=source_wallet_public_id,
        capital_origin_id=capital_origin_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        coin_amount=coin_amount,
        description=description,
        idempotency_key=idempotency_key,
        kind=TransactionKind.transfer,
        gas_price=Decimal("0.00000001"),
        nonce=nonce,
        sender_signature=sender_signature,
        source_previous_coin_balance=source_previous_coin_balance,
        target_previous_coin_balance=target_previous_coin_balance,
        transaction_hash=transaction_hash,
        status=TransactionStatus.created,
    )
    # --- AWARE: LOGIC END create


async def create_external_ingress(
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

    # --- AWARE: LOGIC START create_external_ingress
    coin_amount = positive_amount(
        coin_amount,
        field_name="external ingress coin_amount",
    )
    if nonce <= 0:
        raise ValueError("transaction.create_external_ingress requires nonce > 0")

    transaction_id = stable_transaction_id(
        capital_origin_id=capital_origin_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        nonce=nonce,
    )
    session = current_session()
    existing = session.imap_get(Transaction, transaction_id) if session is not None else None
    if existing is not None:
        if existing.source_wallet_public_id is not None:
            raise ValueError("transaction.create_external_ingress existing source_wallet_public_id must be absent")
        if existing.capital_origin_id != capital_origin_id:
            raise ValueError("transaction.create_external_ingress existing capital_origin_id mismatch")
        if existing.target_wallet_public_id != target_wallet_public_id:
            raise ValueError("transaction.create_external_ingress existing target_wallet_public_id mismatch")
        if existing.coin_id != coin_id:
            raise ValueError("transaction.create_external_ingress existing coin_id mismatch")
        if existing.nonce != nonce:
            raise ValueError("transaction.create_external_ingress existing nonce mismatch")
        if existing.kind != TransactionKind.external_ingress:
            raise ValueError("transaction.create_external_ingress existing transaction kind mismatch")
        if not amount_equal(existing.coin_amount, coin_amount):
            raise ValueError("transaction.create_external_ingress existing coin_amount mismatch")
        return existing

    amount_key = canonical_amount_text(
        coin_amount,
        field_name="external ingress coin_amount",
    )
    transaction_hash = sha256(
        (
            "external_ingress:"
            f"{capital_origin_id}:{target_wallet_public_id}:{coin_id}:"
            f"{amount_key}:{nonce}:{description or ''}"
        ).encode()
    ).hexdigest()
    return Transaction(
        id=transaction_id,
        source_wallet_public_id=None,
        capital_origin_id=capital_origin_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        coin_amount=coin_amount,
        description=description,
        idempotency_key=idempotency_key,
        kind=TransactionKind.external_ingress,
        gas_price=Decimal("0"),
        nonce=nonce,
        sender_signature=None,
        source_previous_coin_balance=None,
        target_previous_coin_balance=None,
        transaction_hash=transaction_hash,
        status=TransactionStatus.created,
    )
    # --- AWARE: LOGIC END create_external_ingress
