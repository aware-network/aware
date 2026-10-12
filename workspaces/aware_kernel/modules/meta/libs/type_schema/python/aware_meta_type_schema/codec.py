from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from .encoding import FrozenJson, canonical_json
from .model import (
    SCHEMA_CONTRACT,
    SLICE_CONTRACT,
    FieldDefinition,
    IdentityDefinition,
    ScalarKind,
    ShapeKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaSlice,
    ValueShape,
)

SUPPORTED_SCHEMA_CONTRACTS = (SCHEMA_CONTRACT,)
SUPPORTED_SLICE_CONTRACTS = (SLICE_CONTRACT,)


class TypeSchemaDecodeError(ValueError):
    pass


def negotiate_contract(offered: Sequence[str], *, supported: Sequence[str]) -> str:
    offered_values = _token_sequence(offered, "offered")
    supported_values = _token_sequence(supported, "supported")
    for contract in supported_values:
        if contract in offered_values:
            return contract
    raise TypeSchemaDecodeError(
        f"no supported contract; offered={list(offered_values)!r}, "
        f"supported={list(supported_values)!r}"
    )


def encode_schema_bundle(bundle: TypeSchemaBundle) -> bytes:
    if not isinstance(bundle, TypeSchemaBundle):
        raise TypeError("bundle must be TypeSchemaBundle")
    return canonical_json(bundle.to_wire()).encode()


def encode_schema_slice(value: TypeSchemaSlice) -> bytes:
    if not isinstance(value, TypeSchemaSlice):
        raise TypeError("value must be TypeSchemaSlice")
    return canonical_json(value.to_wire()).encode()


def decode_schema_bundle(
    payload: bytes | str,
    *,
    supported_contracts: Sequence[str] = SUPPORTED_SCHEMA_CONTRACTS,
) -> TypeSchemaBundle:
    root = _root(payload)
    _exact(
        root,
        {"contract", "namespace", "semantic_version", "types", "schema_digest"},
        "$",
    )
    contract = _text(root, "contract", "$")
    negotiate_contract((contract,), supported=supported_contracts)
    if contract != SCHEMA_CONTRACT:
        raise TypeSchemaDecodeError(f"decoder does not implement {contract!r}")
    try:
        return TypeSchemaBundle(
            namespace=_text(root, "namespace", "$"),
            semantic_version=_text(root, "semantic_version", "$"),
            types=tuple(
                _decode_type(item, f"$.types[{index}]")
                for index, item in enumerate(_array(root, "types", "$"))
            ),
            schema_digest=_text(root, "schema_digest", "$"),
        )
    except (TypeError, ValueError) as error:
        if isinstance(error, TypeSchemaDecodeError):
            raise
        raise TypeSchemaDecodeError(f"bundle violates {contract}: {error}") from error


def decode_schema_slice(
    payload: bytes | str,
    *,
    supported_contracts: Sequence[str] = SUPPORTED_SLICE_CONTRACTS,
) -> TypeSchemaSlice:
    root = _root(payload)
    _exact(
        root,
        {
            "contract",
            "bundle_digest",
            "namespace",
            "semantic_version",
            "root_type_refs",
            "types",
            "slice_digest",
        },
        "$",
    )
    contract = _text(root, "contract", "$")
    negotiate_contract((contract,), supported=supported_contracts)
    if contract != SLICE_CONTRACT:
        raise TypeSchemaDecodeError(f"decoder does not implement {contract!r}")
    try:
        return TypeSchemaSlice(
            bundle_digest=_text(root, "bundle_digest", "$"),
            namespace=_text(root, "namespace", "$"),
            semantic_version=_text(root, "semantic_version", "$"),
            root_type_refs=_text_array(root, "root_type_refs", "$"),
            types=tuple(
                _decode_type(item, f"$.types[{index}]")
                for index, item in enumerate(_array(root, "types", "$"))
            ),
            slice_digest=_text(root, "slice_digest", "$"),
        )
    except (TypeError, ValueError) as error:
        if isinstance(error, TypeSchemaDecodeError):
            raise
        raise TypeSchemaDecodeError(f"slice violates {contract}: {error}") from error


def _decode_type(value: object, path: str) -> TypeDefinition:
    item = _object(value, path)
    _exact(
        item,
        {
            "type_ref",
            "name",
            "kind",
            "fields",
            "identity",
            "enum_values",
            "union_variants",
            "scalar_target",
            "discriminant_field_ref",
            "constraints",
            "aliases",
        },
        path,
    )
    identity_value = item["identity"]
    scalar_value = item["scalar_target"]
    discriminant = item["discriminant_field_ref"]
    if scalar_value is not None and not isinstance(scalar_value, str):
        raise TypeSchemaDecodeError(f"{path}.scalar_target must be text or null")
    if discriminant is not None and not isinstance(discriminant, str):
        raise TypeSchemaDecodeError(
            f"{path}.discriminant_field_ref must be text or null"
        )
    return TypeDefinition(
        type_ref=_text(item, "type_ref", path),
        name=_text(item, "name", path),
        kind=TypeKind(_text(item, "kind", path)),
        fields=tuple(
            _decode_field(field, f"{path}.fields[{index}]")
            for index, field in enumerate(_array(item, "fields", path))
        ),
        identity=None
        if identity_value is None
        else _decode_identity(identity_value, f"{path}.identity"),
        enum_values=_text_array(item, "enum_values", path),
        union_variants=tuple(
            _decode_shape(shape, f"{path}.union_variants[{index}]")
            for index, shape in enumerate(_array(item, "union_variants", path))
        ),
        scalar_target=None if scalar_value is None else ScalarKind(scalar_value),
        discriminant_field_ref=discriminant,
        constraints=FrozenJson.from_value(item["constraints"]),
        aliases=_text_array(item, "aliases", path),
    )


def _decode_identity(value: object, path: str) -> IdentityDefinition:
    item = _object(value, path)
    _exact(item, {"field_refs"}, path)
    return IdentityDefinition(_text_array(item, "field_refs", path))


def _decode_field(value: object, path: str) -> FieldDefinition:
    item = _object(value, path)
    _exact(
        item,
        {
            "field_ref",
            "name",
            "shape",
            "required",
            "nullable",
            "has_default",
            "default_value",
            "constraints",
            "aliases",
        },
        path,
    )
    has_default = _boolean(item, "has_default", path)
    if not has_default and item["default_value"] is not None:
        raise TypeSchemaDecodeError(
            f"{path}.default_value must be null when has_default is false"
        )
    return FieldDefinition(
        field_ref=_text(item, "field_ref", path),
        name=_text(item, "name", path),
        shape=_decode_shape(item["shape"], f"{path}.shape"),
        required=_boolean(item, "required", path),
        nullable=_boolean(item, "nullable", path),
        default_value=(
            FrozenJson.from_value(item["default_value"]) if has_default else None
        ),
        constraints=FrozenJson.from_value(item["constraints"]),
        aliases=_text_array(item, "aliases", path),
    )


def _decode_shape(value: object, path: str) -> ValueShape:
    item = _object(value, path)
    _exact(
        item,
        {"kind", "scalar_kind", "type_ref", "element", "map_value", "variants"},
        path,
    )
    scalar = item["scalar_kind"]
    type_ref = item["type_ref"]
    if scalar is not None and not isinstance(scalar, str):
        raise TypeSchemaDecodeError(f"{path}.scalar_kind must be text or null")
    if type_ref is not None and not isinstance(type_ref, str):
        raise TypeSchemaDecodeError(f"{path}.type_ref must be text or null")
    return ValueShape(
        kind=ShapeKind(_text(item, "kind", path)),
        scalar_kind=None if scalar is None else ScalarKind(scalar),
        type_ref=type_ref,
        element=None
        if item["element"] is None
        else _decode_shape(item["element"], f"{path}.element"),
        map_value=None
        if item["map_value"] is None
        else _decode_shape(item["map_value"], f"{path}.map_value"),
        variants=tuple(
            _decode_shape(shape, f"{path}.variants[{index}]")
            for index, shape in enumerate(_array(item, "variants", path))
        ),
    )


def _root(payload: bytes | str) -> Mapping[str, object]:
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise TypeSchemaDecodeError("payload is not UTF-8") from error
    elif isinstance(payload, str):
        text = payload
    else:
        raise TypeError("payload must be bytes or str")
    try:
        value = json.loads(text, object_pairs_hook=_without_duplicates)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TypeSchemaDecodeError("payload is not valid UTF-8 JSON") from error
    return _object(value, "$")


def _without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TypeSchemaDecodeError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _object(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise TypeSchemaDecodeError(f"{path} must be an object")
    return value


def _exact(value: Mapping[str, object], keys: set[str], path: str) -> None:
    actual = set(value)
    if actual != keys:
        raise TypeSchemaDecodeError(
            f"{path} keys are not exact; "
            f"missing={sorted(keys - actual)!r}, unknown={sorted(actual - keys)!r}"
        )


def _array(value: Mapping[str, object], field: str, path: str) -> list[object]:
    result = value[field]
    if not isinstance(result, list):
        raise TypeSchemaDecodeError(f"{path}.{field} must be an array")
    return result


def _text(value: Mapping[str, object], field: str, path: str) -> str:
    result = value[field]
    if not isinstance(result, str):
        raise TypeSchemaDecodeError(f"{path}.{field} must be text")
    return result


def _boolean(value: Mapping[str, object], field: str, path: str) -> bool:
    result = value[field]
    if not isinstance(result, bool):
        raise TypeSchemaDecodeError(f"{path}.{field} must be bool")
    return result


def _text_array(value: Mapping[str, object], field: str, path: str) -> tuple[str, ...]:
    result = _array(value, field, path)
    if any(not isinstance(item, str) for item in result):
        raise TypeSchemaDecodeError(f"{path}.{field} must contain text")
    return tuple(result)  # type: ignore[arg-type]


def _token_sequence(values: Sequence[str], field: str) -> tuple[str, ...]:
    result = tuple(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise TypeSchemaDecodeError(f"{field} must contain non-empty text")
    if len(result) != len(set(result)):
        raise TypeSchemaDecodeError(f"{field} contains duplicates")
    return result
