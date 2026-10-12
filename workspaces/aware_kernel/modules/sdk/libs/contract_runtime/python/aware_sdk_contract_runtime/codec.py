from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from aware_meta_type_schema import (
    TypeSchemaDecodeError,
    canonical_json,
    decode_schema_slice,
)

from .model import (
    SDK_CONTRACT,
    SdkContractManifest,
    SdkMethodContract,
    SdkOperationContract,
    SdkTargetContract,
)

SUPPORTED_SDK_CONTRACTS = (SDK_CONTRACT,)


class SdkContractDecodeError(ValueError):
    pass


def negotiate_sdk_contract(
    offered: Sequence[str], *, supported: Sequence[str] = SUPPORTED_SDK_CONTRACTS
) -> str:
    offered_values = _text_sequence(offered, "offered")
    supported_values = _text_sequence(supported, "supported")
    for contract in supported_values:
        if contract in offered_values:
            return contract
    raise SdkContractDecodeError(
        f"no supported SDK contract; offered={list(offered_values)!r}, supported={list(supported_values)!r}"
    )


def encode_sdk_contract_manifest(value: SdkContractManifest) -> bytes:
    if type(value) is not SdkContractManifest:
        raise TypeError("value must be exact SdkContractManifest")
    return canonical_json(value.to_wire()).encode()


def decode_sdk_contract_manifest(payload: bytes | str) -> SdkContractManifest:
    root = _root(payload)
    _exact(
        root,
        {
            "contract",
            "sdk_ref",
            "semantic_version",
            "targets",
            "schema_slices",
            "operations",
            "methods",
            "manifest_digest",
        },
        "$",
    )
    contract = _text(root, "contract", "$")
    negotiate_sdk_contract((contract,))
    try:
        return SdkContractManifest(
            sdk_ref=_text(root, "sdk_ref", "$"),
            semantic_version=_text(root, "semantic_version", "$"),
            targets=tuple(
                _target(value, f"$.targets[{index}]")
                for index, value in enumerate(_array(root, "targets", "$"))
            ),
            schema_slices=tuple(
                decode_schema_slice(canonical_json(value))
                for value in _array(root, "schema_slices", "$")
            ),
            operations=tuple(
                _operation(value, f"$.operations[{index}]")
                for index, value in enumerate(_array(root, "operations", "$"))
            ),
            methods=tuple(
                _method(value, f"$.methods[{index}]")
                for index, value in enumerate(_array(root, "methods", "$"))
            ),
            manifest_digest=_text(root, "manifest_digest", "$"),
        )
    except (TypeError, ValueError, TypeSchemaDecodeError) as error:
        if isinstance(error, SdkContractDecodeError):
            raise
        raise SdkContractDecodeError(
            f"manifest violates {contract}: {error}"
        ) from error


def _target(value: object, path: str) -> SdkTargetContract:
    item = _object(value, path)
    _exact(item, {"language", "root_dir", "package_dir"}, path)
    return SdkTargetContract(
        _text(item, "language", path),
        _text(item, "root_dir", path),
        _text(item, "package_dir", path),
    )


def _operation(value: object, path: str) -> SdkOperationContract:
    item = _object(value, path)
    _exact(
        item,
        {
            "operation_ref",
            "request_schema_digest",
            "result_schema_digest",
            "error_schema_digests",
            "provider_operation_ref",
            "endpoint_refs",
            "dependency_operation_refs",
        },
        path,
    )
    return SdkOperationContract(
        _text(item, "operation_ref", path),
        _text(item, "request_schema_digest", path),
        _text(item, "result_schema_digest", path),
        _text_array(item, "error_schema_digests", path),
        _text(item, "provider_operation_ref", path),
        _text_array(item, "endpoint_refs", path),
        _text_array(item, "dependency_operation_refs", path),
    )


def _method(value: object, path: str) -> SdkMethodContract:
    item = _object(value, path)
    fields = {
        "method_ref",
        "operation_ref",
        "method_family",
        "effect",
        "mutation_scope",
        "confirmation_policy",
        "execution_mode",
    }
    _exact(item, fields, path)
    return SdkMethodContract(
        _text(item, "method_ref", path),
        _text(item, "operation_ref", path),
        _text(item, "method_family", path),
        _text(item, "effect", path),
        _text(item, "mutation_scope", path),
        _text(item, "confirmation_policy", path),
        _text(item, "execution_mode", path),
    )


def _root(payload: bytes | str) -> Mapping[str, object]:
    if isinstance(payload, bytes):
        try:
            source = payload.decode()
        except UnicodeDecodeError as error:
            raise SdkContractDecodeError("payload is not UTF-8") from error
    elif isinstance(payload, str):
        source = payload
    else:
        raise TypeError("payload must be bytes or str")
    try:
        value = json.loads(source, object_pairs_hook=_without_duplicates)
    except json.JSONDecodeError as error:
        raise SdkContractDecodeError("payload is not valid JSON") from error
    return _object(value, "$")


def _without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SdkContractDecodeError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _object(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise SdkContractDecodeError(f"{path} must be an object")
    return value


def _exact(value: Mapping[str, object], fields: set[str], path: str) -> None:
    if set(value) != fields:
        raise SdkContractDecodeError(
            f"{path} fields differ; missing={sorted(fields - set(value))!r}, unknown={sorted(set(value) - fields)!r}"
        )


def _text(value: Mapping[str, object], field: str, path: str) -> str:
    result = value.get(field)
    if not isinstance(result, str):
        raise SdkContractDecodeError(f"{path}.{field} must be text")
    return result


def _array(value: Mapping[str, object], field: str, path: str) -> list[object]:
    result = value.get(field)
    if not isinstance(result, list):
        raise SdkContractDecodeError(f"{path}.{field} must be an array")
    return result


def _text_array(value: Mapping[str, object], field: str, path: str) -> tuple[str, ...]:
    result = _array(value, field, path)
    if any(not isinstance(item, str) for item in result):
        raise SdkContractDecodeError(f"{path}.{field} must contain text")
    return tuple(item for item in result if isinstance(item, str))


def _text_sequence(value: Sequence[str], field: str) -> tuple[str, ...]:
    result = tuple(value)
    if not result or any(not isinstance(item, str) or not item for item in result):
        raise SdkContractDecodeError(f"{field} must contain nonempty text")
    return result


__all__ = [
    "SUPPORTED_SDK_CONTRACTS",
    "SdkContractDecodeError",
    "decode_sdk_contract_manifest",
    "encode_sdk_contract_manifest",
    "negotiate_sdk_contract",
]
