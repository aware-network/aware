from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from aware_meta_type_schema import (
    SCHEMA_CONTRACT,
    FieldDefinition,
    FrozenJson,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaDecodeError,
    TypeSchemaSlice,
    ValueShape,
    decode_schema_bundle,
    decode_schema_slice,
    encode_schema_bundle,
    encode_schema_slice,
    negotiate_contract,
)


def _bundle() -> TypeSchemaBundle:
    child = TypeDefinition(
        "demo.Child",
        "Child",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Child.value",
                "value",
                ValueShape.scalar(ScalarKind.STRING),
                nullable=True,
                default_value=FrozenJson.from_value(None),
                constraints=FrozenJson.from_value({"max_length": 20}),
            ),
        ),
    )
    root = TypeDefinition(
        "demo.Root",
        "Root",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition("demo.Root.child", "child", ValueShape.named("demo.Child")),
        ),
    )
    return TypeSchemaBundle.create(
        namespace="demo", semantic_version="1.0.0", types=(root, child)
    )


def test_bundle_and_slice_round_trip_exact_canonical_bytes() -> None:
    bundle = _bundle()
    bundle_bytes = encode_schema_bundle(bundle)
    assert decode_schema_bundle(bundle_bytes) == bundle
    assert encode_schema_bundle(decode_schema_bundle(bundle_bytes)) == bundle_bytes

    value = TypeSchemaSlice.create(bundle, root_type_refs=("demo.Root",))
    slice_bytes = encode_schema_slice(value)
    assert decode_schema_slice(slice_bytes) == value
    assert encode_schema_slice(decode_schema_slice(slice_bytes)) == slice_bytes


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value.update({"future": True}),
        lambda value: value.update({"contract": "aware.meta.semantic-type-schema.v2"}),
        lambda value: value["types"][0].update({"future": True}),
        lambda value: value["types"][0]["fields"][0].update({"required": "true"}),
        lambda value: value.update({"schema_digest": "sha256:" + "0" * 64}),
    ),
)
def test_bundle_rejects_unknown_contract_shape_type_and_digest(
    mutation: Callable[[dict[str, object]], None],
) -> None:
    value = _bundle().to_wire()
    mutation(value)
    with pytest.raises(TypeSchemaDecodeError):
        decode_schema_bundle(json.dumps(value))


def test_duplicate_json_keys_and_invalid_default_marker_fail_closed() -> None:
    payload = (
        encode_schema_bundle(_bundle())
        .decode()
        .replace('"namespace":"demo"', '"namespace":"demo","namespace":"other"')
    )
    with pytest.raises(TypeSchemaDecodeError, match="duplicate JSON key"):
        decode_schema_bundle(payload)

    value = _bundle().to_wire()
    field = value["types"][0]["fields"][0]  # type: ignore[index]
    field["has_default"] = False  # type: ignore[index]
    field["default_value"] = "present"  # type: ignore[index]
    with pytest.raises(TypeSchemaDecodeError, match="default_value"):
        decode_schema_bundle(json.dumps(value))


def test_contract_negotiation_is_exact_and_locally_preferred() -> None:
    assert (
        negotiate_contract(
            ("aware.meta.semantic-type-schema.v0", SCHEMA_CONTRACT),
            supported=(SCHEMA_CONTRACT,),
        )
        == SCHEMA_CONTRACT
    )
    with pytest.raises(TypeSchemaDecodeError, match="no supported contract"):
        negotiate_contract(
            ("aware.meta.semantic-type-schema.v2",),
            supported=(SCHEMA_CONTRACT,),
        )
