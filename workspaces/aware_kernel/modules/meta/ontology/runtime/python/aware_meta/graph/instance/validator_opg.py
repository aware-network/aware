from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable, Mapping
from uuid import UUID

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)

from aware_meta.class_.instance.validator import (
    ClassInstanceValidationError,
    validate_class_instance,
)


class OigValidationError(ValueError):
    pass


@dataclass(frozen=True)
class _OcgIndex:
    class_configs_by_id: Mapping[UUID, ClassConfig]
    relationships_by_id: Mapping[UUID, ClassConfigRelationship]
    attribute_configs_by_id: Mapping[UUID, AttributeConfig]


@dataclass(frozen=True)
class _OpgIndex:
    root_node: ObjectProjectionGraphNode
    nodes_by_class_config_id: Mapping[UUID, ObjectProjectionGraphNode]
    edges: list[ObjectProjectionGraphEdge]


def validate_object_instance_graph_against_opg(
    *,
    graph: ObjectInstanceGraph,
    object_config_graph: ObjectConfigGraph,
    object_projection_graph: ObjectProjectionGraph,
) -> None:
    """
    Validate that an ObjectInstanceGraph is a correct instantiation of an OCG + OPG.

    This validator is intentionally *pure*:
    - No DB lookups.
    - No runtime instance access.

    It exists to make canonical OIGs safe and "diff-ready" by enforcing:
    - root consistency (OIG root matches OPG root ClassConfig),
    - membership consistency (instances only for member ClassConfigs),
    - relationship correctness (relationships correspond to OPG edges),
    - include/multiplicity/selection constraints (post-build),
    - class-instance attribute correctness (descriptor-driven value trees; relationship attrs excluded).
    """
    if graph.object_projection_graph_id is not None and graph.object_projection_graph_id != object_projection_graph.id:
        raise OigValidationError(
            f"OIG.object_projection_graph_id mismatch: {graph.object_projection_graph_id} != {object_projection_graph.id}"
        )

    ocg = _build_ocg_index(object_config_graph)
    opg = _build_opg_index(object_projection_graph)

    root_id = graph.root_class_instance_id
    if root_id is None:
        raise OigValidationError("OIG missing root_class_instance_id")

    by_ci_id = _index_class_instances(graph.class_instances or [])
    root_ci = by_ci_id.get(root_id)
    if root_ci is None:
        raise OigValidationError(f"OIG root ClassInstance not found in class_instances: {root_id}")

    if root_ci.class_config_id != opg.root_node.class_config_id:
        raise OigValidationError(
            f"OIG root ClassInstance.class_config_id mismatch: {root_ci.class_config_id} != {opg.root_node.class_config_id}"
        )

    # Membership: implicit from OPG nodes + edge endpoints.
    member_cc_ids = _member_class_config_ids(ocg=ocg, opg=opg)
    for ci in by_ci_id.values():
        if ci.class_config_id not in ocg.class_configs_by_id:
            raise OigValidationError(f"ClassConfig not found for ClassInstance.class_config_id={ci.class_config_id}")
        if ci.class_config_id not in member_cc_ids:
            raise OigValidationError(f"ClassInstance.class_config_id is not a member of the OPG: {ci.class_config_id}")

    relationships = list(graph.class_instance_relationships or [])
    rels_by_source_id: dict[UUID, list[ClassInstanceRelationship]] = defaultdict(list)
    rels_by_target_id: dict[UUID, list[ClassInstanceRelationship]] = defaultdict(list)
    for r in relationships:
        rels_by_source_id[r.source_class_instance_id].append(r)
        rels_by_target_id[r.target_class_instance_id].append(r)

    # Ensure relationships are well-formed and correspond to at least one OPG edge.
    edges_by_rel_id: dict[UUID, list[ObjectProjectionGraphEdge]] = defaultdict(list)
    for edge in opg.edges:
        edges_by_rel_id[edge.class_config_relationship_id].append(edge)

    for rel in relationships:
        _validate_relationship_instance(
            rel=rel,
            ocg=ocg,
            edges_by_rel_id=edges_by_rel_id,
            by_ci_id=by_ci_id,
        )

    # Enforce include/multiplicity/selection constraints post-build.
    for edge in opg.edges:
        rel_cfg = _resolve_relationship_cfg(ocg, edge)
        src_cc_id, tgt_cc_id = _relationship_endpoints(rel_cfg, edge.traversal_direction)
        target_node = opg.nodes_by_class_config_id.get(tgt_cc_id)

        for ci in by_ci_id.values():
            if ci.class_config_id != src_cc_id:
                continue
            out_count = _count_edge_targets(
                source_id=ci.id,
                relationship_id=rel_cfg.id,
                target_class_config_id=tgt_cc_id,
                traversal_direction=edge.traversal_direction,
                rels_by_source_id=rels_by_source_id,
                rels_by_target_id=rels_by_target_id,
                by_ci_id=by_ci_id,
            )
            _enforce_edge_constraints(edge=edge, out_count=out_count)
            _enforce_node_selection(target_node=target_node, out_count=out_count, target_cc_id=tgt_cc_id)

    # Reachability: OIG is a rooted traversal product.
    reachable = _reachable_from_root(root_id=root_id, relationships=relationships)
    if reachable != set(by_ci_id.keys()):
        missing = sorted(set(by_ci_id.keys()) - reachable, key=str)
        raise OigValidationError(f"OIG contains unreachable ClassInstances from root: {missing}")

    # Validate ClassInstance attribute correctness (descriptor-driven; relationship attrs excluded).
    relationship_attr_ids_by_cc = _build_relationship_attribute_config_ids_by_class_config_id(
        class_configs_by_id=ocg.class_configs_by_id,
        relationships_by_id=ocg.relationships_by_id,
    )
    portal_include_attr_ids_by_cc = _build_portal_include_relationship_attribute_config_ids_by_class_config_id(
        object_projection_graph=object_projection_graph,
        class_configs_by_id=ocg.class_configs_by_id,
        relationships_by_id=ocg.relationships_by_id,
    )
    soft_ref_include_attr_ids_by_cc = _build_soft_ref_include_relationship_attribute_config_ids_by_class_config_id(
        object_projection_graph=object_projection_graph,
        class_configs_by_id=ocg.class_configs_by_id,
        relationships_by_id=ocg.relationships_by_id,
    )
    required_fk_include_attr_ids_by_cc = (
        _build_required_fk_include_relationship_attribute_config_ids_by_class_config_id(
            object_projection_graph=object_projection_graph,
            class_configs_by_id=ocg.class_configs_by_id,
            relationships_by_id=ocg.relationships_by_id,
        )
    )

    def _include_relationship_attr_ids_for_class(
        class_config_id: UUID,
    ) -> set[UUID] | None:
        ids: set[UUID] = set()
        ids |= portal_include_attr_ids_by_cc.get(class_config_id, set())
        ids |= soft_ref_include_attr_ids_by_cc.get(class_config_id, set())
        ids |= required_fk_include_attr_ids_by_cc.get(class_config_id, set())
        return ids if ids else None

    for ci in by_ci_id.values():
        cc = ocg.class_configs_by_id[ci.class_config_id]
        try:
            validate_class_instance(
                class_instance=ci,
                class_config=cc,
                relationship_attribute_config_ids=relationship_attr_ids_by_cc.get(ci.class_config_id, set()),
                include_relationship_attribute_config_ids=_include_relationship_attr_ids_for_class(ci.class_config_id),
            )
        except ClassInstanceValidationError as e:
            raise OigValidationError(f"Invalid ClassInstance {ci.id}: {e}") from e


def _build_ocg_index(object_config_graph: ObjectConfigGraph) -> _OcgIndex:
    class_configs: dict[UUID, ClassConfig] = {}
    relationships: dict[UUID, ClassConfigRelationship] = {}
    attr_configs: dict[UUID, AttributeConfig] = {}

    for node in object_config_graph.object_config_graph_nodes or []:
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            class_configs[node.class_config.id] = node.class_config
        if node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
            relationships[node.class_config_relationship.id] = node.class_config_relationship

    # Merge ClassConfig-local relationships/attrs defensively.
    for cc in class_configs.values():
        for rel in cc.class_config_relationships or []:
            relationships.setdefault(rel.id, rel)
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is not None:
                attr_configs[link.attribute_config.id] = link.attribute_config

    return _OcgIndex(
        class_configs_by_id=class_configs,
        relationships_by_id=relationships,
        attribute_configs_by_id=attr_configs,
    )


def _build_opg_index(object_projection_graph: ObjectProjectionGraph) -> _OpgIndex:
    nodes_by_cc: dict[UUID, ObjectProjectionGraphNode] = {}
    root: ObjectProjectionGraphNode | None = None
    for node in object_projection_graph.object_projection_graph_nodes or []:
        nodes_by_cc[node.class_config_id] = node
        if node.is_root:
            if root is not None:
                raise OigValidationError("OPG has multiple root nodes")
            root = node
    if root is None:
        raise OigValidationError("OPG missing root node")
    return _OpgIndex(
        root_node=root,
        nodes_by_class_config_id=nodes_by_cc,
        edges=object_projection_graph.object_projection_graph_edges,
    )


def _index_class_instances(
    instances: Iterable[ClassInstance],
) -> dict[UUID, ClassInstance]:
    by_id: dict[UUID, ClassInstance] = {}
    for ci in instances:
        if ci.id in by_id:
            raise OigValidationError(f"Duplicate ClassInstance.id in OIG: {ci.id}")
        by_id[ci.id] = ci
    return by_id


def _resolve_relationship_cfg(ocg: _OcgIndex, edge: ObjectProjectionGraphEdge) -> ClassConfigRelationship:
    rel = ocg.relationships_by_id.get(edge.class_config_relationship_id) or edge.class_config_relationship
    if rel is None:
        raise OigValidationError(f"ClassConfigRelationship not found for edge: {edge.class_config_relationship_id}")
    return rel


def _member_class_config_ids(*, ocg: _OcgIndex, opg: _OpgIndex) -> set[UUID]:
    members: set[UUID] = set(opg.nodes_by_class_config_id.keys())
    for edge in opg.edges:
        rel = _resolve_relationship_cfg(ocg, edge)
        src_cc_id, tgt_cc_id = _relationship_endpoints(rel, edge.traversal_direction)
        members.add(src_cc_id)
        members.add(tgt_cc_id)
    return members


def _relationship_endpoints(
    relationship: ClassConfigRelationship,
    direction: ClassConfigRelationshipDirection,
) -> tuple[UUID, UUID]:
    if direction == ClassConfigRelationshipDirection.forward:
        return relationship.class_config_id, relationship.target_class_config_id
    if direction == ClassConfigRelationshipDirection.reverse:
        return relationship.target_class_config_id, relationship.class_config_id
    raise OigValidationError(f"Unsupported traversal direction: {direction}")


def _validate_relationship_instance(
    *,
    rel: ClassInstanceRelationship,
    ocg: _OcgIndex,
    edges_by_rel_id: Mapping[UUID, list[ObjectProjectionGraphEdge]],
    by_ci_id: Mapping[UUID, ClassInstance],
) -> None:
    rel_cfg = ocg.relationships_by_id.get(rel.class_config_relationship_id)
    if rel_cfg is None:
        raise OigValidationError(f"Relationship config not found: {rel.class_config_relationship_id}")

    src_ci = by_ci_id.get(rel.source_class_instance_id)
    if src_ci is None:
        raise OigValidationError(f"Relationship source instance not found: {rel.source_class_instance_id}")
    tgt_ci = by_ci_id.get(rel.target_class_instance_id)
    if tgt_ci is None:
        raise OigValidationError(f"Relationship target instance not found: {rel.target_class_instance_id}")

    candidate_edges = edges_by_rel_id.get(rel_cfg.id, [])
    if not candidate_edges:
        raise OigValidationError(f"OIG relationship {rel_cfg.id} is not present in OPG edges")

    # Canonical invariant: relationships are stored in forward orientation only.
    if src_ci.class_config_id != rel_cfg.class_config_id or tgt_ci.class_config_id != rel_cfg.target_class_config_id:
        raise OigValidationError(
            f"OIG relationship endpoints must match canonical forward orientation for relationship_id={rel_cfg.id}"
        )


def _count_edge_targets(
    *,
    source_id: UUID,
    relationship_id: UUID,
    target_class_config_id: UUID,
    traversal_direction: ClassConfigRelationshipDirection,
    rels_by_source_id: Mapping[UUID, list[ClassInstanceRelationship]],
    rels_by_target_id: Mapping[UUID, list[ClassInstanceRelationship]],
    by_ci_id: Mapping[UUID, ClassInstance],
) -> int:
    if traversal_direction == ClassConfigRelationshipDirection.forward:
        count = 0
        for rel in rels_by_source_id.get(source_id, []):
            if rel.class_config_relationship_id != relationship_id:
                continue
            tgt = by_ci_id.get(rel.target_class_instance_id)
            if tgt is None:
                continue
            if tgt.class_config_id != target_class_config_id:
                continue
            count += 1
        return count

    if traversal_direction == ClassConfigRelationshipDirection.reverse:
        # Relationships are stored in canonical forward orientation, so reverse traversal counts "incoming" edges.
        count = 0
        for rel in rels_by_target_id.get(source_id, []):
            if rel.class_config_relationship_id != relationship_id:
                continue
            src = by_ci_id.get(rel.source_class_instance_id)
            if src is None:
                continue
            if src.class_config_id != target_class_config_id:
                continue
            count += 1
        return count

    raise OigValidationError(f"Unsupported traversal direction: {traversal_direction}")


def _enforce_edge_constraints(*, edge: ObjectProjectionGraphEdge, out_count: int) -> None:
    if edge.multiplicity == ObjectProjectionGraphEdgeMultiplicity.one and out_count > 1:
        raise OigValidationError(f"Edge multiplicity=ONE violated for edge {edge.id}: got {out_count}")
    if (
        edge.include == ObjectProjectionGraphEdgeInclude.required
        and edge.multiplicity == ObjectProjectionGraphEdgeMultiplicity.one
        and out_count == 0
    ):
        raise OigValidationError(f"Missing required relationship targets for edge {edge.id}")
    if edge.multiplicity == ObjectProjectionGraphEdgeMultiplicity.at_least_1 and out_count == 0:
        raise OigValidationError(f"Edge multiplicity=AT_LEAST_1 violated for edge {edge.id}")


def _enforce_node_selection(
    *,
    target_node: ObjectProjectionGraphNode | None,
    out_count: int,
    target_cc_id: UUID,
) -> None:
    if target_node is None:
        return

    if target_node.selection == ObjectProjectionGraphNodeSelection.one and out_count > 1:
        raise OigValidationError(f"OPG node selection=ONE violated for class_config_id={target_cc_id}: got {out_count}")

    if target_node.selection == ObjectProjectionGraphNodeSelection.top_n:
        n = target_node.top_n or 0
        if n <= 0 and out_count != 0:
            raise OigValidationError(f"OPG node selection=TOP_N requires top_n>0 for class_config_id={target_cc_id}")
        if out_count > n:
            raise OigValidationError(
                f"OPG node selection=TOP_N violated for class_config_id={target_cc_id}: got {out_count} > {n}"
            )


def _reachable_from_root(
    *,
    root_id: UUID,
    relationships: Iterable[ClassInstanceRelationship],
) -> set[UUID]:
    # Connectivity is treated as undirected for reachability:
    # canonical relationship orientation is forward, but OPG traversal may be reverse-rooted.
    adjacency: dict[UUID, list[UUID]] = defaultdict(list)
    for rel in relationships:
        adjacency[rel.source_class_instance_id].append(rel.target_class_instance_id)
        adjacency[rel.target_class_instance_id].append(rel.source_class_instance_id)

    reachable: set[UUID] = {root_id}
    q: deque[UUID] = deque([root_id])
    while q:
        current = q.popleft()
        for nxt in adjacency.get(current, []):
            if nxt in reachable:
                continue
            reachable.add(nxt)
            q.append(nxt)
    return reachable


def _build_relationship_attribute_config_ids_by_class_config_id(
    *,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    owner_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_id = link.attribute_config.id
            prev = owner_by_attr_id.get(attr_id)
            if prev is not None and prev != cc_id:
                raise OigValidationError(
                    f"AttributeConfig {attr_id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_by_attr_id[attr_id] = cc_id

    ids_by_cc: dict[UUID, set[UUID]] = {cc_id: set() for cc_id in class_configs_by_id}
    for rel in relationships_by_id.values():
        for rel_attr in rel.class_config_relationship_attributes or []:
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            owner_cc_id = owner_by_attr_id.get(attr_id)
            if owner_cc_id is None:
                continue
            ids_by_cc.setdefault(owner_cc_id, set()).add(attr_id)

    return ids_by_cc


def _build_portal_include_relationship_attribute_config_ids_by_class_config_id(
    *,
    object_projection_graph: ObjectProjectionGraph,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    portals = object_projection_graph.object_projection_graph_relationships or []
    if not portals:
        return {}

    owner_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_id = link.attribute_config.id
            prev = owner_by_attr_id.get(attr_id)
            if prev is not None and prev != cc_id:
                raise OigValidationError(
                    f"AttributeConfig {attr_id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_by_attr_id[attr_id] = cc_id

    include_by_cc: dict[UUID, set[UUID]] = {}
    for portal in portals:
        rel = relationships_by_id.get(portal.class_config_relationship_id) or portal.class_config_relationship
        if rel is None:
            raise OigValidationError(
                "Portal relationship missing ClassConfigRelationship binding: "
                f"object_projection_graph_id={object_projection_graph.id} class_config_relationship_id={portal.class_config_relationship_id}"
            )

        fk_attr_id: UUID | None = None
        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.direction != ClassConfigRelationshipDirection.forward:
                continue
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            fk_attr_id = rel_attr.attribute_config_id
            break

        if fk_attr_id is None:
            # v0: only FK-based portals can be represented as lane routing primitives.
            # Other portal shapes are allowed at the OPG layer but are not yet validated
            # as data-attribute inclusions in OIG snapshots.
            continue

        owner_cc_id = owner_by_attr_id.get(fk_attr_id)
        if owner_cc_id is None:
            raise OigValidationError(
                "Portal relationship FOREIGN_KEY attribute_config_id not found on any ClassConfig: "
                f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
            )
        if owner_cc_id != rel.class_config_id:
            raise OigValidationError(
                "Portal relationship FOREIGN_KEY attribute must be owned by the relationship source ClassConfig: "
                f"class_config_relationship_id={rel.id} owner_class_config_id={owner_cc_id} expected={rel.class_config_id}"
            )
        include_by_cc.setdefault(owner_cc_id, set()).add(fk_attr_id)

    return include_by_cc


def _build_soft_ref_include_relationship_attribute_config_ids_by_class_config_id(
    *,
    object_projection_graph: ObjectProjectionGraph,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    """
    Derive relationship AttributeConfig ids that must be retained as *data attributes*
    for deterministic SoftRef semantics.

    v0 rule:
    - If a relationship is not represented as an OPG edge (StrongRef), preserve explicit
      FOREIGN_KEY bindings as commit-tracked data on the FK-owning class.
    - Apply when the FK-owning class is a member of the OPG node set.
    - Direction is intentionally ignored (forward/reverse): ownership determines where
      the deterministic FK primitive lives.
    - Never guess field names; only use explicit `ClassConfigRelationshipAttribute` bindings.
    """
    edges = object_projection_graph.object_projection_graph_edges or []
    edge_relationship_ids: set[UUID] = {e.class_config_relationship_id for e in edges if e.class_config_relationship_id}

    node_cc_ids: set[UUID] = {n.class_config_id for n in (object_projection_graph.object_projection_graph_nodes or [])}

    owner_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_id = link.attribute_config.id
            prev = owner_by_attr_id.get(attr_id)
            if prev is not None and prev != cc_id:
                raise OigValidationError(
                    f"AttributeConfig {attr_id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_by_attr_id[attr_id] = cc_id

    include_by_cc: dict[UUID, set[UUID]] = {}

    for rel in relationships_by_id.values():
        if rel.id is None:
            continue
        # Relationship analysis may retain detached cross-graph relationships
        # whose endpoints are not present in this OCG dependency closure.
        # Those are irrelevant for this projection's soft-ref retention.
        if rel.class_config_id not in class_configs_by_id or rel.target_class_config_id not in class_configs_by_id:
            continue
        if rel.id in edge_relationship_ids:
            continue
        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            fk_attr_id = rel_attr.attribute_config_id
            if fk_attr_id is None:
                continue

            owner_cc_id = owner_by_attr_id.get(fk_attr_id)
            if owner_cc_id is None:
                raise OigValidationError(
                    "SoftRef FOREIGN_KEY attribute_config_id not found on any ClassConfig: "
                    f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
                )
            if owner_cc_id not in {
                rel.class_config_id,
                rel.target_class_config_id,
            }:
                continue
            if owner_cc_id not in node_cc_ids:
                continue

            include_by_cc.setdefault(owner_cc_id, set()).add(fk_attr_id)

    return include_by_cc


def _build_required_fk_include_relationship_attribute_config_ids_by_class_config_id(
    *,
    object_projection_graph: ObjectProjectionGraph,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    """
    Retain required FK primitives as data attributes for commit-truth validation.
    """
    node_cc_ids: set[UUID] = {n.class_config_id for n in (object_projection_graph.object_projection_graph_nodes or [])}

    owner_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_id = link.attribute_config.id
            prev = owner_by_attr_id.get(attr_id)
            if prev is not None and prev != cc_id:
                raise OigValidationError(
                    f"AttributeConfig {attr_id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_by_attr_id[attr_id] = cc_id

    def _is_required_fk(rel: ClassConfigRelationship, *, direction: ClassConfigRelationshipDirection) -> bool:
        if rel.class_config_relationship_association_edge is not None:
            return True
        return bool(rel.forward_required)

    include_by_cc: dict[UUID, set[UUID]] = {}
    for rel in relationships_by_id.values():
        # Relationship analysis may retain detached cross-graph relationships
        # whose endpoints are not present in this OCG dependency closure.
        # Those are irrelevant for this projection's required-FK retention.
        if rel.class_config_id not in class_configs_by_id or rel.target_class_config_id not in class_configs_by_id:
            continue
        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            fk_attr_id = rel_attr.attribute_config_id
            if fk_attr_id is None:
                continue
            if not _is_required_fk(rel, direction=rel_attr.direction):
                continue

            owner_cc_id = owner_by_attr_id.get(fk_attr_id)
            if owner_cc_id is None:
                raise OigValidationError(
                    "Required FK attribute_config_id not found on any ClassConfig: "
                    f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
                )
            if owner_cc_id not in node_cc_ids:
                continue
            include_by_cc.setdefault(owner_cc_id, set()).add(fk_attr_id)

    return include_by_cc


__all__ = [
    "OigValidationError",
    "validate_object_instance_graph_against_opg",
]
