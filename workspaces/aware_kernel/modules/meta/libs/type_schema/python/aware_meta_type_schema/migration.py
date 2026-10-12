from __future__ import annotations

from dataclasses import dataclass

from .compatibility import (
    TypeSchemaCompatibilityOutcome,
    compare_type_schemas,
)
from .diagnostics import (
    DiagnosticCollector,
    TypeSchemaValidationReport,
)
from .encoding import FrozenJson
from .model import (
    FieldDefinition,
    ShapeKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    ValueShape,
)
from .validation import validate_typed_value


def _token(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str")
    if not value or value.strip() != value or any(item.isspace() for item in value):
        raise ValueError(f"{name} must be a non-empty token")
    return value


@dataclass(frozen=True, slots=True)
class RenameField:
    type_ref: str
    source_field_ref: str
    target_field_ref: str

    def __post_init__(self) -> None:
        for name in ("type_ref", "source_field_ref", "target_field_ref"):
            object.__setattr__(self, name, _token(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class AddFieldDefault:
    type_ref: str
    target_field_ref: str
    default_value: FrozenJson

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        object.__setattr__(
            self,
            "target_field_ref",
            _token(self.target_field_ref, "target_field_ref"),
        )
        if not isinstance(self.default_value, FrozenJson):
            raise TypeError("default_value must be FrozenJson")


@dataclass(frozen=True, slots=True)
class DropField:
    type_ref: str
    source_field_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        object.__setattr__(
            self,
            "source_field_ref",
            _token(self.source_field_ref, "source_field_ref"),
        )


@dataclass(frozen=True, slots=True)
class MapEnumValue:
    type_ref: str
    source_value: str
    target_value: str

    def __post_init__(self) -> None:
        for name in ("type_ref", "source_value", "target_value"):
            object.__setattr__(self, name, _token(getattr(self, name), name))


type MigrationStep = RenameField | AddFieldDefault | DropField | MapEnumValue


@dataclass(frozen=True, slots=True)
class TypeSchemaMigrationPlan:
    migration_ref: str
    source_digest: str
    target_digest: str
    root_type_ref: str
    steps: tuple[MigrationStep, ...]

    def __post_init__(self) -> None:
        for name in (
            "migration_ref",
            "source_digest",
            "target_digest",
            "root_type_ref",
        ):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        steps = tuple(self.steps)
        if any(
            not isinstance(
                item, (RenameField, AddFieldDefault, DropField, MapEnumValue)
            )
            for item in steps
        ):
            raise TypeError("steps contain unsupported migration operation")
        object.__setattr__(self, "steps", steps)


@dataclass(frozen=True, slots=True)
class TypeSchemaMigrationResult:
    migration_ref: str
    source_digest: str
    target_digest: str
    value: FrozenJson | None
    report: TypeSchemaValidationReport

    @property
    def succeeded(self) -> bool:
        return self.value is not None and self.report.is_valid


def validate_migration_plan(
    plan: TypeSchemaMigrationPlan,
    source: TypeSchemaBundle,
    target: TypeSchemaBundle,
    *,
    max_diagnostics: int = 100,
) -> TypeSchemaValidationReport:
    if not isinstance(plan, TypeSchemaMigrationPlan):
        raise TypeError("plan must be TypeSchemaMigrationPlan")
    if not isinstance(source, TypeSchemaBundle) or not isinstance(
        target, TypeSchemaBundle
    ):
        raise TypeError("source and target must be TypeSchemaBundle")
    collector = DiagnosticCollector(max_diagnostics)
    if plan.source_digest != source.schema_digest:
        collector.add(
            "$.source_digest", "migration.source_digest", "source digest does not match"
        )
    if plan.target_digest != target.schema_digest:
        collector.add(
            "$.target_digest", "migration.target_digest", "target digest does not match"
        )
    source_types = {item.type_ref: item for item in source.types}
    target_types = {item.type_ref: item for item in target.types}
    if plan.root_type_ref not in source_types:
        collector.add(
            "$.root_type_ref",
            "migration.source_root",
            "root is absent from source schema",
        )
    if plan.root_type_ref not in target_types:
        collector.add(
            "$.root_type_ref",
            "migration.target_root",
            "root is absent from target schema",
        )
    compatibility = compare_type_schemas(source, target)
    if compatibility.outcome is TypeSchemaCompatibilityOutcome.INCOMPATIBLE:
        collector.add(
            "$",
            "migration.incompatible",
            "incompatible schemas cannot be migrated by this contract",
        )
    seen: set[tuple[object, ...]] = set()
    for index, step in enumerate(plan.steps):
        path = f"$.steps[{index}]"
        key = _step_key(step)
        if key in seen:
            collector.add(path, "migration.step_duplicate", "duplicate migration step")
        seen.add(key)
        _validate_step(step, source_types, target_types, path, collector)
    return collector.report()


def migrate_typed_value(
    plan: TypeSchemaMigrationPlan,
    source: TypeSchemaBundle,
    target: TypeSchemaBundle,
    value: object,
    *,
    max_diagnostics: int = 100,
) -> TypeSchemaMigrationResult:
    collector = DiagnosticCollector(max_diagnostics)
    plan_report = validate_migration_plan(
        plan, source, target, max_diagnostics=max_diagnostics
    )
    collector.extend(plan_report)
    source_report = validate_typed_value(
        source, plan.root_type_ref, value, max_diagnostics=max_diagnostics
    )
    for item in source_report.diagnostics:
        collector.add(item.path, f"source.{item.code}", item.message, item.severity)
    if not collector.report().is_valid:
        return _result(plan, None, collector.report())
    portable = FrozenJson.from_value(value).to_wire()
    source_types = {item.type_ref: item for item in source.types}
    target_types = {item.type_ref: item for item in target.types}
    migrated = _migrate_type(
        portable,
        source_types[plan.root_type_ref],
        target_types[plan.root_type_ref],
        source_types,
        target_types,
        plan.steps,
        "$",
        collector,
    )
    target_report = validate_typed_value(
        target, plan.root_type_ref, migrated, max_diagnostics=max_diagnostics
    )
    for item in target_report.diagnostics:
        collector.add(item.path, f"target.{item.code}", item.message, item.severity)
    report = collector.report()
    return _result(
        plan, FrozenJson.from_value(migrated) if report.is_valid else None, report
    )


def _validate_step(
    step: MigrationStep,
    source_types: dict[str, TypeDefinition],
    target_types: dict[str, TypeDefinition],
    path: str,
    collector: DiagnosticCollector,
) -> None:
    source_type = source_types.get(step.type_ref)
    target_type = target_types.get(step.type_ref)
    if source_type is None:
        collector.add(
            path, "migration.source_type", f"source type {step.type_ref!r} is absent"
        )
    if target_type is None:
        collector.add(
            path, "migration.target_type", f"target type {step.type_ref!r} is absent"
        )
    if source_type is None or target_type is None:
        return
    if isinstance(step, RenameField):
        _require_field(source_type, step.source_field_ref, path, "source", collector)
        _require_field(target_type, step.target_field_ref, path, "target", collector)
    elif isinstance(step, AddFieldDefault):
        field = _require_field(
            target_type, step.target_field_ref, path, "target", collector
        )
        if field is not None:
            report = _validate_field_default(target_types, field, step.default_value)
            for item in report.diagnostics:
                collector.add(path, f"migration.default.{item.code}", item.message)
    elif isinstance(step, DropField):
        _require_field(source_type, step.source_field_ref, path, "source", collector)
    elif source_type.kind is not TypeKind.ENUM or target_type.kind is not TypeKind.ENUM:
        collector.add(
            path,
            "migration.enum_type",
            "enum mapping requires enum type in both schemas",
        )
    else:
        if step.source_value not in source_type.enum_values:
            collector.add(path, "migration.source_enum", "source enum value is absent")
        if step.target_value not in target_type.enum_values:
            collector.add(path, "migration.target_enum", "target enum value is absent")


def _validate_field_default(
    types: dict[str, TypeDefinition],
    field: FieldDefinition,
    value: FrozenJson,
) -> TypeSchemaValidationReport:
    synthetic = TypeDefinition(
        "migration.Default",
        "Default",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "migration.Default.value",
                "value",
                field.shape,
                required=True,
                nullable=field.nullable,
                constraints=field.constraints,
            ),
        ),
    )
    bundle = TypeSchemaBundle.create(
        namespace="migration",
        semantic_version="0.0.0",
        types=(synthetic, *types.values()),
    )
    return validate_typed_value(bundle, synthetic.type_ref, {"value": value.to_wire()})


def _require_field(
    definition: TypeDefinition,
    field_ref: str,
    path: str,
    side: str,
    collector: DiagnosticCollector,
) -> FieldDefinition | None:
    field = next(
        (item for item in definition.fields if item.field_ref == field_ref), None
    )
    if field is None:
        collector.add(
            path, f"migration.{side}_field", f"{side} field {field_ref!r} is absent"
        )
    return field


def _migrate_type(
    value: object,
    source: TypeDefinition,
    target: TypeDefinition,
    source_types: dict[str, TypeDefinition],
    target_types: dict[str, TypeDefinition],
    steps: tuple[MigrationStep, ...],
    path: str,
    collector: DiagnosticCollector,
) -> object:
    if source.kind in (TypeKind.VALUE_OBJECT, TypeKind.GRAPH_OBJECT) and isinstance(
        value, dict
    ):
        return _migrate_object(
            value, source, target, source_types, target_types, steps, path, collector
        )
    if source.kind is TypeKind.ENUM and isinstance(value, str):
        for step in steps:
            if (
                isinstance(step, MapEnumValue)
                and step.type_ref == source.type_ref
                and step.source_value == value
            ):
                return step.target_value
    return value


def _migrate_object(
    value: dict[str, object],
    source: TypeDefinition,
    target: TypeDefinition,
    source_types: dict[str, TypeDefinition],
    target_types: dict[str, TypeDefinition],
    steps: tuple[MigrationStep, ...],
    path: str,
    collector: DiagnosticCollector,
) -> dict[str, object]:
    result = dict(value)
    source_fields = {item.field_ref: item for item in source.fields}
    target_fields = {item.field_ref: item for item in target.fields}
    rename_sources: dict[str, str] = {}
    for step in steps:
        if step.type_ref != source.type_ref:
            continue
        if isinstance(step, RenameField):
            before = source_fields[step.source_field_ref]
            after = target_fields[step.target_field_ref]
            rename_sources[step.target_field_ref] = step.source_field_ref
            present = [
                name for name in (before.name, *before.aliases) if name in result
            ]
            if present:
                if after.name in result and after.name not in present:
                    collector.add(
                        f"{path}.{after.name}",
                        "migration.rename_collision",
                        "rename target already exists",
                    )
                else:
                    result[after.name] = result.pop(present[0])
        elif isinstance(step, DropField):
            before = source_fields[step.source_field_ref]
            for name in (before.name, *before.aliases):
                result.pop(name, None)
        elif isinstance(step, AddFieldDefault):
            after = target_fields[step.target_field_ref]
            if not any(name in result for name in (after.name, *after.aliases)):
                result[after.name] = step.default_value.to_wire()
    for target_ref, after in target_fields.items():
        source_ref = rename_sources.get(target_ref, target_ref)
        before = source_fields.get(source_ref)
        if before is None:
            continue
        present = [name for name in (after.name, *after.aliases) if name in result]
        if not present:
            continue
        result[present[0]] = _migrate_shape(
            result[present[0]],
            before.shape,
            after.shape,
            source_types,
            target_types,
            steps,
            f"{path}.{after.name}",
            collector,
        )
    return result


def _migrate_shape(
    value: object,
    source: ValueShape,
    target: ValueShape,
    source_types: dict[str, TypeDefinition],
    target_types: dict[str, TypeDefinition],
    steps: tuple[MigrationStep, ...],
    path: str,
    collector: DiagnosticCollector,
) -> object:
    if source.kind is ShapeKind.NAMED and target.kind is ShapeKind.NAMED:
        assert source.type_ref is not None and target.type_ref is not None
        return _migrate_type(
            value,
            source_types[source.type_ref],
            target_types[target.type_ref],
            source_types,
            target_types,
            steps,
            path,
            collector,
        )
    if (
        source.kind is ShapeKind.LIST
        and target.kind is ShapeKind.LIST
        and isinstance(value, list)
    ):
        assert source.element is not None and target.element is not None
        return [
            _migrate_shape(
                item,
                source.element,
                target.element,
                source_types,
                target_types,
                steps,
                f"{path}[{index}]",
                collector,
            )
            for index, item in enumerate(value)
        ]
    if (
        source.kind is ShapeKind.MAP
        and target.kind is ShapeKind.MAP
        and isinstance(value, dict)
    ):
        assert source.map_value is not None and target.map_value is not None
        return {
            key: _migrate_shape(
                item,
                source.map_value,
                target.map_value,
                source_types,
                target_types,
                steps,
                f"{path}.{key}",
                collector,
            )
            for key, item in value.items()
        }
    return value


def _step_key(step: MigrationStep) -> tuple[object, ...]:
    if isinstance(step, RenameField):
        return ("rename", step.type_ref, step.source_field_ref, step.target_field_ref)
    if isinstance(step, AddFieldDefault):
        return ("add", step.type_ref, step.target_field_ref)
    if isinstance(step, DropField):
        return ("drop", step.type_ref, step.source_field_ref)
    return ("enum", step.type_ref, step.source_value)


def _result(
    plan: TypeSchemaMigrationPlan,
    value: FrozenJson | None,
    report: TypeSchemaValidationReport,
) -> TypeSchemaMigrationResult:
    return TypeSchemaMigrationResult(
        plan.migration_ref,
        plan.source_digest,
        plan.target_digest,
        value,
        report,
    )


__all__ = [
    "AddFieldDefault",
    "DropField",
    "MapEnumValue",
    "MigrationStep",
    "RenameField",
    "TypeSchemaMigrationPlan",
    "TypeSchemaMigrationResult",
    "migrate_typed_value",
    "validate_migration_plan",
]
