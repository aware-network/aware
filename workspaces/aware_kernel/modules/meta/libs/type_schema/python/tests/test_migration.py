from __future__ import annotations

from aware_meta_type_schema import (
    AddFieldDefault,
    DropField,
    FieldDefinition,
    FrozenJson,
    MapEnumValue,
    RenameField,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaMigrationPlan,
    ValueShape,
    migrate_typed_value,
    validate_migration_plan,
)


def _schemas() -> tuple[TypeSchemaBundle, TypeSchemaBundle]:
    source_status = TypeDefinition(
        "demo.Status", "Status", TypeKind.ENUM, enum_values=("open", "closed")
    )
    target_status = TypeDefinition(
        "demo.Status", "Status", TypeKind.ENUM, enum_values=("active", "closed")
    )
    source_child = TypeDefinition(
        "demo.Child",
        "Child",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Child.label",
                "label",
                ValueShape.scalar(ScalarKind.STRING),
                required=True,
            ),
        ),
    )
    target_child = TypeDefinition(
        "demo.Child",
        "Child",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Child.label",
                "name",
                ValueShape.scalar(ScalarKind.STRING),
                required=True,
            ),
        ),
    )
    source_root = TypeDefinition(
        "demo.Root",
        "Root",
        TypeKind.VALUE_OBJECT,
        fields=(
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
            ),
            FieldDefinition(
                "demo.Root.obsolete",
                "obsolete",
                ValueShape.scalar(ScalarKind.STRING),
            ),
        ),
    )
    target_root = TypeDefinition(
        "demo.Root",
        "Root",
        TypeKind.VALUE_OBJECT,
        fields=(
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
            ),
            FieldDefinition(
                "demo.Root.priority",
                "priority",
                ValueShape.scalar(ScalarKind.INTEGER),
                required=True,
            ),
        ),
    )
    source = TypeSchemaBundle.create(
        namespace="demo",
        semantic_version="1.0.0",
        types=(source_root, source_child, source_status),
    )
    target = TypeSchemaBundle.create(
        namespace="demo",
        semantic_version="2.0.0",
        types=(target_root, target_child, target_status),
    )
    return source, target


def _plan(
    source: TypeSchemaBundle, target: TypeSchemaBundle
) -> TypeSchemaMigrationPlan:
    return TypeSchemaMigrationPlan(
        "migration:demo-v2",
        source.schema_digest,
        target.schema_digest,
        "demo.Root",
        (
            RenameField("demo.Child", "demo.Child.label", "demo.Child.label"),
            DropField("demo.Root", "demo.Root.obsolete"),
            AddFieldDefault(
                "demo.Root",
                "demo.Root.priority",
                FrozenJson.from_value(1),
            ),
            MapEnumValue("demo.Status", "open", "active"),
        ),
    )


def test_exact_plan_migrates_nested_values_without_mutating_input() -> None:
    source, target = _schemas()
    plan = _plan(source, target)
    original = {
        "status": "open",
        "children": [{"label": "first"}, {"label": "second"}],
        "obsolete": "remove",
    }

    assert validate_migration_plan(plan, source, target).is_valid
    result = migrate_typed_value(plan, source, target, original)

    assert result.succeeded
    assert result.value is not None
    assert result.value.to_wire() == {
        "status": "active",
        "children": [{"name": "first"}, {"name": "second"}],
        "priority": 1,
    }
    assert original["children"] == [{"label": "first"}, {"label": "second"}]
    assert "obsolete" in original


def test_plan_fails_closed_on_digest_step_and_source_value_errors() -> None:
    source, target = _schemas()
    invalid = TypeSchemaMigrationPlan(
        "migration:invalid",
        "sha256:" + "0" * 64,
        target.schema_digest,
        "demo.Root",
        (DropField("demo.Root", "demo.Root.missing"),),
    )

    report = validate_migration_plan(invalid, source, target)
    assert not report.is_valid
    assert {item.code for item in report.diagnostics} >= {
        "migration.source_digest",
        "migration.source_field",
    }

    result = migrate_typed_value(
        _plan(source, target),
        source,
        target,
        {"status": "missing", "children": []},
    )
    assert not result.succeeded
    assert result.value is None
    assert any(item.code.startswith("source.") for item in result.report.diagnostics)
