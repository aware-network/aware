from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Code
from aware_code.types import JsonObject

# Storage Ontology
from aware_storage_ontology.bucket.storage_bucket_enums import StorageBackend
from aware_storage_ontology.bucket.storage_bucket import StorageBucket

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    backend: StorageBackend = StorageBackend.local,
    allowed_mime_types: list[str] = [],
    config: JsonObject | None = None,
) -> StorageBucket:
    """
    Create a deterministic storage bucket metadata root.

    Contract:
    - Identity is deterministic from `(name)`.
    - Backend/config values are mutable policy metadata.
    """

    # --- AWARE: LOGIC START build
    _aware_construct_values_0 = {
        "name": name,
        "backend": backend,
        "allowed_mime_types": allowed_mime_types,
        "config": config,
    }
    _aware_stable_binding_0 = CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID.get(
        "91115838-1bed-5d70-894b-8b7dbeb9ba6a"
    )
    if _aware_stable_binding_0 is not None:
        _aware_stable_fn_0, _aware_stable_key_names_0 = _aware_stable_binding_0
        _aware_missing_stable_keys_0 = [
            key for key in _aware_stable_key_names_0 if key not in _aware_construct_values_0
        ]
        if _aware_missing_stable_keys_0:
            raise RuntimeError(
                "StorageBucket.build cannot construct StorageBucket: missing stable identity values"
                + f": {_aware_missing_stable_keys_0}"
            )
        _aware_stable_values_0 = {key: _aware_construct_values_0[key] for key in _aware_stable_key_names_0}
        _aware_construct_id_0 = getattr(import_module("aware_storage_ontology.stable_ids"), _aware_stable_fn_0)(
            **_aware_stable_values_0
        )
        _aware_constructed_0 = StorageBucket.get_by_id_cached(_aware_construct_id_0)
        if _aware_constructed_0 is None:
            _aware_constructed_0 = StorageBucket(id=_aware_construct_id_0, **_aware_construct_values_0)
    else:
        _aware_constructed_0 = StorageBucket(**_aware_construct_values_0)
    return _aware_constructed_0
    # --- AWARE: LOGIC END build
