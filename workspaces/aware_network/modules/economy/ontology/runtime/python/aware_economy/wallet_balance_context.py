from __future__ import annotations

# Standard
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance

# Orm
from aware_orm.session.current_session_ctx import current_session


def resolve_unique_wallet_balance(
    *,
    wallet: Wallet,
    coin_id: UUID,
) -> WalletBalance | None:
    candidates: dict[str, WalletBalance] = {}

    for wallet_balance in wallet.wallet_balances:
        if wallet_balance.wallet_id != wallet.id or wallet_balance.coin_id != coin_id:
            continue
        candidates[str(wallet_balance.id)] = wallet_balance

    session = current_session()
    if session is not None:
        for obj in session.imap_all_objects():
            if not isinstance(obj, WalletBalance):
                continue
            if obj.wallet_id != wallet.id or obj.coin_id != coin_id:
                continue
            candidates[str(obj.id)] = obj

    if not candidates:
        return None
    if len(candidates) != 1:
        raise ValueError(
            "wallet balance context is ambiguous for wallet/coin pair: "
            f"wallet_id={wallet.id} coin_id={coin_id} count={len(candidates)}"
        )
    return next(iter(candidates.values()))


def ensure_wallet_balance_link(
    *, wallet: Wallet, wallet_balance: WalletBalance
) -> None:
    for index, existing in enumerate(wallet.wallet_balances):
        if str(existing.id) != str(wallet_balance.id):
            continue
        wallet.wallet_balances[index] = wallet_balance
        return
    wallet.wallet_balances.append(wallet_balance)
