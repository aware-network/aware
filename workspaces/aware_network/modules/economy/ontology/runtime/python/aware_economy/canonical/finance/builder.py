"""Finance domain builders (canonical ORM).

These functions are intended to be called by runtime handlers. They must not
invoke the environment call-chain.
"""

from __future__ import annotations

from uuid import UUID

from aware_orm.session.session import Session

from aware_economy_ontology.finance.finance_entity import FinanceEntity

from aware_economy.canonical.wallet.builder import build_wallet_for_identity


async def build_finance_entity(
    *,
    session: Session | None = None,
    identity_id: UUID,
    role_key: str = "primary",
) -> FinanceEntity:
    wallet = await build_wallet_for_identity(
        session=session,
        identity_id=identity_id,
        role_key=role_key,
    )

    finance_entity = FinanceEntity(
        identity_id=identity_id,
        role_key=role_key,
        wallet=wallet,
        wallet_id=wallet.id,
    )

    # Keep in-memory graph consistent for FS/no-db sessions.
    finance_entity.wallet = wallet
    return finance_entity


__all__ = ["build_finance_entity"]
