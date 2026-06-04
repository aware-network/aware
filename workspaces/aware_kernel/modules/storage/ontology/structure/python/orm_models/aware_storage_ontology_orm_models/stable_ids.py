# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_STORAGE = uuid5(NAMESPACE_URL, "aware://storage/v1")


def stable_storage_blob_id(*, sha: str) -> UUID:
    """Compiler-generated from constructor identity keys: sha"""

    sha_norm = (sha or "").casefold().strip()
    return uuid5(NS_STORAGE, f"aware:storage_blob:{sha_norm}")


def stable_storage_bucket_id(*, name: str) -> UUID:
    """Compiler-generated from constructor identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_STORAGE, f"aware:storage_bucket:{name_norm}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "91115838-1bed-5d70-894b-8b7dbeb9ba6a": ("stable_storage_bucket_id", ("name",)),
    "947d63f4-3429-56ee-8d6c-d93853fd3e83": ("stable_storage_blob_id", ("sha",)),
}

__all__ = [
    "stable_storage_blob_id",
    "stable_storage_bucket_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
