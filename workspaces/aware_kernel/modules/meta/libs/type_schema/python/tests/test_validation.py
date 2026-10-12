from __future__ import annotations

import pytest
from aware_meta_type_schema import (
    FieldDefinition,
    FrozenJson,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaTypedValueNormalizationError,
    ValueShape,
    normalize_typed_value,
    validate_schema_bundle,
    validate_typed_value,
)


def _bundle() -> TypeSchemaBundle:
    status = TypeDefinition(
        "demo.Status",
        "Status",
        TypeKind.ENUM,
        enum_values=("open", "closed"),
    )
    child = TypeDefinition(
        "demo.Child",
        "Child",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Child.label",
                "label",
                ValueShape.scalar(ScalarKind.STRING),
                required=True,
                constraints=FrozenJson.from_value({"min_length": 2}),
            ),
        ),
    )
    root = TypeDefinition(
        "demo.Root",
        "Root",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Root.count",
                "count",
                ValueShape.scalar(ScalarKind.INTEGER),
                required=True,
                constraints=FrozenJson.from_value({"minimum": 1}),
            ),
            FieldDefinition(
                "demo.Root.note",
                "note",
                ValueShape.scalar(ScalarKind.STRING),
                nullable=True,
                aliases=("legacy_note",),
            ),
            FieldDefinition(
                "demo.Root.status",
                "status",
                ValueShape.named("demo.Status"),
                required=True,
            ),
            FieldDefinition(
                "demo.Root.children",
                "children",
                ValueShape.list_of(ValueShape.named("demo.Child")),
                constraints=FrozenJson.from_value({"min_items": 1}),
            ),
        ),
    )
    return TypeSchemaBundle.create(
        namespace="demo",
        semantic_version="1.0.0",
        types=(root, child, status),
    )


def test_typed_validation_accepts_nested_exact_value_and_alias() -> None:
    report = validate_typed_value(
        _bundle(),
        "demo.Root",
        {
            "count": 1,
            "legacy_note": None,
            "status": "open",
            "children": [{"label": "ok"}],
        },
    )

    assert report.is_valid
    assert report.diagnostics == ()


def test_typed_validation_returns_multiple_bounded_diagnostics() -> None:
    value = {
        "count": 0,
        "note": "current",
        "legacy_note": "legacy",
        "status": "missing",
        "children": [{"label": "x", "future": True}],
        "unknown": True,
    }

    report = validate_typed_value(_bundle(), "demo.Root", value)

    assert not report.is_valid
    assert {item.code for item in report.diagnostics} >= {
        "constraint.minimum",
        "field.alias_conflict",
        "value.enum",
        "constraint.min_length",
        "field.unknown",
    }
    bounded = validate_typed_value(_bundle(), "demo.Root", value, max_diagnostics=2)
    assert len(bounded.diagnostics) == 2
    assert bounded.truncated


def test_schema_validation_rejects_unknown_constraints_and_static_json_union() -> None:
    broken = TypeDefinition(
        "demo.Broken",
        "Broken",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Broken.name",
                "name",
                ValueShape.scalar(ScalarKind.STRING),
                constraints=FrozenJson.from_value({"future": True}),
            ),
            FieldDefinition(
                "demo.Broken.choice",
                "choice",
                ValueShape.union_of(
                    ValueShape.scalar(ScalarKind.JSON),
                    ValueShape.scalar(ScalarKind.STRING),
                ),
            ),
        ),
    )
    bundle = TypeSchemaBundle.create(
        namespace="demo", semantic_version="1.0.0", types=(broken,)
    )

    report = validate_schema_bundle(bundle)

    assert not report.is_valid
    assert report.by_code("constraint.unknown")
    assert report.by_code("union.ambiguous_static")


def test_schema_validation_checks_defaults_aliases_and_constraint_order() -> None:
    broken = TypeDefinition(
        "demo.Broken",
        "Broken",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Broken.count",
                "count",
                ValueShape.scalar(ScalarKind.INTEGER),
                nullable=False,
                default_value=FrozenJson.from_value(None),
                constraints=FrozenJson.from_value({"minimum": 10, "maximum": 1}),
                aliases=("count",),
            ),
        ),
    )
    bundle = TypeSchemaBundle.create(
        namespace="demo", semantic_version="1.0.0", types=(broken,)
    )

    report = validate_schema_bundle(bundle)

    assert {item.code for item in report.diagnostics} >= {
        "alias.self",
        "default.nullable",
        "constraint.order",
    }


def test_canonical_scalar_validation_is_exact() -> None:
    scalars = TypeDefinition(
        "demo.Scalars",
        "Scalars",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition("d", "decimal", ValueShape.scalar(ScalarKind.DECIMAL)),
            FieldDefinition("u", "uuid", ValueShape.scalar(ScalarKind.UUID)),
            FieldDefinition("b", "bytes", ValueShape.scalar(ScalarKind.BYTES)),
            FieldDefinition("t", "time", ValueShape.scalar(ScalarKind.DATETIME)),
        ),
    )
    bundle = TypeSchemaBundle.create(
        namespace="demo", semantic_version="1.0.0", types=(scalars,)
    )

    assert validate_typed_value(
        bundle,
        "demo.Scalars",
        {
            "decimal": "10.25",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "bytes": "YWJj",
            "time": "2026-08-21T10:00:00Z",
        },
    ).is_valid
    report = validate_typed_value(
        bundle,
        "demo.Scalars",
        {"decimal": 10.25, "uuid": "UPPER", "bytes": "!", "time": "today"},
    )
    assert {item.code for item in report.diagnostics} == {
        "value.decimal",
        "value.uuid",
        "value.bytes",
        "value.datetime",
    }


def test_typed_normalization_collapses_semantic_scalar_spellings() -> None:
    bundle = TypeSchemaBundle.create(
        namespace="demo",
        semantic_version="1.0.0",
        types=(
            TypeDefinition(
                "demo.Identity",
                "Identity",
                TypeKind.VALUE_OBJECT,
                fields=(
                    FieldDefinition(
                        "demo.Identity.decimal",
                        "decimal",
                        ValueShape.scalar(ScalarKind.DECIMAL),
                    ),
                    FieldDefinition(
                        "demo.Identity.datetime",
                        "datetime",
                        ValueShape.scalar(ScalarKind.DATETIME),
                    ),
                ),
            ),
        ),
    )
    decimal = ValueShape.scalar(ScalarKind.DECIMAL)
    instant = ValueShape.scalar(ScalarKind.DATETIME)

    assert normalize_typed_value(bundle, decimal, "0") == normalize_typed_value(
        bundle, decimal, "-0"
    )
    assert normalize_typed_value(
        bundle, instant, "2026-08-23T00:00:00Z"
    ) == normalize_typed_value(
        bundle, instant, "2026-08-23T00:00:00.000000Z"
    )
    assert b'"scalar_kind":"decimal"' in normalize_typed_value(bundle, decimal, "0")
    assert normalize_typed_value(
        bundle, decimal, "0"
    ) != normalize_typed_value(
        bundle, ValueShape.scalar(ScalarKind.STRING), "0"
    )
    assert normalize_typed_value(
        bundle, decimal, "12345678901234567890123456789"
    ) != normalize_typed_value(
        bundle, decimal, "12345678901234567890123456790"
    )
    assert normalize_typed_value(
        bundle, instant, "2026-08-23T00:00:00.123456Z"
    ) != normalize_typed_value(
        bundle, instant, "2026-08-23T00:00:00.123455Z"
    )
    for unsupported_precision in (
        "2026-08-23T00:00:00.1234561Z",
        "2026-08-23T00:00:00.1234569Z",
    ):
        with pytest.raises(
            TypeSchemaTypedValueNormalizationError,
            match="expected canonical datetime",
        ):
            normalize_typed_value(bundle, instant, unsupported_precision)
