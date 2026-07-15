from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.finance.finance_entity import FinanceEntity

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.stable_ids import stable_finance_entity_id, stable_wallet_id
from aware_economy.wallet_custody import (
    derive_wallet_custody_material,
    normalize_finance_role_key,
)

# --- AWARE: USER_IMPORTS END


async def build(identity_id: UUID, wallet_id: UUID, role_key: str = "primary") -> FinanceEntity:
    """
    Creates a FinanceEntity for the given identity.

    Receipt: FinanceEntity(id=stable(identity_id), role_key=role_key) referencing the deterministic
    Wallet id.

    Notes:
    - This constructor is finance_entity-lane only (it does not create wallet-lane commits).
    - Wallet objects are created via Wallet.build in the `wallet` lane (separate receipt).
    - It does not mutate the Identity.
    - role_key declares the wallet purpose for v0 readiness; `primary` is the default person/agent
    wallet role.

    Validation:
    - wallet_id must match the deterministic wallet id derived from identity_id + role_key custody
    material (v0 anti-footgun).
    """

    # --- AWARE: LOGIC START build
    normalized_role_key = normalize_finance_role_key(role_key)
    custody = derive_wallet_custody_material(
        identity_id=identity_id,
        role_key=normalized_role_key,
    )
    expected_wallet_id = stable_wallet_id(
        public_key=custody.public_key,
        private_key_encrypted=custody.private_key_encrypted,
    )
    if wallet_id != expected_wallet_id:
        raise ValueError(
            "finance_entity.build wallet_id mismatch (anti-footgun): "
            f"identity_id={identity_id} role_key={normalized_role_key} "
            f"wallet_id={wallet_id} expected_wallet_id={expected_wallet_id}"
        )
    finance_entity_id = stable_finance_entity_id(identity_id=identity_id)
    finance_entity = FinanceEntity(
        id=finance_entity_id,
        identity_id=identity_id,
        wallet_id=expected_wallet_id,
        role_key=normalized_role_key,
    )
    return finance_entity
    # --- AWARE: LOGIC END build
