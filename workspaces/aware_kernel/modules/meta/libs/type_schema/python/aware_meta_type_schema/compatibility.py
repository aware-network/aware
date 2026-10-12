from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from .model import FieldDefinition, TypeDefinition, TypeKind, TypeSchemaBundle

_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


@dataclass(frozen=True, slots=True, order=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> SemanticVersion:
        if not isinstance(value, str):
            raise TypeError("semantic version must be text")
        match = _SEMVER.fullmatch(value)
        if match is None:
            raise ValueError("semantic version must be exact major.minor.patch")
        return cls(*(int(item) for item in match.groups()))


class TypeSchemaCompatibilityOutcome(StrEnum):
    EQUIVALENT = "equivalent"
    BACKWARD_COMPATIBLE = "backward_compatible"
    FORWARD_COMPATIBLE = "forward_compatible"
    MIGRATION_REQUIRED = "migration_required"
    INCOMPATIBLE = "incompatible"


class TypeSchemaCompatibilityImpact(StrEnum):
    BACKWARD = "backward"
    FORWARD = "forward"
    MIGRATION = "migration"
    INCOMPATIBLE = "incompatible"


@dataclass(frozen=True, slots=True, order=True)
class TypeSchemaCompatibilityChange:
    path: str
    code: str
    message: str
    impact: TypeSchemaCompatibilityImpact


@dataclass(frozen=True, slots=True)
class TypeSchemaCompatibilityReport:
    outcome: TypeSchemaCompatibilityOutcome
    previous_digest: str
    candidate_digest: str
    previous_version: SemanticVersion | None
    candidate_version: SemanticVersion | None
    changes: tuple[TypeSchemaCompatibilityChange, ...]


def compare_type_schemas(
    previous: TypeSchemaBundle, candidate: TypeSchemaBundle
) -> TypeSchemaCompatibilityReport:
    if not isinstance(previous, TypeSchemaBundle) or not isinstance(
        candidate, TypeSchemaBundle
    ):
        raise TypeError("previous and candidate must be TypeSchemaBundle")
    changes: list[TypeSchemaCompatibilityChange] = []
    previous_version = _version(previous.semantic_version, "previous", changes)
    candidate_version = _version(candidate.semantic_version, "candidate", changes)
    if previous.namespace != candidate.namespace:
        _change(
            changes,
            "$.namespace",
            "namespace.changed",
            "candidate namespace differs from previous namespace",
            TypeSchemaCompatibilityImpact.INCOMPATIBLE,
        )
    if previous_version is not None and candidate_version is not None:
        if candidate_version < previous_version:
            _change(
                changes,
                "$.semantic_version",
                "version.regressed",
                "candidate semantic version regresses",
                TypeSchemaCompatibilityImpact.INCOMPATIBLE,
            )
        elif (
            candidate_version == previous_version
            and candidate.schema_digest != previous.schema_digest
        ):
            _change(
                changes,
                "$.semantic_version",
                "version.reused",
                "one semantic version cannot identify different schema meaning",
                TypeSchemaCompatibilityImpact.INCOMPATIBLE,
            )
    if previous.schema_digest != candidate.schema_digest:
        _compare_types(previous, candidate, changes)
    changes = sorted(set(changes))
    outcome = _outcome(changes)
    return TypeSchemaCompatibilityReport(
        outcome,
        previous.schema_digest,
        candidate.schema_digest,
        previous_version,
        candidate_version,
        tuple(changes),
    )


def _version(
    value: str,
    label: str,
    changes: list[TypeSchemaCompatibilityChange],
) -> SemanticVersion | None:
    try:
        return SemanticVersion.parse(value)
    except (TypeError, ValueError):
        _change(
            changes,
            "$.semantic_version",
            f"version.{label}_invalid",
            f"{label} semantic version is not exact major.minor.patch",
            TypeSchemaCompatibilityImpact.INCOMPATIBLE,
        )
        return None


def _compare_types(
    previous: TypeSchemaBundle,
    candidate: TypeSchemaBundle,
    changes: list[TypeSchemaCompatibilityChange],
) -> None:
    old = {item.type_ref: item for item in previous.types}
    new = {item.type_ref: item for item in candidate.types}
    for ref in sorted(old.keys() - new.keys()):
        _change(
            changes,
            f"$.types[{ref!r}]",
            "type.removed",
            "type removed",
            TypeSchemaCompatibilityImpact.FORWARD,
        )
    for ref in sorted(new.keys() - old.keys()):
        _change(
            changes,
            f"$.types[{ref!r}]",
            "type.added",
            "type added",
            TypeSchemaCompatibilityImpact.BACKWARD,
        )
    for ref in sorted(old.keys() & new.keys()):
        _compare_type(old[ref], new[ref], f"$.types[{ref!r}]", changes)


def _compare_type(
    previous: TypeDefinition,
    candidate: TypeDefinition,
    path: str,
    changes: list[TypeSchemaCompatibilityChange],
) -> None:
    if previous.kind is not candidate.kind:
        _change(
            changes,
            f"{path}.kind",
            "type.kind_changed",
            "stable type ref changed kind",
            TypeSchemaCompatibilityImpact.INCOMPATIBLE,
        )
        return
    _compare_name_aliases(
        previous.name,
        previous.aliases,
        candidate.name,
        candidate.aliases,
        path,
        "type",
        changes,
    )
    if previous.constraints != candidate.constraints:
        _change(
            changes,
            f"{path}.constraints",
            "type.constraints_changed",
            "type constraints changed",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )
    if previous.identity != candidate.identity:
        _change(
            changes,
            f"{path}.identity",
            "type.identity_changed",
            "identity metadata changed",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )
    if previous.discriminant_field_ref != candidate.discriminant_field_ref:
        _change(
            changes,
            f"{path}.discriminant_field_ref",
            "type.discriminant_changed",
            "union discriminant changed",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )
    if previous.kind in (TypeKind.VALUE_OBJECT, TypeKind.GRAPH_OBJECT):
        _compare_fields(previous.fields, candidate.fields, path, changes)
    elif previous.kind is TypeKind.ENUM:
        _compare_enum(previous, candidate, path, changes)
    elif previous.kind is TypeKind.UNION:
        _compare_variants(previous, candidate, path, changes)
    elif previous.scalar_target is not candidate.scalar_target:
        _change(
            changes,
            f"{path}.scalar_target",
            "type.scalar_target_changed",
            "scalar alias target changed",
            TypeSchemaCompatibilityImpact.INCOMPATIBLE,
        )


def _compare_fields(
    previous: tuple[FieldDefinition, ...],
    candidate: tuple[FieldDefinition, ...],
    type_path: str,
    changes: list[TypeSchemaCompatibilityChange],
) -> None:
    old = {item.field_ref: item for item in previous}
    new = {item.field_ref: item for item in candidate}
    for ref in sorted(old.keys() - new.keys()):
        _change(
            changes,
            f"{type_path}.fields[{ref!r}]",
            "field.removed",
            "field removed",
            TypeSchemaCompatibilityImpact.FORWARD,
        )
    for ref in sorted(new.keys() - old.keys()):
        field = new[ref]
        impact = (
            TypeSchemaCompatibilityImpact.MIGRATION
            if field.required and field.default_value is None
            else TypeSchemaCompatibilityImpact.BACKWARD
        )
        _change(
            changes,
            f"{type_path}.fields[{ref!r}]",
            "field.required_added"
            if impact is TypeSchemaCompatibilityImpact.MIGRATION
            else "field.optional_added",
            "required field without default added"
            if impact is TypeSchemaCompatibilityImpact.MIGRATION
            else "optional or defaulted field added",
            impact,
        )
    for ref in sorted(old.keys() & new.keys()):
        _compare_field(old[ref], new[ref], f"{type_path}.fields[{ref!r}]", changes)


def _compare_field(
    previous: FieldDefinition,
    candidate: FieldDefinition,
    path: str,
    changes: list[TypeSchemaCompatibilityChange],
) -> None:
    _compare_name_aliases(
        previous.name,
        previous.aliases,
        candidate.name,
        candidate.aliases,
        path,
        "field",
        changes,
    )
    if previous.shape != candidate.shape:
        _change(
            changes,
            f"{path}.shape",
            "field.shape_changed",
            "field value shape changed",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )
    if previous.required and not candidate.required:
        _change(
            changes,
            f"{path}.required",
            "field.required_relaxed",
            "required field became optional",
            TypeSchemaCompatibilityImpact.BACKWARD,
        )
    elif not previous.required and candidate.required:
        _change(
            changes,
            f"{path}.required",
            "field.required_tightened",
            "optional field became required",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )
    if not previous.nullable and candidate.nullable:
        _change(
            changes,
            f"{path}.nullable",
            "field.nullable_relaxed",
            "field now accepts null",
            TypeSchemaCompatibilityImpact.BACKWARD,
        )
    elif previous.nullable and not candidate.nullable:
        _change(
            changes,
            f"{path}.nullable",
            "field.nullable_tightened",
            "nullable field became non-nullable",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )
    if previous.default_value != candidate.default_value:
        _change(
            changes,
            f"{path}.default_value",
            "field.default_changed",
            "field default changed",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )
    if previous.constraints != candidate.constraints:
        _change(
            changes,
            f"{path}.constraints",
            "field.constraints_changed",
            "field constraints changed",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )


def _compare_name_aliases(
    previous_name: str,
    previous_aliases: tuple[str, ...],
    candidate_name: str,
    candidate_aliases: tuple[str, ...],
    path: str,
    prefix: str,
    changes: list[TypeSchemaCompatibilityChange],
) -> None:
    if previous_name != candidate_name:
        impact = (
            TypeSchemaCompatibilityImpact.BACKWARD
            if previous_name in candidate_aliases
            else TypeSchemaCompatibilityImpact.MIGRATION
        )
        _change(
            changes,
            f"{path}.name",
            f"{prefix}.renamed_with_alias"
            if impact is TypeSchemaCompatibilityImpact.BACKWARD
            else f"{prefix}.renamed",
            "wire name changed with predecessor alias"
            if impact is TypeSchemaCompatibilityImpact.BACKWARD
            else "wire name changed without predecessor alias",
            impact,
        )
    added = set(candidate_aliases) - set(previous_aliases)
    removed = set(previous_aliases) - set(candidate_aliases)
    if added:
        _change(
            changes,
            f"{path}.aliases",
            f"{prefix}.aliases_added",
            f"accepted aliases added: {sorted(added)!r}",
            TypeSchemaCompatibilityImpact.BACKWARD,
        )
    if removed:
        _change(
            changes,
            f"{path}.aliases",
            f"{prefix}.aliases_removed",
            f"accepted aliases removed: {sorted(removed)!r}",
            TypeSchemaCompatibilityImpact.FORWARD,
        )


def _compare_enum(
    previous: TypeDefinition,
    candidate: TypeDefinition,
    path: str,
    changes: list[TypeSchemaCompatibilityChange],
) -> None:
    added = set(candidate.enum_values) - set(previous.enum_values)
    removed = set(previous.enum_values) - set(candidate.enum_values)
    if added:
        _change(
            changes,
            f"{path}.enum_values",
            "enum.values_added",
            f"enum values added: {sorted(added)!r}",
            TypeSchemaCompatibilityImpact.BACKWARD,
        )
    if removed:
        _change(
            changes,
            f"{path}.enum_values",
            "enum.values_removed",
            f"enum values removed: {sorted(removed)!r}",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )


def _compare_variants(
    previous: TypeDefinition,
    candidate: TypeDefinition,
    path: str,
    changes: list[TypeSchemaCompatibilityChange],
) -> None:
    added = set(candidate.union_variants) - set(previous.union_variants)
    removed = set(previous.union_variants) - set(candidate.union_variants)
    if added:
        _change(
            changes,
            f"{path}.union_variants",
            "union.variants_added",
            "union variants added",
            TypeSchemaCompatibilityImpact.BACKWARD,
        )
    if removed:
        _change(
            changes,
            f"{path}.union_variants",
            "union.variants_removed",
            "union variants removed",
            TypeSchemaCompatibilityImpact.MIGRATION,
        )


def _outcome(
    changes: list[TypeSchemaCompatibilityChange],
) -> TypeSchemaCompatibilityOutcome:
    impacts = {item.impact for item in changes}
    if TypeSchemaCompatibilityImpact.INCOMPATIBLE in impacts:
        return TypeSchemaCompatibilityOutcome.INCOMPATIBLE
    if TypeSchemaCompatibilityImpact.MIGRATION in impacts or {
        TypeSchemaCompatibilityImpact.BACKWARD,
        TypeSchemaCompatibilityImpact.FORWARD,
    }.issubset(impacts):
        return TypeSchemaCompatibilityOutcome.MIGRATION_REQUIRED
    if TypeSchemaCompatibilityImpact.BACKWARD in impacts:
        return TypeSchemaCompatibilityOutcome.BACKWARD_COMPATIBLE
    if TypeSchemaCompatibilityImpact.FORWARD in impacts:
        return TypeSchemaCompatibilityOutcome.FORWARD_COMPATIBLE
    return TypeSchemaCompatibilityOutcome.EQUIVALENT


def _change(
    changes: list[TypeSchemaCompatibilityChange],
    path: str,
    code: str,
    message: str,
    impact: TypeSchemaCompatibilityImpact,
) -> None:
    changes.append(TypeSchemaCompatibilityChange(path, code, message, impact))


__all__ = [
    "SemanticVersion",
    "TypeSchemaCompatibilityChange",
    "TypeSchemaCompatibilityImpact",
    "TypeSchemaCompatibilityOutcome",
    "TypeSchemaCompatibilityReport",
    "compare_type_schemas",
]
