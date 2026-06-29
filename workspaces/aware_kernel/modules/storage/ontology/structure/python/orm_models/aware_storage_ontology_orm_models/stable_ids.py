# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_STORAGE = uuid5(NAMESPACE_URL, "aware://storage/v1")


def stable_storage_blob_id(*, sha: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: sha"""

    sha_norm = (sha or "").casefold().strip()
    return uuid5(NS_STORAGE, f"aware:storage_blob:{sha_norm}")


def stable_storage_bucket_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_STORAGE, f"aware:storage_bucket:{name_norm}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "20ce9a91-cb0a-5517-b919-e9256e5c4fa8": ("stable_storage_blob_id", ("sha",)),
    "972c654a-5d48-54f4-9a67-974fac6f96d1": ("stable_storage_bucket_id", ("name",)),
}

__all__ = [
    "stable_storage_blob_id",
    "stable_storage_bucket_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
