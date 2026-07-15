from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID


PRIMARY_FINANCE_ROLE_KEY = "primary"
WALLET_CUSTODY_PREFIX = "custody:aware-wallet:v1"


@dataclass(frozen=True, slots=True)
class WalletCustodyMaterial:
    identity_id: UUID
    role_key: str
    public_key: str
    address: str
    private_key_encrypted: str


def normalize_finance_role_key(role_key: str | None = None) -> str:
    normalized = str(role_key or PRIMARY_FINANCE_ROLE_KEY).strip().casefold()
    if not normalized:
        raise ValueError("finance_role_key is required")
    return normalized


def derive_wallet_custody_material(
    *,
    identity_id: UUID,
    role_key: str | None = None,
) -> WalletCustodyMaterial:
    normalized_role = normalize_finance_role_key(role_key)
    digest = sha256(f"{identity_id}:{normalized_role}".encode()).hexdigest()
    return WalletCustodyMaterial(
        identity_id=identity_id,
        role_key=normalized_role,
        public_key=f"aware-wallet-v1:{digest}",
        address=f"0x{digest[:40]}",
        private_key_encrypted=f"{WALLET_CUSTODY_PREFIX}:{digest}",
    )


def reject_dev_private_key_material(value: str, *, field_name: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    if raw.casefold().startswith("dev:"):
        raise ValueError(
            f"{field_name} must be an opaque custody handle or encrypted key reference, not dev material"
        )
    return raw


__all__ = [
    "PRIMARY_FINANCE_ROLE_KEY",
    "WALLET_CUSTODY_PREFIX",
    "WalletCustodyMaterial",
    "derive_wallet_custody_material",
    "normalize_finance_role_key",
    "reject_dev_private_key_material",
]
