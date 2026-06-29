"""
Builder for constructing ObjectProjectionGraph from ObjectConfigGraph and ObjectProjectionGraphBinding.
"""

from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
    ObjectProjectionGraphBinding,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# Aware Meta
from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id
from aware_meta.graph.config.relationship_analysis import (
    stable_reified_association_target_relationship_id,
)
from aware_meta.graph.projection.hash import calculate_hash
from aware_meta.graph.projection.stable_ids import (
    stable_object_projection_graph_id,
    stable_object_projection_graph_node_id,
    stable_object_projection_graph_edge_id,
)
from aware_utils.string_transform import singularize, to_snake_case


_PLACEHOLDER_OPG_ID = UUID("00000000-0000-0000-0000-000000000000")


def _expand_graph_dependency_closure(graphs: list[ObjectConfigGraph]) -> list[ObjectConfigGraph]:
    ordered: list[ObjectConfigGraph] = []
    seen: set[UUID] = set()
    stack: list[ObjectConfigGraph] = list(graphs)
    while stack:
        graph = stack.pop(0)
        if graph.id in seen:
            continue
        seen.add(graph.id)
        ordered.append(graph)
        for rel in graph.object_config_graph_relationships or []:
            target = rel.target_object_config_graph
            if target is None or target.id in seen:
                continue
            stack.append(target)
    return ordered


def _binding_namespace(binding: ObjectProjectionGraphBinding) -> str:
    namespace = getattr(binding, "namespace", None)
    if not isinstance(namespace, str):
        raise ValueError("Projection binding requires namespace")
    return namespace.strip()


def _class_fqn(*, fqn_prefix: str, namespace: str, class_name: str) -> str:
    namespace = (namespace or "").strip()
    if not namespace:
        return f"{fqn_prefix}.{class_name}"
    return f"{fqn_prefix}.{namespace}.{class_name}"


def build_object_projection_graph(
    name: str,
    description: str | None,
    ocg: ObjectConfigGraph,
    projection_bindings: list[ObjectProjectionGraphBinding],
    *,
    external_graphs: list[ObjectConfigGraph] | None = None,
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]] | None = None,
) -> ObjectProjectionGraph:
    # We compute projection_hash first, then derive stable ids. Use a constant placeholder id
    # while building nodes/edges so the build is deterministic end-to-end.
    opg_id = _PLACEHOLDER_OPG_ID

    # Use a map to deduplicate nodes per ClassConfig while allowing us to
    # upgrade an existing node to root when needed.
    nodes_by_class_id: dict[UUID, ObjectProjectionGraphNode] = {}
    object_projection_graph_edges: list[ObjectProjectionGraphEdge] = []

    class_fqn_to_id: dict[str, UUID] = {}
    class_id_to_fqn: dict[UUID, str] = {}
    graphs: list[ObjectConfigGraph] = _expand_graph_dependency_closure([ocg, *(external_graphs or [])])
    for g in graphs:
        ns_by_node_id = build_node_namespace_by_node_id(g)
        for node in g.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
                continue
            ns = ns_by_node_id.get(node.id)
            explicit_fqn = (getattr(node.class_config, "class_fqn", None) or "").strip()
            fqn = explicit_fqn or (ns.fqn(node.class_config.name) if ns is not None else "")
            if not fqn:
                continue
            prev = class_fqn_to_id.get(fqn)
            if prev is not None and prev != node.class_config.id:
                raise ValueError(f"OPG build: duplicate class FQN {fqn!r} maps to {prev} and {node.class_config.id}")
            class_fqn_to_id[fqn] = node.class_config.id
            prev_fqn = class_id_to_fqn.get(node.class_config.id)
            if prev_fqn is not None and prev_fqn != fqn:
                raise ValueError(
                    f"OPG build: class_config_id={node.class_config.id} maps "
                    f"to multiple FQNs: {prev_fqn!r} and {fqn!r}"
                )
            class_id_to_fqn[node.class_config.id] = fqn

    # Class lookup (for relationship -> attribute name binding). Includes externals so projections can target deps.
    class_by_id: dict[UUID, ClassConfig] = {}
    for g in graphs:
        for node in g.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                class_by_id.setdefault(node.class_config.id, node.class_config)

    # AttributeConfig.id -> (owner_class_id, attr_name)
    attr_name_by_id: dict[UUID, tuple[UUID, str]] = {}
    attr_by_id: dict[UUID, AttributeConfig] = {}
    for c in class_by_id.values():
        for link in c.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            prev = attr_name_by_id.get(link.attribute_config.id)
            cur = (c.id, link.attribute_config.name)
            if prev is not None and prev != cur:
                raise ValueError(f"OPG build: duplicate attribute_config_id={link.attribute_config.id} across graphs")
            attr_name_by_id[link.attribute_config.id] = cur
            attr_by_id.setdefault(link.attribute_config.id, link.attribute_config)

    detached_relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
    if cross_relationships_by_target_ocg:
        for rels in cross_relationships_by_target_ocg.values():
            for rel in rels or []:
                if rel is None or rel.id is None:
                    continue
                detached_relationships_by_id.setdefault(rel.id, rel)

    # External dependency graphs may already carry cross-OCG relationship materializations via
    # `ObjectConfigGraph.object_config_graph_relationships[].class_config_relationships`.
    #
    # Canonical contract:
    # - Cross-OCG relationships are not embedded as RELATIONSHIP nodes in the source OCG.
    # - When a graph is persisted as a dependency artifact (`.aware/environment.json`), its cross-OCG
    #   relationships must remain available to downstream builds for projection traversal.
    for g in graphs:
        for ocg_rel in g.object_config_graph_relationships:
            for rel in ocg_rel.class_config_relationships:
                if rel is None or rel.id is None:
                    continue
                detached_relationships_by_id.setdefault(rel.id, rel)

    detached_relationships = [detached_relationships_by_id[k] for k in sorted(detached_relationships_by_id, key=str)]

    reified_source_by_canonical_id: dict[UUID, ClassConfigRelationship] = {}

    def _track_reified_source(rel: ClassConfigRelationship) -> None:
        if rel.reified_from_relationship_id is None:
            return
        if rel.reified_role != ClassConfigRelationshipReifiedRole.source_to_association:
            return
        prev = reified_source_by_canonical_id.get(rel.reified_from_relationship_id)
        if prev is not None and prev.id != rel.id:
            raise ValueError(
                "OPG build: multiple reified source relationships for canonical "
                f"relationship_id={rel.reified_from_relationship_id}: {prev.id} vs {rel.id}"
            )
        reified_source_by_canonical_id[rel.reified_from_relationship_id] = rel

    for g in graphs:
        for node in g.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
                _track_reified_source(node.class_config_relationship)
        for ocg_rel in g.object_config_graph_relationships:
            for rel in ocg_rel.class_config_relationships:
                if rel is None or rel.id is None:
                    continue
                _track_reified_source(rel)
    for rel in detached_relationships:
        _track_reified_source(rel)

    def _reference_attr_name(rel: ClassConfigRelationship) -> str:
        """Return the canonical declaring attribute name for a relationship (FORWARD+REFERENCE)."""
        ref_attr_id: UUID | None = None
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
            ):
                ref_attr_id = ra.attribute_config_id
                break
        if ref_attr_id is None:
            raise ValueError(f"OPG build: relationship {rel.id} missing FORWARD+REFERENCE attribute binding")
        owner_and_name = attr_name_by_id.get(ref_attr_id)
        if owner_and_name is None:
            raise ValueError(
                f"OPG build: relationship {rel.id} reference attribute_config_id={ref_attr_id} not found on any class"
            )
        owner_class_id, attr_name = owner_and_name
        if owner_class_id != rel.class_config_id:
            raise ValueError(
                f"OPG build: relationship {rel.id} reference attribute_config_id={ref_attr_id} "
                f"is not owned by the relationship source class_id={rel.class_config_id}"
            )
        return attr_name

    def _reference_attr_required(rel: ClassConfigRelationship) -> bool:
        """Return whether the canonical declaring attribute for a relationship is required."""
        ref_attr_id: UUID | None = None
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
            ):
                ref_attr_id = ra.attribute_config_id
                break
        if ref_attr_id is None:
            if (
                rel.reified_role == ClassConfigRelationshipReifiedRole.association_to_target
                and rel.relationship_key
            ):
                return bool(rel.forward_required)
            raise ValueError(f"OPG build: relationship {rel.id} missing FORWARD+REFERENCE attribute binding")
        attr = attr_by_id.get(ref_attr_id)
        if attr is None:
            raise ValueError(
                f"OPG build: relationship {rel.id} reference attribute_config_id={ref_attr_id} not found on any class"
            )
        return bool(attr.is_required)

    # Relationship lookup: (source_class_id, declaring_attribute_name) -> relationship
    rel_by_source_and_attr: dict[tuple[UUID, str], ClassConfigRelationship] = {}

    def _index_relationship(rel: ClassConfigRelationship) -> None:
        if rel.class_config_id not in class_by_id:
            raise ValueError(
                f"OPG build: relationship {rel.id} source class_config_id={rel.class_config_id} not found"
            )
        attr_name = _reference_attr_name(rel)
        key = (rel.class_config_id, attr_name)
        prev = rel_by_source_and_attr.get(key)
        if prev is not None and prev.id != rel.id:
            raise ValueError(f"OPG build: ambiguous relationship key {key} -> {prev.id} and {rel.id}")
        rel_by_source_and_attr[key] = rel

    for g in graphs:
        for node in g.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.relationship or node.class_config_relationship is None:
                continue
            _index_relationship(node.class_config_relationship)

    # Canonical: detached cross-OCG relationships are not embedded as relationship nodes, but
    # projections still reference them deterministically via class_config_relationship_id.
    for rel in detached_relationships:
        _index_relationship(rel)

    for class_config in class_by_id.values():
        for rel in class_config.class_config_relationships or []:
            _index_relationship(rel)

    projection_only_relationships: dict[UUID, ClassConfigRelationship] = {}

    def _association_edge_endpoint_name(rel: ClassConfigRelationship) -> str | None:
        target_class = class_by_id.get(rel.target_class_config_id)
        if target_class is None:
            return None
        endpoint_name = to_snake_case(target_class.name)
        if rel.class_config_id == rel.target_class_config_id:
            reference_name = _reference_attr_name(rel)
            endpoint_name = to_snake_case(singularize(reference_name) or reference_name)
        return endpoint_name

    def _resolve_association_edge_endpoint_relationship(
        *,
        source_class_id: UUID,
        attribute_name: str,
    ) -> ClassConfigRelationship | None:
        """
        Resolve a canonical association-edge endpoint such as `Edge::target`.

        Runtime derivation reifies A->Edge and Edge->B relationships, but API dependency
        materialization can build OPGs directly from canonical graphs. In that mode the
        association class has no authored endpoint relationship, so synthesize the stable
        projection-only Edge->target relationship id from the owning canonical relation.
        """

        for rel in list(rel_by_source_and_attr.values()) + detached_relationships:
            assoc_edge = rel.class_config_relationship_association_edge
            assoc_class_id = assoc_edge.class_config_id if assoc_edge is not None else None
            if assoc_class_id != source_class_id:
                continue
            if _association_edge_endpoint_name(rel) != attribute_name:
                continue

            rel_id = stable_reified_association_target_relationship_id(relationship_id=rel.id)
            existing = projection_only_relationships.get(rel_id)
            if existing is not None:
                return existing

            relationship_type = (
                ClassConfigRelationshipType.many_to_one
                if rel.relationship_type
                in {
                    ClassConfigRelationshipType.one_to_many,
                    ClassConfigRelationshipType.many_to_many,
                }
                else ClassConfigRelationshipType.one_to_one
            )
            synthesized = ClassConfigRelationship(
                id=rel_id,
                relationship_key=attribute_name,
                relationship_type=relationship_type,
                identity_rail=ClassConfigRelationshipIdentityRail.reference,
                forward_required=True,
                forward_loading_strategy=(
                    assoc_edge.reverse_loading_strategy if assoc_edge is not None else None
                ),
                reverse_loading_strategy=None,
                class_config_id=source_class_id,
                target_class_config=class_by_id.get(rel.target_class_config_id),
                target_class_config_id=rel.target_class_config_id,
                reified_from_relationship_id=rel.id,
                reified_role=ClassConfigRelationshipReifiedRole.association_to_target,
            )
            projection_only_relationships[rel_id] = synthesized
            return synthesized
        return None

    def _resolve_traversal_relationship(
        rel: ClassConfigRelationship,
    ) -> ClassConfigRelationship:
        if rel.reified_from_relationship_id is not None:
            return rel
        if rel.class_config_relationship_association_edge is None:
            return rel
        reified = reified_source_by_canonical_id.get(rel.id)
        return reified or rel

    def _ensure_node(class_config_id: UUID, *, is_root: bool) -> None:
        existing = nodes_by_class_id.get(class_config_id)
        if existing is None:
            nodes_by_class_id[class_config_id] = ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=class_config_id,
                is_root=is_root,
                required_for_validity=is_root,
                selection=(
                    ObjectProjectionGraphNodeSelection.one if is_root else ObjectProjectionGraphNodeSelection.all
                ),
            )
        else:
            # If we see a root annotation later, upgrade the node.
            if is_root and not existing.is_root:
                existing.is_root = True
                existing.required_for_validity = True
                existing.selection = ObjectProjectionGraphNodeSelection.one

    for code_section_project in projection_bindings:
        # Invariants: binding already carries resolved namespace, class_name, and attribute_name.
        namespace = _binding_namespace(code_section_project)
        class_name = code_section_project.class_name
        attribute_name = code_section_project.attribute_name

        # Canonical OPG v0: only forward traversal is supported (no reverse/member synthesis).
        if code_section_project.side is not None and code_section_project.side.strip().lower() not in {"", "forward"}:
            raise ValueError(
                f"OPG build: unsupported project side={code_section_project.side!r} for "
                f"{namespace}.{class_name}::{attribute_name or ''}. Canonical OPG currently supports forward only."
            )

        # Resolve class config id from fully-qualified path
        fqn = _class_fqn(
            fqn_prefix=code_section_project.fqn_prefix,
            namespace=namespace,
            class_name=class_name,
        )
        class_id = class_fqn_to_id.get(fqn)
        if class_id is None:
            raise ValueError(
                "Class not found for projection target: "
                + f"{fqn} "
                + f"(projection={name!r}, graph_id={ocg.id}, "
                + "external_graph_ids="
                + f"{[str(ext.id) for ext in (external_graphs or [])]}, "
                + "available_fqns_sample="
                + f"{sorted(class_fqn_to_id.keys())[:12]})"
            )

        if not attribute_name:
            _ensure_node(class_id, is_root=True)
            continue

        _ensure_node(class_id, is_root=False)
        rel = rel_by_source_and_attr.get((class_id, attribute_name))
        if rel is None:
            rel = _resolve_association_edge_endpoint_relationship(
                source_class_id=class_id,
                attribute_name=attribute_name,
            )
        if rel is None:
            raise ValueError(f"Relationship not found for projection edge: {fqn}::{attribute_name}")
        include_required = _reference_attr_required(rel)
        traversal_rel = _resolve_traversal_relationship(rel)

        member_target_class_id = traversal_rel.target_class_config_id
        assoc_edge = rel.class_config_relationship_association_edge
        if (
            traversal_rel.id == rel.id
            and assoc_edge is not None
            and assoc_edge.class_config_id is not None
        ):
            # Canonical projection declarations target reified association membership.
            # Runtime derivation later expands the edge to explicit A->Edge->B traversal,
            # but canonical OPG membership must still include the edge class so portals
            # such as `Edge::target TargetProjection` can resolve deterministically.
            member_target_class_id = assoc_edge.class_config_id

        _ensure_node(member_target_class_id, is_root=False)
        multiplicity = (
            ObjectProjectionGraphEdgeMultiplicity.one
            if traversal_rel.relationship_type
            in {
                ClassConfigRelationshipType.one_to_one,
                ClassConfigRelationshipType.many_to_one,
            }
            else ObjectProjectionGraphEdgeMultiplicity.many
        )
        object_projection_graph_edges.append(
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=traversal_rel.id,
                include=(
                    ObjectProjectionGraphEdgeInclude.required
                    if include_required
                    else ObjectProjectionGraphEdgeInclude.optional
                ),
                multiplicity=multiplicity,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            )
        )

    # Deterministic ordering for hashing and downstream serialization.
    nodes_list = sorted(list(nodes_by_class_id.values()), key=lambda n: str(n.class_config_id))
    edges_list = sorted(
        object_projection_graph_edges,
        key=lambda e: (
            str(e.class_config_relationship_id),
            str(e.traversal_direction.value),
            str(e.include.value),
        ),
    )

    projection_hash = calculate_hash(
        ocg=ocg,
        nodes=nodes_list,
        edges=edges_list,
        external_graphs=external_graphs,
        additional_relationships=[
            *detached_relationships,
            *projection_only_relationships.values(),
        ],
    )

    stable_opg_id = stable_object_projection_graph_id(object_config_graph_id=ocg.id, name=name)

    # Assign stable ids + fk links for nodes/edges now that opg id is known.
    for n in nodes_list:
        n.object_projection_graph_id = stable_opg_id
        n.id = stable_object_projection_graph_node_id(
            opg_id=stable_opg_id,
            class_config_id=n.class_config_id,
            is_root=bool(n.is_root),
            required_for_validity=bool(n.required_for_validity),
            selection=n.selection.value,
            top_n=n.top_n,
            selector_condition_id=n.selector_condition_id,
            policy_refs=list(n.policy_refs or []),
        )
    for e in edges_list:
        e.object_projection_graph_id = stable_opg_id
        e.id = stable_object_projection_graph_edge_id(
            opg_id=stable_opg_id,
            class_config_relationship_id=e.class_config_relationship_id,
            include=e.include.value,
            multiplicity=e.multiplicity.value,
            traversal_direction=e.traversal_direction.value,
            depth_limit=e.depth_limit,
            attribute_role=(e.attribute_role.value if e.attribute_role is not None else None),
            loading_override=(e.loading_override.value if e.loading_override is not None else None),
        )

    opg = ObjectProjectionGraph(
        id=stable_opg_id,
        object_config_graph_id=ocg.id,
        name=name,
        description=description,
        language=CodeLanguage(ocg.language.value),
        projection_hash=projection_hash,
    )
    opg.object_projection_graph_nodes = nodes_list
    opg.object_projection_graph_edges = edges_list
    return opg
