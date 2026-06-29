"""Canonical OIG builder (OPG → OIG).

This module is the SSOT for constructing a canonical ObjectInstanceGraph from:
- an ObjectConfigGraph (OCG: class + relationship config),
- an ObjectProjectionGraph (OPG: membership + traversal contract),
- in-memory runtime instances (ModelIntrospection).

Invariant (v0): no DB lookups. Any required instances must be hydrated or provided via registry.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Callable, Iterable, Mapping, Protocol
from uuid import UUID

# Aware Kernel Graph Ontology
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
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
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
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as DescKind,
    AttributeTypeDescriptorRole as DescRole,
)

# Aware Kernel Meta
from aware_meta.graph.config.stable_ids import stable_class_instance_id
from aware_meta_ontology.stable_ids import stable_object_instance_graph_id
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.class_.instance.builder import (
    ClassInstanceBuildProfile,
    ClassInstanceBuildError,
    build_class_instance,
)
from aware_meta.class_.instance.stable_ids import stable_class_instance_relationship_id
from aware_meta.attribute.instance.value.builder import (
    EnumOptionResolver,
    UnionSelection,
)

from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks


# Aware ORM
from aware_orm.models.introspection import ModelIntrospection


class OigBuildError(ValueError):
    pass


class BuildTimings(Protocol):
    def add(self, name: str, duration_s: float) -> object: ...

    def metric(self, key: str, value: object) -> object: ...


@dataclass(frozen=True)
class InstanceRegistry:
    by_id: Mapping[UUID, ModelIntrospection]
    by_class_config_id: Mapping[UUID, list[ModelIntrospection]]

    @classmethod
    def from_instances(
        cls, instances: Iterable[ModelIntrospection]
    ) -> "InstanceRegistry":
        by_id: dict[UUID, ModelIntrospection] = {}
        by_cc: dict[UUID, list[ModelIntrospection]] = {}
        for inst in instances:
            by_id[inst.id] = inst
            cc_id = inst.try_class_config_id()
            if cc_id is not None:
                by_cc.setdefault(cc_id, []).append(inst)
        return cls(by_id=by_id, by_class_config_id=by_cc)


@dataclass(frozen=True)
class _TraversalContextSource(ModelIntrospection):
    source: ModelIntrospection
    values_by_name: Mapping[str, object]

    @property
    def id(self) -> UUID:
        return self.source.id

    def field_is_declared(self, name: str) -> bool:
        return name in self.values_by_name or self.source.field_is_declared(name)

    def field_is_set(self, name: str) -> bool:
        return name in self.values_by_name or self.source.field_is_set(name)

    def try_field_value(
        self, name: str, *, include_unset: bool = False
    ) -> tuple[bool, object]:
        found, value = self.source.try_field_value(name, include_unset=include_unset)
        if found:
            return True, value
        if name in self.values_by_name:
            return True, self.values_by_name[name]
        return False, None

    def try_virtual_value(
        self, attribute_config: AttributeConfig
    ) -> tuple[bool, object]:
        return self.source.try_virtual_value(attribute_config)

    def try_attribute_value(
        self, attribute_config: AttributeConfig
    ) -> tuple[bool, object]:
        found, value = self.source.try_attribute_value(attribute_config)
        if found:
            return True, value
        if attribute_config.name in self.values_by_name:
            return True, self.values_by_name[attribute_config.name]
        return False, None

    def try_class_config_id(self) -> UUID | None:
        return self.source.try_class_config_id()


class RelationshipResolver(Protocol):
    def resolve_targets(
        self,
        *,
        source_instance: ModelIntrospection,
        edge: ObjectProjectionGraphEdge,
        relationship: ClassConfigRelationship,
        reference_field_name: str | None,
        target_class_config_id: UUID,
        registry: InstanceRegistry,
    ) -> list[ModelIntrospection]: ...


class InMemoryRelationshipResolver:
    """
    Default relationship resolver for canonical OIG building.

    Rules:
    - No DB lookups.
    - Prefer hydrated references (`obj.rel`).
    - Optional fallback: when the REFERENCE field is unset/unhydrated, use deterministic FK bindings
      from `ClassConfigRelationship.class_config_relationship_attributes`.
    - Reverse/FK scan traversal is memoized per registry + field to avoid repeated hot-path loops.
    """

    def __init__(
        self, *, attribute_configs_by_id: Mapping[UUID, AttributeConfig] | None = None
    ) -> None:
        self._attribute_configs_by_id = attribute_configs_by_id or {}
        self._reverse_reference_indexes: dict[
            tuple[int, UUID, str], dict[UUID, list[ModelIntrospection]]
        ] = {}
        self._foreign_key_scan_indexes: dict[
            tuple[int, UUID, str], dict[UUID, list[ModelIntrospection]]
        ] = {}

    def _reverse_reference_index(
        self,
        *,
        registry: InstanceRegistry,
        class_config_id: UUID,
        field_name: str,
    ) -> dict[UUID, list[ModelIntrospection]]:
        key = (id(registry), class_config_id, field_name)
        cached = self._reverse_reference_indexes.get(key)
        if cached is not None:
            return cached

        indexed: dict[UUID, list[ModelIntrospection]] = {}
        for candidate in registry.by_class_config_id.get(class_config_id, []):
            _, value = candidate.try_field_value(field_name, include_unset=True)
            seen_target_ids: set[UUID] = set()
            for target in _coerce_targets(value):
                target_id = target.id
                if target_id in seen_target_ids:
                    continue
                seen_target_ids.add(target_id)
                indexed.setdefault(target_id, []).append(candidate)

        self._reverse_reference_indexes[key] = indexed
        return indexed

    def _foreign_key_scan_index(
        self,
        *,
        registry: InstanceRegistry,
        class_config_id: UUID,
        field_name: str,
        relationship_id: UUID,
    ) -> dict[UUID, list[ModelIntrospection]]:
        key = (id(registry), class_config_id, field_name)
        cached = self._foreign_key_scan_indexes.get(key)
        if cached is not None:
            return cached

        indexed: dict[UUID, list[ModelIntrospection]] = {}
        for candidate in registry.by_class_config_id.get(class_config_id, []):
            declared, fk_value = candidate.try_field_value(
                field_name, include_unset=True
            )
            if not declared:
                raise OigBuildError(
                    "Relationship FOREIGN_KEY attribute is not declared on target instance: "
                    f"field={field_name} target_id={candidate.id} rel_id={relationship_id}"
                )
            seen_source_ids: set[UUID] = set()
            for source_id in _coerce_foreign_key_ids(fk_value):
                if source_id in seen_source_ids:
                    continue
                seen_source_ids.add(source_id)
                indexed.setdefault(source_id, []).append(candidate)

        self._foreign_key_scan_indexes[key] = indexed
        return indexed

    def resolve_targets(
        self,
        *,
        source_instance: ModelIntrospection,
        edge: ObjectProjectionGraphEdge,
        relationship: ClassConfigRelationship,
        reference_field_name: str | None,
        target_class_config_id: UUID,
        registry: InstanceRegistry,
    ) -> list[ModelIntrospection]:
        direction = edge.traversal_direction
        if direction == ClassConfigRelationshipDirection.forward:
            return _resolve_targets_forward(
                source_instance=source_instance,
                edge=edge,
                relationship=relationship,
                reference_field_name=reference_field_name,
                target_class_config_id=target_class_config_id,
                registry=registry,
                attribute_configs_by_id=self._attribute_configs_by_id,
                foreign_key_scan_index_getter=self._foreign_key_scan_index,
            )
        if direction == ClassConfigRelationshipDirection.reverse:
            return _resolve_targets_reverse(
                source_instance=source_instance,
                relationship=relationship,
                reference_field_name=reference_field_name,
                registry=registry,
                target_class_config_id=target_class_config_id,
                edge=edge,
                attribute_configs_by_id=self._attribute_configs_by_id,
                reverse_reference_index_getter=self._reverse_reference_index,
                foreign_key_scan_index_getter=self._foreign_key_scan_index,
            )
        raise OigBuildError(f"Unsupported traversal_direction={direction}")


@dataclass(slots=True)
class _OigBuildProfile:
    build_indexes_s: float = 0.0
    build_registry_s: float = 0.0
    queue_walk_s: float = 0.0
    finalize_graph_s: float = 0.0
    queue_pops: int = 0
    edges_visited: int = 0
    targets_resolved: int = 0
    relationships_emitted: int = 0
    class_instances_built: int = 0
    class_instance_cache_hits: int = 0
    class_instance_profile: ClassInstanceBuildProfile = field(
        default_factory=ClassInstanceBuildProfile
    )


def _record_oig_build_profile(
    *,
    timings: BuildTimings | None,
    prefix: str | None,
    profile: _OigBuildProfile | None,
) -> None:
    if timings is None or profile is None:
        return
    timing_prefix = (prefix or "").strip()
    if not timing_prefix:
        return

    metric_prefix = timing_prefix.replace(".", "_")
    timing_values = {
        "build_indexes": profile.build_indexes_s,
        "build_registry": profile.build_registry_s,
        "queue_walk": profile.queue_walk_s,
        "finalize_graph": profile.finalize_graph_s,
        "class_instance.plan_attributes": profile.class_instance_profile.plan_attributes_s,
        "class_instance.materialize_attributes": profile.class_instance_profile.materialize_attributes_s,
    }
    for name, duration_s in timing_values.items():
        if duration_s <= 0:
            continue
        try:
            _ = timings.add(f"{timing_prefix}.{name}", duration_s)
        except Exception:
            pass

    metrics = {
        "queue_pops": profile.queue_pops,
        "edges_visited": profile.edges_visited,
        "targets_resolved": profile.targets_resolved,
        "relationships_emitted": profile.relationships_emitted,
        "class_instances_built": profile.class_instances_built,
        "class_instance_cache_hits": profile.class_instance_cache_hits,
        "class_instance_attr_links_total": profile.class_instance_profile.attr_links_total,
        "class_instance_relationship_attribute_ids_total": profile.class_instance_profile.relationship_attribute_ids_total,
        "class_instance_required_fk_attribute_ids_total": profile.class_instance_profile.required_fk_attribute_ids_total,
        "class_instance_attributes_built": profile.class_instance_profile.attributes_built,
        "class_instance_virtual_attributes_skipped": profile.class_instance_profile.virtual_attributes_skipped,
        "class_instance_relationship_attributes_skipped": profile.class_instance_profile.relationship_attributes_skipped,
        "class_instance_optional_attributes_omitted": profile.class_instance_profile.optional_attributes_omitted,
        "class_instance_default_values_used": profile.class_instance_profile.default_values_used,
    }
    for key, value in metrics.items():
        try:
            _ = timings.metric(f"{metric_prefix}_{key}", value)
        except Exception:
            pass


def build_object_instance_graph(
    *,
    root_instance: ModelIntrospection,
    object_config_graph: ObjectConfigGraph,
    object_projection_graph: ObjectProjectionGraph,
    key: str | None = None,
    name: str,
    description: str,
    oig_id: UUID | None = None,
    instance_registry: Iterable[ModelIntrospection] | None = None,
    relationship_resolver: RelationshipResolver | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
    timings: BuildTimings | None = None,
    timing_key_prefix: str | None = None,
) -> ObjectInstanceGraph:
    """
    Build a canonical ObjectInstanceGraph from:
    - a root runtime instance (in-memory),
    - an OCG (ClassConfig + ClassConfigRelationship SSOT),
    - an OPG (membership + traversal contract).

    Invariant (today): never performs DB lookups. Any required instances must be
    reachable via hydrated references or provided through `instance_registry`.
    """
    build_profile = (
        _OigBuildProfile()
        if timings is not None and (timing_key_prefix or "").strip()
        else None
    )

    indexes_started_at = time.perf_counter() if build_profile is not None else 0.0
    ocg = _build_ocg_index(object_config_graph)
    resolver = relationship_resolver or InMemoryRelationshipResolver(
        attribute_configs_by_id=ocg.attribute_configs_by_id
    )

    opg = _build_opg_index(object_projection_graph)
    relationship_attr_ids_by_cc_id = (
        build_relationship_attribute_config_ids_by_class_config_id(
            class_configs_by_id=ocg.class_configs_by_id,
            relationships_by_id=ocg.relationships_by_id,
        )
    )
    include_relationship_attr_ids_by_cc_id = (
        build_include_relationship_attribute_config_ids_by_class_config_id(
            object_projection_graph=object_projection_graph,
            class_configs_by_id=ocg.class_configs_by_id,
            relationships_by_id=ocg.relationships_by_id,
        )
    )

    edges_by_source_cc_id = _index_edges_by_source(
        edges=object_projection_graph.object_projection_graph_edges,
        relationships_by_id=ocg.relationships_by_id,
    )
    if build_profile is not None:
        build_profile.build_indexes_s += time.perf_counter() - indexes_started_at

    root_node = opg.root_node
    root_cc = ocg.class_configs_by_id.get(root_node.class_config_id)
    if root_cc is None:
        raise OigBuildError(f"Root ClassConfig not found: {root_node.class_config_id}")

    graph_key = key or name
    graph_id = oig_id or stable_object_instance_graph_id(
        object_projection_graph_id=object_projection_graph.id,
        key=graph_key,
    )
    root_id = root_instance.id

    registry_started_at = time.perf_counter() if build_profile is not None else 0.0
    all_instances: list[ModelIntrospection] = [root_instance]
    if instance_registry is not None:
        all_instances.extend(list(instance_registry))
    registry = InstanceRegistry.from_instances(all_instances)
    if build_profile is not None:
        build_profile.build_registry_s += time.perf_counter() - registry_started_at

    visited: dict[tuple[UUID, UUID], ClassInstance] = {}
    relationships: list[ClassInstanceRelationship] = []
    relationship_keys: set[tuple[UUID, UUID, UUID]] = set()

    queue: deque[tuple[ModelIntrospection, UUID, int]] = deque()
    queue.append((root_instance, root_cc.id, 0))

    queue_walk_started_at = time.perf_counter() if build_profile is not None else 0.0
    while queue:
        current_instance, current_cc_id, depth = queue.popleft()
        if build_profile is not None:
            build_profile.queue_pops += 1

        current_ci, current_ci_built = _get_or_build_class_instance(
            object_instance_graph_id=graph_id,
            visited=visited,
            class_config=ocg.class_configs_by_id.get(current_cc_id),
            source=current_instance,
            enum_option_resolver=enum_option_resolver,
            union_selections=union_selections,
            relationship_attribute_config_ids=relationship_attr_ids_by_cc_id.get(
                current_cc_id
            ),
            include_relationship_attribute_config_ids=include_relationship_attr_ids_by_cc_id.get(
                current_cc_id
            ),
            build_profile=(
                build_profile.class_instance_profile
                if build_profile is not None
                else None
            ),
        )
        if build_profile is not None:
            if current_ci_built:
                build_profile.class_instances_built += 1
            else:
                build_profile.class_instance_cache_hits += 1

        for edge in edges_by_source_cc_id.get(current_cc_id, []):
            if build_profile is not None:
                build_profile.edges_visited += 1
            relationship = ocg.relationships_by_id.get(
                edge.class_config_relationship_id
            )
            if relationship is None:
                raise OigBuildError(
                    f"ClassConfigRelationship not found: {edge.class_config_relationship_id}"
                )

            src_cc_id, tgt_cc_id = _relationship_endpoints(
                relationship, edge.traversal_direction
            )
            if src_cc_id != current_cc_id:
                # Edge is attached under a different source in the index; skip defensively.
                continue

            reference_field_name = _reference_field_name_for_relationship(
                relationship=relationship,
                attribute_configs_by_id=ocg.attribute_configs_by_id,
            )

            targets = resolver.resolve_targets(
                source_instance=current_instance,
                edge=edge,
                relationship=relationship,
                reference_field_name=reference_field_name,
                target_class_config_id=tgt_cc_id,
                registry=registry,
            )

            target_node = opg.nodes_by_class_config_id.get(tgt_cc_id)
            targets = _apply_node_selection(targets, target_node)
            try:
                _enforce_edge_cardinality(
                    edge=edge, targets=targets, ref=reference_field_name
                )
            except OigBuildError as exc:
                raise OigBuildError(
                    f"{exc} edge_id={edge.id} relationship_id={edge.class_config_relationship_id} "
                    f"source_instance_id={current_instance.id} source_class_config_id={current_cc_id} "
                    f"target_class_config_id={tgt_cc_id}"
                ) from exc
            if build_profile is not None:
                build_profile.targets_resolved += len(targets)

            for target_instance in targets:
                target_id = target_instance.id

                target_cc = ocg.class_configs_by_id.get(tgt_cc_id)
                if target_cc is None:
                    raise OigBuildError(f"Target ClassConfig not found: {tgt_cc_id}")

                target_key = (tgt_cc_id, target_id)
                newly_discovered = target_key not in visited
                target_source = _with_traversal_context_values(
                    source=target_instance,
                    target_class=target_cc,
                    relationship=relationship,
                    source_instance=current_instance,
                    attribute_configs_by_id=ocg.attribute_configs_by_id,
                )

                target_ci, target_ci_built = _get_or_build_class_instance(
                    object_instance_graph_id=graph_id,
                    visited=visited,
                    class_config=target_cc,
                    source=target_source,
                    enum_option_resolver=enum_option_resolver,
                    union_selections=union_selections,
                    relationship_attribute_config_ids=relationship_attr_ids_by_cc_id.get(
                        tgt_cc_id
                    ),
                    include_relationship_attribute_config_ids=include_relationship_attr_ids_by_cc_id.get(
                        tgt_cc_id
                    ),
                    build_profile=(
                        build_profile.class_instance_profile
                        if build_profile is not None
                        else None
                    ),
                )
                if build_profile is not None:
                    if target_ci_built:
                        build_profile.class_instances_built += 1
                    else:
                        build_profile.class_instance_cache_hits += 1

                canonical_source_ci_id, canonical_target_ci_id = (
                    _canonical_relationship_endpoints(
                        edge=edge,
                        current_ci=current_ci,
                        target_ci=target_ci,
                    )
                )
                rel_key = (
                    relationship.id,
                    canonical_source_ci_id,
                    canonical_target_ci_id,
                )
                if rel_key not in relationship_keys:
                    relationship_keys.add(rel_key)

                    with disable_change_tracking_hooks():
                        relationships.append(
                            ClassInstanceRelationship(
                                id=stable_class_instance_relationship_id(
                                    class_config_relationship_id=relationship.id,
                                    source_class_instance_id=canonical_source_ci_id,
                                    target_class_instance_id=canonical_target_ci_id,
                                ),
                                object_instance_graph_id=graph_id,
                                class_config_relationship_id=relationship.id,
                                source_class_instance_id=canonical_source_ci_id,
                                target_class_instance_id=canonical_target_ci_id,
                            )
                        )
                    if build_profile is not None:
                        build_profile.relationships_emitted += 1

                next_depth = depth + 1
                if edge.depth_limit is not None and next_depth > edge.depth_limit:
                    continue

                if newly_discovered:
                    queue.append((target_instance, tgt_cc_id, next_depth))
    if build_profile is not None:
        build_profile.queue_walk_s += time.perf_counter() - queue_walk_started_at

    root_ci = visited[(root_cc.id, root_id)]
    finalize_started_at = time.perf_counter() if build_profile is not None else 0.0
    graph = build_object_instance_graph_from_class_instances(
        key=graph_key,
        name=name,
        description=description,
        object_config_graph_id=object_config_graph.id,
        object_projection_graph_id=object_projection_graph.id,
        root_class_instance=root_ci,
        class_instances=list(visited.values()),
        class_instance_relationships=relationships,
        oig_id=graph_id,
    )
    if build_profile is not None:
        build_profile.finalize_graph_s += time.perf_counter() - finalize_started_at
    _record_oig_build_profile(
        timings=timings,
        prefix=timing_key_prefix,
        profile=build_profile,
    )
    return graph


def build_object_instance_graph_from_class_instances(
    *,
    key: str | None = None,
    name: str,
    description: str,
    object_config_graph_id: UUID,
    object_projection_graph_id: UUID,
    root_class_instance: ClassInstance,
    class_instances: list[ClassInstance],
    class_instance_relationships: list[ClassInstanceRelationship],
    oig_id: UUID | None = None,
) -> ObjectInstanceGraph:
    # Canonical OIG snapshots are pure in-memory artifacts; avoid implicit
    # session binding side effects (global identity map pollution, slow deep copies).
    graph_key = key or name
    graph_id = oig_id or stable_object_instance_graph_id(
        object_projection_graph_id=object_projection_graph_id,
        key=graph_key,
    )
    with disable_change_tracking_hooks():
        with disable_autobind():
            graph = ObjectInstanceGraph(
                id=graph_id,
                key=graph_key,
                name=name,
                description=description,
                object_projection_graph_id=object_projection_graph_id,
                root_class_instance_id=root_class_instance.id,
                root_class_instance=root_class_instance,
                class_instances=class_instances,
                class_instance_relationships=class_instance_relationships,
                hash="",
            )

    index = build_index(graph)
    graph.hash = compute_hash(graph, index=index)
    return graph


def _root_class_config_id_from_object_projection_graph(
    *,
    object_projection_graph: ObjectProjectionGraph,
) -> UUID:
    root_nodes = [
        node
        for node in object_projection_graph.object_projection_graph_nodes
        if node.is_root
    ]
    if len(root_nodes) != 1:
        raise OigBuildError(
            "Rooted OIG base requires exactly one root ObjectProjectionGraphNode; "
            + f"have={len(root_nodes)} object_projection_graph_id={object_projection_graph.id}"
        )
    return root_nodes[0].class_config_id


def build_rooted_object_instance_graph_base(
    *,
    key: str,
    name: str = "EMPTY",
    description: str = "EMPTY",
    object_config_graph: ObjectConfigGraph | None = None,
    object_projection_graph: ObjectProjectionGraph | None = None,
    object_config_graph_id: UUID | None = None,
    object_projection_graph_id: UUID | None = None,
    root_source_object_id: UUID,
    root_class_config_id: UUID | None = None,
    oig_id: UUID | None = None,
) -> ObjectInstanceGraph:
    """
    Build a rooted canonical ObjectInstanceGraph base snapshot.

    Empty OIGs are not allowed. The returned graph always contains one root
    ClassInstance with no attributes/relationships yet.
    """
    ocg_id = (
        object_config_graph_id
        if object_config_graph_id is not None
        else getattr(object_config_graph, "id", None)
    )
    if ocg_id is None:
        raise OigBuildError("ObjectConfigGraph id is required")
    opg_id = (
        object_projection_graph_id
        if object_projection_graph_id is not None
        else getattr(object_projection_graph, "id", None)
    )
    if opg_id is None:
        raise OigBuildError("ObjectProjectionGraph id is required")
    if object_projection_graph is None:
        raise OigBuildError("ObjectProjectionGraph with a root node is required")
    root_cc_id = (
        root_class_config_id
        or _root_class_config_id_from_object_projection_graph(
            object_projection_graph=object_projection_graph
        )
    )
    graph_id = oig_id or stable_object_instance_graph_id(
        object_projection_graph_id=opg_id,
        key=key,
    )
    root_class_instance_id = stable_class_instance_id(
        object_instance_graph_id=graph_id,
        class_config_id=root_cc_id,
        source_object_id=root_source_object_id,
    )
    with disable_change_tracking_hooks():
        with disable_autobind():
            root_class_instance = ClassInstance(
                id=root_class_instance_id,
                object_instance_graph_id=graph_id,
                class_config_id=root_cc_id,
                source_object_id=root_source_object_id,
                class_instance_attributes=[],
            )
            graph = ObjectInstanceGraph(
                id=graph_id,
                key=key,
                name=name,
                description=description,
                object_projection_graph_id=opg_id,
                root_class_instance_id=root_class_instance.id,
                root_class_instance=root_class_instance,
                class_instances=[root_class_instance],
                class_instance_relationships=[],
                hash="",
            )
    index = build_index(graph)
    graph.hash = compute_hash(graph, index=index)
    return graph


def build_object_instance_graph_empty(
    *,
    name: str = "EMPTY",
    description: str = "EMPTY",
    object_config_graph: ObjectConfigGraph | None = None,
    object_projection_graph: ObjectProjectionGraph | None = None,
    object_config_graph_id: UUID | None = None,
    object_projection_graph_id: UUID | None = None,
    oig_id: UUID | None = None,
) -> ObjectInstanceGraph:
    raise OigBuildError(
        "build_object_instance_graph_empty has been removed. "
        + "ObjectInstanceGraph must be rooted; use build_rooted_object_instance_graph_base."
    )


def build_empty(
    *,
    name: str = "EMPTY",
    description: str = "EMPTY",
    object_config_graph: ObjectConfigGraph | None = None,
    object_projection_graph: ObjectProjectionGraph | None = None,
    object_config_graph_id: UUID | None = None,
    object_projection_graph_id: UUID | None = None,
    oig_id: UUID | None = None,
) -> ObjectInstanceGraph:
    raise OigBuildError(
        "build_empty has been removed. ObjectInstanceGraph must be rooted."
    )


@dataclass(frozen=True)
class _OcgIndex:
    class_configs_by_id: Mapping[UUID, ClassConfig]
    relationships_by_id: Mapping[UUID, ClassConfigRelationship]
    attribute_configs_by_id: Mapping[UUID, AttributeConfig]


def _build_ocg_index(object_config_graph: ObjectConfigGraph) -> _OcgIndex:
    class_configs: dict[UUID, ClassConfig] = {}
    relationships: dict[UUID, ClassConfigRelationship] = {}
    attr_configs: dict[UUID, AttributeConfig] = {}

    for node in object_config_graph.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
        ):
            class_configs[node.class_config.id] = node.class_config
        if (
            node.type == ObjectConfigGraphNodeType.relationship
            and node.class_config_relationship is not None
        ):
            relationships[node.class_config_relationship.id] = (
                node.class_config_relationship
            )

    # Cross-OCG relationships are stored under `ObjectConfigGraph.object_config_graph_relationships`.
    # Include them so OPG edges can resolve detached relationships without requiring a prior
    # runtime-derivation pass that attaches them to ClassConfig objects.
    for ocg_rel in object_config_graph.object_config_graph_relationships:
        for rel in ocg_rel.class_config_relationships:
            if rel is None or rel.id is None:
                continue
            relationships.setdefault(rel.id, rel)

    # Relationships are also available under ClassConfig; merge to be safe.
    for cc in class_configs.values():
        for rel in cc.class_config_relationships:
            relationships.setdefault(rel.id, rel)
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is not None:
                attr_configs[link.attribute_config.id] = link.attribute_config

    return _OcgIndex(
        class_configs_by_id=class_configs,
        relationships_by_id=relationships,
        attribute_configs_by_id=attr_configs,
    )


@dataclass(frozen=True)
class _OpgIndex:
    root_node: ObjectProjectionGraphNode
    nodes_by_class_config_id: Mapping[UUID, ObjectProjectionGraphNode]
    edges: list[ObjectProjectionGraphEdge]


def _build_opg_index(object_projection_graph: ObjectProjectionGraph) -> _OpgIndex:
    nodes_by_cc: dict[UUID, ObjectProjectionGraphNode] = {}
    root: ObjectProjectionGraphNode | None = None
    for n in object_projection_graph.object_projection_graph_nodes:
        nodes_by_cc[n.class_config_id] = n
        if n.is_root:
            if root is not None:
                raise OigBuildError("ObjectProjectionGraph has multiple root nodes")
            root = n
    if root is None:
        raise OigBuildError("ObjectProjectionGraph missing root node")
    return _OpgIndex(
        root_node=root,
        nodes_by_class_config_id=nodes_by_cc,
        edges=list(object_projection_graph.object_projection_graph_edges),
    )


def _index_edges_by_source(
    *,
    edges: list[ObjectProjectionGraphEdge],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, list[ObjectProjectionGraphEdge]]:
    edges_by_src: dict[UUID, list[ObjectProjectionGraphEdge]] = {}
    for edge in edges:
        rel = (
            relationships_by_id.get(edge.class_config_relationship_id)
            or edge.class_config_relationship
        )
        if rel is None:
            raise OigBuildError(
                f"ClassConfigRelationship not found for edge: {edge.class_config_relationship_id}"
            )
        src_cc_id, _ = _relationship_endpoints(rel, edge.traversal_direction)
        edges_by_src.setdefault(src_cc_id, []).append(edge)
    return edges_by_src


def _relationship_endpoints(
    relationship: ClassConfigRelationship,
    direction: ClassConfigRelationshipDirection,
) -> tuple[UUID, UUID]:
    if direction == ClassConfigRelationshipDirection.forward:
        return relationship.class_config_id, relationship.target_class_config_id
    if direction == ClassConfigRelationshipDirection.reverse:
        return relationship.target_class_config_id, relationship.class_config_id
    raise OigBuildError(f"Unsupported direction={direction}")


def _reference_field_name_for_relationship(
    *,
    relationship: ClassConfigRelationship,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> str:
    attr_cfg = _reference_attribute_config_for_relationship(
        relationship=relationship,
        attribute_configs_by_id=attribute_configs_by_id,
    )
    _enforce_single_relationship_target_class(
        relationship=relationship,
        reference_attribute_config=attr_cfg,
    )
    return attr_cfg.name


def _reference_attribute_config_for_relationship(
    *,
    relationship: ClassConfigRelationship,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> AttributeConfig:
    # Canonical relationships define the forward reference attribute.
    for rel_attr in relationship.class_config_relationship_attributes:
        if rel_attr.direction != ClassConfigRelationshipDirection.forward:
            continue
        if rel_attr.role.value != "reference":
            continue
        attr_id = rel_attr.attribute_config_id
        if attr_id is None:
            raise OigBuildError(
                f"Relationship {relationship.id} missing attribute_config_id for REFERENCE attribute"
            )
        attr_cfg = attribute_configs_by_id.get(attr_id)
        if attr_cfg is None:
            raise OigBuildError(
                f"Relationship {relationship.id} REFERENCE AttributeConfig not found: {attr_id}"
            )
        return attr_cfg
    raise OigBuildError(
        f"Relationship {relationship.id} missing FORWARD REFERENCE attribute"
    )


def _enforce_single_relationship_target_class(
    *,
    relationship: ClassConfigRelationship,
    reference_attribute_config: AttributeConfig,
) -> None:
    """
    v0 honesty rule:
    Relationship attributes must resolve to exactly 1 target ClassConfig.

    This prevents ambiguous/polymorphic relationship graphs (e.g. union of multiple class targets).
    """
    class_config_ids = _class_config_ids_from_descriptor(
        reference_attribute_config.type_descriptor
    )
    if len(class_config_ids) != 1:
        raise OigBuildError(
            f"Relationship attribute '{reference_attribute_config.name}' must resolve to exactly 1 class_config_id, "
            f"got {sorted([str(i) for i in class_config_ids])}"
        )
    only = next(iter(class_config_ids))
    if only != relationship.target_class_config_id:
        raise OigBuildError(
            f"Relationship attribute '{reference_attribute_config.name}' targets class_config_id={only} "
            f"but relationship.target_class_config_id={relationship.target_class_config_id}"
        )


def _class_config_ids_from_descriptor(desc: AttributeTypeDescriptor) -> set[UUID]:
    if desc.kind == DescKind.class_:
        return {desc.class_config_id} if desc.class_config_id is not None else set()

    if desc.kind == DescKind.collection:
        collection_out: set[UUID] = set()
        for link in desc.child_links or []:
            if link.role != DescRole.element:
                continue
            collection_out |= _class_config_ids_from_descriptor(link.child)
        return collection_out

    if desc.kind == DescKind.union:
        union_out: set[UUID] = set()
        for link in desc.child_links or []:
            if link.role != DescRole.member:
                continue
            union_out |= _class_config_ids_from_descriptor(link.child)
        return union_out

    return set()


def _canonical_relationship_endpoints(
    *,
    edge: ObjectProjectionGraphEdge,
    current_ci: ClassInstance,
    target_ci: ClassInstance,
) -> tuple[UUID, UUID]:
    """
    Store ClassInstanceRelationships in canonical forward orientation:
    relationship.class_config_id -> relationship.target_class_config_id.

    This keeps the OIG topology stable regardless of OPG traversal direction.
    """
    if edge.traversal_direction == ClassConfigRelationshipDirection.forward:
        return current_ci.id, target_ci.id
    if edge.traversal_direction == ClassConfigRelationshipDirection.reverse:
        return target_ci.id, current_ci.id
    raise OigBuildError(f"Unsupported traversal_direction={edge.traversal_direction}")


def _build_relationship_attribute_config_ids_by_class_config_id(
    *,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    """
    Derive relationship AttributeConfig ids per ClassConfig.

    Canonical note:
    - Relationship attribute bindings are SSOT on ClassConfigRelationship.class_config_relationship_attributes.
    - ClassConfig objects may not carry `class_config_relationships` directly (OCG stores relationships as nodes).
    - ClassInstance building must *not* treat relationship attributes as data attributes; they are modeled as
      ClassInstanceRelationship instead.
    """
    owner_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_id = link.attribute_config.id
            prev = owner_by_attr_id.get(attr_id)
            if prev is not None and prev != cc_id:
                raise OigBuildError(
                    f"AttributeConfig {attr_id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_by_attr_id[attr_id] = cc_id

    ids_by_cc: dict[UUID, set[UUID]] = {cc_id: set() for cc_id in class_configs_by_id}
    for rel in relationships_by_id.values():
        for rel_attr in rel.class_config_relationship_attributes:
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            owner_cc_id = owner_by_attr_id.get(attr_id)
            if owner_cc_id is None:
                continue
            ids_by_cc.setdefault(owner_cc_id, set()).add(attr_id)

    return ids_by_cc


def build_relationship_attribute_config_ids_by_class_config_id(
    *,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    """
    Public relationship-attribute classification rail for ClassInstance builders.

    Relationship FK/reference attributes are excluded from data snapshots by default;
    callers pair this map with
    `build_include_relationship_attribute_config_ids_by_class_config_id` when a
    projection must retain selected FK scalars as commit truth.
    """
    return _build_relationship_attribute_config_ids_by_class_config_id(
        class_configs_by_id=class_configs_by_id,
        relationships_by_id=relationships_by_id,
    )


def _build_portal_include_relationship_attribute_config_ids_by_class_config_id(
    *,
    object_projection_graph: ObjectProjectionGraph,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    """
    Derive relationship AttributeConfig ids that must be retained as *data attributes*
    when the OPG models a ClassConfigRelationship as a cross-projection portal.

    v0 rule:
    - Only FORWARD FOREIGN_KEY bindings are retained (typically `<ref>_id`), because they
      are the deterministic lane routing primitive required by runtime without DB lookups.
    """
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
                raise OigBuildError(
                    f"AttributeConfig {attr_id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_by_attr_id[attr_id] = cc_id

    include_by_cc: dict[UUID, set[UUID]] = {}

    for portal in portals:
        rel = (
            relationships_by_id.get(portal.class_config_relationship_id)
            or portal.class_config_relationship
        )
        if rel is None:
            raise OigBuildError(
                "Portal relationship missing ClassConfigRelationship binding: "
                f"object_projection_graph_id={object_projection_graph.id} class_config_relationship_id={portal.class_config_relationship_id}"
            )

        fk_attr_id: UUID | None = None
        for rel_attr in rel.class_config_relationship_attributes:
            if rel_attr.direction != ClassConfigRelationshipDirection.forward:
                continue
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            fk_attr_id = rel_attr.attribute_config_id
            break

        if fk_attr_id is None:
            # v0: only FK-based portals can be retained as lane routing primitives.
            # Other portal shapes (e.g. reverse or collection-backed) are supported
            # at the OPG layer but are not yet representable in a single-lane OIG
            # snapshot without additional runtime machinery.
            continue

        owner_cc_id = owner_by_attr_id.get(fk_attr_id)
        if owner_cc_id is None:
            raise OigBuildError(
                "Portal relationship FOREIGN_KEY attribute_config_id not found on any ClassConfig: "
                f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
            )
        if owner_cc_id != rel.class_config_id:
            raise OigBuildError(
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
    edge_relationship_ids: set[UUID] = {
        e.class_config_relationship_id for e in edges if e.class_config_relationship_id
    }

    node_cc_ids: set[UUID] = {
        n.class_config_id
        for n in (object_projection_graph.object_projection_graph_nodes or [])
    }

    # AttributeConfig.id -> owner_class_id
    owner_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_id = link.attribute_config.id
            prev = owner_by_attr_id.get(attr_id)
            if prev is not None and prev != cc_id:
                raise OigBuildError(
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
        if (
            rel.class_config_id not in class_configs_by_id
            or rel.target_class_config_id not in class_configs_by_id
        ):
            continue
        if rel.id in edge_relationship_ids:
            # StrongRef in this projection: relationship truth is carried as a relationship instance.
            continue
        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            fk_attr_id = rel_attr.attribute_config_id
            if fk_attr_id is None:
                continue

            owner_cc_id = owner_by_attr_id.get(fk_attr_id)
            if owner_cc_id is None:
                raise OigBuildError(
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
    Retain required FK primitives as data attributes for commit truth.

    This keeps commit payloads self-contained for portal/hard-boundary contexts even
    when relationship edges are present.
    """
    node_cc_ids: set[UUID] = {
        n.class_config_id
        for n in (object_projection_graph.object_projection_graph_nodes or [])
    }

    owner_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_id = link.attribute_config.id
            prev = owner_by_attr_id.get(attr_id)
            if prev is not None and prev != cc_id:
                raise OigBuildError(
                    f"AttributeConfig {attr_id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_by_attr_id[attr_id] = cc_id

    def _is_required_fk(
        rel: ClassConfigRelationship, *, direction: ClassConfigRelationshipDirection
    ) -> bool:
        if rel.class_config_relationship_association_edge is not None:
            return True
        return bool(rel.forward_required)

    include_by_cc: dict[UUID, set[UUID]] = {}
    for rel in relationships_by_id.values():
        # Relationship analysis may retain detached cross-graph relationships
        # whose endpoints are not present in this OCG dependency closure.
        # Those are irrelevant for this projection's required-FK retention.
        if (
            rel.class_config_id not in class_configs_by_id
            or rel.target_class_config_id not in class_configs_by_id
        ):
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
                raise OigBuildError(
                    "Required FK attribute_config_id not found on any ClassConfig: "
                    f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
                )
            if owner_cc_id not in node_cc_ids:
                continue
            include_by_cc.setdefault(owner_cc_id, set()).add(fk_attr_id)

    return include_by_cc


def build_include_relationship_attribute_config_ids_by_class_config_id(
    *,
    object_projection_graph: ObjectProjectionGraph,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> dict[UUID, set[UUID]]:
    """
    Public include rail for relationship FK scalars retained in OIG attributes.

    This is intentionally projection-driven. Portal FKs, deterministic SoftRef FKs,
    and required FK primitives remain data attributes even when the relationship
    topology itself is not traversed by this projection.
    """
    include_by_cc: dict[UUID, set[UUID]] = {}
    include_sources = (
        _build_portal_include_relationship_attribute_config_ids_by_class_config_id(
            object_projection_graph=object_projection_graph,
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=relationships_by_id,
        ),
        _build_soft_ref_include_relationship_attribute_config_ids_by_class_config_id(
            object_projection_graph=object_projection_graph,
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=relationships_by_id,
        ),
        _build_required_fk_include_relationship_attribute_config_ids_by_class_config_id(
            object_projection_graph=object_projection_graph,
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=relationships_by_id,
        ),
    )
    for source in include_sources:
        for class_config_id, attribute_config_ids in source.items():
            include_by_cc.setdefault(class_config_id, set()).update(
                attribute_config_ids
            )
    return include_by_cc


def _with_traversal_context_values(
    *,
    source: ModelIntrospection,
    target_class: ClassConfig,
    relationship: ClassConfigRelationship,
    source_instance: ModelIntrospection,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
) -> ModelIntrospection:
    target_attribute_config_ids = {
        link.attribute_config_id
        for link in target_class.class_config_attribute_configs
        if link.attribute_config_id is not None
    }
    values_by_name: dict[str, object] = {}
    for rel_attr in relationship.class_config_relationship_attributes or []:
        if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
            continue
        attribute_config_id = rel_attr.attribute_config_id
        if (
            attribute_config_id is None
            or attribute_config_id not in target_attribute_config_ids
        ):
            continue
        attribute_config = rel_attr.attribute_config or attribute_configs_by_id.get(
            attribute_config_id
        )
        if attribute_config is None or not attribute_config.name:
            continue
        found, _ = source.try_attribute_value(attribute_config)
        if found:
            continue
        values_by_name[attribute_config.name] = source_instance.id
    if not values_by_name:
        return source
    return _TraversalContextSource(source=source, values_by_name=values_by_name)


def _get_or_build_class_instance(
    *,
    object_instance_graph_id: UUID,
    visited: dict[tuple[UUID, UUID], ClassInstance],
    class_config: ClassConfig | None,
    source: ModelIntrospection,
    enum_option_resolver: EnumOptionResolver | None,
    union_selections: dict[str, UnionSelection] | None,
    relationship_attribute_config_ids: Iterable[UUID] | None = None,
    include_relationship_attribute_config_ids: Iterable[UUID] | None = None,
    build_profile: ClassInstanceBuildProfile | None = None,
) -> tuple[ClassInstance, bool]:
    if class_config is None:
        raise OigBuildError("Missing ClassConfig for instance build")
    inst_id = source.id

    key = (class_config.id, inst_id)
    existing = visited.get(key)
    if existing is not None:
        return existing, False

    try:
        ci = build_class_instance(
            object_instance_graph_id=object_instance_graph_id,
            class_config=class_config,
            source=source,
            enum_option_resolver=enum_option_resolver,
            union_selections=union_selections,
            relationship_attribute_config_ids=relationship_attribute_config_ids,
            include_relationship_attribute_config_ids=include_relationship_attribute_config_ids,
            build_profile=build_profile,
        )
    except ClassInstanceBuildError as e:
        raise OigBuildError(str(e)) from e
    visited[key] = ci
    return ci, True


def _apply_node_selection(
    targets: list[ModelIntrospection], node: ObjectProjectionGraphNode | None
) -> list[ModelIntrospection]:
    if node is None:
        return targets
    if node.selection == ObjectProjectionGraphNodeSelection.all:
        return targets
    if node.selection == ObjectProjectionGraphNodeSelection.one:
        if len(targets) > 1:
            raise OigBuildError(
                f"OPG node selection=ONE but got {len(targets)} targets for class_config_id={node.class_config_id}"
            )
        return targets
    if node.selection == ObjectProjectionGraphNodeSelection.top_n:
        n = node.top_n or 0
        if n <= 0:
            return []
        return sorted(targets, key=lambda t: str(t.id))[:n]
    return targets


def _enforce_edge_cardinality(
    *,
    edge: ObjectProjectionGraphEdge,
    targets: list[ModelIntrospection],
    ref: str | None,
) -> None:
    if (
        edge.multiplicity == ObjectProjectionGraphEdgeMultiplicity.one
        and len(targets) > 1
    ):
        raise OigBuildError(
            f"Edge multiplicity=ONE but got {len(targets)} targets (ref={ref})"
        )

    # `include=REQUIRED` means the edge must be representable in the projection, but
    # "no targets" is valid for MANY edges (an empty list). Use multiplicity to enforce
    # non-emptiness (`ONE` / `AT_LEAST_1`) rather than `include`.
    if (
        edge.include == ObjectProjectionGraphEdgeInclude.required
        and edge.multiplicity == ObjectProjectionGraphEdgeMultiplicity.one
        and not targets
    ):
        raise OigBuildError(f"Missing required relationship targets (ref={ref})")

    if (
        edge.multiplicity == ObjectProjectionGraphEdgeMultiplicity.at_least_1
        and not targets
    ):
        raise OigBuildError(
            f"Edge multiplicity=AT_LEAST_1 but got 0 targets (ref={ref})"
        )


def _resolve_targets_forward(
    *,
    source_instance: ModelIntrospection,
    edge: ObjectProjectionGraphEdge,
    relationship: ClassConfigRelationship,
    reference_field_name: str | None,
    target_class_config_id: UUID,
    registry: InstanceRegistry,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    foreign_key_scan_index_getter: (
        Callable[..., Mapping[UUID, list[ModelIntrospection]]] | None
    ) = None,
) -> list[ModelIntrospection]:
    role = edge.attribute_role
    if role == ObjectProjectionGraphAttributeRole.reference:
        if reference_field_name is None:
            return []

        declared, value = source_instance.try_field_value(
            reference_field_name, include_unset=True
        )
        if not declared:
            raise OigBuildError(
                "Relationship REFERENCE attribute is not declared on source instance: "
                f"field={reference_field_name} source_id={source_instance.id} rel_id={relationship.id}"
            )
        targets = _coerce_targets(value)
        if targets:
            return targets

        # Only attempt FK-based fallback when the reference field is not explicitly set.
        # This avoids overriding explicitly-empty relationship state and prevents
        # accidental inference for relationship types that aren't representable by a single FK.
        try:
            is_set = source_instance.field_is_set(reference_field_name)
        except Exception:
            is_set = True
        if is_set:
            return []

        return _resolve_targets_via_foreign_key(
            source_instance=source_instance,
            relationship=relationship,
            traversal_direction=edge.traversal_direction,
            target_class_config_id=target_class_config_id,
            registry=registry,
            attribute_configs_by_id=attribute_configs_by_id,
            require_binding=False,
            foreign_key_scan_index_getter=foreign_key_scan_index_getter,
        )

    if role == ObjectProjectionGraphAttributeRole.foreign_key:
        return _resolve_targets_via_foreign_key(
            source_instance=source_instance,
            relationship=relationship,
            traversal_direction=edge.traversal_direction,
            target_class_config_id=target_class_config_id,
            registry=registry,
            attribute_configs_by_id=attribute_configs_by_id,
            require_binding=True,
            foreign_key_scan_index_getter=foreign_key_scan_index_getter,
        )

    raise OigBuildError(f"Unsupported attribute_role={role}")


def _resolve_targets_reverse(
    *,
    source_instance: ModelIntrospection,
    relationship: ClassConfigRelationship,
    reference_field_name: str | None,
    registry: InstanceRegistry,
    target_class_config_id: UUID,
    edge: ObjectProjectionGraphEdge,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    reverse_reference_index_getter: (
        Callable[..., Mapping[UUID, list[ModelIntrospection]]] | None
    ) = None,
    foreign_key_scan_index_getter: (
        Callable[..., Mapping[UUID, list[ModelIntrospection]]] | None
    ) = None,
) -> list[ModelIntrospection]:
    if reference_field_name is None:
        return []

    # If the edge explicitly requests FK traversal, prefer deterministic FK bindings
    # (avoids requiring forward ref hydration for reverse traversal).
    if edge.attribute_role == ObjectProjectionGraphAttributeRole.foreign_key:
        return _resolve_targets_via_foreign_key(
            source_instance=source_instance,
            relationship=relationship,
            traversal_direction=edge.traversal_direction,
            target_class_config_id=target_class_config_id,
            registry=registry,
            attribute_configs_by_id=attribute_configs_by_id,
            require_binding=True,
            foreign_key_scan_index_getter=foreign_key_scan_index_getter,
        )

    # Reverse traversal: find forward-source instances that reference the current instance.
    current_id = source_instance.id

    forward_source_cc_id = relationship.class_config_id
    if reverse_reference_index_getter is not None:
        index = reverse_reference_index_getter(
            registry=registry,
            class_config_id=forward_source_cc_id,
            field_name=reference_field_name,
        )
        return list(index.get(current_id, ()))

    candidates = registry.by_class_config_id.get(forward_source_cc_id, [])
    matches: list[ModelIntrospection] = []
    for cand in candidates:
        _, value = cand.try_field_value(reference_field_name, include_unset=True)
        for target in _coerce_targets(value):
            if target.id == current_id:
                matches.append(cand)
                break
    return matches


def _resolve_targets_via_foreign_key(
    *,
    source_instance: ModelIntrospection,
    relationship: ClassConfigRelationship,
    traversal_direction: ClassConfigRelationshipDirection,
    target_class_config_id: UUID,
    registry: InstanceRegistry,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    require_binding: bool,
    foreign_key_scan_index_getter: (
        Callable[..., Mapping[UUID, list[ModelIntrospection]]] | None
    ) = None,
) -> list[ModelIntrospection]:
    """
    Resolve relationship targets using explicit FOREIGN_KEY attribute bindings.

    Rules:
    - Never guess FK field names (`*_id` heuristics are forbidden).
    - Supports two deterministic shapes:
      1) FK on the traversal source (direct lookup by id -> registry).
      2) FK on the traversal target (scan target instances for fk == source.id).
    """

    if traversal_direction == ClassConfigRelationshipDirection.forward:
        direct_fk_dir = ClassConfigRelationshipDirection.forward
        scan_fk_dir = ClassConfigRelationshipDirection.reverse
    elif traversal_direction == ClassConfigRelationshipDirection.reverse:
        direct_fk_dir = ClassConfigRelationshipDirection.reverse
        scan_fk_dir = ClassConfigRelationshipDirection.forward
    else:
        raise OigBuildError(f"Unsupported traversal_direction={traversal_direction}")

    direct_fk = _try_fk_field_name_for_relationship(
        relationship=relationship,
        direction=direct_fk_dir,
        attribute_configs_by_id=attribute_configs_by_id,
        strict=require_binding,
    )
    if direct_fk is not None:
        declared, fk_value = source_instance.try_field_value(
            direct_fk, include_unset=True
        )
        if not declared:
            raise OigBuildError(
                "Relationship FOREIGN_KEY attribute is not declared on source instance: "
                f"field={direct_fk} source_id={source_instance.id} rel_id={relationship.id}"
            )
        return _resolve_ids_to_instances(fk_value, registry)

    scan_fk = _try_fk_field_name_for_relationship(
        relationship=relationship,
        direction=scan_fk_dir,
        attribute_configs_by_id=attribute_configs_by_id,
        strict=require_binding,
    )
    if scan_fk is not None:
        source_id = source_instance.id
        if foreign_key_scan_index_getter is not None:
            index = foreign_key_scan_index_getter(
                registry=registry,
                class_config_id=target_class_config_id,
                field_name=scan_fk,
                relationship_id=relationship.id,
            )
            return list(index.get(source_id, ()))

        out: list[ModelIntrospection] = []
        candidates = registry.by_class_config_id.get(target_class_config_id, [])
        for cand in candidates:
            declared, fk_value = cand.try_field_value(scan_fk, include_unset=True)
            if not declared:
                raise OigBuildError(
                    "Relationship FOREIGN_KEY attribute is not declared on target instance: "
                    f"field={scan_fk} target_id={cand.id} rel_id={relationship.id}"
                )
            if fk_value is None:
                continue
            if isinstance(fk_value, UUID):
                if fk_value == source_id:
                    out.append(cand)
            elif isinstance(fk_value, (list, tuple, set)):
                for v in fk_value:
                    if isinstance(v, UUID) and v == source_id:
                        out.append(cand)
                        break
        return out

    if require_binding:
        raise OigBuildError(
            "Missing FOREIGN_KEY relationship binding for FK traversal: "
            f"rel_id={relationship.id} traversal_direction={traversal_direction}"
        )
    return []


def _coerce_foreign_key_ids(value: object) -> list[UUID]:
    if value is None:
        return []
    if isinstance(value, UUID):
        return [value]
    if isinstance(value, (list, tuple, set)):
        out: list[UUID] = []
        for item in value:
            if isinstance(item, UUID):
                out.append(item)
        return out
    return []


def _try_fk_field_name_for_relationship(
    *,
    relationship: ClassConfigRelationship,
    direction: ClassConfigRelationshipDirection,
    attribute_configs_by_id: Mapping[UUID, AttributeConfig],
    strict: bool,
) -> str | None:
    """
    Resolve the FK field name for a relationship side.

    If strict=False:
    - returns None when missing or ambiguous (unsupported without additional traversal machinery).
    """
    fk_attr_ids: list[UUID] = []
    for rel_attr in relationship.class_config_relationship_attributes:
        if rel_attr.direction != direction:
            continue
        if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
            continue
        attr_id = rel_attr.attribute_config_id
        if attr_id is None:
            raise OigBuildError(
                f"Relationship {relationship.id} missing attribute_config_id for FOREIGN_KEY binding (direction={direction})"
            )
        fk_attr_ids.append(attr_id)

    if not fk_attr_ids:
        return None
    if len(fk_attr_ids) > 1:
        if strict:
            raise OigBuildError(
                "Ambiguous FOREIGN_KEY relationship binding: "
                f"rel_id={relationship.id} direction={direction} attribute_config_ids={sorted([str(i) for i in fk_attr_ids])}"
            )
        return None

    attr_cfg = attribute_configs_by_id.get(fk_attr_ids[0])
    if attr_cfg is None:
        raise OigBuildError(
            "Relationship FOREIGN_KEY AttributeConfig not found: "
            f"rel_id={relationship.id} attribute_config_id={fk_attr_ids[0]}"
        )
    return attr_cfg.name


def _resolve_ids_to_instances(
    value: object, registry: InstanceRegistry
) -> list[ModelIntrospection]:
    if value is None:
        return []
    if isinstance(value, UUID):
        inst = registry.by_id.get(value)
        return [inst] if inst is not None else []
    if isinstance(value, (list, tuple, set)):
        out: list[ModelIntrospection] = []
        for v in value:
            if isinstance(v, UUID):
                inst = registry.by_id.get(v)
                if inst is not None:
                    out.append(inst)
        return out
    return []


def _coerce_targets(value: object) -> list[ModelIntrospection]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        out: list[ModelIntrospection] = []
        for v in value:
            if v is None:
                continue
            if not isinstance(v, ModelIntrospection):
                raise OigBuildError(
                    f"Expected relationship target to implement ModelIntrospection, got {type(v).__name__}"
                )
            out.append(v)
        return out
    if not isinstance(value, ModelIntrospection):
        raise OigBuildError(
            f"Expected relationship target to implement ModelIntrospection, got {type(value).__name__}"
        )
    return [value]


__all__ = [
    "InstanceRegistry",
    "InMemoryRelationshipResolver",
    "OigBuildError",
    "RelationshipResolver",
    "build_include_relationship_attribute_config_ids_by_class_config_id",
    "build_object_instance_graph_from_class_instances",
    "build_object_instance_graph",
    "build_empty",
    "build_relationship_attribute_config_ids_by_class_config_id",
]
