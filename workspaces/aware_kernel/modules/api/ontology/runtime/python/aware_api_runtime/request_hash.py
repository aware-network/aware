from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from decimal import Decimal
from hashlib import sha256
import json
from uuid import UUID

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance

from aware_api_runtime.service_protocol import decode_inline_value_instance_to_mapping_strict


def compute_api_request_hash_from_inline_value_instance(
    *,
    inline_value_instance: InlineValueInstance,
    class_config: ClassConfig,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> str:
    payload = decode_inline_value_instance_to_mapping_strict(
        inline_value_instance=inline_value_instance,
        class_config=class_config,
        class_configs_by_id=class_configs_by_id,
    )
    return compute_api_request_hash_from_mapping(payload=payload)


def compute_api_request_hash_from_mapping(
    *,
    payload: Mapping[str, object],
) -> str:
    canonical = json.dumps(
        _normalize_hash_payload_mapping(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(canonical).hexdigest()}"


def _normalize_hash_payload_mapping(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        str(key): _normalize_hash_payload_value(value)
        for key, value in payload.items()
    }


def _normalize_hash_payload_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return _normalize_hash_payload_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize_hash_payload_value(item) for item in value]
    raise RuntimeError(
        "API request hash canonicalization encountered unsupported payload value type: "
        f"{type(value)!r}"
    )


__all__ = [
    "compute_api_request_hash_from_inline_value_instance",
    "compute_api_request_hash_from_mapping",
]
