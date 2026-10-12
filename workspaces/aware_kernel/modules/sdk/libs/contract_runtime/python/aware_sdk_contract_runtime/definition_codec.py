from __future__ import annotations

import json
from collections.abc import Mapping

from aware_meta_type_schema import TypeSchemaEncodingError, canonical_json

from .codec import SdkContractDecodeError, decode_sdk_contract_manifest
from .definition import (
    SDK_DEFINITION_STATE,
    SdkContractInventory,
    SdkDefinitionState,
    SdkMethodInventoryEntry,
    SdkOperationInventoryEntry,
)
from .definition_transition import (
    SDK_DEFINITION_TRANSITION,
    SDK_PREPARED_DEFINITION_EFFECT,
    SdkDefinitionTransition,
    SdkPreparedDefinitionEffect,
    derive_sdk_definition_transition,
    prepare_sdk_definition_effect,
)


class SdkDefinitionDecodeError(ValueError):
    pass


def encode_sdk_definition_state(value: SdkDefinitionState) -> bytes:
    if type(value) is not SdkDefinitionState:
        raise TypeError("value must be exact SdkDefinitionState")
    try:
        return canonical_json(value.to_wire()).encode("utf-8")
    except (TypeError, ValueError, TypeSchemaEncodingError) as error:
        raise ValueError(f"SDK definition state is not exact: {error}") from error


def decode_sdk_definition_state(payload: bytes | str) -> SdkDefinitionState:
    text, root = _root(payload)
    _exact(root, {"contract", "manifest", "inventory", "definition_digest"}, "$")
    if _text(root, "contract", "$") != SDK_DEFINITION_STATE:
        raise SdkDefinitionDecodeError("$.contract is unsupported")
    manifest_wire = _object(root.get("manifest"), "$.manifest")
    inventory_wire = _object(root.get("inventory"), "$.inventory")
    _exact(
        inventory_wire,
        {
            "sdk_ref",
            "operation_count",
            "contracted_operation_count",
            "legacy_operation_count",
            "method_count",
            "operations",
            "methods",
            "inventory_digest",
        },
        "$.inventory",
    )
    try:
        manifest = decode_sdk_contract_manifest(canonical_json(manifest_wire))
        operations = tuple(
            _inventory_operation(item, f"$.inventory.operations[{index}]")
            for index, item in enumerate(_array(inventory_wire, "operations", "$.inventory"))
        )
        methods = tuple(
            _inventory_method(item, f"$.inventory.methods[{index}]")
            for index, item in enumerate(_array(inventory_wire, "methods", "$.inventory"))
        )
        inventory = SdkContractInventory(
            sdk_ref=_text(inventory_wire, "sdk_ref", "$.inventory"),
            operation_refs=tuple(item.operation_ref for item in operations),
            contracted_operation_refs=tuple(item.operation_ref for item in operations if item.contract_posture == "contracted"),
            legacy_operation_refs=tuple(item.operation_ref for item in operations if item.contract_posture == "legacy"),
            method_refs=tuple(item.method_ref for item in methods),
            operations=operations,
            methods=methods,
        )
        for field, expected in (
            ("operation_count", len(inventory.operation_refs)),
            ("contracted_operation_count", len(inventory.contracted_operation_refs)),
            ("legacy_operation_count", len(inventory.legacy_operation_refs)),
            ("method_count", len(inventory.method_refs)),
        ):
            if _integer(inventory_wire, field, "$.inventory") != expected:
                raise SdkDefinitionDecodeError(f"$.inventory.{field} differs from entries")
        if _text(inventory_wire, "inventory_digest", "$.inventory") != inventory.inventory_digest:
            raise SdkDefinitionDecodeError("$.inventory.inventory_digest differs from fresh derivation")
        state = SdkDefinitionState(
            manifest=manifest,
            inventory=inventory,
            definition_digest=_text(root, "definition_digest", "$"),
        )
    except (TypeError, ValueError, SdkContractDecodeError) as error:
        if isinstance(error, SdkDefinitionDecodeError):
            raise
        raise SdkDefinitionDecodeError(f"definition state violates its contract: {error}") from error
    expected_text = encode_sdk_definition_state(state).decode("utf-8")
    if text != expected_text:
        raise SdkDefinitionDecodeError("definition payload differs from exact canonical reconstruction")
    return state


def encode_sdk_definition_transition(
    value: SdkDefinitionTransition,
    *,
    predecessor: SdkDefinitionState | None,
    result: SdkDefinitionState,
) -> bytes:
    if type(value) is not SdkDefinitionTransition:
        raise TypeError("value must be exact SdkDefinitionTransition")
    try:
        return canonical_json(value.to_wire(predecessor=predecessor, result=result)).encode("utf-8")
    except (TypeError, ValueError, TypeSchemaEncodingError) as error:
        raise ValueError(f"SDK definition transition is not exact: {error}") from error


def decode_sdk_definition_transition(
    payload: bytes | str,
    *,
    predecessor: SdkDefinitionState | None,
    result: SdkDefinitionState,
) -> SdkDefinitionTransition:
    text, root = _root(payload)
    _exact(
        root,
        {
            "contract",
            "sdk_ref",
            "predecessor_kind",
            "predecessor_definition_digest",
            "result_definition_digest",
            "predecessor_manifest_digest",
            "result_manifest_digest",
            "predecessor_inventory_digest",
            "result_inventory_digest",
            "movements",
            "transition_digest",
        },
        "$",
    )
    if _text(root, "contract", "$") != SDK_DEFINITION_TRANSITION:
        raise SdkDefinitionDecodeError("$.contract is unsupported")
    _require_canonical(text, root, "transition")
    try:
        expected = derive_sdk_definition_transition(predecessor, result)
        expected_text = encode_sdk_definition_transition(expected, predecessor=predecessor, result=result).decode("utf-8")
    except (TypeError, ValueError) as error:
        raise SdkDefinitionDecodeError(f"supplied definition context is invalid: {error}") from error
    if text != expected_text:
        raise SdkDefinitionDecodeError("transition differs from fresh supplied-state derivation")
    return expected


def encode_sdk_prepared_definition_effect(
    value: SdkPreparedDefinitionEffect,
    *,
    predecessor: SdkDefinitionState | None,
    result: SdkDefinitionState,
) -> bytes:
    if type(value) is not SdkPreparedDefinitionEffect:
        raise TypeError("value must be exact SdkPreparedDefinitionEffect")
    try:
        return canonical_json(value.to_wire(predecessor=predecessor, result=result)).encode("utf-8")
    except (TypeError, ValueError, TypeSchemaEncodingError) as error:
        raise ValueError(f"SDK prepared definition effect is not exact: {error}") from error


def decode_sdk_prepared_definition_effect(
    payload: bytes | str,
    *,
    predecessor: SdkDefinitionState | None,
    result: SdkDefinitionState,
) -> SdkPreparedDefinitionEffect:
    text, root = _root(payload)
    _exact(
        root,
        {
            "contract",
            "transition_digest",
            "predecessor_definition_digest",
            "result_definition_digest",
            "result_state",
            "movements",
            "effect_digest",
        },
        "$",
    )
    if _text(root, "contract", "$") != SDK_PREPARED_DEFINITION_EFFECT:
        raise SdkDefinitionDecodeError("$.contract is unsupported")
    _require_canonical(text, root, "effect")
    try:
        expected = prepare_sdk_definition_effect(predecessor, result)
        expected_text = encode_sdk_prepared_definition_effect(expected, predecessor=predecessor, result=result).decode("utf-8")
    except (TypeError, ValueError) as error:
        raise SdkDefinitionDecodeError(f"supplied definition context is invalid: {error}") from error
    if text != expected_text:
        raise SdkDefinitionDecodeError("effect differs from fresh supplied-state derivation")
    return expected


def _inventory_operation(value: object, path: str) -> SdkOperationInventoryEntry:
    item = _object(value, path)
    _exact(
        item,
        {
            "operation_ref",
            "contract_posture",
            "request_type_ref",
            "result_type_ref",
            "error_type_refs",
            "provider_operation_ref",
            "endpoint_refs",
            "dependency_operation_refs",
            "method_refs",
        },
        path,
    )
    return SdkOperationInventoryEntry(
        operation_ref=_text(item, "operation_ref", path),
        contract_posture=_text(item, "contract_posture", path),
        request_type_ref=_optional_text(item, "request_type_ref", path),
        result_type_ref=_optional_text(item, "result_type_ref", path),
        error_type_refs=_text_array(item, "error_type_refs", path),
        provider_operation_ref=_optional_text(item, "provider_operation_ref", path),
        endpoint_refs=_text_array(item, "endpoint_refs", path),
        dependency_operation_refs=_text_array(item, "dependency_operation_refs", path),
        method_refs=_text_array(item, "method_refs", path),
    )


def _inventory_method(value: object, path: str) -> SdkMethodInventoryEntry:
    item = _object(value, path)
    fields = {
        "method_ref",
        "operation_ref",
        "method_family",
        "effect",
        "mutation_scope",
        "confirmation_policy",
        "execution_mode",
        "runtime_binding_kind",
    }
    _exact(item, fields, path)
    return SdkMethodInventoryEntry(**{field: _text(item, field, path) for field in fields})


def _root(payload: bytes | str) -> tuple[str, Mapping[str, object]]:
    if type(payload) is bytes:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SdkDefinitionDecodeError("payload is not UTF-8") from error
    elif type(payload) is str:
        text = payload
    else:
        raise TypeError("payload must be exact bytes or str")
    try:
        value = json.loads(text, object_pairs_hook=_without_duplicates)
    except json.JSONDecodeError as error:
        raise SdkDefinitionDecodeError("payload is not one valid JSON document") from error
    return text, _object(value, "$")


def _without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SdkDefinitionDecodeError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _require_canonical(text: str, root: Mapping[str, object], name: str) -> None:
    try:
        canonical = canonical_json(root)
    except TypeSchemaEncodingError as error:
        raise SdkDefinitionDecodeError(f"{name} is not canonical JSON: {error}") from error
    if text != canonical:
        raise SdkDefinitionDecodeError(f"{name} must use exact canonical UTF-8 JSON")


def _object(value: object, path: str) -> Mapping[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise SdkDefinitionDecodeError(f"{path} must be an exact object")
    return value


def _exact(value: Mapping[str, object], fields: set[str], path: str) -> None:
    actual = set(value)
    if actual != fields:
        raise SdkDefinitionDecodeError(f"{path} fields differ; missing={sorted(fields - actual)!r}, unknown={sorted(actual - fields)!r}")


def _text(value: Mapping[str, object], field: str, path: str) -> str:
    result = value.get(field)
    if type(result) is not str:
        raise SdkDefinitionDecodeError(f"{path}.{field} must be exact text")
    return result


def _optional_text(value: Mapping[str, object], field: str, path: str) -> str | None:
    result = value.get(field)
    if result is not None and type(result) is not str:
        raise SdkDefinitionDecodeError(f"{path}.{field} must be exact text or null")
    return result


def _integer(value: Mapping[str, object], field: str, path: str) -> int:
    result = value.get(field)
    if type(result) is not int or result < 0:
        raise SdkDefinitionDecodeError(f"{path}.{field} must be an exact nonnegative integer")
    return result


def _array(value: Mapping[str, object], field: str, path: str) -> list[object]:
    result = value.get(field)
    if type(result) is not list:
        raise SdkDefinitionDecodeError(f"{path}.{field} must be an exact array")
    return result


def _text_array(value: Mapping[str, object], field: str, path: str) -> tuple[str, ...]:
    result = _array(value, field, path)
    if any(type(item) is not str for item in result):
        raise SdkDefinitionDecodeError(f"{path}.{field} must contain exact text")
    return tuple(result)  # type: ignore[arg-type]


__all__ = [
    "SdkDefinitionDecodeError",
    "decode_sdk_definition_state",
    "decode_sdk_definition_transition",
    "decode_sdk_prepared_definition_effect",
    "encode_sdk_definition_state",
    "encode_sdk_definition_transition",
    "encode_sdk_prepared_definition_effect",
]
