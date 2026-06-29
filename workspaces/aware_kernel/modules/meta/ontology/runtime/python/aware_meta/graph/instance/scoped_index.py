from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol, TypeAlias, cast
from uuid import UUID

from aware_meta.graph.config.lane.telemetry import SeedTimings
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph


RelationshipMembershipTuple: TypeAlias = tuple[UUID, UUID, UUID]
AttributeFingerprint: TypeAlias = tuple[str, str]
ClassInstanceFingerprint: TypeAlias = tuple[str, tuple[AttributeFingerprint, ...]]
GraphDiffIndexSidecarPayload: TypeAlias = dict[str, object]


class _RelationshipLike(Protocol):
    @property
    def id(self) -> UUID | None: ...

    @property
    def class_config_relationship_id(self) -> UUID: ...

    @property
    def source_class_instance_id(self) -> UUID: ...

    @property
    def target_class_instance_id(self) -> UUID: ...


@dataclass(frozen=True)
class _OigRelationshipScopeIndex:
    """Read-only relationship lookup indexes for scoped-diff selection."""

    relationships: tuple[ClassInstanceRelationship, ...]
    scope_maps_built: bool
    membership_map_built: bool
    by_relationship_id: dict[UUID, tuple[ClassInstanceRelationship, ...]]
    by_source: dict[UUID, tuple[ClassInstanceRelationship, ...]]
    by_target: dict[UUID, tuple[ClassInstanceRelationship, ...]]
    by_relationship_config: dict[UUID, tuple[ClassInstanceRelationship, ...]]
    by_membership_tuple: dict[RelationshipMembershipTuple, tuple[ClassInstanceRelationship, ...]]


@dataclass(frozen=True)
class _OigGraphDiffIndex:
    """Single-pass graph index used by OIG fingerprint-scoped diff rails."""

    class_instances_by_id: dict[UUID, ClassInstance]
    class_instance_fingerprints: dict[UUID, ClassInstanceFingerprint]
    relationship_membership_tuples: set[RelationshipMembershipTuple]


OigRelationshipScopeIndex: TypeAlias = _OigRelationshipScopeIndex
OigGraphDiffIndex: TypeAlias = _OigGraphDiffIndex

_OIG_GRAPH_DIFF_INDEX_SIDECAR_VERSION = 1


def _relationship_membership_tuple(
    relationship: _RelationshipLike,
) -> RelationshipMembershipTuple:
    return (
        relationship.class_config_relationship_id,
        relationship.source_class_instance_id,
        relationship.target_class_instance_id,
    )


def _relationship_matches_membership_tuple_set(
    *,
    relationship: _RelationshipLike,
    tuples: set[RelationshipMembershipTuple],
) -> bool:
    return _relationship_membership_tuple(relationship) in tuples


def _relationship_sort_key(
    relationship: _RelationshipLike,
) -> tuple[str, str, str, str]:
    relationship_id = "" if relationship.id is None else str(relationship.id)
    return (
        str(relationship.class_config_relationship_id),
        str(relationship.source_class_instance_id),
        str(relationship.target_class_instance_id),
        relationship_id,
    )


def _relationship_identity_key(
    relationship: _RelationshipLike,
) -> UUID | int:
    relationship_id = relationship.id
    if relationship_id is not None:
        return relationship_id
    return id(relationship)


def _build_oig_relationship_scope_index(
    *,
    graph: ObjectInstanceGraph,
    include_scope_maps: bool,
    include_membership_map: bool,
) -> OigRelationshipScopeIndex:
    """Build endpoint/config/tuple indexes once for repeated scoped relationship selection."""
    by_relationship_id_tmp: dict[UUID, list[ClassInstanceRelationship]] = defaultdict(list)
    by_source_tmp: dict[UUID, list[ClassInstanceRelationship]] = defaultdict(list)
    by_target_tmp: dict[UUID, list[ClassInstanceRelationship]] = defaultdict(list)
    by_relationship_config_tmp: dict[UUID, list[ClassInstanceRelationship]] = defaultdict(list)
    by_membership_tuple_tmp: dict[RelationshipMembershipTuple, list[ClassInstanceRelationship]] = defaultdict(list)

    relationships = tuple(graph.class_instance_relationships)
    for relationship in relationships:
        if include_scope_maps:
            by_relationship_id_tmp[relationship.id].append(relationship)
            by_source_tmp[relationship.source_class_instance_id].append(relationship)
            by_target_tmp[relationship.target_class_instance_id].append(relationship)
            by_relationship_config_tmp[relationship.class_config_relationship_id].append(relationship)

        if include_membership_map:
            by_membership_tuple_tmp[_relationship_membership_tuple(relationship)].append(relationship)

    return _OigRelationshipScopeIndex(
        relationships=relationships,
        scope_maps_built=include_scope_maps,
        membership_map_built=include_membership_map,
        by_relationship_id={key: tuple(value) for key, value in by_relationship_id_tmp.items()},
        by_source={key: tuple(value) for key, value in by_source_tmp.items()},
        by_target={key: tuple(value) for key, value in by_target_tmp.items()},
        by_relationship_config={key: tuple(value) for key, value in by_relationship_config_tmp.items()},
        by_membership_tuple={key: tuple(value) for key, value in by_membership_tuple_tmp.items()},
    )


def _sort_relationships_deterministic(
    relationships: list[ClassInstanceRelationship],
) -> list[ClassInstanceRelationship]:
    relationships.sort(key=_relationship_sort_key)
    return relationships


def _select_relationships_from_scope_index(
    *,
    index: OigRelationshipScopeIndex,
    candidate_ids: set[UUID],
    include_relationship_config_ids: bool,
) -> list[ClassInstanceRelationship]:
    if not index.scope_maps_built:
        raise ValueError("Relationship scope selection requires index built with include_scope_maps=True")
    if not candidate_ids:
        return []

    selected: list[ClassInstanceRelationship] = []
    seen: set[UUID | int] = set()

    def _add(relationship: ClassInstanceRelationship) -> None:
        identity_key = _relationship_identity_key(relationship)
        if identity_key in seen:
            return
        seen.add(identity_key)
        selected.append(relationship)

    for candidate_id in sorted(candidate_ids, key=str):
        for relationship in index.by_relationship_id.get(candidate_id, ()):
            _add(relationship)
        for relationship in index.by_source.get(candidate_id, ()):
            _add(relationship)
        for relationship in index.by_target.get(candidate_id, ()):
            _add(relationship)
        if include_relationship_config_ids:
            for relationship in index.by_relationship_config.get(candidate_id, ()):
                _add(relationship)

    return _sort_relationships_deterministic(selected)


def _select_relationships_for_membership_tuples(
    *,
    index: OigRelationshipScopeIndex,
    membership_tuples: set[RelationshipMembershipTuple],
) -> list[ClassInstanceRelationship]:
    if not index.membership_map_built:
        raise ValueError("Relationship membership selection requires index built with include_membership_map=True")
    if not membership_tuples:
        return []

    selected: list[ClassInstanceRelationship] = []
    seen: set[UUID | int] = set()

    def _add(relationship: ClassInstanceRelationship) -> None:
        identity_key = _relationship_identity_key(relationship)
        if identity_key in seen:
            return
        seen.add(identity_key)
        selected.append(relationship)

    for membership_tuple in sorted(membership_tuples, key=lambda item: (str(item[0]), str(item[1]), str(item[2]))):
        for relationship in index.by_membership_tuple.get(membership_tuple, ()):
            _add(relationship)

    return _sort_relationships_deterministic(selected)


def _emit_relationship_scope_index_metrics(
    *,
    timings: SeedTimings | None,
    metric_prefix: str,
    index: OigRelationshipScopeIndex,
) -> None:
    if not metric_prefix or timings is None:
        return
    _ = timings.metric(f"{metric_prefix}_scope_maps_built", index.scope_maps_built)
    _ = timings.metric(f"{metric_prefix}_membership_map_built", index.membership_map_built)
    _ = timings.metric(f"{metric_prefix}_rows", len(index.relationships))
    _ = timings.metric(f"{metric_prefix}_unique_relationship_ids", len(index.by_relationship_id))
    _ = timings.metric(f"{metric_prefix}_unique_sources", len(index.by_source))
    _ = timings.metric(f"{metric_prefix}_unique_targets", len(index.by_target))
    _ = timings.metric(f"{metric_prefix}_unique_relationship_configs", len(index.by_relationship_config))
    _ = timings.metric(f"{metric_prefix}_unique_membership_tuples", len(index.by_membership_tuple))


def _build_class_instances_by_id(
    *,
    graph: ObjectInstanceGraph,
) -> dict[UUID, ClassInstance]:
    return {class_instance.id: class_instance for class_instance in graph.class_instances}


def _serialize_oig_graph_diff_index_sidecar(
    *,
    index: OigGraphDiffIndex,
    graph_hash: str,
) -> GraphDiffIndexSidecarPayload:
    fingerprints = tuple(
        (
            class_instance_id,
            fingerprint[0],
            tuple(fingerprint[1]),
        )
        for class_instance_id, fingerprint in sorted(
            index.class_instance_fingerprints.items(),
            key=lambda item: str(item[0]),
        )
    )
    relationship_membership_tuples = tuple(
        sorted(
            index.relationship_membership_tuples,
            key=lambda item: (str(item[0]), str(item[1]), str(item[2])),
        )
    )
    return {
        "v": _OIG_GRAPH_DIFF_INDEX_SIDECAR_VERSION,
        "graph_hash": graph_hash.strip(),
        "fingerprints": fingerprints,
        "relationship_membership_tuples": relationship_membership_tuples,
    }


def _coerce_string_key_mapping(value: object, *, error_code: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(error_code)
    source_mapping = cast(dict[object, object], value)
    typed_mapping: dict[str, object] = {}
    for raw_key, raw_item in source_mapping.items():
        if not isinstance(raw_key, str):
            raise ValueError(error_code)
        typed_mapping[raw_key] = raw_item
    return typed_mapping


def _coerce_sequence(value: object, *, error_code: str) -> list[object]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(error_code)
    source_items = cast(list[object] | tuple[object, ...], value)
    typed_items: list[object] = []
    for raw_item in source_items:
        typed_items.append(raw_item)
    return typed_items


def _coerce_sidecar_version(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        return int(value)
    raise ValueError("version_mismatch")


def _coerce_uuid(value: object, *, error_code: str) -> UUID:
    if not isinstance(value, UUID):
        raise ValueError(error_code)
    return value


def _deserialize_attribute_fingerprint_rows(
    rows_raw: object,
) -> tuple[AttributeFingerprint, ...]:
    rows = _coerce_sequence(rows_raw, error_code="fingerprint_attrs_invalid")
    parsed_rows: list[AttributeFingerprint] = []
    for row_raw in rows:
        row = _coerce_sequence(row_raw, error_code="fingerprint_attr_row_invalid")
        if len(row) != 2:
            raise ValueError("fingerprint_attr_row_invalid")
        parsed_rows.append((str(row[0]), str(row[1])))
    return tuple(parsed_rows)


def _deserialize_class_instance_fingerprints(
    rows_raw: object,
) -> dict[UUID, ClassInstanceFingerprint]:
    rows = _coerce_sequence(rows_raw, error_code="fingerprints_invalid")
    parsed_rows: dict[UUID, ClassInstanceFingerprint] = {}
    for row_raw in rows:
        row = _coerce_sequence(row_raw, error_code="fingerprint_row_invalid")
        if len(row) != 3:
            raise ValueError("fingerprint_row_invalid")
        class_instance_id = _coerce_uuid(row[0], error_code="fingerprint_id_invalid")
        parsed_rows[class_instance_id] = (
            str(row[1]),
            _deserialize_attribute_fingerprint_rows(row[2]),
        )
    return parsed_rows


def _deserialize_relationship_membership_tuples(
    rows_raw: object,
) -> set[RelationshipMembershipTuple]:
    rows = _coerce_sequence(rows_raw, error_code="relationship_membership_tuples_invalid")
    parsed_rows: set[RelationshipMembershipTuple] = set()
    for row_raw in rows:
        row = _coerce_sequence(row_raw, error_code="relationship_membership_row_invalid")
        if len(row) != 3:
            raise ValueError("relationship_membership_row_invalid")
        parsed_rows.add(
            (
                _coerce_uuid(row[0], error_code="relationship_membership_uuid_invalid"),
                _coerce_uuid(row[1], error_code="relationship_membership_uuid_invalid"),
                _coerce_uuid(row[2], error_code="relationship_membership_uuid_invalid"),
            )
        )
    return parsed_rows


def _deserialize_oig_graph_diff_index_sidecar(
    *,
    payload: object,
    graph: ObjectInstanceGraph,
    expected_graph_hash: str,
) -> OigGraphDiffIndex:
    payload_mapping = _coerce_string_key_mapping(payload, error_code="payload_not_dict")
    version_raw = payload_mapping.get("v", -1)
    if _coerce_sidecar_version(version_raw) != _OIG_GRAPH_DIFF_INDEX_SIDECAR_VERSION:
        raise ValueError("version_mismatch")
    sidecar_graph_hash = str(payload_mapping.get("graph_hash", "")).strip()
    if sidecar_graph_hash != expected_graph_hash.strip():
        raise ValueError("graph_hash_mismatch")

    class_instances_by_id = _build_class_instances_by_id(graph=graph)
    class_instance_fingerprints = _deserialize_class_instance_fingerprints(
        payload_mapping.get("fingerprints"),
    )
    if set(class_instance_fingerprints) != set(class_instances_by_id):
        raise ValueError("fingerprint_key_set_mismatch")

    relationship_membership_tuples = _deserialize_relationship_membership_tuples(
        payload_mapping.get("relationship_membership_tuples"),
    )
    return _OigGraphDiffIndex(
        class_instances_by_id=class_instances_by_id,
        class_instance_fingerprints=class_instance_fingerprints,
        relationship_membership_tuples=relationship_membership_tuples,
    )


def _attribute_fingerprint(attribute: Attribute) -> AttributeFingerprint:
    from aware_meta.attribute.instance.value.builder import (
        fingerprint_attribute_value,
    )

    return (
        str(attribute.attribute_config_id),
        fingerprint_attribute_value(attribute.value_root),
    )


def _build_oig_graph_diff_index(
    *,
    graph: ObjectInstanceGraph,
) -> OigGraphDiffIndex:
    """Build class-instance and relationship membership indexes in one pass."""
    class_instances_by_id = _build_class_instances_by_id(graph=graph)
    class_instance_fingerprints = {
        class_instance_id: (
            str(class_instance.class_config_id),
            tuple(
                sorted(
                    (_attribute_fingerprint(attribute) for attribute in class_instance.attributes),
                    key=lambda item: item[0],
                )
            ),
        )
        for class_instance_id, class_instance in class_instances_by_id.items()
    }
    relationship_membership_tuples = {
        _relationship_membership_tuple(relationship)
        for relationship in graph.class_instance_relationships
    }

    return _OigGraphDiffIndex(
        class_instances_by_id=class_instances_by_id,
        class_instance_fingerprints=class_instance_fingerprints,
        relationship_membership_tuples=relationship_membership_tuples,
    )


def relationship_matches_membership_tuple_set(
    *,
    relationship: _RelationshipLike,
    tuples: set[RelationshipMembershipTuple],
) -> bool:
    return _relationship_matches_membership_tuple_set(relationship=relationship, tuples=tuples)


def build_oig_relationship_scope_index(
    *,
    graph: ObjectInstanceGraph,
    include_scope_maps: bool,
    include_membership_map: bool,
) -> OigRelationshipScopeIndex:
    return _build_oig_relationship_scope_index(
        graph=graph,
        include_scope_maps=include_scope_maps,
        include_membership_map=include_membership_map,
    )


def emit_relationship_scope_index_metrics(
    *,
    timings: SeedTimings | None,
    metric_prefix: str,
    index: OigRelationshipScopeIndex,
) -> None:
    _emit_relationship_scope_index_metrics(
        timings=timings,
        metric_prefix=metric_prefix,
        index=index,
    )


def deserialize_oig_graph_diff_index_sidecar(
    *,
    payload: object,
    graph: ObjectInstanceGraph,
    expected_graph_hash: str,
) -> OigGraphDiffIndex:
    return _deserialize_oig_graph_diff_index_sidecar(
        payload=payload,
        graph=graph,
        expected_graph_hash=expected_graph_hash,
    )


def serialize_oig_graph_diff_index_sidecar(
    *,
    index: OigGraphDiffIndex,
    graph_hash: str,
) -> GraphDiffIndexSidecarPayload:
    return _serialize_oig_graph_diff_index_sidecar(index=index, graph_hash=graph_hash)


def select_relationships_for_membership_tuples(
    *,
    index: OigRelationshipScopeIndex,
    membership_tuples: set[RelationshipMembershipTuple],
) -> list[ClassInstanceRelationship]:
    return _select_relationships_for_membership_tuples(
        index=index,
        membership_tuples=membership_tuples,
    )


def select_relationships_from_scope_index(
    *,
    index: OigRelationshipScopeIndex,
    candidate_ids: set[UUID],
    include_relationship_config_ids: bool,
) -> list[ClassInstanceRelationship]:
    return _select_relationships_from_scope_index(
        index=index,
        candidate_ids=candidate_ids,
        include_relationship_config_ids=include_relationship_config_ids,
    )


def build_oig_graph_diff_index(
    *,
    graph: ObjectInstanceGraph,
) -> OigGraphDiffIndex:
    return _build_oig_graph_diff_index(graph=graph)


__all__ = [
    "AttributeFingerprint",
    "ClassInstanceFingerprint",
    "GraphDiffIndexSidecarPayload",
    "OigGraphDiffIndex",
    "OigRelationshipScopeIndex",
    "RelationshipMembershipTuple",
    "build_oig_graph_diff_index",
    "build_oig_relationship_scope_index",
    "deserialize_oig_graph_diff_index_sidecar",
    "emit_relationship_scope_index_metrics",
    "relationship_matches_membership_tuple_set",
    "select_relationships_for_membership_tuples",
    "select_relationships_from_scope_index",
    "serialize_oig_graph_diff_index_sidecar",
]
