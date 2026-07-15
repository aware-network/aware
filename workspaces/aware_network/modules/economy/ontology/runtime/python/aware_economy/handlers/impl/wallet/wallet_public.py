from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.escrow.escrow import Escrow
from aware_economy_ontology.wallet.wallet_public import WalletPublic

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.capital_amount import positive_amount
from aware_economy.stable_ids import stable_wallet_public_id

# --- AWARE: USER_IMPORTS END


async def build(address: str, public_key: str) -> WalletPublic:
    """
    Creates a wallet public record.

    Receipt: WalletPublic (address + public_key).
    """

    # --- AWARE: LOGIC START build
    wallet_public_id = stable_wallet_public_id(public_key=public_key)
    return WalletPublic(id=wallet_public_id, address=address, public_key=public_key)
    # --- AWARE: LOGIC END build


async def lock_escrow(
    wallet_public: WalletPublic,
    smart_contract_reservation_id: UUID,
    op_nonce: int,
    coin_id: UUID,
    locked_amount: Annotated[Decimal, DecimalWire()],
    description: str | None = None,
) -> Escrow:
    """
    Locks funds by creating an escrow under this wallet public key.

    Receipt: Escrow(status=locked) + WalletPublic.escrows link (commit-backed).
    """

    # --- AWARE: LOGIC START lock_escrow
    if op_nonce <= 0:
        raise ValueError("wallet_public.lock_escrow requires op_nonce > 0")
    locked_amount = positive_amount(
        locked_amount,
        field_name="escrow locked_amount",
    )

    escrow = await Escrow.create_via_wallet_public(
        smart_contract_reservation_id=smart_contract_reservation_id,
        wallet_public_id=wallet_public.id,
        op_nonce=op_nonce,
        coin_id=coin_id,
        locked_amount=locked_amount,
        description=description,
    )
    wallet_public.escrows.append(escrow)
    wallet_public.nonce_counter = max(wallet_public.nonce_counter, op_nonce)
    return escrow
    # --- AWARE: LOGIC END lock_escrow
