"""Owning portable values and arguments; no runtime, issuer or provider authority."""

from __future__ import annotations

import builtins
import hashlib
import importlib as _owner_native_importlib
import importlib.util as _owner_native_import_util
import json
import sys
from _operator import attrgetter as _native_attrgetter
from _operator import is_ as _same_object
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, make_dataclass
from enum import Enum, StrEnum
from itertools import chain as _native_chain
from threading import RLock
from types import BuiltinMethodType, FunctionType, MemberDescriptorType, ModuleType
from typing import TYPE_CHECKING, Any, ClassVar, cast
from weakref import WeakKeyDictionary

from aware_meta_type_schema import (
    ScalarKind as ScalarKind,
)
from aware_meta_type_schema import (
    ShapeKind as ShapeKind,
)
from aware_meta_type_schema import (
    ValueShape as ValueShape,
)

type JsonScalar = None | bool | int | str
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


class OntologyRuntimeEncodingError(ValueError):
    pass


def normalize_json(value: object, *, path: str = "$") -> JsonValue:
    if type(path) is not str:
        raise TypeError("path must be exact str")
    if value is None or type(value) is bool or type(value) is str:
        if type(value) is str:
            value.encode("utf-8", "strict")
        return cast(JsonScalar, value)
    if type(value) is int:
        return value
    if type(value) is float:
        raise OntologyRuntimeEncodingError(
            f"{path} uses a floating-point number; encode decimals as strings"
        )
    if type(value) is list:
        return [
            normalize_json(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if type(value) is dict:
        normalized: dict[str, JsonValue] = {}
        if any(type(key) is not str or not key for key in value):
            raise OntologyRuntimeEncodingError("JSON keys must be exact non-empty strings")
        for key in sorted(value):
            if not isinstance(key, str) or not key:
                raise OntologyRuntimeEncodingError(
                    f"{path} object keys must be non-empty strings"
                )
            normalized[key] = normalize_json(value[key], path=f"{path}.{key}")
        return normalized
    raise OntologyRuntimeEncodingError("unsupported JSON value type")




def canonical_json(value: object) -> str:
    return json.dumps(
        normalize_json(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def digest_payload(contract: str, payload: object) -> str:
    if type(contract) is not str or not contract or contract.strip() != contract:
        raise OntologyRuntimeEncodingError("contract must be a non-empty token")
    encoded = f"{contract}\n{canonical_json(payload)}".encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _unique_pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in items:
        if key in output:
            raise OntologyRuntimeEncodingError("duplicate JSON key")
        output[key] = value
    return output


def _reject_number(value: str) -> object:
    raise OntologyRuntimeEncodingError("non-integer JSON number")


def _decode_frozen(canonical: str) -> JsonValue:
    if type(canonical) is not str:
        raise TypeError("FrozenJson.canonical must be exact str")
    decoded = json.loads(canonical, object_pairs_hook=_unique_pairs,
                         parse_float=_reject_number, parse_constant=_reject_number)
    if canonical_json(decoded) != canonical:
        raise OntologyRuntimeEncodingError("FrozenJson must use canonical encoding")
    return normalize_json(decoded)


@dataclass(frozen=True, slots=True)
class FrozenJson:
    canonical: str

    def __post_init__(self) -> None:
        if type(self) is not FrozenJson:
            raise TypeError("FrozenJson must be exact")
        _decode_frozen(self.canonical)

    @classmethod
    def from_value(cls, value: object) -> FrozenJson:
        if cls is not FrozenJson:
            raise TypeError("FrozenJson subclasses are not supported")
        return cls(canonical_json(value))

    def to_wire(self) -> JsonValue:
        if type(self) is not FrozenJson:
            raise TypeError("FrozenJson must be exact")
        return _decode_frozen(self.canonical)


class ValueKind(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    DATETIME = "datetime"
    REFERENCE = "reference"
    JSON = "json"


def _strict_token(value: object, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be exact str")
    if (
        not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise ValueError(f"{field} must be a non-empty token")
    return value


def _digest(value: object, field: str) -> str:
    value = _strict_token(value, field)
    if len(value) != 71 or not value.startswith("sha256:"):
        raise ValueError(f"{field} must be a sha256 digest")
    try:
        bytes.fromhex(value[7:])
    except ValueError as error:
        raise ValueError(f"{field} must be a sha256 digest") from error
    return value


def _ordinal(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _exact_mapping(value: object, field: str) -> dict[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise TypeError(f"{field} must be an exact string-keyed dict")
    return value


def _exact_sequence(value: object, field: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{field} must be an exact list")
    return value


def _exact_keys(
    value: Mapping[str, object], expected: frozenset[str], field: str
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise ValueError(f"{field} keys mismatched: missing={missing}, unknown={unknown}")


def _strict_json_value(value: object, field: str) -> object:
    if value is None or type(value) is bool or type(value) is int or type(value) is str:
        return value
    if type(value) is list:
        return [
            _strict_json_value(item, f"{field}[{index}]")
            for index, item in enumerate(value)
        ]
    if type(value) is dict:
        if any(type(key) is not str or not key for key in value):
            raise TypeError(f"{field} must use exact non-empty string keys")
        return {
            key: _strict_json_value(value[key], f"{field}.{key}")
            for key in sorted(value)
        }
    raise TypeError(f"{field} must contain only exact canonical JSON values")


def _strict_frozen_json(value: object, field: str) -> FrozenJson:
    if type(value) is not FrozenJson or type(value.canonical) is not str:
        raise TypeError(f"{field} must be exact FrozenJson with exact str bytes")
    return FrozenJson(value.canonical)


@dataclass(frozen=True, slots=True)
class RuntimeValue:
    value_kind: ValueKind
    value: FrozenJson

    def __post_init__(self) -> None:
        if type(self) is not RuntimeValue:
            raise TypeError("RuntimeValue must be exact")
        if type(self.value_kind) is not ValueKind and type(self.value_kind) is not str:
            raise TypeError("value_kind must be exact enum or string")
        object.__setattr__(self, "value_kind", ValueKind(self.value_kind))
        if type(self.value) is not FrozenJson:
            object.__setattr__(self, "value", FrozenJson.from_value(self.value))
        self.to_wire()

    @classmethod
    def of(cls, value_kind: ValueKind, value: object) -> RuntimeValue:
        if cls is not RuntimeValue:
            raise TypeError("RuntimeValue subclasses are not supported")
        return cls(value_kind, FrozenJson.from_value(value))

    def to_wire(self) -> dict[str, object]:
        if type(self) is not RuntimeValue:
            raise TypeError("RuntimeValue must be exact")
        if type(self) is not RuntimeValue or type(self.value_kind) is not ValueKind:
            raise TypeError("runtime value must be exact")
        if type(self.value) is not FrozenJson:
            raise TypeError("runtime content must be exact FrozenJson")
        raw = FrozenJson.to_wire(self.value)
        scalar_type = {
            ValueKind.STRING: str, ValueKind.INTEGER: int, ValueKind.BOOLEAN: bool,
            ValueKind.DECIMAL: str, ValueKind.DATETIME: str, ValueKind.REFERENCE: str,
        }.get(self.value_kind)
        if scalar_type is not None:
            elements = raw if type(raw) is list else [raw]
            if any(type(element) is not scalar_type for element in elements):
                raise TypeError("runtime element does not match tagged kind")
        return {"value_kind": self.value_kind.value, "value": raw}


class OntologyRuntimeActionTargetKind(StrEnum):
    SCHEMA_FIELDS = "schema_fields"
    INSTANCE_REF = "instance_ref"
    OPERATION_LOCAL_RESULT = "operation_local_result"


@dataclass(frozen=True, slots=True)
class OntologyRuntimeActionSchemaFieldsTarget:
    type_ref: str
    identity_field_refs: tuple[str, ...]
    identity_contract_digest: str
    normalized_semantic_key: FrozenJson
    tag: OntologyRuntimeActionTargetKind = OntologyRuntimeActionTargetKind.SCHEMA_FIELDS

    def __post_init__(self) -> None:
        if type(self) is not OntologyRuntimeActionSchemaFieldsTarget:
            raise TypeError("OntologyRuntimeActionSchemaFieldsTarget must be exact")
        if self.tag is not OntologyRuntimeActionTargetKind.SCHEMA_FIELDS:
            raise ValueError("schema_fields target tag mismatched")
        object.__setattr__(
            self, "type_ref", _strict_token(self.type_ref, "type_ref")
        )
        if type(self.identity_field_refs) is not tuple:
            raise TypeError("identity_field_refs must be an exact tuple")
        fields = self.identity_field_refs
        if (
            not fields
            or any(type(item) is not str for item in fields)
            or fields != tuple(sorted(fields))
            or len(fields) != len(set(fields))
        ):
            raise ValueError("identity_field_refs must be canonical, non-empty and unique")
        for item in fields:
            _strict_token(item, "identity_field_refs")
        object.__setattr__(
            self,
            "identity_contract_digest",
            _digest(self.identity_contract_digest, "identity_contract_digest"),
        )
        object.__setattr__(
            self,
            "normalized_semantic_key",
            _strict_frozen_json(
                self.normalized_semantic_key, "normalized_semantic_key"
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        type_ref: str,
        identity_field_refs: Iterable[str],
        identity_contract_digest: str,
        normalized_semantic_key: object,
    ) -> OntologyRuntimeActionSchemaFieldsTarget:
        if cls is not OntologyRuntimeActionSchemaFieldsTarget:
            raise TypeError("schema_fields target subclasses are not supported")
        if type(identity_field_refs) is not tuple:
            raise TypeError("identity_field_refs must be an exact tuple")
        if any(type(item) is not str for item in identity_field_refs):
            raise TypeError("identity_field_refs must contain exact strings")
        return OntologyRuntimeActionSchemaFieldsTarget(
            type_ref,
            tuple(sorted(identity_field_refs)),
            identity_contract_digest,
            FrozenJson.from_value(
                _strict_json_value(
                    normalized_semantic_key, "normalized_semantic_key"
                )
            ),
        )

    def to_wire(self) -> dict[str, object]:
        if type(self) is not OntologyRuntimeActionSchemaFieldsTarget:
            raise TypeError("OntologyRuntimeActionSchemaFieldsTarget must be exact")
        OntologyRuntimeActionSchemaFieldsTarget.__post_init__(self)
        return {
            "tag": self.tag.value,
            "type_ref": self.type_ref,
            "identity_field_refs": list(self.identity_field_refs),
            "identity_contract_digest": self.identity_contract_digest,
            "normalized_semantic_key": self.normalized_semantic_key.to_wire(),
        }


@dataclass(frozen=True, slots=True)
class OntologyRuntimeActionInstanceRefTarget:
    type_ref: str
    provider_key: str
    provider_generation: str
    instance_ref: str
    tag: OntologyRuntimeActionTargetKind = OntologyRuntimeActionTargetKind.INSTANCE_REF

    def __post_init__(self) -> None:
        if type(self) is not OntologyRuntimeActionInstanceRefTarget:
            raise TypeError("OntologyRuntimeActionInstanceRefTarget must be exact")
        if self.tag is not OntologyRuntimeActionTargetKind.INSTANCE_REF:
            raise ValueError("instance_ref target tag mismatched")
        for field in ("type_ref", "provider_key", "provider_generation", "instance_ref"):
            object.__setattr__(
                self, field, _strict_token(getattr(self, field), field)
            )

    def to_wire(self) -> dict[str, object]:
        if type(self) is not OntologyRuntimeActionInstanceRefTarget:
            raise TypeError("OntologyRuntimeActionInstanceRefTarget must be exact")
        OntologyRuntimeActionInstanceRefTarget.__post_init__(self)
        return {
            "tag": self.tag.value,
            "type_ref": self.type_ref,
            "provider_key": self.provider_key,
            "provider_generation": self.provider_generation,
            "instance_ref": self.instance_ref,
        }


@dataclass(frozen=True, slots=True)
class OntologyRuntimeActionOperationLocalResultTarget:
    type_ref: str
    operation_ref: str
    producer_action_digest: str
    result_symbol: str
    ordinal: int
    tag: OntologyRuntimeActionTargetKind = (
        OntologyRuntimeActionTargetKind.OPERATION_LOCAL_RESULT
    )

    def __post_init__(self) -> None:
        if type(self) is not OntologyRuntimeActionOperationLocalResultTarget:
            raise TypeError("OntologyRuntimeActionOperationLocalResultTarget must be exact")
        if self.tag is not OntologyRuntimeActionTargetKind.OPERATION_LOCAL_RESULT:
            raise ValueError("operation_local_result target tag mismatched")
        for field in ("type_ref", "operation_ref", "result_symbol"):
            object.__setattr__(
                self, field, _strict_token(getattr(self, field), field)
            )
        object.__setattr__(
            self,
            "producer_action_digest",
            _digest(self.producer_action_digest, "producer_action_digest"),
        )
        object.__setattr__(self, "ordinal", _ordinal(self.ordinal, "ordinal"))

    def to_wire(self) -> dict[str, object]:
        if type(self) is not OntologyRuntimeActionOperationLocalResultTarget:
            raise TypeError("OntologyRuntimeActionOperationLocalResultTarget must be exact")
        OntologyRuntimeActionOperationLocalResultTarget.__post_init__(self)
        return {
            "tag": self.tag.value,
            "type_ref": self.type_ref,
            "operation_ref": self.operation_ref,
            "producer_action_digest": self.producer_action_digest,
            "result_symbol": self.result_symbol,
            "ordinal": self.ordinal,
        }


OntologyRuntimeActionTarget = (
    OntologyRuntimeActionSchemaFieldsTarget
    | OntologyRuntimeActionInstanceRefTarget
    | OntologyRuntimeActionOperationLocalResultTarget
)


_ACTION_TARGET_TYPES = (
    OntologyRuntimeActionSchemaFieldsTarget,
    OntologyRuntimeActionInstanceRefTarget,
    OntologyRuntimeActionOperationLocalResultTarget,
)


def _reconstruct_action_target(
    target: OntologyRuntimeActionTarget,
) -> OntologyRuntimeActionTarget:
    if type(target) is OntologyRuntimeActionSchemaFieldsTarget:
        return OntologyRuntimeActionSchemaFieldsTarget(
            target.type_ref,
            target.identity_field_refs,
            target.identity_contract_digest,
            target.normalized_semantic_key,
            target.tag,
        )
    if type(target) is OntologyRuntimeActionInstanceRefTarget:
        return OntologyRuntimeActionInstanceRefTarget(
            target.type_ref,
            target.provider_key,
            target.provider_generation,
            target.instance_ref,
            target.tag,
        )
    if type(target) is OntologyRuntimeActionOperationLocalResultTarget:
        return OntologyRuntimeActionOperationLocalResultTarget(
            target.type_ref,
            target.operation_ref,
            target.producer_action_digest,
            target.result_symbol,
            target.ordinal,
            target.tag,
        )
    raise TypeError("Action target must be an exact tagged target")


def _target_from_wire(value: object, field: str) -> OntologyRuntimeActionTarget:
    body = _exact_mapping(value, field)
    tag = _strict_token(body.get("tag"), f"{field}.tag")
    if tag == OntologyRuntimeActionTargetKind.SCHEMA_FIELDS.value:
        _exact_keys(
            body,
            frozenset(
                {
                    "tag",
                    "type_ref",
                    "identity_field_refs",
                    "identity_contract_digest",
                    "normalized_semantic_key",
                }
            ),
            field,
        )
        fields = _exact_sequence(body["identity_field_refs"], f"{field}.identity_field_refs")
        return OntologyRuntimeActionSchemaFieldsTarget(
            _strict_token(body["type_ref"], f"{field}.type_ref"),
            tuple(
                _strict_token(item, f"{field}.identity_field_refs")
                for item in fields
            ),
            _digest(
                body["identity_contract_digest"],
                f"{field}.identity_contract_digest",
            ),
            FrozenJson.from_value(
                _strict_json_value(
                    body["normalized_semantic_key"],
                    f"{field}.normalized_semantic_key",
                )
            ),
        )
    if tag == OntologyRuntimeActionTargetKind.INSTANCE_REF.value:
        _exact_keys(
            body,
            frozenset(
                {"tag", "type_ref", "provider_key", "provider_generation", "instance_ref"}
            ),
            field,
        )
        return OntologyRuntimeActionInstanceRefTarget(
            _strict_token(body["type_ref"], f"{field}.type_ref"),
            _strict_token(body["provider_key"], f"{field}.provider_key"),
            _strict_token(
                body["provider_generation"], f"{field}.provider_generation"
            ),
            _strict_token(body["instance_ref"], f"{field}.instance_ref"),
        )
    if tag == OntologyRuntimeActionTargetKind.OPERATION_LOCAL_RESULT.value:
        _exact_keys(
            body,
            frozenset(
                {
                    "tag",
                    "type_ref",
                    "operation_ref",
                    "producer_action_digest",
                    "result_symbol",
                    "ordinal",
                }
            ),
            field,
        )
        return OntologyRuntimeActionOperationLocalResultTarget(
            _strict_token(body["type_ref"], f"{field}.type_ref"),
            _strict_token(body["operation_ref"], f"{field}.operation_ref"),
            _digest(
                body["producer_action_digest"],
                f"{field}.producer_action_digest",
            ),
            _strict_token(body["result_symbol"], f"{field}.result_symbol"),
            _ordinal(body["ordinal"], f"{field}.ordinal"),
        )
    raise ValueError(f"{field} has unsupported target tag")


@dataclass(frozen=True, slots=True)
class OntologyRuntimeActionArgumentValue:
    runtime_value: RuntimeValue | None = None
    object_target: OntologyRuntimeActionTarget | None = None

    def __post_init__(self) -> None:
        if type(self) is not OntologyRuntimeActionArgumentValue:
            raise TypeError("OntologyRuntimeActionArgumentValue must be exact")
        runtime = self.runtime_value
        target = self.object_target
        if (runtime is None) == (target is None):
            raise ValueError("Action argument value requires exactly one tagged variant")
        if runtime is not None:
            if (
                type(runtime) is not RuntimeValue
                or type(runtime.value_kind) is not ValueKind
            ):
                raise TypeError("runtime_value must be exact RuntimeValue")
            object.__setattr__(
                self,
                "runtime_value",
                RuntimeValue(
                    runtime.value_kind,
                    _strict_frozen_json(runtime.value, "runtime_value.value"),
                ),
            )
        if target is not None and not any(type(target) is kind for kind in _ACTION_TARGET_TYPES):
            raise TypeError("object_target must be an exact tagged Action target")
        if target is not None:
            object.__setattr__(
                self, "object_target", _reconstruct_action_target(target)
            )

    @classmethod
    def runtime(cls, value: RuntimeValue) -> OntologyRuntimeActionArgumentValue:
        if cls is not OntologyRuntimeActionArgumentValue:
            raise TypeError("Action argument value subclasses are not supported")
        return OntologyRuntimeActionArgumentValue(runtime_value=value)

    @classmethod
    def target(
        cls, value: OntologyRuntimeActionTarget
    ) -> OntologyRuntimeActionArgumentValue:
        if cls is not OntologyRuntimeActionArgumentValue:
            raise TypeError("Action argument value subclasses are not supported")
        return OntologyRuntimeActionArgumentValue(object_target=value)

    @property
    def tag(self) -> str:
        if type(self) is not OntologyRuntimeActionArgumentValue:
            raise TypeError("OntologyRuntimeActionArgumentValue must be exact")
        return "runtime_value" if self.runtime_value is not None else "object_target"

    def to_wire(self) -> dict[str, object]:
        if type(self) is not OntologyRuntimeActionArgumentValue:
            raise TypeError("OntologyRuntimeActionArgumentValue must be exact")
        OntologyRuntimeActionArgumentValue.__post_init__(self)
        if self.runtime_value is not None:
            return {"tag": "runtime_value", "runtime_value": self.runtime_value.to_wire()}
        assert self.object_target is not None
        return {"tag": "object_target", "object_target": self.object_target.to_wire()}

    @classmethod
    def from_wire(cls, value: object, field: str) -> OntologyRuntimeActionArgumentValue:
        if type(field) is not str:
            raise TypeError("field must be exact str")
        if cls is not OntologyRuntimeActionArgumentValue:
            raise TypeError("Action argument value subclasses are not supported")
        body = _exact_mapping(value, field)
        tag = _strict_token(body.get("tag"), f"{field}.tag")
        if tag == "runtime_value":
            _exact_keys(body, frozenset({"tag", "runtime_value"}), field)
            runtime = _exact_mapping(body["runtime_value"], f"{field}.runtime_value")
            _exact_keys(runtime, frozenset({"value_kind", "value"}), f"{field}.runtime_value")
            return cls.runtime(
                RuntimeValue.of(
                    ValueKind(
                        _strict_token(
                            runtime["value_kind"], f"{field}.runtime_value.value_kind"
                        )
                    ),
                    _strict_json_value(
                        runtime["value"], f"{field}.runtime_value.value"
                    ),
                )
            )
        if tag == "object_target":
            _exact_keys(body, frozenset({"tag", "object_target"}), field)
            return cls.target(_target_from_wire(body["object_target"], f"{field}.object_target"))
        raise ValueError(f"{field} has unsupported argument tag")


@dataclass(frozen=True, slots=True, order=True)
class ActionArgument:
    parameter_ref: str
    value: OntologyRuntimeActionArgumentValue

    def __post_init__(self) -> None:
        if type(self) is not ActionArgument:
            raise TypeError("ActionArgument must be exact")
        object.__setattr__(
            self,
            "parameter_ref",
            _strict_token(self.parameter_ref, "parameter_ref"),
        )
        if type(self.value) is not OntologyRuntimeActionArgumentValue:
            raise TypeError("ActionArgument.value must be exact tagged value")
        object.__setattr__(
            self,
            "value",
            OntologyRuntimeActionArgumentValue(
                runtime_value=self.value.runtime_value,
                object_target=self.value.object_target,
            ),
        )

    @classmethod
    def runtime(cls, parameter_ref: str, value: RuntimeValue) -> ActionArgument:
        if cls is not ActionArgument:
            raise TypeError("ActionArgument subclasses are not supported")
        return ActionArgument(
            parameter_ref, OntologyRuntimeActionArgumentValue.runtime(value)
        )

    @classmethod
    def target(
        cls, parameter_ref: str, value: OntologyRuntimeActionTarget
    ) -> ActionArgument:
        if cls is not ActionArgument:
            raise TypeError("ActionArgument subclasses are not supported")
        return ActionArgument(
            parameter_ref, OntologyRuntimeActionArgumentValue.target(value)
        )

    def to_wire(self) -> dict[str, object]:
        if type(self) is not ActionArgument:
            raise TypeError("ActionArgument must be exact")
        ActionArgument.__post_init__(self)
        return {"parameter_ref": self.parameter_ref, "value": self.value.to_wire()}

    @classmethod
    def from_wire(cls, value: object, field: str) -> ActionArgument:
        if type(field) is not str:
            raise TypeError("field must be exact str")
        if cls is not ActionArgument:
            raise TypeError("ActionArgument subclasses are not supported")
        body = _exact_mapping(value, field)
        _exact_keys(body, frozenset({"parameter_ref", "value"}), field)
        return ActionArgument(
            _strict_token(body["parameter_ref"], f"{field}.parameter_ref"),
            OntologyRuntimeActionArgumentValue.from_wire(body["value"], f"{field}.value"),
        )




def _binding_token(value: object, field: str) -> str:
    check = _binding_guard
    check()
    token = _strict_token
    if type(token) is not FunctionType:
        raise TypeError("token operation identity mismatched")
    code = token.__code__
    result = token(value, field)
    if _strict_token is not token or token.__code__ is not code:
        raise TypeError("token operation identity mismatched")
    check()
    return result


def _binding_digest(domain: str, payload: object) -> str:
    check = _binding_guard
    check()
    result = digest_payload(domain, payload)
    check()
    return result


def _native_enum(value: object, kind: type[StrEnum], field: str) -> None:
    if type(value) is not kind and type(value) is not str:
        raise TypeError(f"{field} must be exact enum or str")
    if type(value) is kind:
        if type(object.__getattribute__(value, "_value_")) is not str or type(object.__getattribute__(value, "_name_")) is not str:
            raise TypeError("enum must retain native data")


def _shape_copy(value: ValueShape, active: set[int] | None = None) -> ValueShape:
    check = _shape_guard
    copy_shape = _shape_copy
    shape_class = ValueShape
    check()
    if type(value) is not shape_class:
        raise TypeError("shape must be exact ValueShape")
    seen = set() if active is None else active
    key = id(value)
    if key in seen:
        raise ValueError("cyclic shape")
    seen.add(key)
    try:
        kind = object.__getattribute__(value, "kind")
        scalar = object.__getattribute__(value, "scalar_kind")
        ref = object.__getattribute__(value, "type_ref")
        element = object.__getattribute__(value, "element")
        mapped = object.__getattribute__(value, "map_value")
        variants = object.__getattribute__(value, "variants")
        _native_enum(kind, ShapeKind, "shape kind")
        if scalar is not None:
            _native_enum(scalar, ScalarKind, "scalar kind")
        if ref is not None:
            _binding_token(ref, "type_ref")
        if type(variants) is not tuple:
            raise TypeError("shape variants must be exact tuple")
        # Delegate payload laws to the sole Meta constructor, after recursively
        # admitting native data. No copied shape grammar or alternate codec.
        check()
        copied_element = None if element is None else copy_shape(element, seen)
        check()
        copied_map = None if mapped is None else copy_shape(mapped, seen)
        check()
        copied_variants = []
        for item in variants:
            copied_variants.append(copy_shape(item, seen))
            check()
        arguments = dict(kind=kind, scalar_kind=scalar, type_ref=ref,
                         element=copied_element, map_value=copied_map,
                         variants=tuple(copied_variants))
        check()
        result = shape_class(**arguments)
        check()
        return result
    finally:
        seen.remove(key)


def _shape_wire(value: ValueShape) -> dict[str, object]:
    check = _binding_guard
    check()
    result = _shape_copy(value)
    check()
    wire = result.to_wire()
    check()
    return wire


def _binding_items(values: object, kind: type) -> tuple:
    check = _binding_guard
    check()
    if type(values) is not tuple and type(values) is not list:
        raise TypeError("bindings must be exact tuple or list")
    items = tuple(values)
    for item in items:
        check()
        _binding_native(item, kind)
        check()
    return items


def _binding_native(value: object, kind: type) -> None:
    check = _binding_guard
    check()
    if type(value) is not kind:
        raise TypeError("binding must have its exact owning class")
    name = kind.__name__
    strings = {
        "OntologyObjectRelationshipConstructorPath": ("constructor_action_ref",),
        "OntologyObjectFieldBinding": ("field_ref", "attribute_name"),
        "OntologyObjectActionParameterBinding": ("parameter_ref",),
        "OntologyObjectActionBinding": ("action_ref", "method_name"),
        "OntologyObjectRelationshipBinding": ("relationship_ref", "method_name", "source_type_ref", "target_type_ref"),
        "OntologyObjectClassBinding": ("type_ref", "class_name", "binding_digest"),
    }[name]
    for field in strings:
        _binding_token(object.__getattribute__(value, field), field)
        check()
    if name == "OntologyObjectFieldBinding" or name == "OntologyObjectActionParameterBinding":
        _shape_copy(object.__getattribute__(value, "shape"))
        check()
        for field in ("required", "nullable"):
            if type(object.__getattribute__(value, field)) is not bool:
                raise TypeError("binding flags must be exact bool")
    if name == "OntologyObjectActionParameterBinding":
        position = object.__getattribute__(value, "position")
        if type(position) is not int or position < 0:
            raise ValueError("position must be non-negative exact int")
        _native_enum(object.__getattribute__(value, "value_mode"), ActionValueMode, "value_mode")
    elif name == "OntologyObjectRelationshipConstructorPath":
        refs = object.__getattribute__(value, "relationship_refs")
        if type(refs) is not tuple and type(refs) is not list:
            raise TypeError("relationship_refs must be exact tuple or list")
        for ref in refs:
            _binding_token(ref, "relationship_ref")
            check()
    elif name == "OntologyObjectActionBinding":
        _binding_items(object.__getattribute__(value, "parameters"), OntologyObjectActionParameterBinding)
        _binding_items(object.__getattribute__(value, "relationship_constructor_paths"), OntologyObjectRelationshipConstructorPath)
        _native_enum(object.__getattribute__(value, "role"), OntologyObjectActionRole, "role")
    elif name == "OntologyObjectRelationshipBinding":
        for field, enum_type in (("direction", OntologyObjectRelationshipDirection), ("cardinality", Cardinality), ("traversal", TraversalPolicy)):
            _native_enum(object.__getattribute__(value, field), enum_type, field)
        residence = object.__getattribute__(value, "endpoint_residence")
        if residence is not None:
            _native_enum(residence, RelationshipEndpointResidence, "endpoint_residence")
    elif name == "OntologyObjectClassBinding":
        for field, item_type in (("fields", OntologyObjectFieldBinding), ("actions", OntologyObjectActionBinding), ("relationships", OntologyObjectRelationshipBinding)):
            _binding_items(object.__getattribute__(value, field), item_type)

class Cardinality(StrEnum):
    ONE = "one"
    OPTIONAL_ONE = "optional_one"
    MANY = "many"


class TraversalPolicy(StrEnum):
    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"
    BIDIRECTIONAL = "bidirectional"


class ActionValueMode(StrEnum):
    VALUE = "value"
    INSTANCE_REF = "instance_ref"


class RelationshipEndpointResidence(StrEnum):
    RESIDENT_TARGET = "resident_target"
    EXTERNAL_DEPENDENCY = "external_dependency"


class OntologyObjectContractError(ValueError):
    pass


class OntologyObjectRelationshipDirection(StrEnum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"


OBJECT_ABI_CONTRACT = "aware.ontology.object-abi.v1"


class OntologyObjectActionRole(StrEnum):
    INSTANCE = "instance"
    CONSTRUCTOR = "constructor"


@dataclass(frozen=True, slots=True, order=True)
class OntologyObjectRelationshipConstructorPath:
    relationship_refs: tuple[str, ...]
    constructor_action_ref: str

    def __post_init__(self) -> None:
        _binding_native(self, OntologyObjectRelationshipConstructorPath)
        values = tuple(
            _binding_token(item, "relationship_ref") for item in self.relationship_refs
        )
        if not values:
            raise OntologyObjectContractError(
                "relationship constructor path must not be empty"
            )
        object.__setattr__(self, "relationship_refs", values)
        object.__setattr__(
            self,
            "constructor_action_ref",
            _binding_token(self.constructor_action_ref, "constructor_action_ref"),
        )

    def to_wire(self) -> dict[str, object]:
        _binding_native(self, OntologyObjectRelationshipConstructorPath)
        return {
            "relationship_refs": list(self.relationship_refs),
            "constructor_action_ref": self.constructor_action_ref,
        }


def _member_name(ref: str, field: str) -> str:
    _binding_token(ref, "ref")
    _binding_token(field, "field")
    name = ref.rsplit(".", 1)[-1]
    if not name.isidentifier() or name.startswith("_"):
        raise OntologyObjectContractError(
            f"{field} {ref!r} does not expose a safe object member name"
        )
    return name


@dataclass(frozen=True, slots=True, order=True)
class OntologyObjectFieldBinding:
    field_ref: str
    attribute_name: str
    shape: ValueShape
    required: bool
    nullable: bool

    def __post_init__(self) -> None:
        _binding_native(self, OntologyObjectFieldBinding)
        _binding_token(self.field_ref, "field_ref")
        _binding_token(self.attribute_name, "attribute_name")
        if not self.attribute_name.isidentifier() or self.attribute_name.startswith(
            "_"
        ):
            raise OntologyObjectContractError(
                "attribute_name must be a public identifier"
            )
        if not isinstance(self.shape, ValueShape):
            raise TypeError("shape must be ValueShape")
        if not isinstance(self.required, bool) or not isinstance(self.nullable, bool):
            raise TypeError("field flags must be bool")

    def to_wire(self) -> dict[str, object]:
        _binding_native(self, OntologyObjectFieldBinding)
        return {
            "field_ref": self.field_ref,
            "attribute_name": self.attribute_name,
            "shape": _shape_wire(self.shape),
            "required": self.required,
            "nullable": self.nullable,
        }


@dataclass(frozen=True, slots=True, order=True)
class OntologyObjectActionParameterBinding:
    parameter_ref: str
    position: int
    shape: ValueShape
    required: bool
    nullable: bool
    value_mode: ActionValueMode

    def __post_init__(self) -> None:
        _binding_native(self, OntologyObjectActionParameterBinding)
        _binding_token(self.parameter_ref, "parameter_ref")
        _member_name(self.parameter_ref, "parameter_ref")
        if type(self.position) is not int or self.position < 0:
            raise OntologyObjectContractError("position must be non-negative int")
        if not isinstance(self.shape, ValueShape):
            raise TypeError("shape must be ValueShape")
        if not isinstance(self.required, bool) or not isinstance(self.nullable, bool):
            raise TypeError("parameter flags must be bool")
        object.__setattr__(self, "value_mode", ActionValueMode(self.value_mode))

    @property
    def argument_name(self) -> str:
        _binding_native(self, OntologyObjectActionParameterBinding)
        return _member_name(self.parameter_ref, "parameter_ref")

    def to_wire(self) -> dict[str, object]:
        _binding_native(self, OntologyObjectActionParameterBinding)
        return {
            "parameter_ref": self.parameter_ref,
            "position": self.position,
            "shape": _shape_wire(self.shape),
            "required": self.required,
            "nullable": self.nullable,
            "value_mode": self.value_mode.value,
        }


@dataclass(frozen=True, slots=True)
class OntologyObjectActionBinding:
    action_ref: str
    method_name: str
    parameters: tuple[OntologyObjectActionParameterBinding, ...]
    role: OntologyObjectActionRole = OntologyObjectActionRole.INSTANCE
    relationship_constructor_paths: tuple[
        OntologyObjectRelationshipConstructorPath, ...
    ] = ()

    def __post_init__(self) -> None:
        _binding_native(self, OntologyObjectActionBinding)
        _binding_token(self.action_ref, "action_ref")
        _binding_token(self.method_name, "method_name")
        if not self.method_name.isidentifier() or self.method_name.startswith("_"):
            raise OntologyObjectContractError("method_name must be a public identifier")
        values = tuple(sorted(self.parameters, key=lambda item: item.position))
        if any(
            not isinstance(item, OntologyObjectActionParameterBinding)
            for item in values
        ):
            raise TypeError("parameters contain an invalid binding")
        if len({item.position for item in values}) != len(values) or len(
            {item.parameter_ref for item in values}
        ) != len(values):
            raise OntologyObjectContractError("Action parameters are ambiguous")
        if len({item.argument_name for item in values}) != len(values):
            raise OntologyObjectContractError(
                "Action parameter Python member names collide"
            )
        object.__setattr__(self, "role", OntologyObjectActionRole(self.role))
        paths = tuple(sorted(self.relationship_constructor_paths))
        if any(
            not isinstance(item, OntologyObjectRelationshipConstructorPath)
            for item in paths
        ):
            raise TypeError("relationship constructor paths contain an invalid value")
        if self.role is OntologyObjectActionRole.CONSTRUCTOR and paths:
            raise OntologyObjectContractError(
                "constructor Action bindings cannot own relationship paths"
            )
        object.__setattr__(self, "parameters", values)
        object.__setattr__(self, "relationship_constructor_paths", paths)

    def to_wire(self) -> dict[str, object]:
        _binding_native(self, OntologyObjectActionBinding)
        return {
            "action_ref": self.action_ref,
            "method_name": self.method_name,
            "parameters": [item.to_wire() for item in self.parameters],
            "role": self.role.value,
            "relationship_constructor_paths": [
                item.to_wire() for item in self.relationship_constructor_paths
            ],
        }

    def relationship_constructor_action_ref(self, name: str) -> str:
        """Resolve only constructors authored on this instance Action binding."""
        _binding_native(self, OntologyObjectActionBinding)
        _binding_token(name, "member_name")

        candidate_name = _binding_token(name, "constructor_action_name")
        authored_refs = tuple(
            sorted(
                {
                    item.constructor_action_ref
                    for item in self.relationship_constructor_paths
                }
            )
        )
        if candidate_name in authored_refs:
            return candidate_name
        short_matches = tuple(
            item for item in authored_refs if item.rsplit(".", 1)[-1] == candidate_name
        )
        if len(short_matches) != 1:
            raise OntologyObjectContractError(
                f"constructor Action {candidate_name!r} is absent or ambiguous on authored paths"
            )
        return short_matches[0]


@dataclass(frozen=True, slots=True, order=True)
class OntologyObjectRelationshipBinding:
    relationship_ref: str
    method_name: str
    source_type_ref: str
    target_type_ref: str
    direction: OntologyObjectRelationshipDirection
    cardinality: Cardinality
    traversal: TraversalPolicy
    endpoint_residence: RelationshipEndpointResidence | None

    def __post_init__(self) -> None:
        _binding_native(self, OntologyObjectRelationshipBinding)
        for field in (
            "relationship_ref",
            "method_name",
            "source_type_ref",
            "target_type_ref",
        ):
            _binding_token(getattr(self, field), field)
        if not self.method_name.isidentifier() or self.method_name.startswith("_"):
            raise OntologyObjectContractError("relationship method must be public")
        object.__setattr__(
            self, "direction", OntologyObjectRelationshipDirection(self.direction)
        )
        object.__setattr__(self, "cardinality", Cardinality(self.cardinality))
        object.__setattr__(self, "traversal", TraversalPolicy(self.traversal))
        if self.endpoint_residence is not None:
            object.__setattr__(
                self,
                "endpoint_residence",
                RelationshipEndpointResidence(self.endpoint_residence),
            )
        permitted = (
            (TraversalPolicy.SOURCE_TO_TARGET, TraversalPolicy.BIDIRECTIONAL)
            if self.direction is OntologyObjectRelationshipDirection.OUTGOING
            else (TraversalPolicy.TARGET_TO_SOURCE, TraversalPolicy.BIDIRECTIONAL)
        )
        if self.traversal not in permitted:
            raise OntologyObjectContractError(
                "relationship binding direction escapes authored traversal"
            )

    def to_wire(self) -> dict[str, str | None]:
        _binding_native(self, OntologyObjectRelationshipBinding)
        return {
            "relationship_ref": self.relationship_ref,
            "method_name": self.method_name,
            "source_type_ref": self.source_type_ref,
            "target_type_ref": self.target_type_ref,
            "direction": self.direction.value,
            "cardinality": self.cardinality.value,
            "traversal": self.traversal.value,
            "endpoint_residence": (
                None
                if self.endpoint_residence is None
                else self.endpoint_residence.value
            ),
        }


@dataclass(frozen=True, slots=True)
class OntologyObjectClassBinding:
    type_ref: str
    class_name: str
    fields: tuple[OntologyObjectFieldBinding, ...]
    actions: tuple[OntologyObjectActionBinding, ...]
    relationships: tuple[OntologyObjectRelationshipBinding, ...]
    binding_digest: str

    def __post_init__(self) -> None:
        _binding_native(self, OntologyObjectClassBinding)
        _binding_token(self.type_ref, "type_ref")
        _binding_token(self.class_name, "class_name")
        _binding_token(self.binding_digest, "binding_digest")
        fields = tuple(sorted(self.fields, key=lambda item: item.field_ref))
        actions = tuple(sorted(self.actions, key=lambda item: item.action_ref))
        relationships = tuple(
            sorted(self.relationships, key=lambda item: item.relationship_ref)
        )
        if any(not isinstance(item, OntologyObjectFieldBinding) for item in fields):
            raise TypeError("fields contain an invalid binding")
        if any(not isinstance(item, OntologyObjectActionBinding) for item in actions):
            raise TypeError("actions contain an invalid binding")
        if any(
            not isinstance(item, OntologyObjectRelationshipBinding)
            for item in relationships
        ):
            raise TypeError("relationships contain an invalid binding")
        if len({item.field_ref for item in fields}) != len(fields):
            raise OntologyObjectContractError(
                f"field semantic coordinates collide for {self.type_ref}"
            )
        if len({item.action_ref for item in actions}) != len(actions):
            raise OntologyObjectContractError(
                f"Action semantic coordinates collide for {self.type_ref}"
            )
        coordinates = [
            (item.relationship_ref, item.direction) for item in relationships
        ]
        if len(coordinates) != len(set(coordinates)):
            raise OntologyObjectContractError(
                f"relationship coordinates collide for {self.type_ref}"
            )
        members = (
            [item.attribute_name for item in fields]
            + [item.method_name for item in actions]
            + [item.method_name for item in relationships]
        )
        if len(members) != len(set(members)):
            collisions = tuple(
                sorted({value for value in members if members.count(value) > 1})
            )
            raise OntologyObjectContractError(
                f"object members collide for {self.type_ref}: {collisions!r}"
            )
        object.__setattr__(self, "fields", fields)
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "relationships", relationships)
        expected = _binding_digest(OBJECT_ABI_CONTRACT + ".class", self._wire_payload())
        if self.binding_digest != expected:
            raise OntologyObjectContractError("class binding digest mismatched")

    @classmethod
    def create(
        cls,
        *,
        type_ref: str,
        class_name: str,
        fields: Iterable[OntologyObjectFieldBinding],
        actions: Iterable[OntologyObjectActionBinding],
        relationships: Iterable[OntologyObjectRelationshipBinding],
    ) -> OntologyObjectClassBinding:
        check = _binding_guard
        check()
        if cls is not OntologyObjectClassBinding:
            raise TypeError("class must be exact OntologyObjectClassBinding")
        _binding_token(type_ref, "type_ref")
        _binding_token(class_name, "class_name")
        fields = _binding_items(fields, OntologyObjectFieldBinding)
        actions = _binding_items(actions, OntologyObjectActionBinding)
        relationships = _binding_items(relationships, OntologyObjectRelationshipBinding)
        normalized_fields = tuple(sorted(fields, key=lambda item: item.field_ref))
        normalized_actions = tuple(sorted(actions, key=lambda item: item.action_ref))
        normalized_relationships = tuple(
            sorted(relationships, key=lambda item: item.relationship_ref)
        )
        payload = {
            "type_ref": type_ref,
            "class_name": class_name,
            "fields": [item.to_wire() for item in normalized_fields],
            "actions": [item.to_wire() for item in normalized_actions],
            "relationships": [item.to_wire() for item in normalized_relationships],
        }
        binding_digest = _binding_digest(OBJECT_ABI_CONTRACT + ".class", payload)
        check()
        return cls(
            type_ref=type_ref,
            class_name=class_name,
            fields=normalized_fields,
            actions=normalized_actions,
            relationships=normalized_relationships,
            binding_digest=binding_digest,
        )

    def _wire_payload(self) -> dict[str, object]:
        _binding_native(self, OntologyObjectClassBinding)
        return {
            "type_ref": self.type_ref,
            "class_name": self.class_name,
            "fields": [item.to_wire() for item in self.fields],
            "actions": [item.to_wire() for item in self.actions],
            "relationships": [item.to_wire() for item in self.relationships],
        }

    def to_wire(self) -> dict[str, object]:
        _binding_native(self, OntologyObjectClassBinding)
        return {**self._wire_payload(), "binding_digest": self.binding_digest}

    def field(self, name: str) -> OntologyObjectFieldBinding | None:
        _binding_native(self, OntologyObjectClassBinding)
        _binding_token(name, "member_name")
        return next(
            (
                item
                for item in self.fields
                if item.attribute_name == name or item.field_ref == name
            ),
            None,
        )

    def action(self, name: str) -> OntologyObjectActionBinding | None:
        _binding_native(self, OntologyObjectClassBinding)
        _binding_token(name, "member_name")
        return next(
            (
                item
                for item in self.actions
                if item.method_name == name or item.action_ref == name
            ),
            None,
        )

    def relationship(
        self,
        name: str,
        direction: OntologyObjectRelationshipDirection | None = None,
    ) -> OntologyObjectRelationshipBinding | None:
        _binding_native(self, OntologyObjectClassBinding)
        _binding_token(name, "member_name")
        if direction is not None and type(direction) is not OntologyObjectRelationshipDirection:
            raise TypeError("direction must be exact direction enum")
        matches = tuple(
            item
            for item in self.relationships
            if (item.method_name == name or item.relationship_ref == name)
            and (direction is None or item.direction is direction)
        )
        if len(matches) > 1:
            raise OntologyObjectContractError(
                f"relationship {name!r} requires an exact direction"
            )
        return None if not matches else matches[0]


class MutationScope(StrEnum):
    TARGET = "target"
    CONTAINED = "contained"
    DECLARED_TYPES = "declared_types"


class CoverageGrade(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True, order=True)
class RelationshipInstance:
    instance_ref: str
    relationship_ref: str
    source_instance_ref: str
    target_instance_ref: str

    def __post_init__(self) -> None:
        for field in (
            "instance_ref",
            "relationship_ref",
            "source_instance_ref",
            "target_instance_ref",
        ):
            object.__setattr__(self, field, _token(getattr(self, field), field))

    def to_wire(self) -> dict[str, object]:
        return {
            "instance_ref": self.instance_ref,
            "relationship_ref": self.relationship_ref,
            "source_instance_ref": self.source_instance_ref,
            "target_instance_ref": self.target_instance_ref,
        }


def _record_slot(value: object, field: str) -> object:
    check = _record_guard
    check()
    kind = type(value)
    if not any(kind is expected for expected in (
        FieldValue, ObjectInstance, RelationshipInstance, ProjectionCoverage,
        SchemaActionParameterDefinition, SchemaActionDefinition, RuntimeValue, FrozenJson,
    )):
        raise TypeError("record must have its exact owning class")
    if type(field) is not str:
        raise TypeError("record field must be exact str")
    result = object.__getattribute__(value, field)
    check()
    return result


def _record_token(value: object, field: str) -> str:
    check = _record_guard
    check()
    result = _binding_token(value, field)
    check()
    return result


def _record_refs(values: object, field: str) -> tuple[str, ...]:
    check = _record_guard
    check()
    if type(values) is not tuple and type(values) is not list:
        raise TypeError("refs must be an exact tuple or list")
    refs = []
    for value in values:
        refs.append(_record_token(value, field))
        check()
    normalized = tuple(sorted(refs))
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field} contains duplicates")
    return normalized


def _record_items(values: object, kind: type) -> tuple:
    check = _record_guard
    check()
    if type(values) is not tuple and type(values) is not list:
        raise TypeError("records must be an exact tuple or list")
    result = tuple(values)
    for value in result:
        _record_native(value, kind)
        check()
    return result


def _record_value_wire(value: object) -> dict[str, object]:
    check = _record_guard
    check()
    if type(value) is not RuntimeValue:
        raise TypeError("field value must be exact RuntimeValue")
    kind = _record_slot(value, "value_kind")
    check()
    if type(kind) is not ValueKind:
        raise TypeError("value kind must be exact ValueKind")
    _native_enum(kind, ValueKind, "value_kind")
    check()
    frozen = _record_slot(value, "value")
    check()
    if type(frozen) is not FrozenJson:
        raise TypeError("runtime content must be exact FrozenJson")
    canonical = _record_slot(frozen, "canonical")
    check()
    if type(canonical) is not str:
        raise TypeError("frozen content must be exact str")
    result = RuntimeValue.to_wire(value)
    check()
    return result


def _record_native(value: object, kind: type) -> None:
    check = _record_guard
    check()
    if type(value) is not kind:
        raise TypeError("record must have its exact owning class")
    if kind is FieldValue:
        _record_token(_record_slot(value, "field_ref"), "field_ref")
        check()
        _record_value_wire(_record_slot(value, "value"))
        check()
    elif kind is ObjectInstance:
        for field in ("instance_ref", "type_ref"):
            _record_token(_record_slot(value, field), field)
            check()
        _record_items(_record_slot(value, "fields"), FieldValue)
        check()
    elif kind is RelationshipInstance:
        for field in ("instance_ref", "relationship_ref", "source_instance_ref", "target_instance_ref"):
            _record_token(_record_slot(value, field), field)
            check()
    elif kind is ProjectionCoverage:
        _native_enum(_record_slot(value, "grade"), CoverageGrade, "coverage grade")
        check()
        _record_refs(_record_slot(value, "missing_refs"), "missing_refs")
        check()
    elif kind is SchemaActionParameterDefinition:
        _record_token(_record_slot(value, "parameter_ref"), "parameter_ref")
        check()
        position = _record_slot(value, "position")
        check()
        if type(position) is not int or position < 0:
            raise ValueError("position must be a non-negative integer")
        shape = _record_slot(value, "shape")
        check()
        if type(shape) is not ValueShape:
            raise TypeError("shape must be exact ValueShape")
        _shape_copy(shape)
        check()
        for field in ("required", "nullable"):
            if type(_record_slot(value, field)) is not bool:
                raise TypeError("parameter flags must be bool")
            check()
        _native_enum(_record_slot(value, "value_mode"), ActionValueMode, "value mode")
        check()
    elif kind is SchemaActionDefinition:
        for field in ("action_ref", "target_type_ref"):
            _record_token(_record_slot(value, field), field)
            check()
        _record_items(_record_slot(value, "parameters"), SchemaActionParameterDefinition)
        check()
        shape = _record_slot(value, "result_shape")
        check()
        if shape is not None:
            if type(shape) is not ValueShape:
                raise TypeError("result shape must be exact ValueShape or None")
            _shape_copy(shape)
            check()
        _native_enum(_record_slot(value, "result_value_mode"), ActionValueMode, "result value mode")
        check()
        _native_enum(_record_slot(value, "mutation_scope"), MutationScope, "mutation scope")
        check()
        _record_refs(_record_slot(value, "mutation_type_refs"), "mutation_type_refs")
        check()
    else:
        raise TypeError("unsupported portable record class")


@dataclass(frozen=True, slots=True, order=True)
class FieldValue:
    field_ref: str
    value: RuntimeValue

    def __post_init__(self) -> None:
        check = _record_guard
        check()
        _record_native(self, FieldValue)
        check()

    def to_wire(self) -> dict[str, object]:
        check = _record_guard
        check()
        _record_native(self, FieldValue)
        check()
        field = _record_slot(self, "field_ref")
        check()
        value = _record_value_wire(_record_slot(self, "value"))
        check()
        return {"field_ref": field, "value": value}


@dataclass(frozen=True, slots=True)
class ObjectInstance:
    instance_ref: str
    type_ref: str
    fields: tuple[FieldValue, ...]

    def __post_init__(self) -> None:
        check = _record_guard
        check()
        _record_native(self, ObjectInstance)
        check()
        fields = _record_items(_record_slot(self, "fields"), FieldValue)
        check()
        object.__setattr__(self, "fields", tuple(sorted(fields, key=lambda value: value.field_ref)))

    def to_wire(self) -> dict[str, object]:
        check = _record_guard
        check()
        _record_native(self, ObjectInstance)
        check()
        if type(self.fields) is not tuple:
            raise TypeError("fields must be exact tuple")
        values = []
        for field in self.fields:
            check()
            values.append(FieldValue.to_wire(field))
            check()
        return {"instance_ref": self.instance_ref, "type_ref": self.type_ref, "fields": values}


@dataclass(frozen=True, slots=True)
class ProjectionCoverage:
    grade: CoverageGrade
    missing_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        check = _record_guard
        check()
        _record_native(self, ProjectionCoverage)
        check()
        grade = CoverageGrade(self.grade)
        check()
        refs = _record_refs(self.missing_refs, "missing_refs")
        check()
        object.__setattr__(self, "grade", grade)
        object.__setattr__(self, "missing_refs", refs)
        if grade is CoverageGrade.COMPLETE and refs:
            raise ValueError("complete coverage cannot carry missing_refs")
        if grade is CoverageGrade.PARTIAL and not refs:
            raise ValueError("partial coverage requires missing_refs")

    def to_wire(self) -> dict[str, object]:
        check = _record_guard
        check()
        _record_native(self, ProjectionCoverage)
        check()
        if type(self.grade) is not CoverageGrade or type(self.missing_refs) is not tuple:
            raise TypeError("coverage must retain exact normalized data")
        if tuple(sorted(set(self.missing_refs))) != self.missing_refs:
            raise ValueError("missing refs unordered or duplicated")
        if (self.grade is CoverageGrade.COMPLETE) != (not self.missing_refs):
            raise ValueError("coverage grade and missing refs disagree")
        return {"grade": self.grade.value, "missing_refs": list(self.missing_refs)}


@dataclass(frozen=True, slots=True, order=True)
class SchemaActionParameterDefinition:
    parameter_ref: str
    position: int
    shape: ValueShape
    required: bool = True
    nullable: bool = False
    value_mode: ActionValueMode = ActionValueMode.VALUE

    def __post_init__(self) -> None:
        check = _record_guard
        check()
        _record_native(self, SchemaActionParameterDefinition)
        check()
        shape = _shape_copy(self.shape)
        check()
        mode = ActionValueMode(self.value_mode)
        check()
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "value_mode", mode)

    def to_wire(self) -> dict[str, object]:
        check = _record_guard
        check()
        _record_native(self, SchemaActionParameterDefinition)
        check()
        if type(self.value_mode) is not ActionValueMode:
            raise TypeError("parameter mode must retain its exact enum")
        shape = _shape_wire(self.shape)
        check()
        return {"parameter_ref": self.parameter_ref, "position": self.position,
                "shape": shape, "required": self.required, "nullable": self.nullable,
                "value_mode": self.value_mode.value}


@dataclass(frozen=True, slots=True)
class SchemaActionDefinition:
    action_ref: str
    target_type_ref: str
    parameters: tuple[SchemaActionParameterDefinition, ...] = ()
    result_shape: ValueShape | None = None
    result_value_mode: ActionValueMode = ActionValueMode.VALUE
    mutation_scope: MutationScope = MutationScope.TARGET
    mutation_type_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        check = _record_guard
        check()
        _record_native(self, SchemaActionDefinition)
        check()
        values = _record_items(self.parameters, SchemaActionParameterDefinition)
        check()
        result_shape = None if self.result_shape is None else _shape_copy(self.result_shape)
        check()
        mode = ActionValueMode(self.result_value_mode)
        check()
        scope = MutationScope(self.mutation_scope)
        check()
        refs = _record_refs(self.mutation_type_refs, "mutation_type_refs")
        check()
        object.__setattr__(self, "parameters", tuple(sorted(values, key=lambda value: (value.position, value.parameter_ref))))
        object.__setattr__(self, "result_shape", result_shape)
        object.__setattr__(self, "result_value_mode", mode)
        object.__setattr__(self, "mutation_scope", scope)
        object.__setattr__(self, "mutation_type_refs", refs)
        if scope is MutationScope.DECLARED_TYPES:
            if not refs:
                raise ValueError("declared_types requires mutation_type_refs")
        elif refs:
            raise ValueError("mutation_type_refs require declared_types")

    def to_wire(self) -> dict[str, object]:
        check = _record_guard
        check()
        _record_native(self, SchemaActionDefinition)
        check()
        if type(self.parameters) is not tuple or type(self.mutation_type_refs) is not tuple:
            raise TypeError("Action collections must retain exact tuples")
        if type(self.result_value_mode) is not ActionValueMode or type(self.mutation_scope) is not MutationScope:
            raise TypeError("Action modes must retain exact enums")
        parameters = []
        for value in self.parameters:
            check()
            parameters.append(SchemaActionParameterDefinition.to_wire(value))
            check()
        result = None if self.result_shape is None else _shape_wire(self.result_shape)
        check()
        return {"action_ref": self.action_ref, "target_type_ref": self.target_type_ref,
                "parameters": parameters, "result_shape": result,
                "result_value_mode": self.result_value_mode.value,
                "mutation_scope": self.mutation_scope.value,
                "mutation_type_refs": list(self.mutation_type_refs)}


def _protect_relationship_method(operation: FunctionType):
    """Preserve the historical class source with native preflight outside it."""
    original_code = operation.__code__

    def protected(self):
        check = _record_guard
        check()
        _record_native(self, RelationshipInstance)
        check()
        if operation.__code__ is not original_code:
            raise TypeError("record operation identity mismatched")
        result = operation(self)
        check()
        return result

    return protected


# Original method bodies remain source-pinned; both wrappers and originals are retained.
_record_originals = (RelationshipInstance.__post_init__, RelationshipInstance.to_wire)
RelationshipInstance.__post_init__ = _protect_relationship_method(_record_originals[0])
RelationshipInstance.to_wire = _protect_relationship_method(_record_originals[1])
_token = _record_token



OBJECT_ACTION_ROLES_CONTRACT = "aware.ontology.object-action-roles.v1"


def _abi_slot(value: object, field: str) -> object:
    check = _abi_guard
    check()
    kind = type(value)
    if not any(kind is expected for expected in (
        OntologyObjectActionRoleDeclaration, OntologyObjectActionRoleManifest,
        OntologyObjectAbi, OntologyObjectClassBinding, SchemaActionDefinition,
    )):
        raise TypeError("ABI slot receiver must have its exact owning class")
    descriptor = vars(kind).get(field)
    if type(descriptor) is not MemberDescriptorType:
        raise TypeError("ABI data must retain native slots")
    result = descriptor.__get__(value, kind)
    check()
    return result


def _abi_items(values: object, kind: type) -> tuple:
    check = _abi_guard
    check()
    if type(values) is not tuple and type(values) is not list:
        raise TypeError("ABI items must be exact tuple or list")
    result = tuple(values)
    for item in result:
        check()
        if kind is OntologyObjectActionRoleDeclaration or kind is OntologyObjectActionRoleManifest:
            _abi_native(item, kind)
        else:
            _binding_native(item, kind)
        check()
    return result


def _abi_paths(values: object) -> tuple:
    check = _abi_guard
    check()
    paths = _abi_items(values, OntologyObjectRelationshipConstructorPath)
    check()
    return tuple((tuple(path.relationship_refs), path.constructor_action_ref) for path in paths)


def _abi_native(value: object, kind: type) -> None:
    check = _abi_guard
    check()
    if type(value) is not kind:
        raise TypeError("ABI value must have its exact owning class")
    if kind is OntologyObjectActionRoleDeclaration:
        definition = _abi_slot(value, "definition")
        check()
        _record_native(definition, SchemaActionDefinition)
        check()
        role = _abi_slot(value, "role")
        check()
        _native_enum(role, OntologyObjectActionRole, "role")
        check()
        paths = _abi_slot(value, "relationship_constructor_paths")
        check()
        _abi_paths(paths)
        check()
    elif kind is OntologyObjectActionRoleManifest or kind is OntologyObjectAbi:
        fields = ("contract", "topology_digest", "manifest_digest") if kind is OntologyObjectActionRoleManifest else ("contract", "topology_digest", "schema_digest", "schema_slice_digest", "abi_digest")
        for field in fields:
            token = _abi_slot(value, field)
            check()
            _binding_token(token, field)
            check()
        if kind is OntologyObjectActionRoleManifest:
            items = _abi_slot(value, "actions")
            check()
            _abi_items(items, OntologyObjectActionRoleDeclaration)
            check()
        else:
            roles = _abi_slot(value, "action_roles")
            check()
            _abi_native(roles, OntologyObjectActionRoleManifest)
            check()
            classes = _abi_slot(value, "classes")
            check()
            _abi_items(classes, OntologyObjectClassBinding)
            check()
    else:
        raise TypeError("unsupported ABI aggregate")


def _abi_wire(value: Any, kind: type) -> dict[str, object]:
    check = _abi_guard
    check()
    if kind is SchemaActionDefinition:
        _record_native(value, kind)
    elif kind is OntologyObjectClassBinding or kind is OntologyObjectRelationshipConstructorPath:
        _binding_native(value, kind)
    else:
        _abi_native(value, kind)
    check()
    result = kind.to_wire(value)
    check()
    return result


def _abi_order(values: tuple, field: str, *, declarations: bool = False) -> tuple:
    check = _abi_guard
    check()
    keys = []
    for index, value in enumerate(values):
        target = value.definition if declarations else value
        key = _abi_slot(target, field)
        check()
        _binding_token(key, field)
        check()
        keys.append((key, index))
    return tuple(values[index] for _, index in sorted(keys))


@dataclass(frozen=True, slots=True)
class OntologyObjectActionRoleDeclaration:
    definition: SchemaActionDefinition
    role: OntologyObjectActionRole
    relationship_constructor_paths: tuple[OntologyObjectRelationshipConstructorPath, ...] = ()

    def __post_init__(self) -> None:
        check = _abi_guard
        check()
        _abi_native(self, OntologyObjectActionRoleDeclaration)
        check()
        role = OntologyObjectActionRole(self.role)
        check()
        keys = _abi_paths(self.relationship_constructor_paths)
        check()
        if len(keys) != len(set(keys)):
            raise OntologyObjectContractError("relationship constructor paths contain duplicates")
        if role is OntologyObjectActionRole.CONSTRUCTOR and keys:
            raise OntologyObjectContractError("constructor Actions cannot own relationship constructor paths")
        ordered = tuple(self.relationship_constructor_paths[index] for _, index in sorted((key, index) for index, key in enumerate(keys)))
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "relationship_constructor_paths", ordered)

    @property
    def action_ref(self) -> str:
        check = _abi_guard
        check()
        _abi_native(self, OntologyObjectActionRoleDeclaration)
        check()
        return self.definition.action_ref

    def to_wire(self) -> dict[str, object]:
        check = _abi_guard
        check()
        _abi_native(self, OntologyObjectActionRoleDeclaration)
        check()
        if type(self.role) is not OntologyObjectActionRole:
            raise TypeError("role must retain exact normalized enum")
        definition = _abi_wire(self.definition, SchemaActionDefinition)
        check()
        paths = []
        for item in self.relationship_constructor_paths:
            paths.append(_abi_wire(item, OntologyObjectRelationshipConstructorPath))
            check()
        return {"definition": definition, "role": self.role.value, "relationship_constructor_paths": paths}


@dataclass(frozen=True, slots=True)
class OntologyObjectActionRoleManifest:
    topology_digest: str
    actions: tuple[OntologyObjectActionRoleDeclaration, ...]
    manifest_digest: str
    contract: str = OBJECT_ACTION_ROLES_CONTRACT

    def __post_init__(self) -> None:
        check = _abi_guard
        check()
        _abi_native(self, OntologyObjectActionRoleManifest)
        check()
        if self.contract != OBJECT_ACTION_ROLES_CONTRACT:
            raise OntologyObjectContractError("object Action-role contract is unsupported")
        values = _abi_order(tuple(self.actions), "action_ref", declarations=True)
        check()
        if len({item.definition.action_ref for item in values}) != len(values):
            raise OntologyObjectContractError("Action-role manifest contains duplicate Actions")
        object.__setattr__(self, "actions", values)
        payload = self._wire_payload()
        check()
        expected = digest_payload(OBJECT_ACTION_ROLES_CONTRACT, payload)
        check()
        if self.manifest_digest != expected:
            raise OntologyObjectContractError("Action-role manifest digest mismatched")

    def _wire_payload(self) -> dict[str, object]:
        check = _abi_guard
        check()
        _abi_native(self, OntologyObjectActionRoleManifest)
        check()
        values = []
        for item in self.actions:
            values.append(_abi_wire(item, OntologyObjectActionRoleDeclaration))
            check()
        return {"contract": self.contract, "topology_digest": self.topology_digest, "actions": values}

    def to_wire(self) -> dict[str, object]:
        check = _abi_guard
        check()
        payload = self._wire_payload()
        check()
        return {**payload, "manifest_digest": self.manifest_digest}

    def action(self, action_ref: str) -> OntologyObjectActionRoleDeclaration:
        check = _abi_guard
        check()
        _binding_token(action_ref, "action_ref")
        check()
        _abi_native(self, OntologyObjectActionRoleManifest)
        check()
        for item in self.actions:
            if item.definition.action_ref == action_ref:
                return item
        raise OntologyObjectContractError(f"Action {action_ref!r} is outside object Action-role manifest")


@dataclass(frozen=True, slots=True)
class OntologyObjectAbi:
    topology_digest: str
    schema_digest: str
    schema_slice_digest: str
    action_roles: OntologyObjectActionRoleManifest
    classes: tuple[OntologyObjectClassBinding, ...]
    abi_digest: str
    contract: str = OBJECT_ABI_CONTRACT

    def __post_init__(self) -> None:
        check = _abi_guard
        check()
        _abi_native(self, OntologyObjectAbi)
        check()
        if self.contract != OBJECT_ABI_CONTRACT:
            raise OntologyObjectContractError("object ABI contract is unsupported")
        if self.action_roles.topology_digest != self.topology_digest:
            raise OntologyObjectContractError("object ABI Action-role topology digest mismatched")
        values = _abi_order(tuple(self.classes), "type_ref")
        check()
        if not values:
            raise OntologyObjectContractError("object ABI requires class bindings")
        if len({item.type_ref for item in values}) != len(values):
            raise OntologyObjectContractError("object ABI contains duplicate types")
        object.__setattr__(self, "classes", values)
        _validate_object_abi_binding_closure(self.action_roles, values)
        check()
        payload = self._wire_payload()
        check()
        expected = digest_payload(OBJECT_ABI_CONTRACT, payload)
        check()
        if self.abi_digest != expected:
            raise OntologyObjectContractError("object ABI digest mismatched")

    def _wire_payload(self) -> dict[str, object]:
        check = _abi_guard
        check()
        _abi_native(self, OntologyObjectAbi)
        check()
        roles = _abi_wire(self.action_roles, OntologyObjectActionRoleManifest)
        check()
        values = []
        for item in self.classes:
            values.append(_abi_wire(item, OntologyObjectClassBinding))
            check()
        return {"contract": self.contract, "topology_digest": self.topology_digest,
                "schema_digest": self.schema_digest, "schema_slice_digest": self.schema_slice_digest,
                "action_roles": roles, "classes": values}

    def to_wire(self) -> dict[str, object]:
        check = _abi_guard
        check()
        payload = self._wire_payload()
        check()
        return {**payload, "abi_digest": self.abi_digest}

    def class_binding(self, type_ref: str) -> OntologyObjectClassBinding:
        check = _abi_guard
        check()
        _binding_token(type_ref, "type_ref")
        check()
        _abi_native(self, OntologyObjectAbi)
        check()
        for item in self.classes:
            if item.type_ref == type_ref:
                return item
        raise OntologyObjectContractError(f"type {type_ref!r} is outside object ABI")


def _abi_parameters(parameters: tuple) -> tuple:
    check = _abi_guard
    check()
    values = []
    for item in parameters:
        shape = _shape_wire(item.shape)
        check()
        mode = item.value_mode
        if type(mode) is not ActionValueMode:
            raise TypeError("parameter mode must retain its exact normalized enum")
        values.append((item.parameter_ref, item.position, shape, item.required, item.nullable, mode.value))
    return tuple(values)


def _validate_object_abi_binding_closure(
    action_roles: OntologyObjectActionRoleManifest,
    classes: tuple[OntologyObjectClassBinding, ...],
) -> None:
    """Validate the semantic closure shared by direct and decoded ABI values."""

    check = _abi_guard
    check()
    _abi_native(action_roles, OntologyObjectActionRoleManifest)
    check()
    _abi_items(classes, OntologyObjectClassBinding)
    check()
    roles = {item.definition.action_ref: item for item in action_roles.actions}
    classes_by_ref = {item.type_ref: item for item in classes}
    bound_action_refs: list[str] = []
    for class_binding in classes:
        for action in class_binding.actions:
            declared_paths = _abi_paths(roles[action.action_ref].relationship_constructor_paths) if action.action_ref in roles else ()
            check()
            bound_paths = _abi_paths(action.relationship_constructor_paths)
            check()
            declaration = roles.get(action.action_ref)
            if declaration is None or (
                declaration.definition.target_type_ref != class_binding.type_ref
                or declaration.role is not action.role
                or declared_paths != bound_paths
            ):
                raise OntologyObjectContractError(
                    "object ABI Action binding escaped authored role authority"
                )
            expected_parameters = _abi_parameters(declaration.definition.parameters)
            check()
            actual_parameters = _abi_parameters(action.parameters)
            check()
            if actual_parameters != expected_parameters:
                raise OntologyObjectContractError(
                    "object ABI Action signature escaped authored role authority"
                )
            bound_action_refs.append(action.action_ref)

            for path in action.relationship_constructor_paths:
                current_type_ref = class_binding.type_ref
                for relationship_ref in path.relationship_refs:
                    current_class = classes_by_ref.get(current_type_ref)
                    if current_class is None:
                        raise OntologyObjectContractError(
                            "relationship constructor path escaped class closure"
                        )
                    matches = tuple(
                        relationship
                        for relationship in current_class.relationships
                        if relationship.relationship_ref == relationship_ref
                        and relationship.direction
                        is OntologyObjectRelationshipDirection.OUTGOING
                        and relationship.source_type_ref == current_type_ref
                    )
                    if len(matches) != 1:
                        raise OntologyObjectContractError(
                            "relationship constructor path is disconnected or direction-invalid"
                        )
                    current_type_ref = matches[0].target_type_ref
                constructor = roles.get(path.constructor_action_ref)
                if (
                    constructor is None
                    or constructor.role is not OntologyObjectActionRole.CONSTRUCTOR
                    or constructor.definition.target_type_ref != current_type_ref
                ):
                    raise OntologyObjectContractError(
                        "relationship constructor path terminal Action mismatched"
                    )

        for relationship in class_binding.relationships:
            outgoing = (
                relationship.direction is OntologyObjectRelationshipDirection.OUTGOING
            )
            owner_type_ref = (
                relationship.source_type_ref
                if outgoing
                else relationship.target_type_ref
            )
            peer_type_ref = (
                relationship.target_type_ref
                if outgoing
                else relationship.source_type_ref
            )
            if owner_type_ref != class_binding.type_ref or (
                peer_type_ref not in classes_by_ref
            ) != (
                relationship.endpoint_residence
                is RelationshipEndpointResidence.EXTERNAL_DEPENDENCY
            ):
                raise OntologyObjectContractError(
                    "object ABI relationship binding escaped class closure"
                )

    expected_action_refs = tuple(sorted(roles))
    if tuple(sorted(bound_action_refs)) != expected_action_refs:
        raise OntologyObjectContractError(
            "object ABI class bindings do not exactly cover authored Action roles"
        )


def _protect_shape_dispatch(binding_classes: tuple[type, ...] = (), *,
                            guard_name: str | None = None, helpers: tuple[FunctionType, ...] = (),
                            extra_modules: tuple[ModuleType, ...] = (),
                            guard_namespace: dict[str, object] | None = None,
                            retained_guard_cell: Any = None, guard_aliases: tuple = ()):
    attempt_guard_cell = _attempt_guard_cell
    expected_guard = guard_name or ("_binding_guard" if binding_classes else "_shape_guard")
    """Retain the sole shape owner's executable and lookup dependencies."""
    native_type, object_get = type, object.__getattribute__
    dict_get, dict_keys = dict.get, dict.keys
    dict_type, class_get = dict, type.__getattribute__
    length = len
    tuple_type, string_type, module_type = tuple, str, ModuleType
    native_map, native_all, same_object = map, all, _same_object
    dict_values = dict.values
    proxy_values = type(type.__dict__).values
    failure = TypeError
    modules = tuple(sys.modules[name] for name in (
        "aware_meta_type_schema.model", "enum", "_operator",
    ))
    def unique(values):
        result = []
        for value in values:
            if not any(value is prior for prior in result):
                result.append(value)
        return tuple(result)
    modules = unique((*modules, *extra_modules))
    namespaces = tuple((module, tuple(vars(module)), tuple(vars(module).items())) for module in modules)
    guard_values = globals() if guard_namespace is None else guard_namespace
    absent = tuple((module, tuple(name for name in vars(builtins) if name not in vars(module))) for module in modules)
    classes = (ValueShape, ShapeKind, ScalarKind, Enum, StrEnum, type(StrEnum), vars(sys.modules["enum"])["property"], *binding_classes)
    classes = unique(classes)
    class_members = tuple((kind, tuple(vars(kind)), tuple(vars(kind).items())) for kind in classes)
    class_kinds = tuple((kind, native_type(kind)) for kind in classes)
    guard_alias_namespaces = tuple((object_get(module, "__dict__"), name) for module, name in guard_aliases)
    member_namespaces = []
    for kind in classes:
        members = vars(kind).get("_member_map_")
        if type(members) is dict:
            for member in members.values():
                values = object.__getattribute__(member, "__dict__")
                member_namespaces.append((values, tuple(values), tuple(values.items())))
    functions = []
    containers = []
    if expected_guard == "_attempt_guard":
        for name in ("_attempt_specs", "_attempt_domains", "_attempt_nullable", "_attempt_enums"):
            value = globals()[name]
            containers.append((value, tuple(value.items())))
    descriptors = []
    for _, _, items in (*namespaces, *class_members):
        for _, operation in items:
            if type(operation) is dict:
                containers.append((operation, tuple(operation.items())))
            elif type(operation) is list:
                containers.append((operation, tuple(operation)))
            if type(operation) is property or type(operation) is vars(sys.modules["enum"])["property"]:
                accessors = tuple((name, object.__getattribute__(operation, name)) for name in ("fget", "fset", "fdel"))
                descriptors.append((operation, accessors))
                for _, accessor in accessors:
                    if type(accessor) is FunctionType:
                        functions.append((accessor, accessor.__code__, accessor.__defaults__, accessor.__kwdefaults__))
            if type(operation) is classmethod or type(operation) is staticmethod:
                operation = operation.__func__
            if type(operation) is FunctionType:
                functions.append((operation, operation.__code__, operation.__defaults__, operation.__kwdefaults__))
    functions.extend((operation, operation.__code__, operation.__defaults__, operation.__kwdefaults__)
                     for operation in (_shape_copy, _shape_wire, _native_enum, _binding_native, _binding_items, _binding_token, _binding_digest))
    functions.extend((operation, operation.__code__, operation.__defaults__, operation.__kwdefaults__)
                     for operation in helpers)
    seen = []
    functions = tuple(entry for entry in functions
                      if not any(entry[0] is prior for prior in seen)
                      and not seen.append(entry[0]))
    functions = tuple((operation, code, defaults, kwdefaults,
                       tuple((cell, cell.cell_contents) for cell in (operation.__closure__ or ())))
                      for operation, code, defaults, kwdefaults in functions)
    for _, _, _, kwdefaults, _ in functions:
        if type(kwdefaults) is dict:
            containers.append((kwdefaults, tuple(kwdefaults.items())))
    seen = []
    containers = tuple(entry for entry in containers
                       if not any(entry[0] is prior for prior in seen)
                       and not seen.append(entry[0]))
    seen = []
    descriptors = tuple(entry for entry in descriptors
                        if not any(entry[0] is prior for prior in seen)
                        and not seen.append(entry[0]))
    # Globals used at nested return boundaries are also exact owner aliases.
    namespace = globals()
    owner_keys = tuple(namespace) + tuple(name for name in ("_shape_guard", "_binding_guard", "_record_guard", "_abi_guard") if name not in namespace)
    builtin_namespace: dict[str, object] = object_get(builtins, "__dict__")
    builtin_keys = tuple(builtin_namespace)
    builtin_bindings = tuple(builtin_namespace.items())
    primitive_bindings = tuple((name, name in namespace, namespace.get(name)) for name in builtin_namespace)
    aliases = tuple((name, namespace[name]) for name in ("ValueShape", "ShapeKind", "ScalarKind", "_shape_copy", "_shape_wire", "_native_enum", "_binding_native", "_binding_items", "_binding_token", "_binding_digest"))

    if expected_guard == "_record_guard" or expected_guard == "_abi_guard" or expected_guard == "_attempt_guard" or guard_namespace is not None:
        aliases += tuple((name, value) for name, value in tuple(namespace.items())
                         if not name.startswith("__") and name != expected_guard and name != "_attempt_guard")

    # Seal each exceptional verifier alias once, instead of rebuilding a
    # generator for every ordinary binding on every return check.
    checked_namespaces = tuple((module, names, tuple(
        (name, expected, any(object_get(module, "__dict__") is ns and name == alias
                             for ns, alias in guard_alias_namespaces))
        for name, expected in items)) for module, names, items in namespaces)

    # These are definition-time expectations, not positive admission results.
    # Retain every original object alongside its identity vector; every check
    # reads all current slots again, with no equality dispatch on their values.
    owner_indices = tuple(dict.fromkeys(
        [owner_keys.index(name) for name, present, _ in primitive_bindings if present]
        + [owner_keys.index(name) for name, _ in aliases]
    ))
    owner_expected = tuple(namespace[owner_keys[index]] for index in owner_indices)
    owner_plan = ((primitive_bindings, aliases), owner_indices, owner_expected)
    builtin_plan = (builtin_bindings, tuple(builtin_namespace.values()))
    class_plans = tuple((kind, names, items, tuple(value for _, value in items))
                        for kind, names, items in class_members)
    member_plans = tuple((values, names, items, tuple(value for _, value in items))
                         for values, names, items in member_namespaces)
    container_plans = tuple((container, expected,
                            tuple(key for key, _ in expected) if native_type(container) is dict_type else (),
                            tuple(value for _, value in expected) if native_type(container) is dict_type else expected)
                           for container, expected in containers)
    # Shared closures can expose the same physical slot through hundreds of
    # functions. Retain one original expectation per slot, then freshly read
    # every distinct slot on EVERY check. This deduplicates the read schedule,
    # never a successful admission or an observed runtime value.
    distinct_cells = {}
    distinct_special_cells = {}
    for row in functions:
        for cell, expected in row[4]:
            if cell is retained_guard_cell or cell is attempt_guard_cell:
                distinct_special_cells[id(cell)] = cell
                continue
            previous = distinct_cells.get(id(cell))
            if previous is not None and (previous[0] is not cell or previous[1] is not expected):
                raise failure("inconsistent original owner closure slot")
            distinct_cells[id(cell)] = (cell, expected)
    ordinary_cells = tuple(distinct_cells.values())
    cell_plan = (ordinary_cells, tuple(cell for cell, _ in ordinary_cells),
                 tuple(expected for _, expected in ordinary_cells))
    special_cells = tuple(distinct_special_cells.values())
    read_cell = _native_attrgetter("cell_contents")
    function_targets = tuple(row[0] for row in functions)
    expected_codes = tuple(row[1] for row in functions)
    expected_defaults = tuple(row[2] for row in functions)
    expected_kwdefaults = tuple(row[3] for row in functions)
    read_code = _native_attrgetter("__code__")
    read_defaults = _native_attrgetter("__defaults__")
    read_kwdefaults = _native_attrgetter("__kwdefaults__")
    descriptor_kinds = tuple((target, native_type(target)) for target, _ in descriptors)
    flatten = _native_chain.from_iterable
    dictionary_targets = tuple(row[0] for row in container_plans if native_type(row[0]) is dict_type)
    sequence_targets = tuple(row[0] for row in container_plans if native_type(row[0]) is not dict_type)
    dictionary_lengths = tuple(length(row[1]) for row in container_plans if native_type(row[0]) is dict_type)
    sequence_lengths = tuple(length(row[1]) for row in container_plans if native_type(row[0]) is not dict_type)
    dictionary_expected_keys = tuple(key for row in container_plans if native_type(row[0]) is dict_type for key in row[2])
    dictionary_expected_values = tuple(value for row in container_plans if native_type(row[0]) is dict_type for value in row[3])
    sequence_expected_values = tuple(value for row in container_plans if native_type(row[0]) is not dict_type for value in row[3])
    namespace_plans = ()
    class_targets = tuple(row[0] for row in class_plans)
    class_expected_kinds = tuple(row[1] for row in class_kinds)
    class_namespaces = tuple(class_get(kind, "__dict__") for kind in class_targets)
    class_names = tuple(row[1] for row in class_plans)
    class_lengths = tuple(length(row[3]) for row in class_plans)
    class_values = tuple(value for row in class_plans for value in row[3])
    member_targets = tuple(row[0] for row in member_plans)
    member_names = tuple(row[1] for row in member_plans)
    member_lengths = tuple(length(row[3]) for row in member_plans)
    member_values = tuple(value for row in member_plans for value in row[3])
    namespace_targets = ()
    namespace_dicts = ()
    namespace_names = ()
    namespace_lengths = ()
    namespace_values = ()

    def check():
        native_entry: Any = "__aware_native_owner_scan_anchor_v1__"
        if native_type(native_entry) is not string_type:
            if native_entry(check, check.__code__) is not True:
                raise failure("shape operation identity mismatched")
            return
        if (length(namespace_plans) != length(namespace_targets)
                or length(absent) != length(namespace_targets)
                or length(class_plans) != length(class_targets)
                or length(class_kinds) != length(class_targets)
                or length(member_plans) != length(member_targets)):
            raise failure("shape operation identity mismatched")
        current_keys = tuple_type(dict_keys(namespace))
        if (not native_all(native_map(same_object, native_map(native_type, current_keys), (string_type,) * length(current_keys)))
                or current_keys != owner_keys):
            raise failure("shape operation identity mismatched")
        current_values = tuple_type(dict_values(namespace))
        # The complete ordered-key check above also proves the captured
        # absent/present primitive bindings. Selecting values is native tuple
        # indexing; foreign values never supply hashing or equality callbacks.
        if length(current_values) != length(owner_keys) or not native_all(native_map(
                same_object, native_map(current_values.__getitem__, owner_plan[1]), owner_plan[2])):
            raise failure("shape operation identity mismatched")
        current_builtin_keys = tuple_type(dict_keys(builtin_namespace))
        if (not native_all(native_map(same_object, native_map(native_type, current_builtin_keys), (string_type,) * length(current_builtin_keys)))
                or current_builtin_keys != builtin_keys):
            raise failure("shape operation identity mismatched")
        current_values = tuple_type(dict_values(builtin_namespace))
        if length(current_values) != length(builtin_plan[1]) or not native_all(native_map(same_object, current_values, builtin_plan[1])):
            raise failure("shape operation identity mismatched")
        if dict_get(guard_values, expected_guard) is not check:
            raise failure("shape operation identity mismatched")
        # Live namespace views are non-replaceable on the exact admitted
        # module/type. Batch their fresh reads, retaining each extent so a
        # balanced move between dictionaries cannot conceal substitution.
        if not native_all(native_map(same_object, native_map(native_type, namespace_targets), (module_type,) * length(namespace_targets))):
            raise failure("shape operation identity mismatched")
        current_names = tuple_type(native_map(tuple_type, native_map(dict_keys, namespace_dicts)))
        keys = tuple_type(flatten(current_names))
        if (not native_all(native_map(same_object, native_map(native_type, keys), (string_type,) * length(keys)))
                or current_names != namespace_names):
            raise failure("shape operation identity mismatched")
        current_values = tuple_type(native_map(tuple_type, native_map(dict_values, namespace_dicts)))
        if (tuple_type(native_map(length, current_values)) != namespace_lengths
                or not native_all(native_map(same_object, flatten(current_values), namespace_values))):
            raise failure("shape operation identity mismatched")
        # Exact ordered namespace coverage above also checks every captured
        # absent builtin name: adding even a NULL-valued binding changes keys.
        if not native_all(native_map(same_object, native_map(native_type, class_targets), class_expected_kinds)):
            raise failure("shape operation identity mismatched")
        current_names = tuple_type(native_map(tuple_type, class_namespaces))
        if current_names != class_names:
            raise failure("shape operation identity mismatched")
        current_values = tuple_type(native_map(tuple_type, native_map(proxy_values, class_namespaces)))
        if (tuple_type(native_map(length, current_values)) != class_lengths
                or not native_all(native_map(same_object, flatten(current_values), class_values))):
            raise failure("shape operation identity mismatched")
        current_names = tuple_type(native_map(tuple_type, native_map(dict_keys, member_targets)))
        keys = tuple_type(flatten(current_names))
        if (not native_all(native_map(same_object, native_map(native_type, keys), (string_type,) * length(keys)))
                or current_names != member_names):
            raise failure("shape operation identity mismatched")
        current_values = tuple_type(native_map(tuple_type, native_map(dict_values, member_targets)))
        if (tuple_type(native_map(length, current_values)) != member_lengths
                or not native_all(native_map(same_object, flatten(current_values), member_values))):
            raise failure("shape operation identity mismatched")
        # Fresh complete vectors, not a cached admission. Keep original rows
        # alive; native pointer identity never dispatches foreign equality.
        if (length(container_plans) != length(dictionary_targets) + length(sequence_targets)
                or tuple_type(native_map(length, dictionary_targets)) != dictionary_lengths
                or tuple_type(native_map(length, sequence_targets)) != sequence_lengths
                or not native_all(native_map(same_object, flatten(native_map(dict_keys, dictionary_targets)), dictionary_expected_keys))
                or not native_all(native_map(same_object, flatten(native_map(dict_values, dictionary_targets)), dictionary_expected_values))
                or not native_all(native_map(same_object, flatten(sequence_targets), sequence_expected_values))):
            raise failure("shape operation identity mismatched")
        for target, expected_kind in descriptor_kinds:
            if native_type(target) is not expected_kind:
                raise failure("shape operation identity mismatched")
        for descriptor, accessors in descriptors:
            for name, expected in accessors:
                if object_get(descriptor, name) is not expected:
                    raise failure("shape operation identity mismatched")
        if (length(functions) != length(function_targets)
                or not native_all(native_map(same_object, native_map(read_code, function_targets), expected_codes))
                or not native_all(native_map(same_object, native_map(read_defaults, function_targets), expected_defaults))
                or not native_all(native_map(same_object, native_map(read_kwdefaults, function_targets), expected_kwdefaults))):
            raise failure("shape operation identity mismatched")
        if not native_all(native_map(same_object, native_map(read_cell, cell_plan[1]), cell_plan[2])):
            raise failure("shape operation identity mismatched")
        for cell in special_cells:
            if cell is not retained_guard_cell and cell is not attempt_guard_cell:
                raise failure("shape operation identity mismatched")
            wanted = check if cell is retained_guard_cell else dict_get(namespace, "_attempt_guard")
            if read_cell(cell) is not wanted:
                raise failure("shape operation identity mismatched")

    namespace_plans = tuple((module, names, items, tuple(
        (check if is_guard_alias or (object_get(module, "__dict__") is guard_values and name == expected_guard)
         else expected)
        for name, expected, is_guard_alias in items))
        for module, names, items in checked_namespaces)
    namespace_targets = tuple(row[0] for row in namespace_plans)
    namespace_dicts = tuple(object_get(module, "__dict__") for module in namespace_targets)
    namespace_names = tuple(row[1] for row in namespace_plans)
    namespace_lengths = tuple(length(row[3]) for row in namespace_plans)
    namespace_values = tuple(value for row in namespace_plans for value in row[3])
    return check


if __package__ is None:
    raise ImportError("owner scanner requires its original package")
try:
    _owner_native_scan_module = _owner_native_importlib.import_module(__package__ + "._preparation_scan")
except ModuleNotFoundError as _owner_native_scan_error:
    if _owner_native_scan_error.name != __package__ + "._preparation_scan":
        raise
    if _owner_native_import_util.find_spec(__package__ + "._preparation_scan") is not None:
        raise
    _owner_native_scan_module = None
if _owner_native_scan_module is not None:
    _owner_native_scan_module.bind_owner_installer(_protect_shape_dispatch)


_shape_guard: Any
_binding_guard: Any
_record_guard: Any
_abi_guard: Any


def _install_abi_dispatch() -> None:
    """Seal genuine ABI guards in closures before any public dispatch."""
    guard: Any = None
    unwind = BaseException
    namespace = globals()
    originals = []
    wrappers = []

    native_type = type
    failure = TypeError
    native_visit = _value_native
    native_operations = tuple(value for value in vars(builtins).values()
                              if type(value) is BuiltinMethodType) + (
        bool, int, str, bytes, tuple, list, dict, set, TypeError, ValueError,
        object.__getattribute__, object.__setattr__, type.__getattribute__,
    )
    native_receivers = (str, bytes, tuple, list, dict, set)
    native_any = any
    native_get = object.__getattribute__
    comparisons = ("__eq__", "__lt__", "__le__", "__gt__", "__ge__")
    representations = (*comparisons, "__repr__", "__hash__")

    def protect(operation, *, receiver_kind=None, class_receiver=False):
        originals.append(operation)
        method_name = operation.__name__

        def protected(*args, **kwargs):
            check = guard
            # Native primitives have no replaceable Python body. A substituted
            # lookup falls through to the full verifier before dispatch.
            if method_name == "_call" or method_name == "_value_call":
                target = args[0]
                if native_any(target is expected for expected in native_operations):
                    return target(*args[1:], **kwargs)
                if native_type(target) is BuiltinMethodType:
                    receiver = native_get(target, "__self__")
                    if native_any(native_type(receiver) is expected for expected in native_receivers):
                        return target(*args[1:], **kwargs)
            check()
            if receiver_kind is not None:
                receiver = args[0]
                if class_receiver:
                    if receiver is not receiver_kind:
                        raise failure("Object data factory requires its exact owning class")
                elif native_type(receiver) is not receiver_kind:
                    raise failure("Object data method requires its exact owning class")
            if method_name in representations:
                native_visit(args[0])
                if method_name in comparisons:
                    if native_type(args[1]) is not native_type(args[0]):
                        raise failure("Object data comparison requires its exact owning class")
                    native_visit(args[1])
            try:
                result = operation(*args, **kwargs)
            except unwind:
                check()
                raise
            check()
            return result

        protected.__name__ = operation.__name__
        protected.__qualname__ = operation.__qualname__
        protected.__module__ = operation.__module__
        protected.__annotations__ = operation.__annotations__
        protected.__kwdefaults__ = operation.__kwdefaults__
        protected.__dict__["__wrapped__"] = operation
        wrappers.append(protected)
        return protected

    for name in tuple(namespace):
        if name.startswith("_abi_") or name.startswith("_value_") or name in (
            "_validate_object_abi_binding_closure", "external_relationship_endpoint_sort_key",
        ):
            operation = namespace[name]
            if type(operation) is FunctionType:
                namespace[name] = protect(operation)
    for kind in (OntologyObjectActionRoleDeclaration, OntologyObjectActionRoleManifest, OntologyObjectAbi, *_value_classes):
        for name, operation in tuple(vars(kind).items()):
            if type(operation) is FunctionType:
                setattr(kind, name, protect(operation, receiver_kind=kind))
            elif type(operation) is property:
                setattr(kind, name, property(protect(operation.fget, receiver_kind=kind), operation.fset,
                                             operation.fdel, operation.__doc__))
            elif type(operation) is classmethod:
                setattr(kind, name, classmethod(protect(operation.__func__, receiver_kind=kind, class_receiver=True)))
            elif type(operation) is staticmethod:
                setattr(kind, name, staticmethod(protect(operation.__func__)))
    # Load only definitions after record classes exist; finish their private seal
    # before this owning module becomes an initialized consumer import.
    global _value_codec, _snapshot_codec
    from . import object_value_codec as _value_codec
    from . import object_snapshot_codec as _snapshot_codec
    for module in (_value_codec, _snapshot_codec):
        for name, operation in tuple(vars(module).items()):
            if type(operation) is FunctionType and operation.__module__ == module.__name__:
                object.__getattribute__(module, "__dict__")[name] = protect(operation)
    # All wrappers share this lexical cell. The verifier compares it with its
    # own identity rather than trusting a mutable module lookup or setter.
    guard_cell = next(cell for cell, name in zip(wrappers[0].__closure__, wrappers[0].__code__.co_freevars)
                      if name == "guard")

    namespace["_shape_guard"] = _protect_shape_dispatch()

    namespace["_binding_guard"] = _protect_shape_dispatch((
        OntologyObjectRelationshipConstructorPath, OntologyObjectFieldBinding,
        OntologyObjectActionParameterBinding, OntologyObjectActionBinding,
        OntologyObjectRelationshipBinding, OntologyObjectClassBinding,
        Cardinality, TraversalPolicy, ActionValueMode, RelationshipEndpointResidence,
        OntologyObjectActionRole, OntologyObjectRelationshipDirection,
        OntologyObjectContractError,
    ))


    namespace["_record_guard"] = _protect_shape_dispatch((
        MutationScope, CoverageGrade, FieldValue, ObjectInstance, RelationshipInstance,
        ProjectionCoverage, SchemaActionParameterDefinition, SchemaActionDefinition,
        RuntimeValue, FrozenJson, ValueKind, ActionValueMode,
    ), guard_name="_record_guard", helpers=(
        *tuple(value for name, value in tuple(globals().items())
               if type(value) is FunctionType and all(value is not wrapper for wrapper in wrappers)),
        *_record_originals,
    ))


    guard = _protect_shape_dispatch((
        OntologyObjectActionRoleDeclaration, OntologyObjectActionRoleManifest, OntologyObjectAbi,
        SchemaActionDefinition, SchemaActionParameterDefinition,
        OntologyObjectClassBinding, OntologyObjectActionBinding, OntologyObjectActionParameterBinding,
        OntologyObjectFieldBinding, OntologyObjectRelationshipBinding, OntologyObjectRelationshipConstructorPath,
        OntologyObjectContractError, OntologyObjectActionRole, OntologyObjectRelationshipDirection,
        Cardinality, TraversalPolicy, RelationshipEndpointResidence, ActionValueMode, MutationScope,
        json.JSONEncoder, json.JSONDecoder, json.JSONDecodeError,
        *_value_records, *_value_enums, RelationshipEndpointPortableInputError,
    ), extra_modules=(_value_codec, _snapshot_codec, *tuple(sys.modules[name] for name in ("json", "json.encoder", "json.decoder", "json.scanner", "hashlib"))),
       guard_name="_abi_guard", helpers=(*tuple(value for name, value in tuple(globals().items())
                                            if type(value) is FunctionType),
           *tuple(value for module in (_value_codec, _snapshot_codec) for value in vars(module).values() if type(value) is FunctionType),
           *originals),
       retained_guard_cell=guard_cell,
       guard_aliases=((_value_codec, "_codec_guard"), (_snapshot_codec, "_codec_guard")))
    namespace["_abi_guard"] = guard
    object.__getattribute__(_value_codec, "__dict__")["_codec_guard"] = guard
    object.__getattribute__(_snapshot_codec, "__dict__")["_codec_guard"] = guard




# Complete detached Object values and endpoint claims. No host admission.
EXTERNAL_RELATIONSHIP_ENDPOINT_EVIDENCE_CLAIM_CONTRACT = 'aware.ontology.external-relationship-endpoint-evidence-claim.v1'
EXTERNAL_ASSOCIATION_ENDPOINT_REFERENCE_CONTRACT = 'aware.ontology.external-association-endpoint-reference.v1'
EXTERNAL_SCHEMA_FIELD_ENDPOINT_REFERENCE_CONTRACT = 'aware.ontology.external-schema-field-endpoint-reference.v1'
EXTERNAL_RELATIONSHIP_ENDPOINT_COORDINATE_CONTRACT = 'aware.ontology.external-relationship-endpoint-coordinate.v1'
OBJECT_VALUE_CONTRACT = 'aware.ontology.object-value.v3'
OBJECT_RELATIONSHIP_SLICE_CONTRACT = 'aware.ontology.object-relationship-slice.v1'
OBJECT_SOURCE_AUTHORITY_CONTRACT = 'aware.ontology.object-source-authority.v1'
OBJECT_SNAPSHOT_AUTHORITY_CONTRACT = 'aware.ontology.object-snapshot-authority.v1'
OBJECT_SNAPSHOT_CONTRACT = 'aware.ontology.object-snapshot.v3'

class SchemaTopologyInputGrade(StrEnum):
    PORTABLE_INPUT = 'portable_input'

class RelationshipEndpointPortableInputError(ValueError):
    """Raised when portable endpoint/envelope input is malformed."""

class ExternalRelationshipEndpointEvidenceProfile(StrEnum):
    RESIDENT_LOCAL = 'resident_local'
    SOURCE_BACKED = 'source_backed'
    CANONICAL_REPLICA = 'canonical_replica'

class ExternalRelationshipEndpointVariant(StrEnum):
    SCHEMA_FIELD_RELATIONSHIP = 'schema_field_relationship'
    ASSOCIATION_ENDPOINT_ROLE = 'association_endpoint_role'

@dataclass(frozen=True, slots=True, order=True)
class ExternalRelationshipEndpointCoordinate:
    variant: ExternalRelationshipEndpointVariant
    relationship_ref: str
    owner_instance_ref: str
    target_instance_ref: str

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_enum_operand, self.variant, ExternalRelationshipEndpointVariant)
        _value_call(object.__setattr__, self, 'variant', _value_call(ExternalRelationshipEndpointVariant, self.variant))
        for field in ('relationship_ref', 'owner_instance_ref', 'target_instance_ref'):
            _value_call(object.__setattr__, self, field, _value_call(_token, _value_call(getattr, self, field), field))

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_normalized_enum, self.variant, ExternalRelationshipEndpointVariant)
        return {'contract': EXTERNAL_RELATIONSHIP_ENDPOINT_COORDINATE_CONTRACT, 'variant': self.variant.value, 'relationship_ref': self.relationship_ref, 'owner_instance_ref': self.owner_instance_ref, 'target_instance_ref': self.target_instance_ref}

@dataclass(frozen=True, slots=True, order=True)
class ExternalRelationshipEndpointEvidenceClaim:
    provider_key: str
    provider_generation: str
    profile: ExternalRelationshipEndpointEvidenceProfile
    evidence_ref: str
    input_grade: SchemaTopologyInputGrade
    claim_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        for field in ('provider_key', 'provider_generation', 'evidence_ref', 'claim_digest'):
            _value_call(object.__setattr__, self, field, _value_call(_token, _value_call(getattr, self, field), field))
        _value_call(_value_enum_operand, self.profile, ExternalRelationshipEndpointEvidenceProfile)
        _value_call(object.__setattr__, self, 'profile', _value_call(ExternalRelationshipEndpointEvidenceProfile, self.profile))
        _value_call(_value_enum_operand, self.input_grade, SchemaTopologyInputGrade)
        _value_call(object.__setattr__, self, 'input_grade', _value_call(SchemaTopologyInputGrade, self.input_grade))
        if self.input_grade is not SchemaTopologyInputGrade.PORTABLE_INPUT:
            raise _value_call(RelationshipEndpointPortableInputError, 'endpoint evidence claim may only be portable_input')
        expected = _value_call(_value_digest, EXTERNAL_RELATIONSHIP_ENDPOINT_EVIDENCE_CLAIM_CONTRACT, _value_call(self._wire_payload))
        if self.claim_digest != expected:
            raise _value_call(RelationshipEndpointPortableInputError, f'endpoint evidence claim digest mismatched; expected {expected}')

    @classmethod
    def create(cls, *, provider_key: str, provider_generation: str, profile: ExternalRelationshipEndpointEvidenceProfile, evidence_ref: str) -> ExternalRelationshipEndpointEvidenceClaim:
        _value_call(_value_native, (provider_key, provider_generation, profile, evidence_ref))
        _value_call(_value_enum_operand, profile, ExternalRelationshipEndpointEvidenceProfile)
        _value_call(_value_tokens, provider_key, provider_generation, evidence_ref)
        payload = {'provider_key': provider_key, 'provider_generation': provider_generation, 'profile': _value_call(ExternalRelationshipEndpointEvidenceProfile, profile).value, 'evidence_ref': evidence_ref, 'input_grade': SchemaTopologyInputGrade.PORTABLE_INPUT.value}
        return _value_call(cls, provider_key, provider_generation, profile, evidence_ref, SchemaTopologyInputGrade.PORTABLE_INPUT, _value_call(_value_digest, EXTERNAL_RELATIONSHIP_ENDPOINT_EVIDENCE_CLAIM_CONTRACT, payload))

    def _wire_payload(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_normalized_enum, self.input_grade, SchemaTopologyInputGrade)
        _value_call(_value_normalized_enum, self.profile, ExternalRelationshipEndpointEvidenceProfile)
        return {'provider_key': self.provider_key, 'provider_generation': self.provider_generation, 'profile': self.profile.value, 'evidence_ref': self.evidence_ref, 'input_grade': self.input_grade.value}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        return {'contract': EXTERNAL_RELATIONSHIP_ENDPOINT_EVIDENCE_CLAIM_CONTRACT, **_value_call(self._wire_payload), 'claim_digest': self.claim_digest}

@dataclass(frozen=True, slots=True, order=True)
class ExternalAssociationEndpointReference:
    role_ref: str
    association_instance_ref: str
    association_type_ref: str
    package_ref: str
    type_ref: str
    instance_ref: str
    schema_evidence_ref: str
    endpoint_residence: RelationshipEndpointResidence
    evidence_claim: ExternalRelationshipEndpointEvidenceClaim
    reference_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        for field in ('role_ref', 'association_instance_ref', 'association_type_ref', 'package_ref', 'type_ref', 'instance_ref', 'schema_evidence_ref', 'reference_digest'):
            _value_call(object.__setattr__, self, field, _value_call(_token, _value_call(getattr, self, field), field))
        if not _value_call(_value_is, self.evidence_claim, ExternalRelationshipEndpointEvidenceClaim):
            raise _value_call(TypeError, 'evidence_claim must be ExternalRelationshipEndpointEvidenceClaim')
        _value_call(_value_enum_operand, self.endpoint_residence, RelationshipEndpointResidence)
        _value_call(object.__setattr__, self, 'endpoint_residence', _value_call(RelationshipEndpointResidence, self.endpoint_residence))
        if self.endpoint_residence is not RelationshipEndpointResidence.EXTERNAL_DEPENDENCY:
            raise _value_call(RelationshipEndpointPortableInputError, 'only external_dependency endpoints use the portable sidecar')
        if not _value_call(self.role_ref.startswith, f'{self.association_type_ref}.'):
            raise _value_call(RelationshipEndpointPortableInputError, 'endpoint role differs from association type')
        expected = _value_call(_value_digest, EXTERNAL_ASSOCIATION_ENDPOINT_REFERENCE_CONTRACT, _value_call(self._wire_payload))
        if self.reference_digest != expected:
            raise _value_call(RelationshipEndpointPortableInputError, f'endpoint reference digest mismatched; expected {expected}')

    @classmethod
    def create(cls, *, role_ref: str, association_instance_ref: str, association_type_ref: str, package_ref: str, type_ref: str, instance_ref: str, schema_evidence_ref: str, endpoint_residence: RelationshipEndpointResidence, evidence_claim: ExternalRelationshipEndpointEvidenceClaim) -> ExternalAssociationEndpointReference:
        _value_call(_value_native, (role_ref, association_instance_ref, association_type_ref, package_ref, type_ref, instance_ref, schema_evidence_ref, endpoint_residence, evidence_claim))
        _value_call(_value_tokens, role_ref, association_instance_ref, association_type_ref, package_ref, type_ref, instance_ref, schema_evidence_ref)
        _value_call(_value_operand, evidence_claim, ExternalRelationshipEndpointEvidenceClaim)
        _value_call(_value_enum_operand, endpoint_residence, RelationshipEndpointResidence)
        payload = {'role_ref': role_ref, 'association_instance_ref': association_instance_ref, 'association_type_ref': association_type_ref, 'package_ref': package_ref, 'type_ref': type_ref, 'instance_ref': instance_ref, 'schema_evidence_ref': schema_evidence_ref, 'endpoint_residence': _value_call(RelationshipEndpointResidence, endpoint_residence).value, 'evidence_claim': _value_call(evidence_claim.to_wire)}
        return _value_call(cls, role_ref, association_instance_ref, association_type_ref, package_ref, type_ref, instance_ref, schema_evidence_ref, endpoint_residence, evidence_claim, _value_call(_value_digest, EXTERNAL_ASSOCIATION_ENDPOINT_REFERENCE_CONTRACT, payload))

    def _wire_payload(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_normalized_enum, self.endpoint_residence, RelationshipEndpointResidence)
        return {'role_ref': self.role_ref, 'association_instance_ref': self.association_instance_ref, 'association_type_ref': self.association_type_ref, 'package_ref': self.package_ref, 'type_ref': self.type_ref, 'instance_ref': self.instance_ref, 'schema_evidence_ref': self.schema_evidence_ref, 'endpoint_residence': self.endpoint_residence.value, 'evidence_claim': _value_call(self.evidence_claim.to_wire)}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        return {'contract': EXTERNAL_ASSOCIATION_ENDPOINT_REFERENCE_CONTRACT, **_value_call(self._wire_payload), 'reference_digest': self.reference_digest}

    @property
    def relationship_ref(self) -> str:
        _value_call(_value_native, self)
        return self.role_ref

    @property
    def owner_instance_ref(self) -> str:
        _value_call(_value_native, self)
        return self.association_instance_ref

    @property
    def owner_type_ref(self) -> str:
        _value_call(_value_native, self)
        return self.association_type_ref

    @property
    def coordinate(self) -> ExternalRelationshipEndpointCoordinate:
        _value_call(_value_native, self)
        return _value_call(ExternalRelationshipEndpointCoordinate, ExternalRelationshipEndpointVariant.ASSOCIATION_ENDPOINT_ROLE, self.relationship_ref, self.owner_instance_ref, self.instance_ref)

@dataclass(frozen=True, slots=True, order=True)
class ExternalSchemaFieldEndpointReference:
    relationship_ref: str
    source_instance_ref: str
    source_type_ref: str
    package_ref: str
    type_ref: str
    instance_ref: str
    schema_evidence_ref: str
    endpoint_residence: RelationshipEndpointResidence
    evidence_claim: ExternalRelationshipEndpointEvidenceClaim
    reference_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        for field in ('relationship_ref', 'source_instance_ref', 'source_type_ref', 'package_ref', 'type_ref', 'instance_ref', 'schema_evidence_ref', 'reference_digest'):
            _value_call(object.__setattr__, self, field, _value_call(_token, _value_call(getattr, self, field), field))
        if not _value_call(_value_is, self.evidence_claim, ExternalRelationshipEndpointEvidenceClaim):
            raise _value_call(TypeError, 'evidence_claim must be ExternalRelationshipEndpointEvidenceClaim')
        _value_call(_value_enum_operand, self.endpoint_residence, RelationshipEndpointResidence)
        _value_call(object.__setattr__, self, 'endpoint_residence', _value_call(RelationshipEndpointResidence, self.endpoint_residence))
        if self.endpoint_residence is not RelationshipEndpointResidence.EXTERNAL_DEPENDENCY:
            raise _value_call(RelationshipEndpointPortableInputError, 'only external_dependency endpoints use the portable sidecar')
        if not _value_call(self.relationship_ref.startswith, f'{self.source_type_ref}.'):
            raise _value_call(RelationshipEndpointPortableInputError, 'endpoint relationship differs from source type')
        expected = _value_call(_value_digest, EXTERNAL_SCHEMA_FIELD_ENDPOINT_REFERENCE_CONTRACT, _value_call(self._wire_payload))
        if self.reference_digest != expected:
            raise _value_call(RelationshipEndpointPortableInputError, f'endpoint reference digest mismatched; expected {expected}')

    @classmethod
    def create(cls, *, relationship_ref: str, source_instance_ref: str, source_type_ref: str, package_ref: str, type_ref: str, instance_ref: str, schema_evidence_ref: str, endpoint_residence: RelationshipEndpointResidence, evidence_claim: ExternalRelationshipEndpointEvidenceClaim) -> ExternalSchemaFieldEndpointReference:
        _value_call(_value_native, (relationship_ref, source_instance_ref, source_type_ref, package_ref, type_ref, instance_ref, schema_evidence_ref, endpoint_residence, evidence_claim))
        _value_call(_value_tokens, relationship_ref, source_instance_ref, source_type_ref, package_ref, type_ref, instance_ref, schema_evidence_ref)
        _value_call(_value_operand, evidence_claim, ExternalRelationshipEndpointEvidenceClaim)
        _value_call(_value_enum_operand, endpoint_residence, RelationshipEndpointResidence)
        payload = {'relationship_ref': relationship_ref, 'source_instance_ref': source_instance_ref, 'source_type_ref': source_type_ref, 'package_ref': package_ref, 'type_ref': type_ref, 'instance_ref': instance_ref, 'schema_evidence_ref': schema_evidence_ref, 'endpoint_residence': _value_call(RelationshipEndpointResidence, endpoint_residence).value, 'evidence_claim': _value_call(evidence_claim.to_wire)}
        return _value_call(cls, relationship_ref, source_instance_ref, source_type_ref, package_ref, type_ref, instance_ref, schema_evidence_ref, endpoint_residence, evidence_claim, _value_call(_value_digest, EXTERNAL_SCHEMA_FIELD_ENDPOINT_REFERENCE_CONTRACT, payload))

    @property
    def owner_instance_ref(self) -> str:
        _value_call(_value_native, self)
        return self.source_instance_ref

    @property
    def owner_type_ref(self) -> str:
        _value_call(_value_native, self)
        return self.source_type_ref

    @property
    def coordinate(self) -> ExternalRelationshipEndpointCoordinate:
        _value_call(_value_native, self)
        return _value_call(ExternalRelationshipEndpointCoordinate, ExternalRelationshipEndpointVariant.SCHEMA_FIELD_RELATIONSHIP, self.relationship_ref, self.owner_instance_ref, self.instance_ref)

    def _wire_payload(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_normalized_enum, self.endpoint_residence, RelationshipEndpointResidence)
        return {'relationship_ref': self.relationship_ref, 'source_instance_ref': self.source_instance_ref, 'source_type_ref': self.source_type_ref, 'package_ref': self.package_ref, 'type_ref': self.type_ref, 'instance_ref': self.instance_ref, 'schema_evidence_ref': self.schema_evidence_ref, 'endpoint_residence': self.endpoint_residence.value, 'evidence_claim': _value_call(self.evidence_claim.to_wire)}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        return {'contract': EXTERNAL_SCHEMA_FIELD_ENDPOINT_REFERENCE_CONTRACT, **_value_call(self._wire_payload), 'reference_digest': self.reference_digest}

def external_relationship_endpoint_sort_key(value: ExternalRelationshipEndpointReference) -> tuple[str, str, str, str, str]:
    return (value.coordinate.variant.value, value.coordinate.relationship_ref, value.coordinate.owner_instance_ref, value.coordinate.target_instance_ref, value.reference_digest)

ExternalRelationshipEndpointReference = ExternalSchemaFieldEndpointReference | ExternalAssociationEndpointReference

@dataclass(frozen=True, slots=True, order=True)
class OntologyObjectRelationshipEdgeValue:
    relationship_instance_ref: str
    source_instance_ref: str
    target_instance_ref: str
    peer_instance_ref: str

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        for field in ('relationship_instance_ref', 'source_instance_ref', 'target_instance_ref', 'peer_instance_ref'):
            _value_call(object.__setattr__, self, field, _value_call(_token, _value_call(getattr, self, field), field))

    @classmethod
    def from_instance(cls, instance: RelationshipInstance, *, direction: OntologyObjectRelationshipDirection) -> OntologyObjectRelationshipEdgeValue:
        _value_call(_value_native, (instance, direction))
        _value_call(_value_enum_operand, direction, OntologyObjectRelationshipDirection)
        if not _value_call(_value_is, instance, RelationshipInstance):
            raise _value_call(TypeError, 'instance must be RelationshipInstance')
        direction = _value_call(OntologyObjectRelationshipDirection, direction)
        peer = instance.target_instance_ref if direction is OntologyObjectRelationshipDirection.OUTGOING else instance.source_instance_ref
        return _value_call(cls, instance.instance_ref, instance.source_instance_ref, instance.target_instance_ref, peer)

    def to_wire(self) -> dict[str, str]:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        return {'relationship_instance_ref': self.relationship_instance_ref, 'source_instance_ref': self.source_instance_ref, 'target_instance_ref': self.target_instance_ref, 'peer_instance_ref': self.peer_instance_ref}

@dataclass(frozen=True, slots=True)
class OntologyObjectRelationshipSlice:
    relationship_ref: str
    direction: OntologyObjectRelationshipDirection
    owner_instance_ref: str
    owner_type_ref: str
    peer_type_ref: str
    cardinality: Cardinality
    traversal: TraversalPolicy
    coverage: ProjectionCoverage
    edges: tuple[OntologyObjectRelationshipEdgeValue, ...]
    relationship_value_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        for field in ('relationship_ref', 'owner_instance_ref', 'owner_type_ref', 'peer_type_ref', 'relationship_value_digest'):
            _value_call(object.__setattr__, self, field, _value_call(_token, _value_call(getattr, self, field), field))
        _value_call(_value_enum_operand, self.direction, OntologyObjectRelationshipDirection)
        _value_call(object.__setattr__, self, 'direction', _value_call(OntologyObjectRelationshipDirection, self.direction))
        _value_call(_value_enum_operand, self.cardinality, Cardinality)
        _value_call(object.__setattr__, self, 'cardinality', _value_call(Cardinality, self.cardinality))
        _value_call(_value_enum_operand, self.traversal, TraversalPolicy)
        _value_call(object.__setattr__, self, 'traversal', _value_call(TraversalPolicy, self.traversal))
        if not _value_call(_value_is, self.coverage, ProjectionCoverage):
            raise _value_call(TypeError, 'coverage must be ProjectionCoverage')
        _value_call(_value_members, self.edges, OntologyObjectRelationshipEdgeValue)
        edges = _value_call(tuple, _value_call(sorted, self.edges))
        if _value_call(any, (not _value_call(_value_is, item, OntologyObjectRelationshipEdgeValue) for item in edges)):
            raise _value_call(TypeError, 'edges contain an invalid relationship value')
        if _value_call(len, {item.relationship_instance_ref for item in edges}) != _value_call(len, edges):
            raise _value_call(OntologyObjectContractError, 'relationship slice contains duplicate edge identities')
        outgoing = self.direction is OntologyObjectRelationshipDirection.OUTGOING
        permitted = (TraversalPolicy.SOURCE_TO_TARGET, TraversalPolicy.BIDIRECTIONAL) if outgoing else (TraversalPolicy.TARGET_TO_SOURCE, TraversalPolicy.BIDIRECTIONAL)
        if self.traversal not in permitted:
            raise _value_call(OntologyObjectContractError, 'relationship direction escapes authored traversal policy')
        for edge in edges:
            owner = edge.source_instance_ref if outgoing else edge.target_instance_ref
            peer = edge.target_instance_ref if outgoing else edge.source_instance_ref
            if owner != self.owner_instance_ref or peer != edge.peer_instance_ref:
                raise _value_call(OntologyObjectContractError, 'relationship edge escapes slice direction or owner')
        if self.cardinality in {Cardinality.ONE, Cardinality.OPTIONAL_ONE} and _value_call(len, edges) > 1:
            raise _value_call(OntologyObjectContractError, 'relationship slice exceeds authored cardinality')
        if self.coverage.grade is CoverageGrade.COMPLETE and self.cardinality is Cardinality.ONE and (_value_call(len, edges) != 1):
            raise _value_call(OntologyObjectContractError, 'complete relationship slice violates required cardinality')
        _value_call(object.__setattr__, self, 'edges', edges)
        if self.relationship_value_digest != _value_call(_value_digest, OBJECT_RELATIONSHIP_SLICE_CONTRACT, _value_call(self._wire_payload)):
            raise _value_call(OntologyObjectContractError, 'relationship slice digest mismatched')

    def _wire_payload(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_normalized_enum, self.traversal, TraversalPolicy)
        _value_call(_value_normalized_enum, self.cardinality, Cardinality)
        _value_call(_value_normalized_enum, self.direction, OntologyObjectRelationshipDirection)
        return {'relationship_ref': self.relationship_ref, 'direction': self.direction.value, 'owner_instance_ref': self.owner_instance_ref, 'owner_type_ref': self.owner_type_ref, 'peer_type_ref': self.peer_type_ref, 'cardinality': self.cardinality.value, 'traversal': self.traversal.value, 'coverage': _value_call(self.coverage.to_wire), 'edges': [_value_call(item.to_wire) for item in self.edges]}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        return {'contract': OBJECT_RELATIONSHIP_SLICE_CONTRACT, **_value_call(self._wire_payload), 'relationship_value_digest': self.relationship_value_digest}

@dataclass(frozen=True, slots=True)
class OntologyObjectValue:
    instance_ref: str
    type_ref: str
    fields: tuple[FieldValue, ...]
    relationships: tuple[OntologyObjectRelationshipSlice, ...]
    external_endpoint_references: tuple[ExternalRelationshipEndpointReference, ...]
    value_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        _value_call(object.__setattr__, self, 'instance_ref', _value_call(_token, self.instance_ref, 'instance_ref'))
        _value_call(object.__setattr__, self, 'type_ref', _value_call(_token, self.type_ref, 'type_ref'))
        _value_call(_value_members, self.fields, FieldValue)
        _value_call(_value_members, self.relationships, OntologyObjectRelationshipSlice)
        _value_call(_value_members, self.external_endpoint_references, ExternalSchemaFieldEndpointReference, ExternalAssociationEndpointReference)
        fields = _value_call(tuple, _value_call(sorted, self.fields, key=lambda item: item.field_ref))
        if _value_call(len, {item.field_ref for item in fields}) != _value_call(len, fields):
            raise _value_call(OntologyObjectContractError, 'duplicate Object-value field')
        if _value_call(any, (not _value_call(_value_is, item, FieldValue) for item in fields)):
            raise _value_call(TypeError, 'fields contain an invalid value')
        relationships = _value_call(tuple, _value_call(sorted, self.relationships, key=lambda item: (item.relationship_ref, item.direction.value)))
        if _value_call(any, (not _value_call(_value_is, item, OntologyObjectRelationshipSlice) for item in relationships)):
            raise _value_call(TypeError, 'relationships contain an invalid slice')
        coordinates = _value_call(tuple, ((item.relationship_ref, item.direction) for item in relationships))
        if _value_call(len, coordinates) != _value_call(len, _value_call(set, coordinates)):
            raise _value_call(OntologyObjectContractError, 'object value contains duplicate relationship slices')
        if _value_call(any, (item.owner_instance_ref != self.instance_ref or item.owner_type_ref != self.type_ref for item in relationships)):
            raise _value_call(OntologyObjectContractError, 'relationship slice escapes object identity or type')
        _value_call(object.__setattr__, self, 'fields', fields)
        _value_call(object.__setattr__, self, 'relationships', relationships)
        endpoints = _value_call(tuple, _value_call(sorted, self.external_endpoint_references, key=external_relationship_endpoint_sort_key))
        if _value_call(any, (not _value_call(_value_is, item, ExternalSchemaFieldEndpointReference, ExternalAssociationEndpointReference) for item in endpoints)):
            raise _value_call(TypeError, 'external_endpoint_references contain an invalid value')
        if _value_call(any, (item.owner_instance_ref != self.instance_ref for item in endpoints)):
            raise _value_call(OntologyObjectContractError, 'external endpoint reference escapes object identity')
        endpoint_coordinates = _value_call(tuple, (item.coordinate for item in endpoints))
        if _value_call(len, endpoint_coordinates) != _value_call(len, _value_call(set, endpoint_coordinates)):
            raise _value_call(OntologyObjectContractError, 'object value contains an exact duplicate external endpoint coordinate')
        _value_call(object.__setattr__, self, 'external_endpoint_references', endpoints)
        _value_call(object.__setattr__, self, 'value_digest', _value_call(_token, self.value_digest, 'value_digest'))
        if self.value_digest != _value_call(_value_digest, OBJECT_VALUE_CONTRACT, _value_call(self._wire_payload)):
            raise _value_call(OntologyObjectContractError, 'object value digest mismatched')

    @classmethod
    def create(cls, instance: ObjectInstance, relationships: Iterable[OntologyObjectRelationshipSlice]=(), external_endpoint_references: Iterable[ExternalRelationshipEndpointReference]=()) -> OntologyObjectValue:
        _value_call(_value_native, (instance, relationships, external_endpoint_references))
        if cls is not OntologyObjectValue or _value_call(type, instance) is not ObjectInstance:
            raise _value_call(TypeError, 'Object-value construction requires exact instance')
        if _value_call(type, instance.fields) is not tuple:
            raise _value_call(TypeError, 'instance fields must be exact tuple')
        for field in instance.fields:
            if _value_call(type, field) is not FieldValue:
                raise _value_call(TypeError, 'instance field must be exact')
            _value_call(FieldValue.to_wire, field)
        for collection, kinds in ((relationships, (OntologyObjectRelationshipSlice,)), (external_endpoint_references, (ExternalSchemaFieldEndpointReference, ExternalAssociationEndpointReference))):
            if not _value_call(_value_is, collection, tuple, list):
                raise _value_call(TypeError, 'Object-value members require exact collections')
            for member in collection:
                _value_call(_value_operand, member, *kinds)
        normalized = _value_call(tuple, _value_call(sorted, relationships, key=lambda item: (item.relationship_ref, item.direction.value)))
        endpoints = _value_call(tuple, _value_call(sorted, external_endpoint_references, key=external_relationship_endpoint_sort_key))
        payload = {'instance_ref': instance.instance_ref, 'type_ref': instance.type_ref, 'fields': [_value_call(item.to_wire) for item in instance.fields], 'relationships': [_value_call(item.to_wire) for item in normalized], 'external_endpoint_references': [_value_call(item.to_wire) for item in endpoints]}
        return _value_call(cls, instance.instance_ref, instance.type_ref, instance.fields, normalized, endpoints, _value_call(_value_digest, OBJECT_VALUE_CONTRACT, payload))

    @property
    def instance(self) -> ObjectInstance:
        _value_call(_value_native, self)
        return _value_call(ObjectInstance, self.instance_ref, self.type_ref, self.fields)

    def _wire_payload(self) -> dict[str, object]:
        _value_call(_value_native, self)
        return {'instance_ref': self.instance_ref, 'type_ref': self.type_ref, 'fields': [_value_call(item.to_wire) for item in self.fields], 'relationships': [_value_call(item.to_wire) for item in self.relationships], 'external_endpoint_references': [_value_call(item.to_wire) for item in self.external_endpoint_references]}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_codec._check_record, self)
        wire = {'contract': OBJECT_VALUE_CONTRACT, **_value_call(self._wire_payload), 'value_digest': self.value_digest}
        _value_call(_value_codec._reconstruct, wire)
        return wire

    def canonical_bytes(self) -> bytes:
        wire = _value_call(self.to_wire)
        return _value_call(_value_codec._canonical, wire)

    @classmethod
    def from_wire(cls, wire: dict[str, object]) -> OntologyObjectValue:
        if cls is not OntologyObjectValue:
            raise _value_call(TypeError, 'Object-value subclass is not supported')
        return _value_call(_value_codec._reconstruct, wire)

    @classmethod
    def from_canonical_bytes(cls, body: bytes) -> OntologyObjectValue:
        if cls is not OntologyObjectValue:
            raise _value_call(TypeError, 'Object-value subclass is not supported')
        return _value_call(_value_codec._reconstruct, _value_call(_value_codec._parse, body))

@dataclass(frozen=True, slots=True)
class OntologyObjectSourceAuthorityEvidence:
    source_coordinate_ref: str
    source_observation_ref: str
    source_mapping_digest: str
    source_authority_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_source_wire, self)

    @classmethod
    def create(cls, *, source_coordinate_ref: str, source_observation_ref: str, source_mapping_digest: str) -> OntologyObjectSourceAuthorityEvidence:
        _value_call(_value_native, (source_coordinate_ref, source_observation_ref, source_mapping_digest))
        _value_call(_value_tokens, source_coordinate_ref, source_observation_ref, source_mapping_digest)
        payload = {'source_coordinate_ref': source_coordinate_ref, 'source_observation_ref': source_observation_ref, 'source_mapping_digest': source_mapping_digest}
        return _value_call(cls, source_coordinate_ref, source_observation_ref, source_mapping_digest, _value_call(_value_digest, OBJECT_SOURCE_AUTHORITY_CONTRACT, payload))

    def _wire_payload(self) -> dict[str, str]:
        _value_call(_value_native, self)
        return {'source_coordinate_ref': self.source_coordinate_ref, 'source_observation_ref': self.source_observation_ref, 'source_mapping_digest': self.source_mapping_digest}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        return _value_call(_value_source_wire, self)
@dataclass(frozen=True, slots=True)
class OntologyObjectProviderAuthorityClaim:
    grade: str
    provider_key: str
    authority_ref: str
    provider_generation: str
    canonical_branch_ref: str | None = None
    canonical_commit_ref: str | None = None

    def __post_init__(self) -> None:
        _value_call(_value_native, self)
        _value_call(_value_provider_fields, self.grade, self.provider_key, self.authority_ref, self.provider_generation, self.canonical_branch_ref, self.canonical_commit_ref)

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        _value_call(_value_provider_fields, self.grade, self.provider_key, self.authority_ref, self.provider_generation, self.canonical_branch_ref, self.canonical_commit_ref)
        return {name: _value_call(object.__getattribute__, self, name) for name in self.__dataclass_fields__}

    def canonical_bytes(self) -> bytes:
        return _value_call(_snapshot_codec._canonical, _value_call(self.to_wire))

    @classmethod
    def from_wire(cls, wire: dict[str, object]) -> OntologyObjectProviderAuthorityClaim:
        if cls is not OntologyObjectProviderAuthorityClaim:
            raise _value_call(TypeError, 'provider claim must retain its owning class')
        return _value_call(_snapshot_codec._provider, wire)

    @classmethod
    def from_canonical_bytes(cls, body: bytes) -> OntologyObjectProviderAuthorityClaim:
        return _value_call(cls.from_wire, _value_call(_snapshot_codec._parse, body))

def _value_provider_fields(grade, provider_key, authority_ref, provider_generation, canonical_branch_ref, canonical_commit_ref):
    if _value_call(type, grade) is not str or grade not in ('preview', 'local_operational', 'canonical_replica'):
        raise _value_call(ValueError, 'unsupported provider claim grade')
    for name, value in (('provider_key', provider_key), ('authority_ref', authority_ref), ('provider_generation', provider_generation)):
        _value_call(_token, value, name)
    for name, value in (('canonical_branch_ref', canonical_branch_ref), ('canonical_commit_ref', canonical_commit_ref)):
        if value is not None:
            _value_call(_token, value, name)
    if grade == 'canonical_replica':
        if canonical_branch_ref is None or canonical_commit_ref is None:
            raise _value_call(ValueError, 'canonical replicas require exact branch and commit refs')
    elif canonical_branch_ref is not None or canonical_commit_ref is not None:
        raise _value_call(ValueError, 'only canonical replicas may carry canonical coordinates')

def _value_digest(contract: str, payload: object) -> str:
    if type(contract) is not str or not contract or contract.strip() != contract:
        raise ValueError("contract must be a non-empty token")
    body = _value_call(_value_codec._canonical, payload)
    # Full payload evaluation precedes the checked hash dispatch.
    preimage = contract.encode('utf-8') + b'\n' + body
    hashed = _value_call(hashlib.sha256, preimage)
    return 'sha256:' + _value_call(hashed.hexdigest)


def _value_is(value, *kinds):
    return any(type(value) is kind for kind in kinds)


def _value_native(value):
    """One native-only traversal, fenced by the retained entrance wrapper."""
    native_type, read, class_read = type, object.__getattribute__, type.__getattribute__
    native_any, native_next, missing_slot = any, next, AttributeError
    records, enums, fields, failure = _value_records, _value_enums, _value_fields, TypeError
    def visit(item):
        kind = native_type(item)
        if item is None or kind is str or kind is int or kind is bool or kind is bytes:
            return
        if native_any(kind is enum for enum in enums):
            return
        if kind is tuple or kind is list:
            for child in item:
                visit(child)
            return
        if not native_any(kind is record for record in records):
            raise failure('foreign nested Object data')
        schema = native_next((slots for record, slots in fields if kind is record), ())
        for name in class_read(kind, '__dataclass_fields__'):
            try:
                child = read(item, name)
            except missing_slot:
                raise failure('Object data operand is missing a required slot') from None
            for slot, kinds, members in schema:
                if name != slot:
                    continue
                if not native_any(native_type(child) is expected for expected in kinds):
                    raise failure('Object data slot has an invalid exact type')
                if members:
                    for member in child:
                        if not native_any(native_type(member) is expected for expected in members):
                            raise failure('Object data member has an invalid exact type')
            visit(child)
    visit(value)


def _value_tokens(*values):
    for value in values:
        _value_call(_token, value, 'Object data token')


def _value_members(values, *kinds):
    if not _value_call(_value_is, values, tuple, list):
        raise _value_call(TypeError, 'Object data members require exact collections')
    for value in values:
        _value_call(_value_operand, value, *kinds)


def _value_operand(value, *kinds):
    if not _value_call(_value_is, value, *kinds):
        raise _value_call(TypeError, 'Object data operand requires its exact owning class')
    _value_call(_value_native, value)


def _value_normalized_enum(value, kind):
    if _value_call(type, value) is not kind:
        raise _value_call(TypeError, 'Object data enum slot must retain its owning enum')


def _value_enum_operand(value, kind):
    if not _value_call(_value_is, value, str, kind):
        raise _value_call(TypeError, 'Object data enum operand must be exact text or its owning enum')


def _value_source_wire(source):
    _value_call(_value_operand, source, OntologyObjectSourceAuthorityEvidence)
    for name in ('source_coordinate_ref', 'source_observation_ref', 'source_mapping_digest', 'source_authority_digest'):
        _value_call(_token, _value_call(object.__getattribute__, source, name), name)
    payload = _value_call(source._wire_payload)
    if source.source_authority_digest != _value_call(_value_digest, OBJECT_SOURCE_AUTHORITY_CONTRACT, payload):
        raise _value_call(OntologyObjectContractError, 'source authority digest mismatched')
    return {'contract': OBJECT_SOURCE_AUTHORITY_CONTRACT, **payload, 'source_authority_digest': source.source_authority_digest}


def _value_authority_wire(authority):
    _value_call(_value_operand, authority, OntologyObjectSnapshotAuthorityData)
    _value_call(_value_operand, authority.provider_authority, OntologyObjectProviderAuthorityClaim)
    if authority.source_authority is not None:
        _value_call(_value_operand, authority.source_authority, OntologyObjectSourceAuthorityEvidence)
    for name in ('value_digest', 'class_binding_digest', 'topology_digest', 'branch_ref', 'revision_ref', 'projection_ref', 'view_digest', 'authority_digest'):
        _value_call(_token, _value_call(object.__getattribute__, authority, name), name)
    payload = _value_call(authority._wire_payload)
    if authority.authority_digest != _value_call(_value_digest, OBJECT_SNAPSHOT_AUTHORITY_CONTRACT, payload):
        raise _value_call(OntologyObjectContractError, 'snapshot authority digest mismatched')
    return {'contract': OBJECT_SNAPSHOT_AUTHORITY_CONTRACT, **payload, 'authority_digest': authority.authority_digest}


def _value_snapshot_operands(snapshot):
    _value_call(_value_operand, snapshot, OntologyObjectSnapshotData)
    _value_call(_value_operand, snapshot.value, OntologyObjectValue)
    _value_call(_value_operand, snapshot.authority, OntologyObjectSnapshotAuthorityData)


def _value_snapshot_wire(snapshot):
    _value_call(_value_snapshot_operands, snapshot)
    _value_call(_token, snapshot.snapshot_digest, 'snapshot_digest')
    payload = _value_call(snapshot._wire_payload)
    if snapshot.authority.value_digest != snapshot.value.value_digest:
        raise _value_call(OntologyObjectContractError, 'snapshot authority is bound to another semantic value')
    if snapshot.snapshot_digest != _value_call(_value_digest, OBJECT_SNAPSHOT_CONTRACT, payload):
        raise _value_call(OntologyObjectContractError, 'object snapshot digest mismatched')
    return {'contract': OBJECT_SNAPSHOT_CONTRACT, **payload, 'snapshot_digest': snapshot.snapshot_digest}


def _value_call(operation: Any, /, *args: Any, **kwargs: Any) -> Any:
    return operation(*args, **kwargs)


@dataclass(frozen=True, slots=True)
class OntologyObjectSnapshotAuthorityData:
    value_digest: str
    provider_authority: OntologyObjectProviderAuthorityClaim
    class_binding_digest: str
    topology_digest: str
    branch_ref: str
    revision_ref: str
    projection_ref: str
    view_digest: str
    source_authority: OntologyObjectSourceAuthorityEvidence | None
    authority_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_authority_wire, self)

    @classmethod
    def create(cls, *, value_digest: str, provider_authority: OntologyObjectProviderAuthorityClaim, class_binding_digest: str, topology_digest: str, branch_ref: str, revision_ref: str, projection_ref: str, view_digest: str, source_authority: OntologyObjectSourceAuthorityEvidence | None=None) -> OntologyObjectSnapshotAuthorityData:
        _value_call(_value_native, (value_digest, provider_authority, class_binding_digest, topology_digest, branch_ref, revision_ref, projection_ref, view_digest, source_authority))
        _value_call(_value_operand, provider_authority, OntologyObjectProviderAuthorityClaim)
        _value_call(_value_tokens, value_digest, class_binding_digest, topology_digest, branch_ref, revision_ref, projection_ref, view_digest)
        if source_authority is not None:
            _value_call(_value_operand, source_authority, OntologyObjectSourceAuthorityEvidence)
        payload = {'value_digest': value_digest, 'provider_authority': _value_call(provider_authority.to_wire), 'class_binding_digest': class_binding_digest, 'topology_digest': topology_digest, 'branch_ref': branch_ref, 'revision_ref': revision_ref, 'projection_ref': projection_ref, 'view_digest': view_digest, 'source_authority': None if source_authority is None else _value_call(source_authority.to_wire)}
        return _value_call(cls, value_digest, provider_authority, class_binding_digest, topology_digest, branch_ref, revision_ref, projection_ref, view_digest, source_authority, _value_call(_value_digest, OBJECT_SNAPSHOT_AUTHORITY_CONTRACT, payload))

    def _wire_payload(self) -> dict[str, object]:
        _value_call(_value_native, self)
        return {'value_digest': self.value_digest, 'provider_authority': _value_call(self.provider_authority.to_wire), 'class_binding_digest': self.class_binding_digest, 'topology_digest': self.topology_digest, 'branch_ref': self.branch_ref, 'revision_ref': self.revision_ref, 'projection_ref': self.projection_ref, 'view_digest': self.view_digest, 'source_authority': None if self.source_authority is None else _value_call(self.source_authority.to_wire)}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_native, self)
        return _value_call(_value_authority_wire, self)

    def canonical_bytes(self) -> bytes:
        return _value_call(_snapshot_codec._canonical, _value_call(self.to_wire))

    @classmethod
    def from_wire(cls, wire: dict[str, object]) -> OntologyObjectSnapshotAuthorityData:
        if cls is not OntologyObjectSnapshotAuthorityData:
            raise _value_call(TypeError, 'snapshot data must retain its owning class')
        return _value_call(_snapshot_codec._authority, wire)

    @classmethod
    def from_canonical_bytes(cls, body: bytes) -> OntologyObjectSnapshotAuthorityData:
        return _value_call(cls.from_wire, _value_call(_snapshot_codec._parse, body))

@dataclass(frozen=True, slots=True)
class OntologyObjectSnapshotData:
    value: OntologyObjectValue
    authority: OntologyObjectSnapshotAuthorityData
    snapshot_digest: str

    def __post_init__(self) -> None:
        _value_call(_value_snapshot_wire, self)

    @classmethod
    def create(cls, *, value: OntologyObjectValue, authority: OntologyObjectSnapshotAuthorityData) -> OntologyObjectSnapshotData:
        _value_call(_value_native, (value, authority))
        _value_call(_value_operand, value, OntologyObjectValue)
        _value_call(_value_operand, authority, OntologyObjectSnapshotAuthorityData)
        payload = {'value': _value_call(value.to_wire), 'authority': _value_call(authority.to_wire)}
        return _value_call(cls, value, authority, _value_call(_value_digest, OBJECT_SNAPSHOT_CONTRACT, payload))

    @property
    def instance(self) -> ObjectInstance:
        _value_call(_value_snapshot_operands, self)
        return self.value.instance

    @property
    def class_binding_digest(self) -> str:
        _value_call(_value_snapshot_operands, self)
        return self.authority.class_binding_digest

    @property
    def topology_digest(self) -> str:
        _value_call(_value_snapshot_operands, self)
        return self.authority.topology_digest

    @property
    def branch_ref(self) -> str:
        _value_call(_value_snapshot_operands, self)
        return self.authority.branch_ref

    @property
    def revision_ref(self) -> str:
        _value_call(_value_snapshot_operands, self)
        return self.authority.revision_ref

    @property
    def projection_ref(self) -> str:
        _value_call(_value_snapshot_operands, self)
        return self.authority.projection_ref

    @property
    def view_digest(self) -> str:
        _value_call(_value_snapshot_operands, self)
        return self.authority.view_digest

    def _wire_payload(self) -> dict[str, object]:
        _value_call(_value_snapshot_operands, self)
        return {'value': _value_call(self.value.to_wire), 'authority': _value_call(self.authority.to_wire)}

    def to_wire(self) -> dict[str, object]:
        _value_call(_value_snapshot_operands, self)
        return _value_call(_value_snapshot_wire, self)

    def canonical_bytes(self) -> bytes:
        return _value_call(_snapshot_codec._canonical, _value_call(self.to_wire))

    @classmethod
    def from_wire(cls, wire: dict[str, object]) -> OntologyObjectSnapshotData:
        if cls is not OntologyObjectSnapshotData:
            raise _value_call(TypeError, 'snapshot data must retain its owning class')
        return _value_call(_snapshot_codec._reconstruct, wire)

    @classmethod
    def from_canonical_bytes(cls, body: bytes) -> OntologyObjectSnapshotData:
        return _value_call(cls.from_wire, _value_call(_snapshot_codec._parse, body))

_value_classes = (OntologyObjectRelationshipEdgeValue, OntologyObjectRelationshipSlice, OntologyObjectValue, OntologyObjectSourceAuthorityEvidence, ExternalRelationshipEndpointCoordinate, ExternalRelationshipEndpointEvidenceClaim, ExternalAssociationEndpointReference, ExternalSchemaFieldEndpointReference, OntologyObjectProviderAuthorityClaim, OntologyObjectSnapshotAuthorityData, OntologyObjectSnapshotData,)
_value_records = (FrozenJson, RuntimeValue, FieldValue, ObjectInstance, RelationshipInstance, ProjectionCoverage, *_value_classes)
_value_enums = (ValueKind, Cardinality, CoverageGrade, TraversalPolicy, RelationshipEndpointResidence, OntologyObjectRelationshipDirection, SchemaTopologyInputGrade, ExternalRelationshipEndpointEvidenceProfile, ExternalRelationshipEndpointVariant)


# Enum input slots accept native strings during construction; their wire methods
# separately require normalized enums before reading .value. All other operand
# slots and member collections have their exact recursive data roles.
_value_fields = (
    (ExternalRelationshipEndpointCoordinate, (('variant', (str, ExternalRelationshipEndpointVariant), ()), *tuple((name, (str,), ()) for name in ('relationship_ref', 'owner_instance_ref', 'target_instance_ref')))),
    (ExternalRelationshipEndpointEvidenceClaim, (('profile', (str, ExternalRelationshipEndpointEvidenceProfile), ()), ('input_grade', (str, SchemaTopologyInputGrade), ()), *tuple((name, (str,), ()) for name in ('provider_key', 'provider_generation', 'evidence_ref', 'claim_digest')))),
    (ExternalAssociationEndpointReference, (('endpoint_residence', (str, RelationshipEndpointResidence), ()), ('evidence_claim', (ExternalRelationshipEndpointEvidenceClaim,), ()), *tuple((name, (str,), ()) for name in ('role_ref', 'association_instance_ref', 'association_type_ref', 'package_ref', 'type_ref', 'instance_ref', 'schema_evidence_ref', 'reference_digest')))),
    (ExternalSchemaFieldEndpointReference, (('endpoint_residence', (str, RelationshipEndpointResidence), ()), ('evidence_claim', (ExternalRelationshipEndpointEvidenceClaim,), ()), *tuple((name, (str,), ()) for name in ('relationship_ref', 'source_instance_ref', 'source_type_ref', 'package_ref', 'type_ref', 'instance_ref', 'schema_evidence_ref', 'reference_digest')))),
    (OntologyObjectRelationshipEdgeValue, tuple((name, (str,), ()) for name in ('relationship_instance_ref', 'source_instance_ref', 'target_instance_ref', 'peer_instance_ref'))),
    (OntologyObjectRelationshipSlice, (('direction', (str, OntologyObjectRelationshipDirection), ()), ('cardinality', (str, Cardinality), ()), ('traversal', (str, TraversalPolicy), ()), ('coverage', (ProjectionCoverage,), ()), ('edges', (tuple, list), (OntologyObjectRelationshipEdgeValue,)), *tuple((name, (str,), ()) for name in ('relationship_ref', 'owner_instance_ref', 'owner_type_ref', 'peer_type_ref', 'relationship_value_digest')))),
    (OntologyObjectValue, (('fields', (tuple, list), (FieldValue,)), ('relationships', (tuple, list), (OntologyObjectRelationshipSlice,)), ('external_endpoint_references', (tuple, list), (ExternalSchemaFieldEndpointReference, ExternalAssociationEndpointReference)), *tuple((name, (str,), ()) for name in ('instance_ref', 'type_ref', 'value_digest')))),
    (OntologyObjectSourceAuthorityEvidence, tuple((name, (str,), ()) for name in ('source_coordinate_ref', 'source_observation_ref', 'source_mapping_digest', 'source_authority_digest'))),
    (OntologyObjectProviderAuthorityClaim, (*tuple((name, (str,), ()) for name in ('grade', 'provider_key', 'authority_ref', 'provider_generation')), *tuple((name, (str, type(None)), ()) for name in ('canonical_branch_ref', 'canonical_commit_ref')))),
    (OntologyObjectSnapshotAuthorityData, (('provider_authority', (OntologyObjectProviderAuthorityClaim,), ()), ('source_authority', (OntologyObjectSourceAuthorityEvidence, type(None)), ()), *tuple((name, (str,), ()) for name in ('value_digest', 'class_binding_digest', 'topology_digest', 'branch_ref', 'revision_ref', 'projection_ref', 'view_digest', 'authority_digest')))),
    (OntologyObjectSnapshotData, (('value', (OntologyObjectValue,), ()), ('authority', (OntologyObjectSnapshotAuthorityData,), ()), ('snapshot_digest', (str,), ()))),
    (FrozenJson, (('canonical', (str,), ()),)),
    (RuntimeValue, (('value_kind', (str, ValueKind), ()), ('value', (FrozenJson,), ()))),
    (RelationshipInstance, tuple((name, (str,), ()) for name in ('instance_ref', 'relationship_ref', 'source_instance_ref', 'target_instance_ref'))),
    (ProjectionCoverage, (('grade', (str, CoverageGrade), ()), ('missing_refs', (tuple, list), (str,)))),
    (FieldValue, (('field_ref', (str,), ()), ('value', (RuntimeValue,), ()))),
    (ObjectInstance, (('instance_ref', (str,), ()), ('type_ref', (str,), ()), ('fields', (tuple, list), (FieldValue,)))),
)

# Legacy portable preparation prerequisites: data, never host issuance.
OBJECT_APPLICATION_AUTHORITY_CONTRACT = "aware.ontology.object-application-authority.v1"
OBJECT_EXECUTABLE_AUTHORITY_CONTRACT = "aware.ontology.object-executable-authority.v1"

_attempt_specs: dict[str, tuple[str, str, tuple[str, ...]]] = {'OntologyObjectExecutableSelectionTextRule': ('aware.ontology.object-executable-selection-text-rule.v1',
                                               'rule_digest',
                                               ('kind', 'values', 'rule_digest')),
 'OntologyObjectExecutableSelectionFacts': ('aware.ontology.object-executable-selection-facts.v1',
                                            'facts_digest',
                                            ('provider_key',
                                             'provider_generation',
                                             'authority_ref',
                                             'executable_root_digest',
                                             'vm_implementation_digest',
                                             'capability_catalog_digest',
                                             'actor_rule_body',
                                             'projection_rule_body',
                                             'operation_rule_body',
                                             'idempotency_rule_body',
                                             'facts_digest')),
 'OntologyObjectExecutableSelectionProfile': ('aware.ontology.object-executable-selection-profile.v1',
                                              'profile_digest',
                                              ('selection_facts_body',
                                               'selection_facts_digest',
                                               'branch_ref',
                                               'object_abi_digest',
                                               'application_authority_digest',
                                               'topology_digest',
                                               'schema_digest',
                                               'schema_slice_digest',
                                               'profile_digest')),
 'OntologyObjectExecutableSelectionAdmission': ('aware.ontology.object-executable-selection-admission.v1',
                                                'admission_digest',
                                                ('selection_profile_body',
                                                 'selection_profile_digest',
                                                 'activation_request_digest',
                                                 'execution_admission_request_digest',
                                                 'retained_revision_ref',
                                                 'current_base_operational_digest',
                                                 'executable_authority_body',
                                                 'executable_authority_digest',
                                                 'selection_disposition',
                                                 'admission_digest')),
 'OntologyObjectPrecontactRecoveryProfile': ('aware.ontology.object-precontact-recovery-profile.v1',
                                             'profile_digest',
                                             ('provider_key',
                                              'provider_generation',
                                              'provider_distribution_digest',
                                              'executable_authority_digest',
                                              'attempt_ref_scheme',
                                              'recovery_ref_scheme',
                                              'attempt_head_namespace_digest',
                                              'trace_namespace_digest',
                                              'epoch_check_support',
                                              'action_epoch_check_kind',
                                              'seal_epoch_check_kind',
                                              'owner_write_epoch_check_kind',
                                              'native_fencing_implementation_contract_digest',
                                              'restart_recovery_kind',
                                              'supports_precontact_resolution',
                                              'supports_preseal_resolution',
                                              'supports_seal_intent_recovery',
                                              'profile_contract_digest',
                                              'profile_digest')),
 'OntologyObjectOperationAttempt': ('aware.ontology.object-operation-attempt.v1',
                                    'attempt_digest',
                                    ('provider_profile_digest',
                                     'provider_key',
                                     'provider_generation',
                                     'branch_ref',
                                     'actor_ref',
                                     'projection_ref',
                                     'operation_ref',
                                     'idempotency_key',
                                     'object_abi_digest',
                                     'application_authority_body',
                                     'application_authority_digest',
                                     'executable_authority_body',
                                     'executable_authority_digest',
                                     'topology_digest',
                                     'schema_digest',
                                     'schema_slice_digest',
                                     'base_operational_digest',
                                     'expected_revision_ref',
                                     'activation_request_digest',
                                     'execution_admission_request_digest',
                                     'attempt_ref',
                                     'recovery_ref',
                                     'attempt_digest')),
 'OntologyObjectOperationAttemptAdmission': ('aware.ontology.object-operation-attempt-admission.v1',
                                             'admission_digest',
                                             ('attempt_body',
                                              'attempt_digest',
                                              'provider_profile_digest',
                                              'object_abi_digest',
                                              'application_authority_digest',
                                              'executable_authority_digest',
                                              'execution_admission_request_digest',
                                              'preparation_disposition',
                                              'provider_begin_count',
                                              'provider_read_count',
                                              'provider_action_count',
                                              'provider_seal_count',
                                              'provider_write_count',
                                              'provider_recovery_count',
                                              'admission_digest'))}
_attempt_domains = {'OntologyObjectExecutableSelectionTextRule': 'aware.ontology.object-executable-selection-text-rule.v1',
 'OntologyObjectExecutableSelectionFacts': 'aware.ontology.object-executable-selection-facts.v1',
 'OntologyObjectExecutableSelectionProfile': 'aware.ontology.object-executable-selection-profile.v1',
 'OntologyObjectExecutableSelectionAdmission': 'aware.ontology.object-executable-selection-admission.v1',
 'OntologyObjectPrecontactRecoveryProfile': 'aware.ontology.object-precontact-recovery-profile.v1',
 'OntologyObjectOperationAttempt': 'aware.ontology.object-operation-attempt.v1',
 'OntologyObjectOperationAttemptAdmission': 'aware.ontology.object-operation-attempt-admission.v1'}
_attempt_nullable = {'OntologyObjectPrecontactRecoveryProfile': frozenset({'native_fencing_implementation_contract_digest'}),
 'OntologyObjectOperationAttempt': frozenset({'expected_revision_ref'})}
_attempt_enums = {('OntologyObjectExecutableSelectionTextRule', 'kind'): frozenset({'any_exact_text',
                                                                   'one_of'}),
 ('OntologyObjectExecutableSelectionAdmission', 'selection_disposition'): frozenset({'selected'}),
 ('OntologyObjectPrecontactRecoveryProfile', 'attempt_ref_scheme'): frozenset({'ontology-object-attempt-sha256-v1'}),
 ('OntologyObjectPrecontactRecoveryProfile', 'recovery_ref_scheme'): frozenset({'ontology-object-recovery-sha256-v1'}),
 ('OntologyObjectPrecontactRecoveryProfile', 'epoch_check_support'): frozenset({'durable_head_reread_only',
                                                                                'provider_native_o1_with_durable_boundaries'}),
 ('OntologyObjectPrecontactRecoveryProfile', 'action_epoch_check_kind'): frozenset({'durable_head_reread',
                                                                                    'provider_native_o1'}),
 ('OntologyObjectPrecontactRecoveryProfile', 'seal_epoch_check_kind'): frozenset({'durable_head_reread'}),
 ('OntologyObjectPrecontactRecoveryProfile', 'owner_write_epoch_check_kind'): frozenset({'durable_head_reread'}),
 ('OntologyObjectPrecontactRecoveryProfile', 'restart_recovery_kind'): frozenset({'durable_provider_journal',
                                                                                  'owner_idempotent_source'}),
 ('OntologyObjectOperationAttemptAdmission', 'preparation_disposition'): frozenset({'prepared_without_provider_contact'})}
_attempt_text_tuple_fields = frozenset({"values"})
_attempt_bool_fields = frozenset({"supports_precontact_resolution", "supports_preseal_resolution", "supports_seal_intent_recovery"})
_attempt_tuple_fields = frozenset()

class OntologyObjectOperationAttemptCodecError(ValueError):
    """A detached legacy Object-operation body is not exact."""


def _attempt_error(message):
    # Refusal never dispatches a replaceable Python exception constructor.
    error = BaseException.__new__(OntologyObjectOperationAttemptCodecError)
    BaseException.__init__(error, message)
    return error


def _attempt_text(value, field):
    if type(value) is not str or not value or value.strip() != value:
        raise _attempt_error(f"{field} must be nonempty unpadded exact str")
    return value


def _attempt_normalize(value, *, path="$", mapping_required=False) -> Any:
    kind = type(value)
    if value is None or kind is str or kind is bool or kind is int:
        if kind is str and (not value or value.strip() != value):
            raise _attempt_error(f"{path} text must be nonempty and unpadded")
        return value
    if kind is float:
        raise _attempt_error(f"{path} must not contain floating-point values")
    if kind is list or kind is tuple:
        if mapping_required:
            raise _attempt_error(f"{path} must be an object")
        return [_attempt_normalize(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if kind is dict:
        if any(type(key) is not str or not key for key in value):
            raise _attempt_error(f"{path} keys must be nonempty exact strings")
        return {key: _attempt_normalize(value[key], path=f"{path}.{key}") for key in sorted(value)}
    raise _attempt_error(f"{path} contains unsupported bytes" if kind is bytes else f"{path} contains unsupported data")


def _attempt_encode_normalized(normalized) -> bytes:
    """Encode one caller-private strict snapshot; no selectable JSON options."""
    return json.dumps(
        normalized, ensure_ascii=False, allow_nan=False,
        separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")


def attempt_canonical_bytes(value: Mapping[str, object]) -> bytes:
    normalized = _attempt_normalize(value, path="$", mapping_required=True)
    # This private tree was just copied and strictly checked. Rebuilding it
    # through the more permissive general JSON normalizer adds no validation.
    # The original serializer still dispatches through the fresh checked port.
    return _attempt_call(_attempt_encode_normalized, normalized)


def _attempt_object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if type(key) is not str or not key:
            raise _attempt_error("JSON object keys must be nonempty exact strings")
        if key in result:
            raise _attempt_error(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def decode_attempt_canonical_bytes(body: bytes) -> dict[str, object]:
    if type(body) is not bytes:
        raise TypeError("canonical body must be exact bytes")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _attempt_error("canonical body must be UTF-8") from error
    try:
        decoded = _attempt_call(json.loads, text, object_pairs_hook=_attempt_object_pairs)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise _attempt_error("canonical body is not strict JSON") from error
    if type(decoded) is not dict:
        raise _attempt_error("canonical body must contain one object")
    normalized = _attempt_normalize(decoded, path="$", mapping_required=True)
    # Re-encode this one owned snapshot; do not strictly normalize it twice
    # and then normalize it a third time in canonical_json. This is not a
    # retained admission or a shortcut for an independently supplied tree.
    encoded = _attempt_call(_attempt_encode_normalized, normalized)
    if encoded != body:
        raise _attempt_error("canonical body is not byte-exact")
    return normalized


def attempt_digest_bytes(domain: str, body: bytes) -> str:
    _attempt_text(domain, "digest domain")
    if type(body) is not bytes:
        raise TypeError("digest body must be exact bytes")
    return "sha256:" + _attempt_call(hashlib.sha256, domain.encode("utf-8") + b"\0" + body).hexdigest()


def attempt_digest_wire(domain: str, wire: Mapping[str, object]) -> str:
    return attempt_digest_bytes(domain, attempt_canonical_bytes(wire))


def attempt_require_sha256(value: object, field: str) -> str:
    value = _attempt_text(value, field)
    if len(value) != 71 or not value.startswith("sha256:") or any(char not in "0123456789abcdef" for char in value[7:]):
        raise _attempt_error(f"{field} must be a lowercase SHA-256 coordinate")
    return value


def attempt_require_exact_keys(wire: Mapping[str, object], expected: tuple[str, ...], *, path: str) -> dict[str, object]:
    if type(wire) is not dict:
        raise _attempt_error(f"{path} must be an exact dict")
    if any(type(key) is not str for key in wire):
        raise _attempt_error(f"{path} keys must be exact strings")
    if set(wire) != set(expected) or len(wire) != len(expected):
        raise _attempt_error(f"{path} fields are not exact")
    return dict(wire)


def _attempt_impossible(message):
    raise _attempt_error(message)


def _attempt_call(operation, *args, **kwargs):
    if not any(operation is target for target in (json.loads, canonical_json, digest_payload, hashlib.sha256, _attempt_encode_normalized)):
        raise _attempt_error("portable dispatch target is not retained")
    if "object_pairs_hook" in kwargs and kwargs["object_pairs_hook"] is not _attempt_object_pairs:
        raise _attempt_error("portable JSON hook is not retained")
    return operation(*args, **kwargs)


def _attempt_native(value, *, constructing=False):
    """One native traversal; recursion cannot redispatch through module bindings."""
    native_type, read, native_any = type, object.__getattribute__, any
    kinds, failure = _attempt_classes, OntologyObjectOperationAttemptCodecError
    make_error, initialize = BaseException.__new__, BaseException.__init__
    def refuse():
        error = make_error(failure)
        initialize(error, "portable operand must be exact native or owning data")
        raise error
    def visit(item, initial=False):
        kind = native_type(item)
        if item is None or kind is str or kind is int or kind is bool or kind is bytes or kind is float:
            return
        if kind is list or kind is tuple:
            for child in item:
                visit(child)
            return
        if kind is dict:
            for key, child in item.items():
                if native_type(key) is not str:
                    refuse()
                visit(child)
            return
        if not native_any(kind is record for record in kinds):
            refuse()
        if not (initial and constructing):
            for name in ("schema", "codec_version", *kind._field_names):
                visit(read(item, name))
    visit(value, True)


def _attempt_wire_value(value):
    kind = type(value)
    if any(kind is record for record in _attempt_classes):
        return value.to_wire()
    if kind is tuple or kind is list:
        return [_attempt_wire_value(item) for item in value]
    if kind is dict:
        return {key: _attempt_wire_value(item) for key, item in value.items()}
    return value

def _attempt_validate_contract(class_name: str, wire: dict[str, Any]) -> None:
    nullable = _attempt_nullable.get(class_name, frozenset())
    for name, value in wire.items():
        if value is None:
            if name not in nullable:
                raise _attempt_error(
                    f"{name} must not be null"
                )
            continue
        if name in _attempt_bool_fields:
            if type(value) is not bool or value is not True:
                raise _attempt_error(
                    f"{name} must be exact true"
                )
        elif name == "codec_version":
            continue
        elif name in _attempt_tuple_fields:
            if type(value) is not list or any(not _attempt_is_digest(item) for item in value):
                raise _attempt_error(
                    f"{name} must contain exact SHA-256 values"
                )
        elif name in _attempt_text_tuple_fields:
            if type(value) is not list:
                raise _attempt_error(
                    f"{name} must be an exact text array"
                )
            for item in value:
                if type(item) is not str or not item or item.strip() != item:
                    raise _attempt_error(
                        f"{name} must contain nonempty unpadded exact strings"
                    )
        elif name.endswith("_body") or name == "attempt_body":
            if type(value) is not dict:
                raise _attempt_error(
                    f"{name} must be an exact body"
                )
        elif (
            name.endswith(
                ("_count", "_revision", "_ordinal", "_epoch", "_size", "_sequence")
            )
            and value is not None
        ):
            if type(value) is not int or value < 0:
                raise _attempt_error(
                    f"{name} must be a nonnegative exact int"
                )
        else:
            if type(value) is not str or not value or value.strip() != value:
                raise _attempt_error(
                    f"{name} must be exact nonempty text"
                )
            if "digest" in name:
                attempt_require_sha256(value, name)
        if (class_name, name) in _attempt_enums and value not in _attempt_enums[class_name, name]:
            raise _attempt_error(
                f"{name} has an unsupported tag"
            )
    if class_name == "OntologyObjectOperationAttemptAdmission" and any(
        wire[name] != 0
        for name in (
            "provider_begin_count",
            "provider_read_count",
            "provider_action_count",
            "provider_seal_count",
            "provider_write_count",
            "provider_recovery_count",
        )
    ):
        raise _attempt_error(
            "preparation counters must all be exact zero"
        )
    if class_name == "OntologyObjectExecutableSelectionTextRule":
        values = wire["values"]
        if wire["kind"] == "any_exact_text" and values:
            raise _attempt_error(
                "any_exact_text rule must have no values"
            )
        if wire["kind"] == "one_of" and (
            not values
            or len(values) != len(set(values))
            or values != sorted(values, key=lambda item: item.encode("utf-8"))
        ):
            raise _attempt_error(
                "one_of values must be unique and ordered by UTF-8 bytes"
            )
    if class_name == "OntologyObjectExecutableSelectionProfile":
        facts = wire["selection_facts_body"]
        if wire["selection_facts_digest"] != facts["facts_digest"]:
            raise _attempt_error(
                "selection profile facts digest mismatched"
            )
    if class_name == "OntologyObjectExecutableSelectionAdmission":
        _attempt_validate_executable_selection_admission(wire)
    if class_name == "OntologyObjectPrecontactRecoveryProfile":
        native = wire.get("native_fencing_implementation_contract_digest")
        support = wire.get("epoch_check_support")
        action = wire.get("action_epoch_check_kind")
        if support == "durable_head_reread_only" and (
            native is not None or action != "durable_head_reread"
        ):
            raise _attempt_error(
                "durable reread profile fencing mismatched"
            )
        if support == "provider_native_o1_with_durable_boundaries" and (
            native is None or action != "provider_native_o1"
        ):
            raise _attempt_error(
                "native profile fencing mismatched"
            )
    if class_name == "OntologyObjectOperationAttempt":
        _attempt_validate_attempt(wire)
    if class_name == "OntologyObjectOperationAttemptAdmission":
        attempt = attempt_require_exact_keys(
            wire["attempt_body"],
            ("schema", "codec_version", *_attempt_specs["OntologyObjectOperationAttempt"][2]),
            path="attempt_body",
        )
        if any(
            wire[name] != attempt[name]
            for name in (
                "attempt_digest",
                "provider_profile_digest",
                "object_abi_digest",
                "application_authority_digest",
                "executable_authority_digest",
                "execution_admission_request_digest",
            )
        ):
            raise _attempt_error(
                "attempt admission mismatched its complete attempt"
            )


def _attempt_validate_authority(wire, *, application=False):
    text_fields = ("application_ref",) if application else ("admission_provider_key", "admission_provider_generation", "authority_ref")
    digest_fields = ("implementation_digest", "authority_digest") if application else ("executable_root_digest", "vm_implementation_digest", "capability_catalog_digest", "base_operational_digest", "authority_digest")
    for name in text_fields:
        _attempt_text(wire[name], name)
    for name in digest_fields:
        attempt_require_sha256(wire[name], name)


def _attempt_validate_executable_selection_admission(wire: dict[str, Any]) -> None:
    profile = wire["selection_profile_body"]
    if wire["selection_profile_digest"] != profile["profile_digest"]:
        raise _attempt_error(
            "selection admission profile digest mismatched"
        )
    executable = attempt_require_exact_keys(
        wire["executable_authority_body"],
        (
            "admission_provider_key",
            "admission_provider_generation",
            "authority_ref",
            "executable_root_digest",
            "vm_implementation_digest",
            "capability_catalog_digest",
            "base_operational_digest",
            "authority_digest",
        ),
        path="executable_authority_body",
    )
    _attempt_validate_authority(executable)
    executable_digest = _attempt_call(digest_payload,
        OBJECT_EXECUTABLE_AUTHORITY_CONTRACT,
        {key: value for key, value in executable.items() if key != "authority_digest"},
    )
    facts = profile["selection_facts_body"]
    if (
        wire["executable_authority_digest"] != executable_digest
        or executable["authority_digest"] != executable_digest
        or executable["admission_provider_key"] != facts["provider_key"]
        or executable["admission_provider_generation"]
        != facts["provider_generation"]
        or executable["authority_ref"] != facts["authority_ref"]
        or executable["executable_root_digest"] != facts["executable_root_digest"]
        or executable["vm_implementation_digest"] != facts["vm_implementation_digest"]
        or executable["capability_catalog_digest"]
        != facts["capability_catalog_digest"]
        or executable["base_operational_digest"]
        != wire["current_base_operational_digest"]
    ):
        raise _attempt_error(
            "selection admission executable authority mismatched"
        )

def _attempt_validate_attempt(wire: dict[str, Any]) -> None:

    application = attempt_require_exact_keys(
        wire["application_authority_body"],
        ("application_ref", "implementation_digest", "authority_digest"),
        path="application_authority_body",
    )
    executable = attempt_require_exact_keys(
        wire["executable_authority_body"],
        (
            "admission_provider_key",
            "admission_provider_generation",
            "authority_ref",
            "executable_root_digest",
            "vm_implementation_digest",
            "capability_catalog_digest",
            "base_operational_digest",
            "authority_digest",
        ),
        path="executable_authority_body",
    )
    _attempt_validate_authority(application, application=True)
    _attempt_validate_authority(executable)
    application_digest = _attempt_call(digest_payload,
        OBJECT_APPLICATION_AUTHORITY_CONTRACT,
        {key: value for key, value in application.items() if key != "authority_digest"},
    )
    executable_digest = _attempt_call(digest_payload,
        OBJECT_EXECUTABLE_AUTHORITY_CONTRACT,
        {key: value for key, value in executable.items() if key != "authority_digest"},
    )
    if (
        application["authority_digest"] != application_digest
        or wire["application_authority_digest"] != application_digest
        or executable["authority_digest"] != executable_digest
        or wire["executable_authority_digest"] != executable_digest
        or executable["admission_provider_key"] != wire["provider_key"]
        or executable["admission_provider_generation"] != wire["provider_generation"]
        or executable["base_operational_digest"] != wire["base_operational_digest"]
    ):
        raise _attempt_error(
            "attempt authority closure mismatched"
        )
    activation = {
        "branch_ref": wire["branch_ref"],
        "actor_ref": wire["actor_ref"],
        "projection_ref": wire["projection_ref"],
        "operation_ref": wire["operation_ref"],
        "idempotency_key": wire["idempotency_key"],
        "object_abi_digest": wire["object_abi_digest"],
        "application_authority_body": application,
        "expected_revision_ref": wire["expected_revision_ref"],
    }
    activation_digest = attempt_digest_wire(
        "aware.ontology.object-activation-request.v1", activation
    )
    execution_digest = attempt_digest_wire(
        "aware.ontology.object-execution-admission-request.v1",
        {
            "activation_request_digest": activation_digest,
            "provider_key": wire["provider_key"],
            "provider_generation": wire["provider_generation"],
            "topology_digest": wire["topology_digest"],
            "schema_digest": wire["schema_digest"],
            "schema_slice_digest": wire["schema_slice_digest"],
            "base_operational_digest": wire["base_operational_digest"],
        },
    )
    attempt_ref = "ontology-object-attempt:" + attempt_digest_wire(
        "aware.ontology.object-operation-attempt-coordinate.v1.digest",
        {
            "activation_request_digest": activation_digest,
            "execution_admission_request_digest": execution_digest,
            "provider_profile_digest": wire["provider_profile_digest"],
            "schema": "aware.ontology.object-operation-attempt-coordinate.v1",
        },
    )
    recovery_ref = "ontology-object-recovery:" + attempt_digest_wire(
        "aware.ontology.object-operation-recovery-coordinate.v1.digest",
        {
            "activation_request_digest": activation_digest,
            "attempt_ref": attempt_ref,
            "execution_admission_request_digest": execution_digest,
            "provider_profile_digest": wire["provider_profile_digest"],
            "schema": "aware.ontology.object-operation-recovery-coordinate.v1",
        },
    )
    if (
        wire["activation_request_digest"] != activation_digest
        or wire["execution_admission_request_digest"] != execution_digest
        or wire["attempt_ref"] != attempt_ref
        or wire["recovery_ref"] != recovery_ref
    ):
        raise _attempt_error(
            "attempt request or reference derivation mismatched"
        )

def _attempt_is_digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )

def _attempt_validate_wire(kind, wire):
    fields: tuple[str, ...] = kind._field_names
    exact = attempt_require_exact_keys(wire, ("schema", "codec_version", *fields), path=kind.__name__)
    if type(exact["schema"]) is not str or exact["schema"] != kind._schema or type(exact["codec_version"]) is not int or exact["codec_version"] != 1:
        raise _attempt_error("schema/version mismatched")
    # Recomputed enclosing hashes cannot conceal invalid nested source data.
    nested = {
        "OntologyObjectExecutableSelectionFacts": tuple((name, OntologyObjectExecutableSelectionTextRule) for name in ("actor_rule_body", "projection_rule_body", "operation_rule_body", "idempotency_rule_body")),
        "OntologyObjectExecutableSelectionProfile": (("selection_facts_body", OntologyObjectExecutableSelectionFacts),),
        "OntologyObjectExecutableSelectionAdmission": (("selection_profile_body", OntologyObjectExecutableSelectionProfile),),
        "OntologyObjectOperationAttemptAdmission": (("attempt_body", OntologyObjectOperationAttempt),),
    }
    for name, target in nested.get(kind.__name__, ()):
        _attempt_validate_wire(target, exact[name])
    _attempt_validate_contract(kind.__name__, exact)
    field = kind._digest_field
    expected = attempt_digest_wire(_attempt_domains[kind.__name__], {key: value for key, value in exact.items() if key != field})
    if exact[field] != expected:
        raise _attempt_error(f"{field} mismatched canonical body")


def _attempt_convert_nested(class_name, wire):
    result = dict(wire)
    if "values" in result:
        if type(result["values"]) is not list:
            raise _attempt_error("values must be a list")
        result["values"] = tuple(result["values"])
    nested = {
        "OntologyObjectExecutableSelectionFacts": {name: OntologyObjectExecutableSelectionTextRule for name in ("actor_rule_body", "projection_rule_body", "operation_rule_body", "idempotency_rule_body")},
        "OntologyObjectExecutableSelectionProfile": {"selection_facts_body": OntologyObjectExecutableSelectionFacts},
        "OntologyObjectExecutableSelectionAdmission": {"selection_profile_body": OntologyObjectExecutableSelectionProfile},
        "OntologyObjectOperationAttemptAdmission": {"attempt_body": OntologyObjectOperationAttempt},
    }
    for name, target in nested.get(class_name, {}).items():
        value = result[name]
        if type(value) is not target:
            if type(value) is not dict:
                raise _attempt_error(f"{name} must be an exact nested body")
            result[name] = target.from_wire(value)
    return result


def _attempt_build_portable_value(value_type, **values):
    if not any(value_type is record for record in _attempt_classes):
        raise _attempt_error("portable value type must be exact")
    schema, field, names = _attempt_specs[value_type.__name__]
    if set(values) - {"schema", "codec_version", field} != set(name for name in names if name != field):
        raise _attempt_error("portable construction fields are not exact")
    wire = {"schema": schema, "codec_version": 1, **{key: _attempt_wire_value(value) for key, value in values.items()}}
    wire[field] = attempt_digest_wire(_attempt_domains[value_type.__name__], {key: value for key, value in wire.items() if key != field})
    return value_type.from_wire(wire)



_attempt_constructed = WeakKeyDictionary()
_attempt_constructed_lock = RLock()

class _AttemptPortableValue:
    schema: str
    codec_version: int
    _schema: ClassVar[str]
    _digest_field: ClassVar[str | None]
    _field_names: ClassVar[tuple[str, ...]]

    def __post_init__(self) -> None:
        if type(self.schema) is not str or self.schema != self._schema:
            raise _attempt_error("schema literal mismatched")
        if type(self.codec_version) is not int or self.codec_version != 1:
            raise _attempt_error(
                "codec_version must be exact int 1"
            )
        wire = self._raw_wire()
        converted = _attempt_convert_nested(type(self).__name__, wire)
        for name in type(self)._field_names:
            if name in converted and any(type(converted[name]) is kind for kind in _attempt_classes):
                object.__setattr__(self, name, converted[name])
        wire = self._raw_wire()
        _attempt_validate_wire(type(self), wire)
        encoded = attempt_canonical_bytes(wire)
        with _attempt_constructed_lock:
            _attempt_constructed[self] = encoded

    def _raw_wire(self) -> dict[str, object]:
        return {name: _attempt_wire_value(object.__getattribute__(self, name))
                for name in ("schema", "codec_version", *type(self)._field_names)}

    def to_wire(self) -> dict[str, object]:
        wire = self._raw_wire()
        _attempt_validate_wire(type(self), wire)
        encoded = attempt_canonical_bytes(wire)
        with _attempt_constructed_lock:
            retained = _attempt_constructed.get(self)
        if retained is None or retained != encoded:
            raise _attempt_error(
                "portable value differs from its reconstructed issuance state"
            )
        return wire

    def canonical_bytes(self) -> bytes:
        return attempt_canonical_bytes(self.to_wire())

    @classmethod
    def from_wire(cls, wire: dict[str, object]):
        if not any(cls is record for record in _attempt_classes):
            raise _attempt_error(
                "portable value type must be exact"
            )
        expected = ("schema", "codec_version", *cls._field_names)
        exact = attempt_require_exact_keys(wire, expected, path=cls.__name__)
        converted = _attempt_convert_nested(cls.__name__, exact)
        return cls(**converted)

    @classmethod
    def from_canonical_bytes(cls, body: bytes):
        value = cls.from_wire(decode_attempt_canonical_bytes(body))
        if value.canonical_bytes() != body:
            raise _attempt_error(
                "decoded body did not reconstruct byte-exactly"
            )
        return value

    @classmethod
    def create(cls, **values: object):
        return _attempt_build_portable_value(cls, **values)

    def __copy__(self):
        raise TypeError(f"{type(self).__name__} is not copyable")

    def __deepcopy__(self, memo: dict[int, object]):
        del memo
        raise TypeError(f"{type(self).__name__} is not copyable")

if TYPE_CHECKING:
    class _AttemptPortableTyping(_AttemptPortableValue):
        def __init__(self, *values: Any, **named_values: Any) -> None: ...
        def __getattr__(self, name: str) -> Any: ...

    class OntologyObjectExecutableSelectionTextRule(_AttemptPortableTyping): ...

    class OntologyObjectExecutableSelectionFacts(_AttemptPortableTyping): ...

    class OntologyObjectExecutableSelectionProfile(_AttemptPortableTyping): ...

    class OntologyObjectExecutableSelectionAdmission(_AttemptPortableTyping): ...

    class OntologyObjectPrecontactRecoveryProfile(_AttemptPortableTyping): ...

    class OntologyObjectOperationAttempt(_AttemptPortableTyping): ...

    class OntologyObjectOperationAttemptAdmission(_AttemptPortableTyping): ...

else:
    OntologyObjectExecutableSelectionTextRule = make_dataclass('OntologyObjectExecutableSelectionTextRule', [("schema", str), ("codec_version", int), *((name, object) for name in ('kind', 'values', 'rule_digest'))], bases=(_AttemptPortableValue,), namespace={"__module__": __name__, "_schema": 'aware.ontology.object-executable-selection-text-rule.v1', "_digest_field": 'rule_digest', "_field_names": ('kind', 'values', 'rule_digest')}, frozen=True, slots=True, weakref_slot=True, eq=False)
    OntologyObjectExecutableSelectionFacts = make_dataclass('OntologyObjectExecutableSelectionFacts', [("schema", str), ("codec_version", int), *((name, object) for name in ('provider_key', 'provider_generation', 'authority_ref', 'executable_root_digest', 'vm_implementation_digest', 'capability_catalog_digest', 'actor_rule_body', 'projection_rule_body', 'operation_rule_body', 'idempotency_rule_body', 'facts_digest'))], bases=(_AttemptPortableValue,), namespace={"__module__": __name__, "_schema": 'aware.ontology.object-executable-selection-facts.v1', "_digest_field": 'facts_digest', "_field_names": ('provider_key', 'provider_generation', 'authority_ref', 'executable_root_digest', 'vm_implementation_digest', 'capability_catalog_digest', 'actor_rule_body', 'projection_rule_body', 'operation_rule_body', 'idempotency_rule_body', 'facts_digest')}, frozen=True, slots=True, weakref_slot=True, eq=False)
    OntologyObjectExecutableSelectionProfile = make_dataclass('OntologyObjectExecutableSelectionProfile', [("schema", str), ("codec_version", int), *((name, object) for name in ('selection_facts_body', 'selection_facts_digest', 'branch_ref', 'object_abi_digest', 'application_authority_digest', 'topology_digest', 'schema_digest', 'schema_slice_digest', 'profile_digest'))], bases=(_AttemptPortableValue,), namespace={"__module__": __name__, "_schema": 'aware.ontology.object-executable-selection-profile.v1', "_digest_field": 'profile_digest', "_field_names": ('selection_facts_body', 'selection_facts_digest', 'branch_ref', 'object_abi_digest', 'application_authority_digest', 'topology_digest', 'schema_digest', 'schema_slice_digest', 'profile_digest')}, frozen=True, slots=True, weakref_slot=True, eq=False)
    OntologyObjectExecutableSelectionAdmission = make_dataclass('OntologyObjectExecutableSelectionAdmission', [("schema", str), ("codec_version", int), *((name, object) for name in ('selection_profile_body', 'selection_profile_digest', 'activation_request_digest', 'execution_admission_request_digest', 'retained_revision_ref', 'current_base_operational_digest', 'executable_authority_body', 'executable_authority_digest', 'selection_disposition', 'admission_digest'))], bases=(_AttemptPortableValue,), namespace={"__module__": __name__, "_schema": 'aware.ontology.object-executable-selection-admission.v1', "_digest_field": 'admission_digest', "_field_names": ('selection_profile_body', 'selection_profile_digest', 'activation_request_digest', 'execution_admission_request_digest', 'retained_revision_ref', 'current_base_operational_digest', 'executable_authority_body', 'executable_authority_digest', 'selection_disposition', 'admission_digest')}, frozen=True, slots=True, weakref_slot=True, eq=False)
    OntologyObjectPrecontactRecoveryProfile = make_dataclass('OntologyObjectPrecontactRecoveryProfile', [("schema", str), ("codec_version", int), *((name, object) for name in ('provider_key', 'provider_generation', 'provider_distribution_digest', 'executable_authority_digest', 'attempt_ref_scheme', 'recovery_ref_scheme', 'attempt_head_namespace_digest', 'trace_namespace_digest', 'epoch_check_support', 'action_epoch_check_kind', 'seal_epoch_check_kind', 'owner_write_epoch_check_kind', 'native_fencing_implementation_contract_digest', 'restart_recovery_kind', 'supports_precontact_resolution', 'supports_preseal_resolution', 'supports_seal_intent_recovery', 'profile_contract_digest', 'profile_digest'))], bases=(_AttemptPortableValue,), namespace={"__module__": __name__, "_schema": 'aware.ontology.object-precontact-recovery-profile.v1', "_digest_field": 'profile_digest', "_field_names": ('provider_key', 'provider_generation', 'provider_distribution_digest', 'executable_authority_digest', 'attempt_ref_scheme', 'recovery_ref_scheme', 'attempt_head_namespace_digest', 'trace_namespace_digest', 'epoch_check_support', 'action_epoch_check_kind', 'seal_epoch_check_kind', 'owner_write_epoch_check_kind', 'native_fencing_implementation_contract_digest', 'restart_recovery_kind', 'supports_precontact_resolution', 'supports_preseal_resolution', 'supports_seal_intent_recovery', 'profile_contract_digest', 'profile_digest')}, frozen=True, slots=True, weakref_slot=True, eq=False)
    OntologyObjectOperationAttempt = make_dataclass('OntologyObjectOperationAttempt', [("schema", str), ("codec_version", int), *((name, object) for name in ('provider_profile_digest', 'provider_key', 'provider_generation', 'branch_ref', 'actor_ref', 'projection_ref', 'operation_ref', 'idempotency_key', 'object_abi_digest', 'application_authority_body', 'application_authority_digest', 'executable_authority_body', 'executable_authority_digest', 'topology_digest', 'schema_digest', 'schema_slice_digest', 'base_operational_digest', 'expected_revision_ref', 'activation_request_digest', 'execution_admission_request_digest', 'attempt_ref', 'recovery_ref', 'attempt_digest'))], bases=(_AttemptPortableValue,), namespace={"__module__": __name__, "_schema": 'aware.ontology.object-operation-attempt.v1', "_digest_field": 'attempt_digest', "_field_names": ('provider_profile_digest', 'provider_key', 'provider_generation', 'branch_ref', 'actor_ref', 'projection_ref', 'operation_ref', 'idempotency_key', 'object_abi_digest', 'application_authority_body', 'application_authority_digest', 'executable_authority_body', 'executable_authority_digest', 'topology_digest', 'schema_digest', 'schema_slice_digest', 'base_operational_digest', 'expected_revision_ref', 'activation_request_digest', 'execution_admission_request_digest', 'attempt_ref', 'recovery_ref', 'attempt_digest')}, frozen=True, slots=True, weakref_slot=True, eq=False)
    OntologyObjectOperationAttemptAdmission = make_dataclass('OntologyObjectOperationAttemptAdmission', [("schema", str), ("codec_version", int), *((name, object) for name in ('attempt_body', 'attempt_digest', 'provider_profile_digest', 'object_abi_digest', 'application_authority_digest', 'executable_authority_digest', 'execution_admission_request_digest', 'preparation_disposition', 'provider_begin_count', 'provider_read_count', 'provider_action_count', 'provider_seal_count', 'provider_write_count', 'provider_recovery_count', 'admission_digest'))], bases=(_AttemptPortableValue,), namespace={"__module__": __name__, "_schema": 'aware.ontology.object-operation-attempt-admission.v1', "_digest_field": 'admission_digest', "_field_names": ('attempt_body', 'attempt_digest', 'provider_profile_digest', 'object_abi_digest', 'application_authority_digest', 'executable_authority_digest', 'execution_admission_request_digest', 'preparation_disposition', 'provider_begin_count', 'provider_read_count', 'provider_action_count', 'provider_seal_count', 'provider_write_count', 'provider_recovery_count', 'admission_digest')}, frozen=True, slots=True, weakref_slot=True, eq=False)

_attempt_classes = (OntologyObjectExecutableSelectionTextRule, OntologyObjectExecutableSelectionFacts, OntologyObjectExecutableSelectionProfile, OntologyObjectExecutableSelectionAdmission, OntologyObjectPrecontactRecoveryProfile, OntologyObjectOperationAttempt, OntologyObjectOperationAttemptAdmission,)


_attempt_guard: Any = None
_attempt_guard_cell: Any = None


def _install_attempt_dispatch():
    """Seal selected behavior before either public or host consumers can dispatch."""
    guard: Any = None
    originals, wrappers = [], []
    namespace = globals()
    native_type, native_get, native_any = type, object.__getattribute__, any
    native_visit, native_failure = _attempt_native, OntologyObjectOperationAttemptCodecError
    make_failure, initialize_failure = BaseException.__new__, BaseException.__init__
    def refuse(message):
        error = make_failure(native_failure)
        initialize_failure(error, message)
        return error
    native_unwind = BaseException
    known_classes = _attempt_classes
    native_functions = tuple(value for value in vars(builtins).values() if type(value) is BuiltinMethodType) + (hashlib.sha256, BaseException.__new__, BaseException.__init__)

    def protect(operation, *, receiver=None, class_receiver=False):
        originals.append(operation)
        method_name = operation.__name__
        def protected(*args, **kwargs):
            check = guard
            check()
            if receiver is not None:
                if class_receiver:
                    if args[0] is not receiver:
                        raise refuse("portable class receiver must be exact")
                elif native_type(args[0]) is not receiver:
                    raise refuse("portable receiver must be exact")
            if method_name == "_attempt_call":
                target = args[0]
                if not native_any(target is expected for expected in native_functions):
                    if native_type(target) is not FunctionType:
                        raise refuse("portable dispatch must retain an exact function")
                start = 1
            elif method_name == "_attempt_build_portable_value":
                if not native_any(args[0] is kind for kind in known_classes):
                    raise refuse("portable construction class must be exact")
                start = 1
            else:
                start = 1 if class_receiver or method_name == "__init__" else 0
            # JSON's pair hook and a canonical function are admitted executable
            # operands, never caller callbacks. Full guard binding checks precede it.
            for index, value in enumerate(args[start:], start):
                if method_name in ("normalize_json", "canonical_json", "digest_payload"):
                    continue
                if method_name == "_attempt_call" and native_type(value) is FunctionType:
                    continue
                if method_name == "_attempt_validate_wire" and index == 0 and native_any(value is kind for kind in known_classes):
                    continue
                native_visit(value)
            for key, value in kwargs.items():
                if native_type(key) is not str:
                    raise refuse("portable keyword names must be exact strings")
                if method_name in ("normalize_json", "canonical_json", "digest_payload"):
                    continue
                if method_name == "_attempt_call" and native_type(value) is FunctionType:
                    continue
                native_visit(value)
            try:
                result = operation(*args, **kwargs)
            except native_unwind:
                check()
                raise
            check()
            return result
        protected.__name__ = operation.__name__
        protected.__qualname__ = operation.__qualname__
        protected.__module__ = operation.__module__
        protected.__annotations__ = operation.__annotations__
        protected.__dict__["__wrapped__"] = operation
        wrappers.append(protected)
        return protected

    for name, operation in tuple(namespace.items()):
        if (name.startswith("_attempt_") or name.startswith("attempt_") or name in ("decode_attempt_canonical_bytes", "normalize_json", "canonical_json", "digest_payload")) and type(operation) is FunctionType:
            namespace[name] = protect(operation)
    # Inherited methods are installed on each exact class so subclass dispatch
    # cannot enter the public body. Generated frozen/repr methods are sealed too.
    for kind in known_classes:
        members = {**vars(_AttemptPortableValue), **vars(kind)}
        for name, operation in tuple(members.items()):
            if type(operation) is FunctionType:
                setattr(kind, name, protect(operation, receiver=kind))
            elif type(operation) is classmethod:
                setattr(kind, name, classmethod(protect(operation.__func__, receiver=kind, class_receiver=True)))
    # The base is retained separately: no unwrapped inherited entry may dispatch.
    for name, operation in tuple(vars(_AttemptPortableValue).items()):
        if type(operation) is FunctionType:
            setattr(_AttemptPortableValue, name, protect(operation))
        elif type(operation) is classmethod:
            setattr(_AttemptPortableValue, name, classmethod(protect(operation.__func__, class_receiver=True)))
    cell = next(cell for name, cell in zip(wrappers[0].__code__.co_freevars, wrappers[0].__closure__) if name == "guard")
    namespace["_attempt_guard_cell"] = cell

    def seal():
        nonlocal guard
        if guard is not None:
            guard()
            raise refuse("portable dispatch is already sealed")
        guard = _protect_shape_dispatch((*known_classes, _AttemptPortableValue, OntologyObjectOperationAttemptCodecError, OntologyRuntimeEncodingError, WeakKeyDictionary, json.JSONEncoder, json.JSONDecoder, json.JSONDecodeError),
            guard_name="_attempt_guard", helpers=(*tuple(value for value in namespace.values() if type(value) is FunctionType), *originals),
            extra_modules=(sys.modules["json"], sys.modules["json.encoder"], sys.modules["json.decoder"], sys.modules["json.scanner"], sys.modules["hashlib"], sys.modules["weakref"]),
            retained_guard_cell=cell)
        namespace["_attempt_guard"] = guard
    return seal




class _TopologyMeta(type):
    def __call__(cls, *args, **kwargs):
        raise TypeError("topology constructor is not initialized")


class _TopologyEnumMeta(type(StrEnum)):
    def __call__(cls, *args, **kwargs):
        raise TypeError("topology enum constructor is not initialized")


class RelationshipKind(StrEnum, metaclass=_TopologyEnumMeta):
    REFERENCE = "reference"
    CONTAINMENT = "containment"



@dataclass( frozen=True, slots=True)
class ProjectionDefinition(metaclass=_TopologyMeta):
    projection_ref: str
    root_type_refs: tuple[str, ...]
    type_refs: tuple[str, ...]
    field_refs: tuple[str, ...]
    relationship_refs: tuple[str, ...] = ()
    action_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _topology_call(object.__setattr__, self, 'projection_ref', _topology_call(_strict_token, self.projection_ref, 'projection_ref'))
        for field in ('root_type_refs', 'type_refs', 'field_refs', 'relationship_refs', 'action_refs'):
            _topology_call(object.__setattr__, self, field, _topology_call(_record_refs, _topology_call(getattr, self, field), field))
        if not self.root_type_refs or not self.type_refs:
            raise _topology_call(ValueError, 'projections require root_type_refs and type_refs')

    def to_wire(self) -> dict[str, object]:
        return {'projection_ref': self.projection_ref, 'root_type_refs': _topology_call(list, self.root_type_refs), 'type_refs': _topology_call(list, self.type_refs), 'field_refs': _topology_call(list, self.field_refs), 'relationship_refs': _topology_call(list, self.relationship_refs), 'action_refs': _topology_call(list, self.action_refs)}



def _topology_call(operation, /, *args, **kwargs):
    return _topology_modules[0]._call(operation, *args, **kwargs)


from . import topology_values, topology_validation, topology_codec
_topology_modules = (topology_values, topology_validation, topology_codec)
_topology_services = topology_values._install_dispatch(_topology_modules)

_attempt_seal = _install_attempt_dispatch()

_install_abi_dispatch()
_attempt_seal()

_topology_services[0]()
