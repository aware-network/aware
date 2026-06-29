from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Storage Ontology
from aware_storage_ontology.blob.storage_blob import StorageBlob

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
import re

from aware_storage.stable_ids import stable_storage_blob_id
from aware_utils.logging import logger

# --- AWARE: USER_IMPORTS END


async def create(sha: str, mime_type: str, size_bytes: int) -> StorageBlob:
    """
    Registers a StorageBlob metadata record for already-uploaded bytes.

    Contract:
    - Commits must never include raw bytes.
    - Bytes are uploaded out-of-band (HTTP data-plane).
    - This constructor records the immutable metadata required to resolve and validate bytes.

    Parameters:
        sha: SHA-256 hex of the raw bytes.
        mime_type: MIME type of the blob.
        size_bytes: Size of the blob in bytes.

    Returns: The created (or idempotently re-used) StorageBlob.
    """

    # --- AWARE: LOGIC START create
    normalized_sha = (
        "" if ("" if sha is None else sha).strip() is None else ("" if sha is None else sha).strip()
    ).lower()
    if not (normalized_sha != ""):
        raise RuntimeError("sha is required")
    if not (__import__("re").fullmatch("[0-9a-f]{64}", normalized_sha) is not None):
        raise RuntimeError("sha must be a 64-char lowercase hex SHA-256 digest")
    if not (size_bytes >= 0):
        raise RuntimeError("size_bytes must be >= 0")
    normalized_mime = (
        "application/octet-stream"
        if (
            ""
            if ("" if mime_type is None else mime_type).strip() is None
            else ("" if mime_type is None else mime_type).strip()
        ).strip()
        == ""
        else (
            ""
            if ("" if mime_type is None else mime_type).strip() is None
            else ("" if mime_type is None else mime_type).strip()
        )
    )
    object_key = "".join(
        "" if operand is None else operand
        for operand in (
            ("" if normalized_sha is None else normalized_sha)[0:2],
            "/",
            ("" if normalized_sha is None else normalized_sha)[2:],
        )
    )
    _aware_construct_values_6 = {
        "sha": normalized_sha,
        "mime_type": normalized_mime,
        "size_bytes": size_bytes,
        "object_key": object_key,
    }
    _aware_stable_binding_6 = CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID.get(
        "947d63f4-3429-56ee-8d6c-d93853fd3e83"
    )
    if _aware_stable_binding_6 is not None:
        _aware_stable_fn_6, _aware_stable_key_names_6 = _aware_stable_binding_6
        _aware_missing_stable_keys_6 = [
            key for key in _aware_stable_key_names_6 if key not in _aware_construct_values_6
        ]
        if _aware_missing_stable_keys_6:
            raise RuntimeError(
                "StorageBlob.create cannot construct StorageBlob: missing stable identity values"
                + f": {_aware_missing_stable_keys_6}"
            )
        _aware_stable_values_6 = {key: _aware_construct_values_6[key] for key in _aware_stable_key_names_6}
        _aware_construct_id_6 = getattr(import_module("aware_storage_ontology.stable_ids"), _aware_stable_fn_6)(
            **_aware_stable_values_6
        )
        _aware_constructed_6 = StorageBlob.get_by_id_cached(_aware_construct_id_6)
        if _aware_constructed_6 is None:
            _aware_constructed_6 = StorageBlob(id=_aware_construct_id_6, **_aware_construct_values_6)
    else:
        _aware_constructed_6 = StorageBlob(**_aware_construct_values_6)
    return _aware_constructed_6
    # --- AWARE: LOGIC END create
