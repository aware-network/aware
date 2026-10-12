from __future__ import annotations

from aware_meta_type_schema import (
    FieldDefinition,
    ScalarKind,
    SemanticVersion,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaCompatibilityOutcome,
    ValueShape,
    compare_type_schemas,
)


def _bundle(
    version: str,
    *,
    fields: tuple[FieldDefinition, ...] = (),
    enum_values: tuple[str, ...] = ("open", "closed"),
) -> TypeSchemaBundle:
    status = TypeDefinition(
        "demo.Status",
        "Status",
        TypeKind.ENUM,
        enum_values=enum_values,
    )
    root = TypeDefinition(
        "demo.Root",
        "Root",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Root.id",
                "id",
                ValueShape.scalar(ScalarKind.STRING),
                required=True,
            ),
            *fields,
        ),
    )
    return TypeSchemaBundle.create(
        namespace="demo", semantic_version=version, types=(root, status)
    )


def test_semantic_version_is_exact_and_ordered() -> None:
    assert SemanticVersion.parse("2.0.0") > SemanticVersion.parse("1.99.99")
    for invalid in ("1", "1.0", "01.0.0", "1.0.0-dev"):
        try:
            SemanticVersion.parse(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted {invalid!r}")


def test_version_only_change_is_structurally_equivalent() -> None:
    report = compare_type_schemas(_bundle("1.0.0"), _bundle("1.0.1"))

    assert report.outcome is TypeSchemaCompatibilityOutcome.EQUIVALENT
    assert report.previous_digest != report.candidate_digest
    assert report.changes == ()


def test_optional_addition_is_backward_and_removal_is_forward() -> None:
    field = FieldDefinition(
        "demo.Root.note", "note", ValueShape.scalar(ScalarKind.STRING)
    )

    assert (
        compare_type_schemas(
            _bundle("1.0.0"), _bundle("1.1.0", fields=(field,))
        ).outcome
        is TypeSchemaCompatibilityOutcome.BACKWARD_COMPATIBLE
    )
    assert (
        compare_type_schemas(
            _bundle("1.1.0", fields=(field,)), _bundle("2.0.0")
        ).outcome
        is TypeSchemaCompatibilityOutcome.FORWARD_COMPATIBLE
    )


def test_required_addition_enum_removal_and_mixed_direction_require_migration() -> None:
    required = FieldDefinition(
        "demo.Root.title",
        "title",
        ValueShape.scalar(ScalarKind.STRING),
        required=True,
    )
    report = compare_type_schemas(
        _bundle("1.0.0"),
        _bundle("2.0.0", fields=(required,), enum_values=("open",)),
    )

    assert report.outcome is TypeSchemaCompatibilityOutcome.MIGRATION_REQUIRED
    assert {item.code for item in report.changes} >= {
        "field.required_added",
        "enum.values_removed",
    }


def test_same_version_mutation_and_kind_reuse_are_incompatible() -> None:
    optional = FieldDefinition(
        "demo.Root.note", "note", ValueShape.scalar(ScalarKind.STRING)
    )
    same_version = compare_type_schemas(
        _bundle("1.0.0"), _bundle("1.0.0", fields=(optional,))
    )
    assert same_version.outcome is TypeSchemaCompatibilityOutcome.INCOMPATIBLE
    assert any(item.code == "version.reused" for item in same_version.changes)

    old = _bundle("1.0.0")
    changed = TypeSchemaBundle.create(
        namespace="demo",
        semantic_version="2.0.0",
        types=(
            TypeDefinition(
                "demo.Root",
                "Root",
                TypeKind.SCALAR_ALIAS,
                scalar_target=ScalarKind.STRING,
            ),
            next(item for item in old.types if item.type_ref == "demo.Status"),
        ),
    )
    report = compare_type_schemas(old, changed)
    assert report.outcome is TypeSchemaCompatibilityOutcome.INCOMPATIBLE
    assert any(item.code == "type.kind_changed" for item in report.changes)


def test_rename_with_predecessor_alias_is_backward_compatible() -> None:
    before = FieldDefinition(
        "demo.Root.note", "note", ValueShape.scalar(ScalarKind.STRING)
    )
    after = FieldDefinition(
        "demo.Root.note",
        "description",
        ValueShape.scalar(ScalarKind.STRING),
        aliases=("note",),
    )

    report = compare_type_schemas(
        _bundle("1.0.0", fields=(before,)),
        _bundle("1.1.0", fields=(after,)),
    )

    assert report.outcome is TypeSchemaCompatibilityOutcome.BACKWARD_COMPATIBLE
    assert any(item.code == "field.renamed_with_alias" for item in report.changes)
