from __future__ import annotations

# Standard
from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance

# Economy Runtime
from aware_economy.capital_amount import non_negative_amount

# Orm
from aware_orm.session.current_session_ctx import current_session


def _resolve_wallet_id(
    *,
    session_objects: Sequence[object],
    wallet_public_id: UUID,
    side: str,
) -> UUID | None:
    wallet_ids = sorted(
        {
            obj.id
            for obj in session_objects
            if isinstance(obj, Wallet) and obj.wallet_public_id == wallet_public_id
        },
        key=str,
    )
    if not wallet_ids:
        return None
    if len(wallet_ids) != 1:
        raise ValueError(
            f"transaction.create requires exactly one {side} wallet in active lane context"
        )
    return wallet_ids[0]


def _collect_wallet_coin_balances(
    *,
    session_objects: Sequence[object],
    wallet_id: UUID,
    coin_id: UUID,
) -> dict[str, Decimal]:
    balances_by_id: dict[str, Decimal] = {}

    for obj in session_objects:
        if not isinstance(obj, WalletBalance):
            continue
        if obj.wallet_id != wallet_id or obj.coin_id != coin_id:
            continue
        balances_by_id[str(obj.id)] = non_negative_amount(
            obj.balance,
            field_name="wallet balance",
        )

    for obj in session_objects:
        if not isinstance(obj, Wallet):
            continue
        if obj.id != wallet_id:
            continue
        for wallet_balance in obj.wallet_balances:
            if (
                wallet_balance.wallet_id != wallet_id
                or wallet_balance.coin_id != coin_id
            ):
                continue
            balances_by_id[str(wallet_balance.id)] = non_negative_amount(
                wallet_balance.balance,
                field_name="wallet balance",
            )
    return balances_by_id


def _resolve_known_wallet_balance(
    *,
    session_objects: Sequence[object],
    wallet_public_id: UUID,
    coin_id: UUID,
    side: str,
) -> Decimal | None:
    wallet_id = _resolve_wallet_id(
        session_objects=session_objects,
        wallet_public_id=wallet_public_id,
        side=side,
    )
    if wallet_id is None:
        return None

    balances_by_id = _collect_wallet_coin_balances(
        session_objects=session_objects,
        wallet_id=wallet_id,
        coin_id=coin_id,
    )
    if not balances_by_id:
        return None
    if len(balances_by_id) != 1:
        raise ValueError(
            f"transaction.create requires exactly one {side} wallet coin balance in active lane context"
        )
    return next(iter(balances_by_id.values()))


def resolve_known_transaction_previous_balances(
    *,
    source_wallet_public_id: UUID,
    target_wallet_public_id: UUID,
    coin_id: UUID,
) -> tuple[Decimal | None, Decimal | None]:
    session = current_session()
    if session is None:
        return None, None

    session_objects = list(session.imap_all_objects())
    source_previous_balance = _resolve_known_wallet_balance(
        session_objects=session_objects,
        wallet_public_id=source_wallet_public_id,
        coin_id=coin_id,
        side="source",
    )
    target_previous_balance = _resolve_known_wallet_balance(
        session_objects=session_objects,
        wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        side="target",
    )
    return source_previous_balance, target_previous_balance
