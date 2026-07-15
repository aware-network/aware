from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity_ontology.stable_ids import stable_identity_id


@dataclass(frozen=True, slots=True)
class SeedKeypair:
    """
    Seed-owned Ed25519 keypair (server-side).

    Contract:
    - Public keys may be stored in repo seed specs.
    - Private keys MUST be provided via secrets (env/file mounts) and never in repo.
    """

    label: str
    public_key: str
    private_key: str


def _parse_seed_keypairs(payload: Any) -> dict[str, SeedKeypair]:
    if isinstance(payload, list):
        out: dict[str, SeedKeypair] = {}
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Seed keys JSON list entries must be objects")
            label = str(item.get("label") or item.get("name") or "").strip()
            public_key = str(
                item.get("public_key") or item.get("publicKey") or ""
            ).strip()
            private_key = str(
                item.get("private_key") or item.get("privateKey") or ""
            ).strip()
            if not label:
                raise ValueError("Seed keys JSON entries require a non-empty 'label'")
            if not public_key or not private_key:
                raise ValueError(
                    f"Seed keys JSON entry {label!r} missing public_key/private_key"
                )
            out[label] = SeedKeypair(
                label=label, public_key=public_key, private_key=private_key
            )
        return out

    if isinstance(payload, dict):
        if "identities" in payload:
            return _parse_seed_keypairs(payload["identities"])
        if "keys" in payload:
            return _parse_seed_keypairs(payload["keys"])
        out: dict[str, SeedKeypair] = {}
        for label, item in payload.items():
            if not isinstance(item, dict):
                raise ValueError("Seed keys JSON dict entries must be objects")
            public_key = str(
                item.get("public_key") or item.get("publicKey") or ""
            ).strip()
            private_key = str(
                item.get("private_key") or item.get("privateKey") or ""
            ).strip()
            if not public_key or not private_key:
                raise ValueError(
                    f"Seed keys JSON entry {label!r} missing public_key/private_key"
                )
            key_label = str(label).strip() or "default"
            out[key_label] = SeedKeypair(
                label=key_label, public_key=public_key, private_key=private_key
            )
        return out

    raise ValueError("Seed keys payload must be a list or dict")


def load_seed_keypairs() -> dict[str, SeedKeypair]:
    """
    Load seed keypairs from secrets.

    Supported inputs:
    - `AWARE_KERNEL_SEED_KEYS_JSON`: JSON payload (list or dict).
    - `AWARE_KERNEL_SEED_KEYS_FILE`: path to JSON file.
    """

    raw = os.getenv("AWARE_KERNEL_SEED_KEYS_JSON")
    keys_file = os.getenv("AWARE_KERNEL_SEED_KEYS_FILE")
    if (raw is None or not raw.strip()) and keys_file and keys_file.strip():
        raw = Path(keys_file.strip()).read_text(encoding="utf-8")
    if raw is None or not raw.strip():
        raise RuntimeError(
            "Kernel seed apply requires private keys. Set either "
            "AWARE_KERNEL_SEED_KEYS_JSON or AWARE_KERNEL_SEED_KEYS_FILE."
        )

    payload = json.loads(raw)
    keypairs = _parse_seed_keypairs(payload)
    if not keypairs:
        raise RuntimeError("Kernel seed keys resolved to an empty key set")
    return keypairs


def resolve_seed_keypair(
    *,
    keypairs: dict[str, SeedKeypair],
    identity_id: UUID,
    identity_type_value: str,
) -> SeedKeypair:
    """
    Resolve a keypair deterministically from the identity stable id.

    This prevents "label routing" hacks: the seed runner must prove the key material
    matches the identity it claims to act as.
    """

    matches: list[SeedKeypair] = []
    for keypair in keypairs.values():
        canonical_public_key, _ = canonicalize_ed25519_public_key(keypair.public_key)
        resolved_identity_id = stable_identity_id(
            public_key=canonical_public_key,
            type=identity_type_value,
        )
        if resolved_identity_id == identity_id:
            matches.append(keypair)

    if not matches:
        available = sorted(keypairs.keys())
        raise RuntimeError(
            "No configured seed keypair matches identity_id="
            f"{identity_id} identity_type={identity_type_value!r}. Available labels: {available}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            "Multiple configured seed keypairs resolve to the same identity_id="
            f"{identity_id} identity_type={identity_type_value!r}. Labels: {[m.label for m in matches]}"
        )
    return matches[0]


__all__ = [
    "SeedKeypair",
    "load_seed_keypairs",
    "resolve_seed_keypair",
]
