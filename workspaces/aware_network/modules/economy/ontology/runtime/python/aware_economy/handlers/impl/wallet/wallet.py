from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.transaction.transaction import Transaction
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance
from aware_economy_ontology.wallet.wallet_external_ingress_application import WalletExternalIngressApplication

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.capital_amount import (
    ZERO_AMOUNT,
    amount_equal,
    non_negative_amount,
    positive_amount,
)
from aware_economy.ontology.materialization import (
    materialize_wallet_coin_balance_absolute,
    materialize_wallet_coin_balance_delta,
    materialize_wallet_coin_balance_reconciliation,
    materialize_wallet_coin_hold,
    materialize_wallet_coin_hold_release,
    materialize_wallet_coin_hold_settlement,
)
from aware_economy.stable_ids import stable_wallet_id
from aware_economy.wallet_custody import reject_dev_private_key_material

# Economy Ontology
from aware_economy_ontology.wallet.wallet_private import WalletPrivate
from aware_economy_ontology.wallet.wallet_public import WalletPublic
from aware_economy_ontology.stable_ids import (
    stable_wallet_external_ingress_application_id,
)

# --- AWARE: USER_IMPORTS END


async def build(address: str, public_key: str, private_key_encrypted: str) -> Wallet:
    """
    Creates a wallet + custody/key records in a single commit (wallet lane bootstrap).

    Receipt: Wallet + WalletPublic + WalletPrivate linked together.

    Fail-closed:
    - private_key_encrypted must be an opaque custody handle or encrypted key reference.
    - production-visible `dev:` private-key material is rejected.
    """

    # --- AWARE: LOGIC START build
    private_key_encrypted = reject_dev_private_key_material(
        private_key_encrypted,
        field_name="wallet private_key_encrypted",
    )
    wallet_public = await WalletPublic.build(address=address, public_key=public_key)
    wallet_private = await WalletPrivate.build(private_key_encrypted=private_key_encrypted)

    wallet_id = stable_wallet_id(
        public_key=wallet_public.public_key,
        private_key_encrypted=wallet_private.private_key_encrypted,
    )
    wallet = Wallet(
        id=wallet_id,
        wallet_public_id=wallet_public.id,
        wallet_private_id=wallet_private.id,
        public_key=wallet_public.public_key,
        private_key_encrypted=wallet_private.private_key_encrypted,
    )
    wallet.wallet_public = wallet_public
    wallet.wallet_private = wallet_private
    return wallet
    # --- AWARE: LOGIC END build


async def initiate_transaction(
    wallet: Wallet,
    target_wallet_public_id: UUID,
    coin_id: UUID,
    coin_amount: Annotated[Decimal, DecimalWire()],
    nonce: int,
    description: str | None = None,
    idempotency_key: str | None = None,
) -> Transaction:
    """
    Creates and signs a transaction from this wallet.

    Receipt: Transaction + Wallet.transactions link (commit-backed).
    """

    # --- AWARE: LOGIC START initiate_transaction
    if wallet.wallet_public_id is None:
        raise ValueError("wallet.initiate_transaction requires wallet_public_id")
    if nonce <= 0:
        raise ValueError("wallet.initiate_transaction requires nonce > 0")
    coin_amount = positive_amount(
        coin_amount,
        field_name="transaction coin_amount",
    )

    tx = await Transaction.create(
        source_wallet_public_id=wallet.wallet_public_id,
        capital_origin_id=wallet.wallet_public_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        coin_amount=coin_amount,
        nonce=nonce,
        description=description,
        idempotency_key=idempotency_key,
    )
    if not any(str(candidate.id) == str(tx.id) for candidate in wallet.transactions):
        wallet.transactions.append(tx)
    return tx
    # --- AWARE: LOGIC END initiate_transaction


async def set_coin_balance(wallet: Wallet, coin_id: UUID, balance: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
    """
    Sets absolute balance for a coin in this wallet.

    Receipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.
    """

    # --- AWARE: LOGIC START set_coin_balance
    return await materialize_wallet_coin_balance_absolute(
        wallet=wallet,
        coin_id=coin_id,
        balance=balance,
    )
    # --- AWARE: LOGIC END set_coin_balance


async def apply_coin_delta(wallet: Wallet, coin_id: UUID, delta: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
    """
    Applies a signed delta to this wallet coin balance.

    Receipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.

    Fail-closed:
    - Rejects zero delta.
    - Rejects negative resulting balance.
    """

    # --- AWARE: LOGIC START apply_coin_delta
    return await materialize_wallet_coin_balance_delta(
        wallet=wallet,
        coin_id=coin_id,
        delta=delta,
    )
    # --- AWARE: LOGIC END apply_coin_delta


async def apply_external_ingress(
    wallet: Wallet, transaction_id: UUID, coin_id: UUID, amount: Annotated[Decimal, DecimalWire()]
) -> WalletExternalIngressApplication:
    """
    Applies one verified external-ingress Transaction to this wallet exactly once.

    Receipt: contained WalletExternalIngressApplication plus updated WalletBalance.
    """

    # --- AWARE: LOGIC START apply_external_ingress
    amount = positive_amount(amount, field_name="external ingress amount")
    existing = next(
        (candidate for candidate in wallet.external_ingress_applications if candidate.transaction_id == transaction_id),
        None,
    )
    if existing is not None:
        if existing.coin_id != coin_id or not amount_equal(existing.amount, amount):
            raise ValueError("wallet.apply_external_ingress existing application mismatch")
        expected_new = (
            non_negative_amount(
                existing.previous_balance,
                field_name="external ingress previous_balance",
            )
            + amount
        )
        if not amount_equal(existing.new_balance, expected_new):
            raise ValueError("wallet.apply_external_ingress existing application balance mismatch")
        return existing

    matches = [balance for balance in wallet.wallet_balances if balance.coin_id == coin_id]
    if len(matches) > 1:
        raise ValueError("wallet.apply_external_ingress requires at most one WalletBalance per Coin")
    previous_balance = non_negative_amount(matches[0].balance, field_name="wallet balance") if matches else ZERO_AMOUNT
    wallet_balance = await materialize_wallet_coin_balance_delta(
        wallet=wallet,
        coin_id=coin_id,
        delta=amount,
    )
    application = WalletExternalIngressApplication(
        id=stable_wallet_external_ingress_application_id(
            transaction_id=transaction_id,
        ),
        wallet_id=wallet.id,
        transaction_id=transaction_id,
        coin_id=coin_id,
        amount=amount,
        previous_balance=previous_balance,
        new_balance=non_negative_amount(
            wallet_balance.balance,
            field_name="external ingress new_balance",
        ),
    )
    wallet.external_ingress_applications.append(application)
    return application
    # --- AWARE: LOGIC END apply_external_ingress


async def reconcile_coin_balance(
    wallet: Wallet,
    coin_id: UUID,
    expected_balance: Annotated[Decimal, DecimalWire()],
    new_balance: Annotated[Decimal, DecimalWire()],
) -> WalletBalance:
    """
    Applies an idempotent absolute balance transition for a coin.

    Receipt: WalletBalance(updated/created) linked under Wallet.wallet_balances.

    Fail-closed:
    - Rejects negative `new_balance`.
    - Allows no-op when current balance is already `new_balance`.
    - Otherwise requires current balance to match `expected_balance`.
    """

    # --- AWARE: LOGIC START reconcile_coin_balance
    return await materialize_wallet_coin_balance_reconciliation(
        wallet=wallet,
        coin_id=coin_id,
        expected_balance=expected_balance,
        new_balance=new_balance,
    )
    # --- AWARE: LOGIC END reconcile_coin_balance


async def reserve_coin_hold(wallet: Wallet, coin_id: UUID, amount: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
    """
    Moves available wallet capital into held capital for a reservation.

    Receipt: WalletBalance(held_balance increased, available_balance reduced).

    Fail-closed:
    - Rejects non-positive amount.
    - Rejects amount greater than current available balance.
    """

    # --- AWARE: LOGIC START reserve_coin_hold
    return await materialize_wallet_coin_hold(
        wallet=wallet,
        coin_id=coin_id,
        amount=amount,
    )
    # --- AWARE: LOGIC END reserve_coin_hold


async def release_coin_hold(wallet: Wallet, coin_id: UUID, amount: Annotated[Decimal, DecimalWire()]) -> WalletBalance:
    """
    Releases held wallet capital back to available balance.

    Receipt: WalletBalance(held_balance reduced, total balance unchanged).

    Fail-closed:
    - Rejects non-positive amount.
    - Rejects amount greater than current held balance.
    """

    # --- AWARE: LOGIC START release_coin_hold
    return await materialize_wallet_coin_hold_release(
        wallet=wallet,
        coin_id=coin_id,
        amount=amount,
    )
    # --- AWARE: LOGIC END release_coin_hold


async def settle_coin_hold(
    wallet: Wallet,
    coin_id: UUID,
    reserved_amount: Annotated[Decimal, DecimalWire()],
    final_cost: Annotated[Decimal, DecimalWire()],
) -> WalletBalance:
    """
    Consumes a reservation hold and debits the settled final cost from total balance.

    Receipt: WalletBalance(held_balance reduced by reserved_amount, balance reduced by final_cost).

    Fail-closed:
    - Rejects non-positive reserved_amount.
    - Rejects final_cost greater than reserved_amount.
    - Rejects reserved_amount greater than current held balance.
    """

    # --- AWARE: LOGIC START settle_coin_hold
    return await materialize_wallet_coin_hold_settlement(
        wallet=wallet,
        coin_id=coin_id,
        reserved_amount=reserved_amount,
        final_cost=final_cost,
    )
    # --- AWARE: LOGIC END settle_coin_hold
