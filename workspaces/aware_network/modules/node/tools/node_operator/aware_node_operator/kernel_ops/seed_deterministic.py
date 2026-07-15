from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import UUID

from aware_economy.stable_ids import stable_wallet_id


def build_seed_agent_profile_request(
    *,
    label: str,
    identity_id: UUID,
    spec_id: str,
    spec_version: int,
) -> dict[str, Any]:
    """
    Deterministic agent profile request used by kernel seed onboarding.

    NOTE: Keep this logic deterministic and stable: changes here can change seeded
    IdentityProfile ids (stable by public_handle).
    """

    raw = (label or "agent").strip().casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    if not slug:
        slug = "agent"

    # Stable + globally unique handle (idempotent across reruns and nodes).
    handle_prefix = slug[:20].rstrip("-") or "agent"
    identity_suffix = str(identity_id).split("-")[0]
    public_handle = f"{handle_prefix}-{identity_suffix}"

    words = [part for part in re.split(r"[-_]+", slug) if part]
    display_core = " ".join(part.capitalize() for part in words[:4]) or "Agent"
    display_name = f"{display_core} Agent"
    full_name = f"Aware {display_name}"
    bio = f"Seeded executor identity ({spec_id} v{spec_version})"

    return {
        "display_name": display_name,
        "public_handle": public_handle,
        "full_name": full_name,
        "country_code": "US",
        "language_code": "en",
        "bio": bio,
        "identity_type": "agent",
    }


@dataclass(frozen=True, slots=True)
class KernelWalletSeed:
    address: str
    public_key: str
    private_key_encrypted: str
    wallet_id: UUID


def economy_wallet_seed(*, identity_id: UUID) -> KernelWalletSeed:
    """
    v0 deterministic economy wallet seed.

    This matches the FinanceEntity.build anti-footgun contract:
    - public_key = sha256(identity_id)
    - private_key_encrypted = "dev:" + sha256(identity_id)
    - wallet_id = stable_wallet_id(pub, priv)
    """

    seed = sha256(str(identity_id).encode()).hexdigest()
    public_key = seed
    private_key_encrypted = f"dev:{seed}"
    address = f"dev:{seed}"
    wallet_id = stable_wallet_id(
        public_key=public_key,
        private_key_encrypted=private_key_encrypted,
    )
    return KernelWalletSeed(
        address=address,
        public_key=public_key,
        private_key_encrypted=private_key_encrypted,
        wallet_id=wallet_id,
    )


__all__ = [
    "KernelWalletSeed",
    "build_seed_agent_profile_request",
    "economy_wallet_seed",
]
