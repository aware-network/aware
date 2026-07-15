from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Economy Ontology
from aware_economy_ontology.wallet.wallet_private import WalletPrivate

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.stable_ids import stable_wallet_private_id
from aware_economy.wallet_custody import reject_dev_private_key_material

# --- AWARE: USER_IMPORTS END


async def build(private_key_encrypted: str) -> WalletPrivate:
    """
    Creates a wallet private/custody record.

    Receipt: WalletPrivate (opaque custody handle or encrypted key reference).

    Fail-closed:
    - production-visible `dev:` private-key material is rejected.
    """

    # --- AWARE: LOGIC START build
    private_key_encrypted = reject_dev_private_key_material(
        private_key_encrypted,
        field_name="wallet private_key_encrypted",
    )
    wallet_private_id = stable_wallet_private_id(private_key_encrypted=private_key_encrypted)
    return WalletPrivate(
        id=wallet_private_id,
        private_key_encrypted=private_key_encrypted,
    )
    # --- AWARE: LOGIC END build
