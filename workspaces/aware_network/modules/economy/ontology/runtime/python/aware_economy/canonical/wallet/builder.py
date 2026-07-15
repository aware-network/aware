"""Wallet domain builders (canonical ORM)."""

from __future__ import annotations

from uuid import UUID

from aware_orm.session.session import Session

from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_private import WalletPrivate
from aware_economy_ontology.wallet.wallet_public import WalletPublic

from aware_economy.stable_ids import (
    stable_wallet_id,
    stable_wallet_private_id,
    stable_wallet_public_id,
)
from aware_economy.wallet_custody import derive_wallet_custody_material


async def build_wallet_for_identity(
    *, session: Session | None = None, identity_id: UUID, role_key: str = "primary"
) -> Wallet:
    _ = session
    custody = derive_wallet_custody_material(
        identity_id=identity_id,
        role_key=role_key,
    )

    wallet_public = WalletPublic(
        id=stable_wallet_public_id(public_key=custody.public_key),
        address=custody.address,
        public_key=custody.public_key,
    )
    wallet_private = WalletPrivate(
        id=stable_wallet_private_id(
            private_key_encrypted=custody.private_key_encrypted
        ),
        private_key_encrypted=custody.private_key_encrypted,
    )

    wallet = Wallet(
        id=stable_wallet_id(
            private_key_encrypted=custody.private_key_encrypted,
            public_key=custody.public_key,
        ),
        private_key_encrypted=custody.private_key_encrypted,
        public_key=custody.public_key,
        wallet_public_id=wallet_public.id,
        wallet_private_id=wallet_private.id,
    )

    # Keep in-memory graph consistent for FS/no-db sessions.
    wallet.wallet_public = wallet_public
    wallet.wallet_private = wallet_private
    return wallet


__all__ = ["build_wallet_for_identity"]
