from __future__ import annotations

from collections.abc import Mapping

from aware_api_runtime.request_hash import compute_api_request_hash_from_mapping


def compute_service_operation_request_hash(
    *,
    request_payload: Mapping[str, object],
) -> str:
    """Return the canonical API request hash used by Service admission."""

    return compute_api_request_hash_from_mapping(payload=request_payload)


__all__ = ["compute_service_operation_request_hash"]
