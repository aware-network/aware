from __future__ import annotations

# pyright: reportImportCycles=false
import json
from collections.abc import Mapping, Sequence
from typing import Any

from aware_meta_type_schema import TypeSchemaSlice, ValueShape

from .owner_values import (
    Cardinality,
    MutationScope,
    ProjectionDefinition,
    RelationshipKind,
    TraversalPolicy,
    _TopologyMeta,
    canonical_json,
)
from .topology_validation import validate_schema_topology
from .topology_values import (
    SCHEMA_TOPOLOGY_CONTRACT,
    ActionValueMode,
    AssociationEndpointDirection,
    AssociationEndpointRoleInput,
    GraphIdentityMode,
    GraphTypeBinding,
    RelationshipEndpointResidence,
    SchemaActionDefinition,
    SchemaActionParameterDefinition,
    SchemaFieldRelationshipInput,
    SchemaOntologyRuntimeTopology,
    SchemaRelationshipInputKind,
    SchemaTopologyInputGrade,
    SchemaTopologyRelationshipInput,
    _revalidate,
)

SUPPORTED_SCHEMA_TOPOLOGY_CONTRACTS = (SCHEMA_TOPOLOGY_CONTRACT,)


def _call(operation: Any, /, *args: Any, **kwargs: Any) -> Any:
    # Replaced by the sealed dispatcher during owner initialization.
    return operation(*args, **kwargs)


def _lower_shape(value: object, path: str) -> ValueShape:
    raise TypeError("owning Meta decoder is not initialized")


class SchemaTopologyManifestDecodeError(ValueError, metaclass=_TopologyMeta):
    pass


def negotiate_schema_topology_contract(
    offered_contracts: Sequence[str],
    *,
    supported_contracts: Sequence[str] = SUPPORTED_SCHEMA_TOPOLOGY_CONTRACTS,
) -> str:
    offered = _call(_tokens, offered_contracts, "offered_contracts")
    supported = _call(_tokens, supported_contracts, "supported_contracts")
    for contract in supported:
        if contract in offered:
            return contract
    raise _call(
        SchemaTopologyManifestDecodeError,
        f"no supported schema topology contract; offered={_call(list, offered)!r}, supported={_call(list, supported)!r}",
    )


def encode_schema_topology_manifest(
    topology: SchemaOntologyRuntimeTopology, schema_slice: TypeSchemaSlice
) -> bytes:
    topology = _call(_revalidate, topology)
    schema_slice = _call(_revalidate, schema_slice)
    _call(validate_schema_topology, topology, schema_slice)
    return _call(_call(canonical_json, _call(topology.to_wire)).encode)


def decode_schema_topology_manifest(
    payload: bytes | str,
    schema_slice: TypeSchemaSlice,
    *,
    supported_contracts: Sequence[str] = SUPPORTED_SCHEMA_TOPOLOGY_CONTRACTS,
) -> SchemaOntologyRuntimeTopology:
    root = _call(_root, payload)
    _call(
        _exact,
        root,
        {
            "contract",
            "namespace",
            "semantic_version",
            "schema_digest",
            "schema_slice_digest",
            "schema_root_type_refs",
            "graph_types",
            "relationships",
            "projections",
            "actions",
            "input_grade",
            "topology_digest",
        },
        "$",
    )
    contract = _call(_text, root, "contract", "$")
    _call(
        negotiate_schema_topology_contract,
        (contract,),
        supported_contracts=supported_contracts,
    )
    if contract != SCHEMA_TOPOLOGY_CONTRACT:
        raise _call(
            SchemaTopologyManifestDecodeError,
            f"decoder does not implement {contract!r}",
        )
    try:
        topology = _call(
            SchemaOntologyRuntimeTopology,
            namespace=_call(_text, root, "namespace", "$"),
            semantic_version=_call(_text, root, "semantic_version", "$"),
            schema_digest=_call(_text, root, "schema_digest", "$"),
            schema_slice_digest=_call(_text, root, "schema_slice_digest", "$"),
            schema_root_type_refs=_call(
                _text_array, root, "schema_root_type_refs", "$"
            ),
            graph_types=_call(
                tuple,
                (
                    _call(_decode_graph_type, value, f"$.graph_types[{index}]")
                    for index, value in _call(
                        enumerate, _call(_array, root, "graph_types", "$")
                    )
                ),
            ),
            relationships=_call(
                tuple,
                (
                    _call(_decode_relationship, value, f"$.relationships[{index}]")
                    for index, value in _call(
                        enumerate, _call(_array, root, "relationships", "$")
                    )
                ),
            ),
            projections=_call(
                tuple,
                (
                    _call(_decode_projection, value, f"$.projections[{index}]")
                    for index, value in _call(
                        enumerate, _call(_array, root, "projections", "$")
                    )
                ),
            ),
            actions=_call(
                tuple,
                (
                    _call(_decode_action, value, f"$.actions[{index}]")
                    for index, value in _call(
                        enumerate, _call(_array, root, "actions", "$")
                    )
                ),
            ),
            input_grade=_call(
                SchemaTopologyInputGrade, _call(_text, root, "input_grade", "$")
            ),
            topology_digest=_call(_text, root, "topology_digest", "$"),
        )
        _call(validate_schema_topology, topology, schema_slice)
        return topology
    except (TypeError, ValueError) as error:
        if _call(isinstance, error, SchemaTopologyManifestDecodeError):
            raise
        raise _call(
            SchemaTopologyManifestDecodeError, f"manifest violates {contract}: {error}"
        ) from error


def _decode_graph_type(value: object, path: str) -> GraphTypeBinding:
    item = _call(_object, value, path)
    _call(
        _exact,
        item,
        {
            "type_ref",
            "identity_mode",
            "identity_field_refs",
            "schema_relationship_field_refs",
            "association_role_refs",
        },
        path,
    )
    return _call(
        GraphTypeBinding,
        type_ref=_call(_text, item, "type_ref", path),
        identity_mode=_call(
            GraphIdentityMode, _call(_text, item, "identity_mode", path)
        ),
        identity_field_refs=_call(_text_array, item, "identity_field_refs", path),
        schema_relationship_field_refs=_call(
            _text_array, item, "schema_relationship_field_refs", path
        ),
        association_role_refs=_call(_text_array, item, "association_role_refs", path),
    )


def _decode_relationship(value: object, path: str) -> SchemaTopologyRelationshipInput:
    item = _call(_object, value, path)
    input_kind = _call(
        SchemaRelationshipInputKind, _call(_text, item, "input_kind", path)
    )
    if input_kind is SchemaRelationshipInputKind.SCHEMA_FIELD_RELATIONSHIP:
        _call(
            _exact,
            item,
            {
                "input_kind",
                "relationship_ref",
                "source_type_ref",
                "target_type_ref",
                "target_package_ref",
                "source_cardinality",
                "target_cardinality",
                "relationship_kind",
                "traversal",
                "endpoint_residence",
                "schema_evidence_ref",
            },
            path,
        )
        return _call(
            SchemaFieldRelationshipInput,
            _call(_text, item, "relationship_ref", path),
            _call(_text, item, "source_type_ref", path),
            _call(_text, item, "target_type_ref", path),
            _call(_text, item, "target_package_ref", path),
            _call(Cardinality, _call(_text, item, "source_cardinality", path)),
            _call(Cardinality, _call(_text, item, "target_cardinality", path)),
            _call(RelationshipKind, _call(_text, item, "relationship_kind", path)),
            _call(TraversalPolicy, _call(_text, item, "traversal", path)),
            _call(
                RelationshipEndpointResidence,
                _call(_text, item, "endpoint_residence", path),
            ),
            _call(_text, item, "schema_evidence_ref", path),
            input_kind,
        )
    _call(
        _exact,
        item,
        {
            "input_kind",
            "role_ref",
            "source_type_ref",
            "source_field_ref",
            "association_type_ref",
            "target_type_ref",
            "target_package_ref",
            "endpoint_residence",
            "member_name",
            "direction",
            "endpoint_cardinality",
            "relationship_semantics",
            "traversal",
            "selecting_projection_ref",
            "projection_role_coordinate",
            "meaning_resolution_digest",
            "association_role_digest",
            "schema_evidence_ref",
        },
        path,
    )
    return _call(
        AssociationEndpointRoleInput,
        _call(_text, item, "role_ref", path),
        _call(_text, item, "source_type_ref", path),
        _call(_text, item, "source_field_ref", path),
        _call(_text, item, "association_type_ref", path),
        _call(_text, item, "target_type_ref", path),
        _call(_text, item, "target_package_ref", path),
        _call(
            RelationshipEndpointResidence,
            _call(_text, item, "endpoint_residence", path),
        ),
        _call(_text, item, "member_name", path),
        _call(AssociationEndpointDirection, _call(_text, item, "direction", path)),
        _call(Cardinality, _call(_text, item, "endpoint_cardinality", path)),
        _call(RelationshipKind, _call(_text, item, "relationship_semantics", path)),
        _call(TraversalPolicy, _call(_text, item, "traversal", path)),
        _call(_text, item, "selecting_projection_ref", path),
        _call(_text, item, "projection_role_coordinate", path),
        _call(_text, item, "meaning_resolution_digest", path),
        _call(_text, item, "association_role_digest", path),
        _call(_text, item, "schema_evidence_ref", path),
        input_kind,
    )


def _decode_projection(value: object, path: str) -> ProjectionDefinition:
    item = _call(_object, value, path)
    _call(
        _exact,
        item,
        {
            "projection_ref",
            "root_type_refs",
            "type_refs",
            "field_refs",
            "relationship_refs",
            "action_refs",
        },
        path,
    )
    return _call(
        ProjectionDefinition,
        _call(_text, item, "projection_ref", path),
        _call(_text_array, item, "root_type_refs", path),
        _call(_text_array, item, "type_refs", path),
        _call(_text_array, item, "field_refs", path),
        _call(_text_array, item, "relationship_refs", path),
        _call(_text_array, item, "action_refs", path),
    )


def _decode_action(value: object, path: str) -> SchemaActionDefinition:
    item = _call(_object, value, path)
    _call(
        _exact,
        item,
        {
            "action_ref",
            "target_type_ref",
            "parameters",
            "result_shape",
            "result_value_mode",
            "mutation_scope",
            "mutation_type_refs",
        },
        path,
    )
    result_shape = item["result_shape"]
    return _call(
        SchemaActionDefinition,
        _call(_text, item, "action_ref", path),
        _call(_text, item, "target_type_ref", path),
        _call(
            tuple,
            (
                _call(_decode_parameter, value, f"{path}.parameters[{index}]")
                for index, value in _call(
                    enumerate, _call(_array, item, "parameters", path)
                )
            ),
        ),
        None
        if result_shape is None
        else _call(_decode_shape, result_shape, f"{path}.result_shape"),
        _call(ActionValueMode, _call(_text, item, "result_value_mode", path)),
        _call(MutationScope, _call(_text, item, "mutation_scope", path)),
        _call(_text_array, item, "mutation_type_refs", path),
    )


def _decode_parameter(value: object, path: str) -> SchemaActionParameterDefinition:
    item = _call(_object, value, path)
    _call(
        _exact,
        item,
        {"parameter_ref", "position", "shape", "required", "nullable", "value_mode"},
        path,
    )
    position = item["position"]
    if not _call(isinstance, position, int) or _call(isinstance, position, bool):
        raise _call(
            SchemaTopologyManifestDecodeError, f"{path}.position must be integer"
        )
    return _call(
        SchemaActionParameterDefinition,
        _call(_text, item, "parameter_ref", path),
        position,
        _call(_decode_shape, item["shape"], f"{path}.shape"),
        _call(_boolean, item, "required", path),
        _call(_boolean, item, "nullable", path),
        _call(ActionValueMode, _call(_text, item, "value_mode", path)),
    )


def _decode_shape(value: object, path: str) -> ValueShape:
    return _call(_lower_shape, value, path)


def _root(payload: Any) -> Mapping[str, object]:
    if _call(isinstance, payload, bytes):
        try:
            payload = _call(payload.decode)
        except UnicodeDecodeError as error:
            raise _call(
                SchemaTopologyManifestDecodeError, "payload is not UTF-8"
            ) from error
    if not _call(isinstance, payload, str):
        raise _call(TypeError, "payload must be bytes or str")
    try:
        return _call(
            _object,
            _call(json.loads, payload, object_pairs_hook=_without_duplicates),
            "$",
        )
    except json.JSONDecodeError as error:
        raise _call(SchemaTopologyManifestDecodeError, "payload is not JSON") from error


def _without_duplicates(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        if key in result:
            raise _call(
                SchemaTopologyManifestDecodeError, f"duplicate JSON key {key!r}"
            )
        result[key] = value
    return result


def _object(value: Any, path: str) -> Mapping[str, object]:
    if not _call(isinstance, value, dict):
        raise _call(SchemaTopologyManifestDecodeError, f"{path} must be object")
    return value


def _exact(value: Mapping[str, object], keys: set[str], path: str) -> None:
    if _call(set, value) != keys:
        raise _call(
            SchemaTopologyManifestDecodeError,
            f"{path} keys are not exact; missing={_call(sorted, keys - _call(set, value))!r}, unknown={_call(sorted, _call(set, value) - keys)!r}",
        )


def _array(value: Mapping[str, object], field: str, path: str) -> list[object]:
    result: Any = value[field]
    if not _call(isinstance, result, list):
        raise _call(SchemaTopologyManifestDecodeError, f"{path}.{field} must be array")
    return result


def _text(value: Mapping[str, object], field: str, path: str) -> str:
    result: Any = value[field]
    if not _call(isinstance, result, str):
        raise _call(SchemaTopologyManifestDecodeError, f"{path}.{field} must be text")
    return result


def _text_array(value: Mapping[str, object], field: str, path: str) -> tuple[str, ...]:
    result = _call(_array, value, field, path)
    texts: list[str] = []
    for item in result:
        if not _call(isinstance, item, str):
            raise _call(
                SchemaTopologyManifestDecodeError, f"{path}.{field} must contain text"
            )
        _call(texts.append, item)
    return _call(tuple, texts)


def _boolean(value: Mapping[str, object], field: str, path: str) -> bool:
    result: Any = value[field]
    if not _call(isinstance, result, bool):
        raise _call(SchemaTopologyManifestDecodeError, f"{path}.{field} must be bool")
    return result


def _tokens(values: Sequence[str], path: str) -> tuple[str, ...]:
    result = _call(tuple, values)
    if (
        not result
        or _call(
            any,
            (
                not _call(isinstance, value, str)
                or not value
                or _call(any, (_call(ch.isspace) for ch in value))
                for value in result
            ),
        )
        or _call(len, result) != _call(len, _call(set, result))
    ):
        raise _call(
            SchemaTopologyManifestDecodeError, f"{path} must be unique non-empty tokens"
        )
    return result


__all__ = [
    "SUPPORTED_SCHEMA_TOPOLOGY_CONTRACTS",
    "SchemaTopologyManifestDecodeError",
    "decode_schema_topology_manifest",
    "encode_schema_topology_manifest",
    "negotiate_schema_topology_contract",
]
