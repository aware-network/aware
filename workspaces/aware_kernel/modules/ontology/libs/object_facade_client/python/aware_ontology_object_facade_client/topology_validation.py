"""Owning v5 topology semantic validation; no nominal admission or execution."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

from aware_meta_type_schema import (
    FieldDefinition as SchemaFieldDefinition,
)
from aware_meta_type_schema import (
    ShapeKind,
    TypeKind,
    TypeSchemaSlice,
    ValueShape,
)

from .owner_values import (
    ActionValueMode,
    Cardinality,
    RelationshipEndpointResidence,
    SchemaTopologyInputGrade,
    _TopologyMeta,
    digest_payload,
)
from .topology_values import (
    SCHEMA_TOPOLOGY_CONTRACT,
    AssociationEndpointRoleInput,
    GraphIdentityMode,
    SchemaFieldRelationshipInput,
    SchemaOntologyRuntimeTopology,
    _revalidate,
)


def _call(operation: Any, /, *args: Any, **kwargs: Any) -> Any:
    return operation(*args, **kwargs)


@dataclass(frozen=True, slots=True)
class ValidationIssue(metaclass=_TopologyMeta):
    path: str
    message: str


class OntologyRuntimeValidationError(ValueError, metaclass=_TopologyMeta):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = _call(tuple, issues)
        _call(
            BaseException.__init__,
            self,
            _call("; ".join, (f"{issue.path}: {issue.message}" for issue in issues)),
        )


def _raise(issues: list[ValidationIssue]) -> None:
    if issues:
        raise _call(OntologyRuntimeValidationError, issues)


def _duplicates(values: list[str]) -> set[str]:
    counts = {}
    for value in values:
        counts[value] = _call(counts.get, value, 0) + 1
    return {value for value, count in _call(counts.items) if count > 1}


def _shape_refs(shape: ValueShape | None) -> frozenset[str]:
    return _call(frozenset) if shape is None else _call(shape.referenced_type_refs)


def validate_schema_topology(
    topology: SchemaOntologyRuntimeTopology, schema_slice: TypeSchemaSlice
) -> None:
    topology = _call(_revalidate, topology)
    schema_slice = _call(_revalidate, schema_slice)
    issues: list[ValidationIssue] = []
    if topology.schema_digest != schema_slice.bundle_digest:
        _call(
            issues.append,
            _call(ValidationIssue, "schema_digest", "bundle digest mismatch"),
        )
    if topology.schema_slice_digest != schema_slice.slice_digest:
        _call(
            issues.append,
            _call(ValidationIssue, "schema_slice_digest", "slice digest mismatch"),
        )
    if topology.schema_root_type_refs != schema_slice.root_type_refs:
        _call(
            issues.append,
            _call(ValidationIssue, "schema_root_type_refs", "slice roots mismatch"),
        )
    if topology.input_grade is not SchemaTopologyInputGrade.PORTABLE_INPUT:
        _call(
            issues.append,
            _call(
                ValidationIssue, "input_grade", "topology must remain portable_input"
            ),
        )
    expected = _call(
        digest_payload, SCHEMA_TOPOLOGY_CONTRACT, _call(topology._wire_payload)
    )
    if topology.topology_digest != expected:
        _call(
            issues.append, _call(ValidationIssue, "topology_digest", "digest mismatch")
        )
    types = {value.type_ref: value for value in schema_slice.types}
    bindings = {value.type_ref: value for value in topology.graph_types}
    relationships = {value.relationship_ref: value for value in topology.relationships}
    actions = {value.action_ref: value for value in topology.actions}
    for path, refs in (
        ("graph_types", [value.type_ref for value in topology.graph_types]),
        ("relationships", [value.relationship_ref for value in topology.relationships]),
        ("projections", [value.projection_ref for value in topology.projections]),
        ("actions", [value.action_ref for value in topology.actions]),
    ):
        for duplicate in _call(sorted, _call(_duplicates, refs)):
            _call(
                issues.append,
                _call(ValidationIssue, path, f"duplicate ref {duplicate}"),
            )
    all_field_refs: dict[str, tuple[str, SchemaFieldDefinition]] = {}
    for type_ref, definition in _call(types.items):
        for field in definition.fields:
            if field.field_ref in all_field_refs:
                _call(
                    issues.append,
                    _call(ValidationIssue, field.field_ref, "field ref reused"),
                )
            all_field_refs[field.field_ref] = (type_ref, field)
    for binding in topology.graph_types:
        definition = _call(types.get, binding.type_ref)
        if definition is None or definition.kind is not TypeKind.GRAPH_OBJECT:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    binding.type_ref,
                    "graph binding requires schema graph_object type",
                ),
            )
            continue
        fields = {value.field_ref: value for value in definition.fields}
        for field_ref in (
            *binding.identity_field_refs,
            *binding.schema_relationship_field_refs,
        ):
            if field_ref not in fields:
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        binding.type_ref,
                        f"unknown schema field {field_ref}",
                    ),
                )
        for field_ref in binding.identity_field_refs:
            field = _call(fields.get, field_ref)
            if field is not None and (not field.required or field.nullable):
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        field_ref,
                        "graph identity must be required and non-nullable",
                    ),
                )
        if _call(set, binding.identity_field_refs) & _call(
            set, binding.schema_relationship_field_refs
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue, binding.type_ref, "identity cannot be edge-backed"
                ),
            )
        authored_identity_refs = (
            () if definition.identity is None else definition.identity.field_refs
        )
        if binding.identity_mode is GraphIdentityMode.SCHEMA_FIELDS:
            if binding.identity_field_refs != authored_identity_refs:
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        binding.type_ref,
                        "schema_fields identity must equal authored schema identity",
                    ),
                )
        elif authored_identity_refs:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    binding.type_ref,
                    "instance_ref identity requires absent authored schema identity",
                ),
            )
    schema_relationships = {
        value.relationship_ref: value
        for value in topology.relationships
        if _call(isinstance, value, SchemaFieldRelationshipInput)
    }
    association_roles = {
        value.relationship_ref: value
        for value in topology.relationships
        if _call(isinstance, value, AssociationEndpointRoleInput)
    }
    for relationship in _call(schema_relationships.values):
        if relationship.source_type_ref not in bindings:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    relationship.relationship_ref,
                    "relationship source must be graph-bound",
                ),
            )
        if (
            relationship.endpoint_residence
            is RelationshipEndpointResidence.RESIDENT_TARGET
            and relationship.target_type_ref not in bindings
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    relationship.relationship_ref,
                    "resident schema-field target must be graph-bound",
                ),
            )
        if (
            relationship.endpoint_residence
            is RelationshipEndpointResidence.EXTERNAL_DEPENDENCY
            and relationship.target_type_ref in bindings
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    relationship.relationship_ref,
                    "external schema-field target must not become a graph binding",
                ),
            )
        owner_field = _call(all_field_refs.get, relationship.relationship_ref)
        source = _call(bindings.get, relationship.source_type_ref)
        if owner_field is None or owner_field[0] != relationship.source_type_ref:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    relationship.relationship_ref,
                    "relationship must bind its source schema field",
                ),
            )
        elif (
            source is None
            or relationship.relationship_ref
            not in source.schema_relationship_field_refs
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    relationship.relationship_ref,
                    "schema field is not declared edge-backed",
                ),
            )
        else:
            shape = owner_field[1].shape
            repeated = shape.kind is ShapeKind.LIST
            target_shape = shape.element if repeated else shape
            if (
                target_shape is None
                or target_shape.kind is not ShapeKind.NAMED
                or target_shape.type_ref != relationship.target_type_ref
            ):
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        relationship.relationship_ref,
                        "edge target does not match schema shape",
                    ),
                )
            expected_cardinality = (
                Cardinality.MANY
                if repeated
                else Cardinality.OPTIONAL_ONE
                if owner_field[1].nullable
                else Cardinality.ONE
            )
            if relationship.source_cardinality is not expected_cardinality:
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        relationship.relationship_ref,
                        "edge cardinality does not match schema field",
                    ),
                )
    edge_refs = {
        ref
        for value in topology.graph_types
        for ref in value.schema_relationship_field_refs
    }
    if edge_refs != _call(set, schema_relationships):
        _call(
            issues.append,
            _call(
                ValidationIssue,
                "relationships",
                "schema relationship fields and inputs must match exactly",
            ),
        )
    role_refs = {
        ref for value in topology.graph_types for ref in value.association_role_refs
    }
    if role_refs != _call(set, association_roles):
        _call(
            issues.append,
            _call(
                ValidationIssue,
                "relationships",
                "association role bindings and inputs must match exactly",
            ),
        )
    if edge_refs & role_refs:
        _call(
            issues.append,
            _call(
                ValidationIssue,
                "relationships",
                "schema relationship and association role refs must be disjoint",
            ),
        )
    for role in _call(association_roles.values):
        source = _call(bindings.get, role.source_type_ref)
        association = _call(bindings.get, role.association_type_ref)
        if source is None:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "association source is not graph-bound",
                ),
            )
        if association is None:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "association type is not graph-bound",
                ),
            )
        elif role.role_ref not in association.association_role_refs:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "association type does not list role",
                ),
            )
        target_definition = _call(types.get, role.target_type_ref)
        if target_definition is None:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "association target lacks schema evidence",
                ),
            )
        elif target_definition.kind is not TypeKind.GRAPH_OBJECT:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "association target must be schema graph_object",
                ),
            )
        owner_field = _call(all_field_refs.get, role.source_field_ref)
        if owner_field is None or owner_field[0] != role.source_type_ref:
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "association source field is not exact",
                ),
            )
        else:
            field = owner_field[1]
            shape = field.shape
            repeated = shape.kind is ShapeKind.LIST
            target_shape = shape.element if repeated else shape
            if (
                target_shape is None
                or target_shape.kind is not ShapeKind.NAMED
                or target_shape.type_ref != role.target_type_ref
            ):
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        role.role_ref,
                        "association endpoint target does not match schema field",
                    ),
                )
            expected_cardinality = (
                Cardinality.MANY
                if repeated
                else Cardinality.ONE
                if field.required and (not field.nullable)
                else Cardinality.OPTIONAL_ONE
            )
            if role.endpoint_cardinality is not expected_cardinality:
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        role.role_ref,
                        "association endpoint cardinality does not match schema field",
                    ),
                )
        if (
            role.endpoint_residence is RelationshipEndpointResidence.RESIDENT_TARGET
            and role.target_type_ref not in bindings
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "resident association target must be graph-bound",
                ),
            )
        if (
            role.endpoint_residence is RelationshipEndpointResidence.EXTERNAL_DEPENDENCY
            and role.target_type_ref in bindings
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    role.role_ref,
                    "external association target must not become a graph binding",
                ),
            )
    for action in topology.actions:
        if action.target_type_ref not in bindings:
            _call(
                issues.append,
                _call(ValidationIssue, action.action_ref, "unknown action target"),
            )
        if not _call(_call(set, action.mutation_type_refs).issubset, bindings):
            _call(
                issues.append,
                _call(ValidationIssue, action.action_ref, "unknown mutation type"),
            )
        if _call(
            _duplicates, [value.parameter_ref for value in action.parameters]
        ) or _call(
            _duplicates, [_call(str, value.position) for value in action.parameters]
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    action.action_ref,
                    "duplicate parameter ref or position",
                ),
            )
        for parameter in action.parameters:
            for ref in _call(_shape_refs, parameter.shape):
                if ref not in types:
                    _call(
                        issues.append,
                        _call(
                            ValidationIssue,
                            parameter.parameter_ref,
                            f"shape ref outside slice: {ref}",
                        ),
                    )
            if parameter.value_mode is ActionValueMode.INSTANCE_REF and (
                not _call(_shape_is_graph_ref, parameter.shape, bindings)
            ):
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        parameter.parameter_ref,
                        "instance_ref mode requires one graph type shape",
                    ),
                )
        for ref in _call(_shape_refs, action.result_shape):
            if ref not in types:
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        action.action_ref,
                        f"result ref outside slice: {ref}",
                    ),
                )
        if (
            action.result_shape is None
            and action.result_value_mode is ActionValueMode.INSTANCE_REF
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    action.action_ref,
                    "void result cannot use instance_ref mode",
                ),
            )
        if (
            action.result_shape is not None
            and action.result_value_mode is ActionValueMode.INSTANCE_REF
            and (not _call(_shape_is_graph_ref, action.result_shape, bindings))
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    action.action_ref,
                    "instance_ref result requires graph type shape",
                ),
            )
    for projection in topology.projections:
        if not _call(
            _call(set, projection.root_type_refs).issubset, projection.type_refs
        ):
            _call(
                issues.append,
                _call(
                    ValidationIssue,
                    projection.projection_ref,
                    "roots must be included types",
                ),
            )
        if not _call(_call(set, projection.type_refs).issubset, bindings):
            _call(
                issues.append,
                _call(ValidationIssue, projection.projection_ref, "unknown graph type"),
            )
        for field_ref in projection.field_refs:
            owner = _call(all_field_refs.get, field_ref)
            if (
                owner is None
                or owner[0] not in projection.type_refs
                or field_ref in edge_refs
            ):
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        projection.projection_ref,
                        f"invalid resident field {field_ref}",
                    ),
                )
        for relationship_ref in projection.relationship_refs:
            relationship = _call(relationships.get, relationship_ref)
            if relationship is None:
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        projection.projection_ref,
                        "unknown relationship",
                    ),
                )
            elif _call(isinstance, relationship, SchemaFieldRelationshipInput):
                if relationship.source_type_ref not in projection.type_refs:
                    _call(
                        issues.append,
                        _call(
                            ValidationIssue,
                            projection.projection_ref,
                            f"relationship source outside projection: {relationship_ref}",
                        ),
                    )
                if (
                    relationship.endpoint_residence
                    is RelationshipEndpointResidence.RESIDENT_TARGET
                    and relationship.target_type_ref not in projection.type_refs
                ):
                    _call(
                        issues.append,
                        _call(
                            ValidationIssue,
                            projection.projection_ref,
                            f"resident relationship target outside projection: {relationship_ref}",
                        ),
                    )
            elif (
                relationship.selecting_projection_ref != projection.projection_ref
                or relationship.source_type_ref not in projection.type_refs
                or relationship.association_type_ref not in projection.type_refs
            ):
                _call(
                    issues.append,
                    _call(
                        ValidationIssue,
                        projection.projection_ref,
                        f"association role escapes selecting projection: {relationship_ref}",
                    ),
                )
        if not _call(_call(set, projection.action_refs).issubset, actions):
            _call(
                issues.append,
                _call(ValidationIssue, projection.projection_ref, "unknown action"),
            )
    _call(_raise, issues)


def _shape_is_graph_ref(shape: ValueShape, bindings: Collection[str]) -> bool:
    return (
        shape.kind is ShapeKind.NAMED
        and shape.type_ref is not None
        and (shape.type_ref in bindings)
    )
