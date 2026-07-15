"""Translate OIG commits (SSOT) into OCG deltas (compiler IR).

This module provides a minimal v0 bridge:
- Input: `ObjectInstanceGraphCommit` for the canonical `object_config_graph` projection lane
- Output: `ObjectConfigGraphDelta` suitable as an intermediate representation (IR)

Notes:
- This is intentionally DTO-only: it does not depend on any repository/code parsing.
- Payloads are derived from commit delta trees (primarily AttributeChange payloads; falls back to scalar change_deltas).
- v0 focuses on top-level OCG node entities: ClassConfig, EnumConfig, FunctionConfig, ClassConfigRelationship.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID

# History Ontology
from aware_history_ontology.change.change_enums import ChangeType, ChangeDeltaKind
from aware_history_ontology.change.change_delta import ChangeDelta

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphDelta,
    ObjectConfigGraphNodeDelta,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange

# Meta Runtime
from aware_meta.graph.config.stable_ids import stable_object_config_graph_node_id

from aware_code.types import JsonObject


class OcgDeltaFromOigCommitError(RuntimeError):
    pass


_META_CLASS_TO_NODE_TYPE: dict[str, ObjectConfigGraphNodeType] = {
    "ClassConfig": ObjectConfigGraphNodeType.class_,
    "EnumConfig": ObjectConfigGraphNodeType.enum,
    "FunctionConfig": ObjectConfigGraphNodeType.function,
    "ClassConfigRelationship": ObjectConfigGraphNodeType.relationship,
}


def _coerce_uuid(value: Any) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, dict) and "value" in value:
        return _coerce_uuid(value.get("value"))
    if isinstance(value, str):
        try:
            return UUID(value)
        except Exception:
            return None
    return None


def _meta_class_name_by_id(*, schema_graph: ObjectConfigGraph) -> dict[UUID, str]:
    out: dict[UUID, str] = {}
    for node in schema_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_:
            continue
        cc = node.class_config
        if cc is None:
            continue
        out[cc.id] = cc.name
    return out


def _attribute_name_by_meta_class_config_id(*, schema_graph: ObjectConfigGraph) -> dict[UUID, dict[UUID, str]]:
    """
    Index meta schema attribute configs for payload extraction.

    Returns:
        { meta_class_config_id: { attribute_config_id: attribute_name } }
    """
    out: dict[UUID, dict[UUID, str]] = {}
    for node in schema_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_:
            continue
        cc = node.class_config
        if cc is None:
            continue
        attr_map: dict[UUID, str] = {}
        for edge in cc.class_config_attribute_configs:
            ac = edge.attribute_config
            attr_map[ac.id] = ac.name
        if attr_map:
            out[cc.id] = attr_map
    return out


def _enum_option_value_by_id(*, schema_graph: ObjectConfigGraph) -> dict[UUID, str]:
    out: dict[UUID, str] = {}
    for node in schema_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.enum:
            continue
        ec = node.enum_config
        if ec is None:
            continue
        for opt in ec.enum_options:
            try:
                out[opt.id] = opt.value
            except Exception:
                continue
    return out


def _payload_from_change_deltas(deltas: Iterable[ChangeDelta]) -> JsonObject:
    payload: JsonObject = JsonObject()
    for d in deltas:
        prop = d.property
        if not prop:
            continue
        kind = d.kind
        if kind != ChangeDeltaKind.scalar_set:
            continue
        raw = d.payload
        if isinstance(raw, dict) and "value" in raw and len(raw) == 1:
            payload[prop] = raw.get("value")
        else:
            payload[prop] = raw
    return payload


def _extract_meta_class_config_id(*, deltas: Iterable[ChangeDelta]) -> UUID | None:
    for d in deltas:
        if d.property != "class_config_id":
            continue
        if d.kind != ChangeDeltaKind.scalar_set:
            continue
        return _coerce_uuid(d.payload)
    return None


def _extract_attribute_config_id(*, deltas: Iterable[ChangeDelta]) -> UUID | None:
    for d in deltas:
        if d.property != "attribute_config_id":
            continue
        if d.kind != ChangeDeltaKind.scalar_set:
            continue
        return _coerce_uuid(d.payload)
    return None


def _unwrap_scalar_delta_payload(delta: ChangeDelta) -> JsonObject | None:
    if isinstance(delta.payload, dict) and "value" in delta.payload and len(delta.payload) == 1:
        return delta.payload.get("value")
    return delta.payload


def _scalar_value_from_value_root_change(
    *,
    value_root_change: AttributeValueChange | None,
    enum_option_value_by_id: Mapping[UUID, str],
) -> Any | None:
    if value_root_change is None:
        return None
    change = value_root_change.change
    for d in change.change_deltas:
        if d.kind != ChangeDeltaKind.scalar_set:
            continue
        prop = d.property or ""
        raw = _unwrap_scalar_delta_payload(d)
        if prop == "primitive_value":
            return raw
        if prop == "enum_option_id":
            opt_id = _coerce_uuid(raw)
            if opt_id is None:
                return None
            return enum_option_value_by_id.get(opt_id) or str(opt_id)
        if prop == "class_instance_id":
            inst_id = _coerce_uuid(raw)
            if inst_id is None:
                return None
            return str(inst_id)
    return None


def _payload_from_attribute_changes(
    *,
    meta_cc_id: UUID,
    attribute_changes: Iterable[AttributeChange],
    attribute_name_by_meta_cc_id: Mapping[UUID, Mapping[UUID, str]],
    enum_option_value_by_id: Mapping[UUID, str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    attr_name_by_id = attribute_name_by_meta_cc_id.get(meta_cc_id) or {}
    if not attr_name_by_id:
        return payload
    for ac in attribute_changes:
        change = ac.change
        attr_cfg_id = _extract_attribute_config_id(deltas=change.change_deltas)
        if attr_cfg_id is None:
            continue
        name = attr_name_by_id.get(attr_cfg_id)
        if not name:
            continue
        value = _scalar_value_from_value_root_change(
            value_root_change=ac.value_root_change,
            enum_option_value_by_id=enum_option_value_by_id,
        )
        if value is None:
            continue
        payload[name] = value
    return payload


@dataclass(frozen=True, slots=True)
class _NodeRef:
    node_type: ObjectConfigGraphNodeType
    entity_id: UUID


def _relationship_edges_from_commit(
    commit: ObjectInstanceGraphCommit,
) -> dict[UUID, set[UUID]]:
    """Best-effort adjacency map derived from relationship change payloads (commit-only)."""
    neighbors: dict[UUID, set[UUID]] = {}
    for ogc in commit.object_instance_graph_changes:
        for rel_change in ogc.class_instance_relationship_changes:
            src = rel_change.source_class_instance_id
            tgt = rel_change.target_class_instance_id
            neighbors.setdefault(src, set()).add(tgt)
            neighbors.setdefault(tgt, set()).add(src)
    return neighbors


def _resolve_node_ref_for_entity(
    *,
    entity_id: UUID,
    meta_cc_id: UUID | None,
    meta_name_by_id: Mapping[UUID, str],
    meta_class_config_id_by_entity_id: Mapping[UUID, UUID] | None,
) -> _NodeRef | None:
    effective_meta_cc_id = meta_cc_id or (meta_class_config_id_by_entity_id or {}).get(entity_id)
    if effective_meta_cc_id is None:
        return None
    meta_name = meta_name_by_id.get(effective_meta_cc_id)
    if meta_name is None:
        return None
    node_type = _META_CLASS_TO_NODE_TYPE.get(meta_name)
    if node_type is None:
        return None
    return _NodeRef(node_type=node_type, entity_id=entity_id)


def _nearest_node_owner_via_bfs(
    *,
    start: UUID,
    neighbors: Mapping[UUID, set[UUID]],
    node_entity_ids: set[UUID],
) -> UUID | None:
    """Return the nearest node-entity id reachable from start (undirected BFS)."""
    if start in node_entity_ids:
        return start
    if start not in neighbors:
        return None

    visited: set[UUID] = {start}
    frontier: list[UUID] = [start]
    while frontier:
        next_frontier: list[UUID] = []
        candidates: list[UUID] = []
        for cur in frontier:
            for nxt in neighbors.get(cur, set()):
                if nxt in visited:
                    continue
                if nxt in node_entity_ids:
                    candidates.append(nxt)
                    continue
                visited.add(nxt)
                next_frontier.append(nxt)
        if candidates:
            # Deterministic tie-break: stable string ordering.
            candidates.sort(key=str)
            return candidates[0]
        frontier = next_frontier
    return None


def _relationship_edges_from_snapshot(
    oig: ObjectInstanceGraph,
) -> dict[UUID, set[UUID]]:
    neighbors: dict[UUID, set[UUID]] = {}
    for rel in oig.class_instance_relationships:
        src = rel.source_class_instance_id
        tgt = rel.target_class_instance_id
        neighbors.setdefault(src, set()).add(tgt)
        neighbors.setdefault(tgt, set()).add(src)
    return neighbors


def index_oig_snapshot_for_ocg_delta(
    *, oig: ObjectInstanceGraph, schema_graph: ObjectConfigGraph
) -> tuple[dict[UUID, UUID], dict[UUID, UUID]]:
    """Build the minimum indexes required to derive OCGΔ from commits.

    This intentionally does not attempt full object hydration. It provides:
    - `meta_class_config_id_by_entity_id`: ClassInstance.id -> ClassInstance.class_config_id
    - `owner_node_entity_id_by_entity_id`: entity_id -> nearest OCG node entity_id in the OIG snapshot
      (node types are derived from the meta schema: ClassConfig/EnumConfig/FunctionConfig/ClassConfigRelationship).
    """
    meta_name_by_id = _meta_class_name_by_id(schema_graph=schema_graph)

    meta_class_config_id_by_entity_id: dict[UUID, UUID] = {}
    node_entity_ids: set[UUID] = set()

    for ci in oig.class_instances:
        cid = ci.id
        meta_cc_id = ci.class_config_id
        meta_class_config_id_by_entity_id[cid] = meta_cc_id
        meta_name = meta_name_by_id.get(meta_cc_id)
        if meta_name is None:
            continue
        if _META_CLASS_TO_NODE_TYPE.get(meta_name) is not None:
            node_entity_ids.add(cid)

    neighbors = _relationship_edges_from_snapshot(oig)
    owner_node_entity_id_by_entity_id: dict[UUID, UUID] = {}
    for entity_id in meta_class_config_id_by_entity_id.keys():
        owner = _nearest_node_owner_via_bfs(start=entity_id, neighbors=neighbors, node_entity_ids=node_entity_ids)
        if owner is not None:
            owner_node_entity_id_by_entity_id[entity_id] = owner

    return meta_class_config_id_by_entity_id, owner_node_entity_id_by_entity_id


def build_ocg_delta_from_oig_commit(
    *,
    commit: ObjectInstanceGraphCommit,
    schema_graph: ObjectConfigGraph,
    meta_class_config_id_by_entity_id_post: Mapping[UUID, UUID] | None = None,
    meta_class_config_id_by_entity_id_pre: Mapping[UUID, UUID] | None = None,
    owner_node_entity_id_by_entity_id_post: Mapping[UUID, UUID] | None = None,
    owner_node_entity_id_by_entity_id_pre: Mapping[UUID, UUID] | None = None,
    payload_by_entity_id_post: Mapping[UUID, dict[str, Any]] | None = None,
) -> ObjectConfigGraphDelta:
    """
    Build an `ObjectConfigGraphDelta` from a single OIG commit payload.

    This is a pure translation step: it does not materialize full pre/post snapshots.
    """
    if commit.commit is None:
        raise OcgDeltaFromOigCommitError("OIG commit missing Commit envelope")

    meta_name_by_id = _meta_class_name_by_id(schema_graph=schema_graph)
    attribute_name_by_meta_cc_id = _attribute_name_by_meta_class_config_id(schema_graph=schema_graph)
    enum_option_values = _enum_option_value_by_id(schema_graph=schema_graph)
    warnings: list[str] = []

    node_delta_by_key: dict[tuple[ObjectConfigGraphNodeType, UUID], ObjectConfigGraphNodeDelta] = {}

    # Commit-only adjacency (best-effort): can resolve ownership for create-style commits.
    neighbors = _relationship_edges_from_commit(commit)

    # Candidate node entities we know about in this translation pass (for BFS fallback),
    # plus their resolved node types (so bubble-up can work without post-state indexes).
    node_ref_by_entity_id: dict[UUID, _NodeRef] = {}

    def _register_node_ref(ref: _NodeRef | None) -> None:
        if ref is None:
            return
        node_ref_by_entity_id[ref.entity_id] = ref

    if meta_class_config_id_by_entity_id_post is not None:
        for entity_id, meta_cc_id in meta_class_config_id_by_entity_id_post.items():
            _register_node_ref(
                _resolve_node_ref_for_entity(
                    entity_id=entity_id,
                    meta_cc_id=meta_cc_id,
                    meta_name_by_id=meta_name_by_id,
                    meta_class_config_id_by_entity_id=None,
                )
            )
    if meta_class_config_id_by_entity_id_pre is not None:
        for entity_id, meta_cc_id in meta_class_config_id_by_entity_id_pre.items():
            _register_node_ref(
                _resolve_node_ref_for_entity(
                    entity_id=entity_id,
                    meta_cc_id=meta_cc_id,
                    meta_name_by_id=meta_name_by_id,
                    meta_class_config_id_by_entity_id=None,
                )
            )

    # First pass: discover node entities directly from the commit (no external indexes).
    for ogc in commit.object_instance_graph_changes:
        for cic in ogc.class_instance_changes:
            change = cic.change
            change_type = change.type
            if change_type not in {
                ChangeType.create,
                ChangeType.update,
                ChangeType.delete,
            }:
                continue

            entity_id = cic.class_instance_id
            meta_cc_id = _extract_meta_class_config_id(deltas=change.change_deltas)
            if meta_cc_id is None:
                if change_type == ChangeType.delete and meta_class_config_id_by_entity_id_pre is not None:
                    meta_cc_id = meta_class_config_id_by_entity_id_pre.get(entity_id)
                elif change_type != ChangeType.delete and meta_class_config_id_by_entity_id_post is not None:
                    meta_cc_id = meta_class_config_id_by_entity_id_post.get(entity_id)
            if meta_cc_id is None:
                continue

            meta_name = meta_name_by_id.get(meta_cc_id)
            if meta_name is None:
                continue
            node_type = _META_CLASS_TO_NODE_TYPE.get(meta_name)
            if node_type is None:
                continue
            _register_node_ref(_NodeRef(node_type=node_type, entity_id=entity_id))

    node_entity_ids: set[UUID] = set(node_ref_by_entity_id.keys())

    def _upsert_node_delta(
        *,
        node_type: ObjectConfigGraphNodeType,
        entity_id: UUID,
        change_type: ChangeType,
        payload: dict[str, Any] | None,
    ) -> None:
        node_id = stable_object_config_graph_node_id(
            object_config_graph_id=commit.object_instance_graph_id,
            type=node_type.value,
            node_key=str(entity_id),
        )
        key = (node_type, entity_id)
        existing = node_delta_by_key.get(key)
        if existing is None:
            node_delta_by_key[key] = ObjectConfigGraphNodeDelta(
                change_type=change_type,
                node_type=node_type,
                node_id=node_id,
                entity_id=entity_id,
                payload=JsonObject(payload) if payload is not None else None,
                entity_fqn=None,
                source_relative_path=None,
                notes=None,
            )
            return

        # Merge duplicate entries (prefer strongest change type).
        # Precedence: delete > create > update.
        order = {ChangeType.update: 0, ChangeType.create: 1, ChangeType.delete: 2}
        if order.get(change_type, 0) > order.get(existing.change_type, 0):
            existing.change_type = change_type
        if existing.payload is None and payload is not None:
            existing.payload = JsonObject(payload)

    def _bubble_up_owner_for_entity(*, entity_id: UUID, change_type: ChangeType) -> None:
        owner = None
        if change_type == ChangeType.delete:
            owner = (owner_node_entity_id_by_entity_id_pre or {}).get(entity_id)
        else:
            owner = (owner_node_entity_id_by_entity_id_post or {}).get(entity_id)

        if owner is None:
            owner = _nearest_node_owner_via_bfs(start=entity_id, neighbors=neighbors, node_entity_ids=node_entity_ids)

        if owner is None:
            warnings.append(f"Unable to resolve owner node for entity_id={entity_id} (change_type={change_type})")
            return

        owner_ref = node_ref_by_entity_id.get(owner)
        if owner_ref is None:
            owner_meta_map = (
                meta_class_config_id_by_entity_id_pre
                if change_type == ChangeType.delete
                else meta_class_config_id_by_entity_id_post
            )
            owner_ref = _resolve_node_ref_for_entity(
                entity_id=owner,
                meta_cc_id=None,
                meta_name_by_id=meta_name_by_id,
                meta_class_config_id_by_entity_id=owner_meta_map,
            )
        if owner_ref is None:
            warnings.append(f"Owner entity_id={owner} is not a recognized OCG node type (entity_id={entity_id})")
            return

        owner_payload = None
        if payload_by_entity_id_post is not None and owner in payload_by_entity_id_post:
            owner_payload = dict(payload_by_entity_id_post[owner])

        _upsert_node_delta(
            node_type=owner_ref.node_type,
            entity_id=owner_ref.entity_id,
            change_type=ChangeType.update,
            payload=owner_payload,
        )

    for ogc in commit.object_instance_graph_changes:
        for cic in ogc.class_instance_changes:
            change = cic.change
            if change is None:
                continue

            change_type = change.type
            if change_type not in {
                ChangeType.create,
                ChangeType.update,
                ChangeType.delete,
            }:
                continue

            entity_id = cic.class_instance_id
            meta_cc_id = _extract_meta_class_config_id(deltas=change.change_deltas)
            if meta_cc_id is None:
                if change_type == ChangeType.delete and meta_class_config_id_by_entity_id_pre is not None:
                    meta_cc_id = meta_class_config_id_by_entity_id_pre.get(entity_id)
                elif change_type != ChangeType.delete and meta_class_config_id_by_entity_id_post is not None:
                    meta_cc_id = meta_class_config_id_by_entity_id_post.get(entity_id)
            if meta_cc_id is None:
                warnings.append(f"Missing class_config_id for ClassInstanceChange entity_id={entity_id}")
                continue

            meta_name = meta_name_by_id.get(meta_cc_id)
            if meta_name is None:
                warnings.append(f"Unknown meta class_config_id={meta_cc_id} for entity_id={entity_id}")
                continue

            node_type = _META_CLASS_TO_NODE_TYPE.get(meta_name)
            if node_type is not None:
                node_entity_ids.add(entity_id)
                node_ref_by_entity_id.setdefault(entity_id, _NodeRef(node_type=node_type, entity_id=entity_id))

            payload = None
            if change_type != ChangeType.delete:
                if payload_by_entity_id_post is not None and entity_id in payload_by_entity_id_post:
                    payload = dict(payload_by_entity_id_post[entity_id])
                else:
                    payload = {}
                    payload.update(
                        _payload_from_attribute_changes(
                            meta_cc_id=meta_cc_id,
                            attribute_changes=cic.attribute_changes,
                            attribute_name_by_meta_cc_id=attribute_name_by_meta_cc_id,
                            enum_option_value_by_id=enum_option_values,
                        )
                    )
                    payload.update(_payload_from_change_deltas(change.change_deltas))
                    if not payload:
                        payload = None

            if node_type is not None:
                _upsert_node_delta(
                    node_type=node_type,
                    entity_id=entity_id,
                    change_type=change_type,
                    payload=payload,
                )
            else:
                # Bubble nested meta-entity changes (EnumOption, AttributeConfig, edge classes, etc)
                # into their owning OCG node (ClassConfig / EnumConfig / FunctionConfig / Relationship).
                _bubble_up_owner_for_entity(entity_id=entity_id, change_type=change_type)

        # Relationship changes can also imply OCG node updates (membership changes, edge rewires).
        for rel_change in ogc.class_instance_relationship_changes:
            change = rel_change.change
            change_type = change.type
            if change_type not in {
                ChangeType.create,
                ChangeType.update,
                ChangeType.delete,
            }:
                continue
            src = rel_change.source_class_instance_id
            tgt = rel_change.target_class_instance_id
            _bubble_up_owner_for_entity(entity_id=src, change_type=change_type)
            _bubble_up_owner_for_entity(entity_id=tgt, change_type=change_type)

    node_deltas = list(node_delta_by_key.values())
    node_deltas.sort(key=lambda d: (d.node_type.value, str(d.entity_id)))

    return ObjectConfigGraphDelta(
        object_config_graph_id=commit.object_instance_graph_id,
        language=commit.source_language,
        graph_hash_pre=None,
        graph_hash_post=None,
        node_deltas=node_deltas,
        warnings=warnings,
    )


__all__ = [
    "OcgDeltaFromOigCommitError",
    "index_oig_snapshot_for_ocg_delta",
    "build_ocg_delta_from_oig_commit",
]
