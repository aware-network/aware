"""Exact null representation; adding it must not silently admit general JSON."""

from __future__ import annotations

import json

import pytest
from aware_meta_type_schema import (
    ScalarKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaTypedValueNormalizationError,
    ValueShape,
    decode_schema_bundle,
    encode_schema_bundle,
    normalize_typed_value,
    validate_schema_bundle,
    validate_typed_value,
)


def bundle() -> TypeSchemaBundle:
    return TypeSchemaBundle.create(
        namespace="aware.primitive",
        semantic_version="1",
        types=(
            TypeDefinition(
                "aware.primitive.Null",
                "Null",
                TypeKind.SCALAR_ALIAS,
                scalar_target=ScalarKind.NULL,
            ),
        ),
    )


def test_null_alias_codec_and_validation() -> None:
    value = bundle()
    assert validate_schema_bundle(value).is_valid
    assert decode_schema_bundle(encode_schema_bundle(value)) == value
    assert validate_typed_value(value, "aware.primitive.Null", None).is_valid
    assert json.loads(
        normalize_typed_value(value, ValueShape.scalar(ScalarKind.NULL), None)
    ) == {
        "shape": ValueShape.scalar(ScalarKind.NULL).to_wire(),
        "value": None,
    }


@pytest.mark.parametrize(
    "value", [False, True, 0, 1, "", "null", [], {}, [None], {"value": None}]
)
def test_null_is_not_a_json_widening(value: object) -> None:
    schema = bundle()
    report = validate_typed_value(schema, "aware.primitive.Null", value)
    assert not report.is_valid
    assert "value.null" in {item.code for item in report.diagnostics}
    with pytest.raises(TypeSchemaTypedValueNormalizationError):
        _ = normalize_typed_value(schema, ValueShape.scalar(ScalarKind.NULL), value)


def test_null_shape_does_not_alter_other_scalar_values() -> None:
    schema = bundle()
    assert normalize_typed_value(
        schema, ValueShape.scalar(ScalarKind.JSON), {"x": None}
    )
    assert normalize_typed_value(schema, ValueShape.scalar(ScalarKind.STRING), "null")
    assert normalize_typed_value(schema, ValueShape.scalar(ScalarKind.INTEGER), 0)
