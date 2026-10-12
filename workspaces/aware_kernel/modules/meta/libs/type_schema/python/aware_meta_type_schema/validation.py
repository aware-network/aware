from __future__ import annotations

import base64
import re
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from .diagnostics import DiagnosticCollector, TypeSchemaValidationReport
from .encoding import (
    FrozenJson,
    TypeSchemaEncodingError,
    canonical_json,
    normalize_json,
)
from .model import (
    ScalarKind,
    ShapeKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    ValueShape,
)

_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$")
_DATETIME = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?Z$"
)
_STRING_CONSTRAINTS = frozenset({"min_length", "max_length", "pattern"})
_NUMBER_CONSTRAINTS = frozenset({"minimum", "maximum"})
_COLLECTION_CONSTRAINTS = frozenset({"min_items", "max_items"})


class TypeSchemaTypedValueNormalizationError(ValueError):
    """Raised when a value cannot produce exact Type Schema-normalized bytes."""


def normalize_typed_value(
    bundle: TypeSchemaBundle,
    shape: ValueShape,
    value: object,
) -> bytes:
    """Return canonical bytes for one exact shape-bound semantic value."""

    if not isinstance(bundle, TypeSchemaBundle):
        raise TypeError("bundle must be TypeSchemaBundle")
    if not isinstance(shape, ValueShape):
        raise TypeError("shape must be ValueShape")
    by_ref = {item.type_ref: item for item in bundle.types}
    collector = DiagnosticCollector(100)
    try:
        _validate_shape(value, shape, by_ref, "$", collector)
    except KeyError as error:
        raise TypeSchemaTypedValueNormalizationError(
            f"shape references unknown type {error.args[0]!r}"
        ) from error
    report = collector.report()
    if not report.is_valid:
        detail = "; ".join(
            f"{item.path}:{item.code}:{item.message}" for item in report.diagnostics
        )
        raise TypeSchemaTypedValueNormalizationError(
            f"typed value is invalid: {detail}"
        )
    normalized = _normalize_shape(value, shape, by_ref)
    return canonical_json(
        {"shape": shape.to_wire(), "value": normalize_json(normalized)}
    ).encode()


def _normalize_shape(
    value: object,
    shape: ValueShape,
    by_ref: Mapping[str, TypeDefinition],
) -> object:
    if shape.kind is ShapeKind.SCALAR:
        assert shape.scalar_kind is not None
        return _normalize_scalar(value, shape.scalar_kind)
    if shape.kind is ShapeKind.NAMED:
        assert shape.type_ref is not None
        return _normalize_type(value, by_ref[shape.type_ref], by_ref)
    if shape.kind is ShapeKind.LIST:
        assert shape.element is not None and isinstance(value, list)
        return [_normalize_shape(item, shape.element, by_ref) for item in value]
    if shape.kind is ShapeKind.MAP:
        assert shape.map_value is not None and isinstance(value, dict)
        return {
            key: _normalize_shape(value[key], shape.map_value, by_ref)
            for key in sorted(value)
        }
    matching = tuple(
        variant
        for variant in shape.variants
        if _shape_accepts(value, variant, by_ref)
    )
    if len(matching) != 1:
        raise TypeSchemaTypedValueNormalizationError(
            "union normalization requires exactly one matching variant"
        )
    return _normalize_shape(value, matching[0], by_ref)


def _shape_accepts(
    value: object,
    shape: ValueShape,
    by_ref: Mapping[str, TypeDefinition],
) -> bool:
    collector = DiagnosticCollector(1)
    _validate_shape(value, shape, dict(by_ref), "$", collector)
    return collector.report().is_valid


def _normalize_type(
    value: object,
    definition: TypeDefinition,
    by_ref: Mapping[str, TypeDefinition],
) -> object:
    if definition.kind in (TypeKind.VALUE_OBJECT, TypeKind.GRAPH_OBJECT):
        assert isinstance(value, dict)
        normalized: dict[str, object] = {}
        for field in definition.fields:
            names = (field.name, *field.aliases)
            present = tuple(name for name in names if name in value)
            if present:
                field_value = value[present[0]]
            elif field.default_value is not None:
                field_value = field.default_value.to_wire()
            else:
                continue
            normalized[field.name] = (
                None
                if field_value is None
                else _normalize_shape(field_value, field.shape, by_ref)
            )
        return normalized
    if definition.kind is TypeKind.ENUM:
        return value
    if definition.kind is TypeKind.UNION:
        return _normalize_shape(
            value, ValueShape.union_of(*definition.union_variants), by_ref
        )
    assert definition.scalar_target is not None
    return _normalize_scalar(value, definition.scalar_target)


def _normalize_scalar(value: object, kind: ScalarKind) -> object:
    if kind is ScalarKind.DECIMAL:
        assert isinstance(value, str)
        return "0" if value == "-0" else value
    if kind is ScalarKind.DATETIME:
        assert isinstance(value, str)
        parsed = datetime.fromisoformat(value).astimezone(UTC)
        return parsed.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return value


def validate_typed_value(
    bundle: TypeSchemaBundle,
    type_ref: str,
    value: object,
    *,
    max_diagnostics: int = 100,
) -> TypeSchemaValidationReport:
    if not isinstance(bundle, TypeSchemaBundle):
        raise TypeError("bundle must be TypeSchemaBundle")
    collector = DiagnosticCollector(max_diagnostics)
    by_ref = {item.type_ref: item for item in bundle.types}
    definition = by_ref.get(type_ref)
    if definition is None:
        collector.add("$", "type.unknown", f"unknown root type {type_ref!r}")
        return collector.report()
    _validate_type(value, definition, by_ref, "$", collector)
    return collector.report()


def validate_schema_bundle(
    bundle: TypeSchemaBundle, *, max_diagnostics: int = 100
) -> TypeSchemaValidationReport:
    if not isinstance(bundle, TypeSchemaBundle):
        raise TypeError("bundle must be TypeSchemaBundle")
    collector = DiagnosticCollector(max_diagnostics)
    by_ref = {item.type_ref: item for item in bundle.types}
    for definition in bundle.types:
        path = f"$.types[{definition.type_ref!r}]"
        _validate_aliases(definition.aliases, path, collector)
        if definition.name in definition.aliases:
            collector.add(path, "alias.self", "type aliases contain the current name")
        definition_shape = (
            ValueShape.scalar(definition.scalar_target)
            if definition.kind is TypeKind.SCALAR_ALIAS
            and definition.scalar_target is not None
            else None
        )
        _validate_constraints(definition.constraints, definition_shape, path, collector)
        if definition.kind in (TypeKind.VALUE_OBJECT, TypeKind.GRAPH_OBJECT):
            accepted_names: dict[str, str] = {}
            for field in definition.fields:
                field_path = f"{path}.fields[{field.field_ref!r}]"
                for name in (field.name, *field.aliases):
                    previous = accepted_names.get(name)
                    if previous is not None and previous != field.field_ref:
                        collector.add(
                            field_path,
                            "field.alias_collision",
                            f"wire name {name!r} is accepted by {previous!r} and {field.field_ref!r}",
                        )
                    accepted_names[name] = field.field_ref
                _validate_aliases(field.aliases, field_path, collector)
                if field.name in field.aliases:
                    collector.add(
                        field_path,
                        "alias.self",
                        "field aliases contain the current name",
                    )
                _validate_constraints(
                    field.constraints, field.shape, field_path, collector
                )
                _validate_shape_schema(field.shape, field_path, collector)
                if field.default_value is not None:
                    default = field.default_value.to_wire()
                    default_path = f"{field_path}.default_value"
                    if default is None:
                        if not field.nullable:
                            collector.add(
                                default_path,
                                "default.nullable",
                                "null default requires a nullable field",
                            )
                    else:
                        _validate_shape(
                            default, field.shape, by_ref, default_path, collector
                        )
                        _apply_constraints(
                            default,
                            field.constraints,
                            field.shape,
                            default_path,
                            collector,
                        )
        elif definition.kind is TypeKind.UNION:
            _check_static_union(definition.union_variants, path, collector)
            for index, variant in enumerate(definition.union_variants):
                _validate_shape_schema(
                    variant, f"{path}.union_variants[{index}]", collector
                )
    return collector.report()


def _validate_type(
    value: object,
    definition: TypeDefinition,
    by_ref: dict[str, TypeDefinition],
    path: str,
    collector: DiagnosticCollector,
) -> None:
    if definition.kind in (TypeKind.VALUE_OBJECT, TypeKind.GRAPH_OBJECT):
        _validate_object(value, definition, by_ref, path, collector)
    elif definition.kind is TypeKind.ENUM:
        if not isinstance(value, str) or value not in definition.enum_values:
            collector.add(
                path,
                "value.enum",
                f"expected one of {list(definition.enum_values)!r}",
            )
    elif definition.kind is TypeKind.UNION:
        _validate_union(value, definition.union_variants, by_ref, path, collector)
    else:
        assert definition.scalar_target is not None
        _validate_scalar(value, definition.scalar_target, path, collector)
        _apply_constraints(value, definition.constraints, None, path, collector)


def _validate_object(
    value: object,
    definition: TypeDefinition,
    by_ref: dict[str, TypeDefinition],
    path: str,
    collector: DiagnosticCollector,
) -> None:
    if not isinstance(value, dict):
        collector.add(path, "value.object", "expected object")
        return
    known: set[str] = set()
    for field in definition.fields:
        accepted = (field.name, *field.aliases)
        known.update(accepted)
        present = [name for name in accepted if name in value]
        field_path = f"{path}.{field.name}"
        if len(present) > 1:
            collector.add(
                field_path,
                "field.alias_conflict",
                f"multiple wire names supplied for {field.field_ref!r}: {present!r}",
            )
            continue
        if not present:
            if field.required and field.default_value is None:
                collector.add(field_path, "field.required", "required field is missing")
            continue
        field_value = value[present[0]]
        if field_value is None:
            if not field.nullable:
                collector.add(field_path, "field.nullable", "field cannot be null")
            continue
        _validate_shape(field_value, field.shape, by_ref, field_path, collector)
        _apply_constraints(
            field_value, field.constraints, field.shape, field_path, collector
        )
    for name in sorted(set(value) - known, key=str):
        collector.add(f"{path}.{name}", "field.unknown", "unknown field")


def _validate_shape(
    value: object,
    shape: ValueShape,
    by_ref: dict[str, TypeDefinition],
    path: str,
    collector: DiagnosticCollector,
) -> None:
    if shape.kind is ShapeKind.SCALAR:
        assert shape.scalar_kind is not None
        _validate_scalar(value, shape.scalar_kind, path, collector)
    elif shape.kind is ShapeKind.NAMED:
        assert shape.type_ref is not None
        _validate_type(value, by_ref[shape.type_ref], by_ref, path, collector)
    elif shape.kind is ShapeKind.LIST:
        if not isinstance(value, list):
            collector.add(path, "value.list", "expected array")
            return
        assert shape.element is not None
        for index, item in enumerate(value):
            _validate_shape(item, shape.element, by_ref, f"{path}[{index}]", collector)
    elif shape.kind is ShapeKind.MAP:
        if not isinstance(value, dict) or any(
            not isinstance(key, str) for key in value
        ):
            collector.add(path, "value.map", "expected object with text keys")
            return
        assert shape.map_value is not None
        for key in sorted(value):
            _validate_shape(
                value[key], shape.map_value, by_ref, f"{path}.{key}", collector
            )
    else:
        _validate_union(value, shape.variants, by_ref, path, collector)


def _validate_union(
    value: object,
    variants: tuple[ValueShape, ...],
    by_ref: dict[str, TypeDefinition],
    path: str,
    collector: DiagnosticCollector,
) -> None:
    matches = 0
    for variant in variants:
        branch = DiagnosticCollector(100)
        _validate_shape(value, variant, by_ref, path, branch)
        if branch.report().is_valid:
            matches += 1
    if matches == 0:
        collector.add(path, "union.no_match", "value matches no union variant")
    elif matches > 1:
        collector.add(path, "union.ambiguous", "value matches multiple union variants")


def _validate_scalar(
    value: object,
    kind: ScalarKind,
    path: str,
    collector: DiagnosticCollector,
) -> None:
    valid = False
    if kind is ScalarKind.STRING:
        valid = isinstance(value, str)
    elif kind is ScalarKind.INTEGER:
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif kind is ScalarKind.BOOLEAN:
        valid = isinstance(value, bool)
    elif kind is ScalarKind.DECIMAL:
        valid = isinstance(value, str) and _DECIMAL.fullmatch(value) is not None
    elif kind is ScalarKind.DATETIME:
        valid = _valid_datetime(value)
    elif kind is ScalarKind.BYTES:
        valid = _valid_base64(value)
    elif kind is ScalarKind.UUID:
        valid = _valid_uuid(value)
    elif kind is ScalarKind.NULL:
        valid = value is None
    else:
        try:
            normalize_json(value)
            valid = True
        except TypeSchemaEncodingError:
            pass
    if not valid:
        collector.add(path, f"value.{kind.value}", f"expected canonical {kind.value}")


def _valid_datetime(value: object) -> bool:
    if not isinstance(value, str) or _DATETIME.fullmatch(value) is None:
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat().endswith("+00:00")


def _valid_base64(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return (
            base64.b64encode(base64.b64decode(value, validate=True)).decode() == value
        )
    except ValueError:
        return False


def _valid_uuid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def _validate_aliases(
    aliases: tuple[str, ...], path: str, collector: DiagnosticCollector
) -> None:
    if len(aliases) != len(set(aliases)):
        collector.add(path, "alias.duplicate", "aliases contain duplicates")


def _validate_constraints(
    constraints: FrozenJson,
    shape: ValueShape | None,
    path: str,
    collector: DiagnosticCollector,
) -> None:
    value = constraints.to_wire()
    if not isinstance(value, dict):
        collector.add(path, "constraint.object", "constraints must be an object")
        return
    allowed: frozenset[str] = frozenset()
    if shape is not None:
        if shape.kind is ShapeKind.SCALAR and shape.scalar_kind is ScalarKind.STRING:
            allowed = _STRING_CONSTRAINTS
        elif shape.kind is ShapeKind.SCALAR and shape.scalar_kind in (
            ScalarKind.INTEGER,
            ScalarKind.DECIMAL,
        ):
            allowed = _NUMBER_CONSTRAINTS
        elif shape.kind in (ShapeKind.LIST, ShapeKind.MAP):
            allowed = _COLLECTION_CONSTRAINTS
    for key in sorted(set(value) - allowed):
        collector.add(
            f"{path}.constraints.{key}", "constraint.unknown", "unknown constraint"
        )
    for key in sorted(set(value) & allowed):
        item = value[key]
        if key in {"min_length", "max_length", "min_items", "max_items"}:
            if not isinstance(item, int) or isinstance(item, bool) or item < 0:
                collector.add(
                    f"{path}.constraints.{key}",
                    "constraint.invalid",
                    "expected non-negative integer",
                )
        elif key == "pattern":
            if not isinstance(item, str):
                collector.add(
                    f"{path}.constraints.{key}",
                    "constraint.invalid",
                    "expected regex text",
                )
            else:
                try:
                    re.compile(item)
                except re.error:
                    collector.add(
                        f"{path}.constraints.{key}",
                        "constraint.invalid",
                        "invalid regex",
                    )
        elif not isinstance(item, (int, str)) or isinstance(item, bool):
            collector.add(
                f"{path}.constraints.{key}",
                "constraint.invalid",
                "expected integer or canonical decimal text",
            )
        elif isinstance(item, str) and _DECIMAL.fullmatch(item) is None:
            collector.add(
                f"{path}.constraints.{key}",
                "constraint.invalid",
                "expected canonical decimal text",
            )
    for lower_key, upper_key in (
        ("min_length", "max_length"),
        ("min_items", "max_items"),
        ("minimum", "maximum"),
    ):
        lower = value.get(lower_key)
        upper = value.get(upper_key)
        try:
            invalid_order = (
                isinstance(lower, int)
                and not isinstance(lower, bool)
                and isinstance(upper, int)
                and not isinstance(upper, bool)
                and lower > upper
            ) or (
                isinstance(lower, str)
                and isinstance(upper, str)
                and _DECIMAL.fullmatch(lower) is not None
                and _DECIMAL.fullmatch(upper) is not None
                and Decimal(lower) > Decimal(upper)
            )
        except InvalidOperation:
            invalid_order = False
        if invalid_order:
            collector.add(
                f"{path}.constraints",
                "constraint.order",
                f"{lower_key} exceeds {upper_key}",
            )


def _apply_constraints(
    value: object,
    constraints: FrozenJson,
    shape: ValueShape | None,
    path: str,
    collector: DiagnosticCollector,
) -> None:
    rules = constraints.to_wire()
    if not isinstance(rules, dict):
        return
    if isinstance(value, str):
        _check_bound(len(value), rules, "min_length", "max_length", path, collector)
        pattern = rules.get("pattern")
        if isinstance(pattern, str):
            try:
                if re.search(pattern, value) is None:
                    collector.add(
                        path, "constraint.pattern", "text does not match pattern"
                    )
            except re.error:
                pass
    if isinstance(value, (list, dict)):
        _check_bound(len(value), rules, "min_items", "max_items", path, collector)
    if isinstance(value, int) and not isinstance(value, bool):
        _check_numeric(Decimal(value), rules, path, collector)
    elif (
        shape is not None
        and shape.kind is ShapeKind.SCALAR
        and shape.scalar_kind is ScalarKind.DECIMAL
        and isinstance(value, str)
    ):
        try:
            _check_numeric(Decimal(value), rules, path, collector)
        except InvalidOperation:
            pass


def _check_bound(
    actual: int,
    rules: Mapping[str, object],
    minimum: str,
    maximum: str,
    path: str,
    collector: DiagnosticCollector,
) -> None:
    lower = rules.get(minimum)
    upper = rules.get(maximum)
    if isinstance(lower, int) and not isinstance(lower, bool) and actual < lower:
        collector.add(path, f"constraint.{minimum}", f"value is below {minimum}")
    if isinstance(upper, int) and not isinstance(upper, bool) and actual > upper:
        collector.add(path, f"constraint.{maximum}", f"value exceeds {maximum}")


def _check_numeric(
    actual: Decimal,
    rules: Mapping[str, object],
    path: str,
    collector: DiagnosticCollector,
) -> None:
    for key, predicate in (
        ("minimum", lambda left, right: left < right),
        ("maximum", lambda left, right: left > right),
    ):
        bound = rules.get(key)
        if isinstance(bound, (int, str)) and not isinstance(bound, bool):
            try:
                if predicate(actual, Decimal(bound)):
                    collector.add(path, f"constraint.{key}", f"value violates {key}")
            except InvalidOperation:
                pass


def _check_static_union(
    variants: tuple[ValueShape, ...], path: str, collector: DiagnosticCollector
) -> None:
    scalar_kinds = [
        item.scalar_kind for item in variants if item.kind is ShapeKind.SCALAR
    ]
    if ScalarKind.JSON in scalar_kinds:
        collector.add(
            path,
            "union.ambiguous_static",
            "explicit json overlaps every other union variant",
        )


def _validate_shape_schema(
    shape: ValueShape, path: str, collector: DiagnosticCollector
) -> None:
    if shape.kind is ShapeKind.UNION:
        _check_static_union(shape.variants, path, collector)
        for index, variant in enumerate(shape.variants):
            _validate_shape_schema(variant, f"{path}.variants[{index}]", collector)
    elif shape.kind is ShapeKind.LIST:
        assert shape.element is not None
        _validate_shape_schema(shape.element, f"{path}.element", collector)
    elif shape.kind is ShapeKind.MAP:
        assert shape.map_value is not None
        _validate_shape_schema(shape.map_value, f"{path}.map_value", collector)


__all__ = ["validate_schema_bundle", "validate_typed_value"]
