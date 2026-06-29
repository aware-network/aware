from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.annotation.code_section_annotation_overlay import (
    CodeSectionAnnotationOverlay,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)
from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
    ObjectProjectionGraphBinding,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_constructor import (
    ObjectProjectionGraphConstructor,
)
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
    ObjectProjectionGraphRelationship,
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
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta.graph.config.model_bootstrap import get_node_function_config

# Object Projection Graph Builder
from aware_meta.graph.projection.builder import (
    build_object_projection_graph,
)
from aware_meta.graph.projection.hash import calculate_hash
from aware_meta.graph.projection.stable_ids import (
    stable_object_projection_graph_relationship_id,
)
from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id

# Object Config Graph Overlay Builder
from aware_meta.graph.config.overlay.builder import (
    build_object_config_graph_overlay_from_annotations,
)
from aware_meta.graph.config.overlay.index import index_ocg_for_overlay
from aware_meta.graph.config.overlay.reserved_keywords import (
    apply_reserved_keyword_overlays,
)

# Namespace Builder
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.graph.projection.declarations import ProjectionDeclaration

from aware_utils.logging import logger
from aware_utils.string_transform import singularize, to_snake_case


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


def _projection_binding_namespace(binding: ObjectProjectionGraphBinding) -> str:
    namespace = getattr(binding, "namespace", None)
    if not isinstance(namespace, str):
        raise ValueError("Projection binding requires namespace")
    return namespace.strip()


def _projection_binding_class_fqn(binding: ObjectProjectionGraphBinding) -> str:
    namespace = _projection_binding_namespace(binding)
    if not namespace:
        return f"{binding.fqn_prefix}.{binding.class_name}"
    return f"{binding.fqn_prefix}.{namespace}.{binding.class_name}"


def build_object_projection_graphs(
    ocg: ObjectConfigGraph,
    *,
    external_graphs: list[ObjectConfigGraph] | None = None,
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]] | None = None,
    projection_declarations_by_name: dict[str, ProjectionDeclaration] | None = None,
    provision_portals: bool = True,
) -> list[ObjectProjectionGraph]:
    """Build OPGs for the given OCG."""
    # Sibling external dependency closure can point back at the root OCG.
    # Keep the root graph unique so later hash/constructor passes never see the
    # same class ids twice as distinct decoded graph objects.
    external_graphs = [
        graph for graph in _expand_graph_dependency_closure(list(external_graphs or [])) if graph.id != ocg.id
    ]

    # Projection membership/portal SSOT is compiler-owned and persisted on the OCG.
    projection_declarations: list[ObjectProjectionGraphDeclaration] = list(
        ocg.object_projection_graph_declarations or []
    )

    # Build OPGs for each projection
    opgs: list[ObjectProjectionGraph] = []
    portal_bindings: list[tuple[str, ObjectProjectionGraphBinding]] = []
    detached_relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
    if cross_relationships_by_target_ocg:
        for rels in cross_relationships_by_target_ocg.values():
            for rel in rels:
                _ = detached_relationships_by_id.setdefault(rel.id, rel)
    for graph in [ocg, *(external_graphs or [])]:
        for ocg_rel in graph.object_config_graph_relationships or []:
            for rel in ocg_rel.class_config_relationships or []:
                _ = detached_relationships_by_id.setdefault(rel.id, rel)
    detached_relationships: list[ClassConfigRelationship] = [
        detached_relationships_by_id[key] for key in sorted(detached_relationships_by_id, key=str)
    ]
    for decl in sorted(
        projection_declarations,
        key=lambda d: (
            (d.projection_name or "").strip(),
            (d.key or "").strip(),
            str(d.id),
        ),
    ):
        projection_name = (decl.projection_name or "").strip()
        if not projection_name:
            continue

        bindings = list(decl.object_projection_graph_bindings or [])
        membership_bindings: list[ObjectProjectionGraphBinding] = []
        for b in bindings:
            if (b.target_projection_name or "").strip():
                portal_bindings.append((projection_name, b))
            else:
                membership_bindings.append(b)

        # Deterministic order within a projection.
        membership_bindings = sorted(
            membership_bindings,
            key=lambda p: (
                p.fqn_prefix,
                _projection_binding_namespace(p),
                p.class_name,
                p.attribute_name or "",
                p.side or "",
            ),
        )

        if not any(b.attribute_name is None for b in membership_bindings):
            raise ValueError(f"OPG build: projection {projection_name!r} missing root binding (attribute_name == null)")

        runtime_decl = projection_declarations_by_name.get(projection_name) if projection_declarations_by_name else None
        description = ((runtime_decl.description or None) if runtime_decl is not None else None) or (
            decl.description or None
        )

        opg = build_object_projection_graph(
            name=projection_name,
            description=description,
            ocg=ocg,
            projection_bindings=membership_bindings,
            external_graphs=external_graphs,
            cross_relationships_by_target_ocg=cross_relationships_by_target_ocg,
        )
        opgs.append(opg)

    # Provision OPG constructors (instance-anchored; derived from root class constructor functions).
    _provision_object_projection_graph_constructors(
        ocg=ocg,
        opgs=opgs,
        external_graphs=external_graphs,
    )

    if provision_portals:
        # Provision explicit cross-OPG relationships (portals).
        _provision_object_projection_graph_relationships(
            ocg=ocg,
            opgs=opgs,
            portal_bindings=portal_bindings,
            detached_relationships=detached_relationships,
            external_graphs=external_graphs,
        )

        # Recompute projection_hash after provisioning portals so the hash reflects the full OPG contract.
        # (Membership hash is computed in the builder; portals are added in a second pass.)
        _recompute_opg_hashes_with_portals(
            ocg=ocg,
            opgs=opgs,
            external_graphs=external_graphs,
            detached_relationships=detached_relationships,
        )
    return opgs


def _provision_object_projection_graph_relationships(
    *,
    ocg: ObjectConfigGraph,
    opgs: list[ObjectProjectionGraph],
    portal_bindings: list[tuple[str, ObjectProjectionGraphBinding]],
    detached_relationships: list[ClassConfigRelationship] | None,
    external_graphs: list[ObjectConfigGraph] | None,
) -> None:
    """
    Attach explicit cross-OPG relationships (portals) onto each OPG instance.

    Contract (Option A):
    - `ObjectProjectionGraphEdge` remains intra-projection membership (members live in one OIG).
    - `ObjectProjectionGraphRelationship` is a portal to another projection (no membership merge).
    - Portal bindings are expressed via projection members with a target projection.

    Projection targets may be:
    - unqualified: `target "Identity"` (requires global uniqueness across dependency graphs)
    - qualified: `target "aware_identity.Identity"` (recommended; deterministic across packages)
    """
    if not portal_bindings:
        return

    # Portal targets may live in external graphs (cross-OCG projections).
    # Projection names are NOT globally unique; they are scoped by `ObjectConfigGraph.fqn_prefix`.
    # Build resolution indexes across the local graph + externals.
    all_opgs: list[ObjectProjectionGraph] = list(opgs)
    for ext in external_graphs or []:
        all_opgs.extend(ext.object_projection_graphs)

    local_opg_by_name: dict[str, ObjectProjectionGraph] = {opg.name: opg for opg in opgs}

    opg_by_owner_and_name: dict[tuple[str, str], ObjectProjectionGraph] = {}
    opgs_by_name: dict[str, list[tuple[str, ObjectProjectionGraph]]] = {}
    opg_ids_by_name: dict[str, set[UUID]] = {}

    def _register(owner_fqn_prefix: str, opg: ObjectProjectionGraph) -> None:
        key = (owner_fqn_prefix, opg.name)
        prev = opg_by_owner_and_name.get(key)
        if prev is not None and prev.id != opg.id:
            raise ValueError(
                "OPG portal: duplicate projection name within the same package "
                + f"(fqn_prefix={owner_fqn_prefix!r}, name={opg.name!r}, opg_id={opg.id}, prev_id={prev.id})"
            )
        opg_by_owner_and_name[key] = opg
        # Runtime-context graphs are read indexes that can re-publish the same
        # OPG id under a synthetic owner. They must not create a second
        # unqualified portal target.
        opg_ids = opg_ids_by_name.setdefault(opg.name, set())
        if opg.id in opg_ids:
            return
        opg_ids.add(opg.id)
        opgs_by_name.setdefault(opg.name, []).append((owner_fqn_prefix, opg))

    for opg in opgs:
        _register(ocg.fqn_prefix, opg)
    for ext in external_graphs or []:
        for opg in ext.object_projection_graphs:
            _register(ext.fqn_prefix, opg)

    known_target_owners: set[str] = {owner for owner, _ in opg_by_owner_and_name.keys()}

    def _parse_projection_target(
        raw: str,
    ) -> tuple[str | None, str]:
        """
        Parse a projection portal target token.

        Supported forms:
        - `Identity` (unqualified projection name)
        - `aware_identity.Identity` (qualified by fqn_prefix; recommended)
        - `condition.ConditionConfig` (class-style ref in projection context)
        """
        token = (raw or "").strip()
        if not token:
            return None, ""

        if "." not in token:
            return None, token

        parts = [p for p in token.split(".") if p]
        if len(parts) != 2:
            raise ValueError(
                "OPG portal: invalid qualified projection target "
                + f"{token!r} (expected '<fqn_prefix>.<ProjectionName>')"
            )

        owner = parts[0].strip()
        symbol = parts[1].strip()
        if not owner or not symbol:
            raise ValueError(
                "OPG portal: invalid qualified projection target "
                + f"{token!r} (expected '<fqn_prefix>.<ProjectionName>')"
            )

        # Context-aware disambiguation:
        # - `<owner>.<ProjectionName>` is explicit qualified projection syntax.
        # - `<namespace>.<ClassName>` is accepted in projection-target context and
        #   resolves to projection name `<ClassName>` (owner remains unqualified
        #   unless the first segment is a known package fqn_prefix).
        projection_name = symbol
        if owner in known_target_owners:
            return owner, projection_name
        return None, projection_name

    nodes_by_opg_id_and_class_id: dict[UUID, dict[UUID, ObjectProjectionGraphNode]] = {}
    for opg in all_opgs:
        nodes_by_opg_id_and_class_id[opg.id] = {n.class_config_id: n for n in opg.object_projection_graph_nodes}

    graphs: list[ObjectConfigGraph] = [ocg, *(external_graphs or [])]

    # Resolve class ids by FQN across local + external graphs.
    class_fqn_to_id: dict[str, UUID] = {}
    class_id_to_fqn: dict[UUID, str] = {}
    class_by_id: dict[UUID, ClassConfig] = {}
    for g in graphs:
        ns_by_node_id = build_node_namespace_by_node_id(g)
        for node in g.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
                continue
            class_by_id.setdefault(node.class_config.id, node.class_config)

            ns = ns_by_node_id.get(node.id)
            if ns is None:
                continue
            fqn = ns.fqn(node.class_config.name)
            prev_id = class_fqn_to_id.get(fqn)
            if prev_id is not None and prev_id != node.class_config.id:
                raise ValueError(
                    f"OPG portal: duplicate class FQN {fqn!r} maps to {prev_id} and {node.class_config.id}"
                )
            class_fqn_to_id[fqn] = node.class_config.id
            prev_fqn = class_id_to_fqn.get(node.class_config.id)
            if prev_fqn is not None and prev_fqn != fqn:
                raise ValueError(
                    f"OPG portal: class_config_id={node.class_config.id} maps "
                    f"to multiple FQNs: {prev_fqn!r} and {fqn!r}"
                )
            class_id_to_fqn[node.class_config.id] = fqn

    # AttributeConfig.id -> (owner_class_id, attr_name)
    attr_name_by_id: dict[UUID, tuple[UUID, str]] = {}
    for c in class_by_id.values():
        for link in c.class_config_attribute_configs:
            prev = attr_name_by_id.get(link.attribute_config.id)
            cur = (c.id, link.attribute_config.name)
            if prev is not None and prev != cur:
                raise ValueError(f"OPG portal: duplicate attribute_config_id={link.attribute_config.id} across graphs")
            attr_name_by_id[link.attribute_config.id] = cur

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
            raise ValueError(f"OPG portal: relationship {rel.id} missing FORWARD+REFERENCE attribute binding")
        owner_and_name = attr_name_by_id.get(ref_attr_id)
        if owner_and_name is None:
            raise ValueError(
                f"OPG portal: relationship {rel.id} reference attribute_config_id={ref_attr_id} not found on any class"
            )
        owner_class_id, attr_name = owner_and_name
        if owner_class_id != rel.class_config_id:
            raise ValueError(
                f"OPG portal: relationship {rel.id} reference attribute_config_id={ref_attr_id} "
                + f"is not owned by the relationship source class_id={rel.class_config_id}"
            )
        return attr_name

    def _resolve_association_edge_endpoint_relationship(
        *,
        source_class_id: UUID,
        attribute_name: str,
    ) -> ClassConfigRelationship | None:
        """
        Resolve an implicit association-edge endpoint relationship from canonical topology.

        Canonical `.aware` edge classes do not declare endpoint relationships explicitly.
        Portal bindings may still target them, for example `Edge::member TargetProjection` when
        `TargetProjection` is the authored projection name.
        When direct relationship lookup misses, recover the endpoint through the owning canonical
        relationship whose association edge class matches the source class.
        """

        for rel in list(rel_by_source_and_attr.values()) + list(detached_relationships or []):
            assoc_edge = rel.class_config_relationship_association_edge
            assoc_class_id = assoc_edge.class_config_id if assoc_edge is not None else None
            if assoc_class_id != source_class_id:
                continue

            target_class = class_by_id.get(rel.target_class_config_id)
            if target_class is None:
                continue

            endpoint_name = to_snake_case(target_class.name)
            if rel.class_config_id == rel.target_class_config_id:
                reference_name = _reference_attr_name(rel)
                endpoint_name = to_snake_case(singularize(reference_name) or reference_name)

            if endpoint_name == attribute_name:
                return rel
        return None

    # Relationship lookup: (source_class_id, declaring_attribute_name) -> relationship
    rel_by_source_and_attr: dict[tuple[UUID, str], ClassConfigRelationship] = {}
    for g in graphs:
        for node in g.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.relationship or node.class_config_relationship is None:
                continue
            rel = node.class_config_relationship
            attr_name = _reference_attr_name(rel)
            key = (rel.class_config_id, attr_name)
            prev = rel_by_source_and_attr.get(key)
            if prev is not None and prev.id != rel.id:
                raise ValueError(f"OPG portal: ambiguous relationship key {key} -> {prev.id} and {rel.id}")
            rel_by_source_and_attr[key] = rel

    # Canonical: detached cross-OCG relationships are not embedded as relationship nodes, but portals
    # may still reference them deterministically via class_config_relationship_id.
    for rel in detached_relationships or []:
        if rel.class_config_id not in class_by_id:
            raise ValueError(
                f"OPG portal: detached relationship {rel.id} source class_config_id={rel.class_config_id} not found"
            )
        attr_name = _reference_attr_name(rel)
        key = (rel.class_config_id, attr_name)
        prev = rel_by_source_and_attr.get(key)
        if prev is not None and prev.id != rel.id:
            raise ValueError(f"OPG portal: ambiguous relationship key {key} -> {prev.id} and {rel.id}")
        rel_by_source_and_attr[key] = rel

    # Deterministic order for portal provisioning.
    portal_bindings_sorted = sorted(
        portal_bindings,
        key=lambda item: (
            item[0],  # source projection_name
            item[1].target_projection_name or "",
            item[1].fqn_prefix,
            _projection_binding_namespace(item[1]),
            item[1].class_name,
            item[1].attribute_name or "",
            item[1].side or "",
        ),
    )

    seen: set[tuple[UUID, UUID, UUID]] = set()  # (source_opg_id, relationship_id, target_opg_id)
    for source_projection_name, portal in portal_bindings_sorted:
        if not portal.target_projection_name:
            continue
        if not portal.attribute_name:
            raise ValueError(
                "OPG portal: portal binding requires an attribute member "
                + f"(got: {_projection_binding_namespace(portal)}.{portal.class_name})"
            )

        if portal.side is not None and portal.side.strip().lower() not in {
            "",
            "forward",
        }:
            raise ValueError(
                f"OPG portal: unsupported project side={portal.side!r} for "
                + f"{_projection_binding_namespace(portal)}.{portal.class_name}::{portal.attribute_name}. "
                + "Canonical OPG currently supports forward only."
            )

        source_opg = local_opg_by_name.get(source_projection_name)
        if source_opg is None:
            raise ValueError(
                "OPG portal: source projection "
                + f"{source_projection_name!r} not defined in the local OCG (fqn_prefix={ocg.fqn_prefix!r}) "
                + "via projection declarations"
            )

        target_owner, target_name = _parse_projection_target(portal.target_projection_name)
        if target_owner is not None:
            target_opg = opg_by_owner_and_name.get((target_owner, target_name))
            if target_opg is None:
                raise ValueError(
                    "OPG portal: target projection not found for qualified target "
                    + f"{portal.target_projection_name!r} (resolved fqn_prefix={target_owner!r}, name={target_name!r})"
                )
        else:
            # Prefer a local target projection (same package) when present.
            target_opg = opg_by_owner_and_name.get((ocg.fqn_prefix, target_name))
            if target_opg is None:
                matches = opgs_by_name.get(target_name) or []
                if not matches:
                    raise ValueError(
                        "OPG portal: target projection " + f"{target_name!r} not defined via projection declarations"
                    )
                if len(matches) != 1:
                    owners = sorted({o for o, _ in matches})
                    raise ValueError(
                        "OPG portal: ambiguous target projection "
                        + f"{target_name!r} across fqn_prefixes {owners}. "
                        + "Use a qualified target like 'aware_identity.Identity'."
                    )
                target_opg = matches[0][1]

        fqn = _projection_binding_class_fqn(portal)
        source_class_id = class_fqn_to_id.get(fqn)
        if source_class_id is None:
            raise ValueError(f"OPG portal: class not found for portal source: {fqn}")

        source_node = nodes_by_opg_id_and_class_id.get(source_opg.id, {}).get(source_class_id)
        if source_node is None:
            raise ValueError(
                f"OPG portal: source class {fqn} is not a member of projection {source_opg.name!r}; "
                + "add a root/member binding for it"
            )

        rel = rel_by_source_and_attr.get((source_class_id, portal.attribute_name))
        if rel is None:
            rel = _resolve_association_edge_endpoint_relationship(
                source_class_id=source_class_id,
                attribute_name=portal.attribute_name,
            )
        if rel is None:
            raise ValueError(f"OPG portal: relationship not found for portal edge: {fqn}::{portal.attribute_name}")

        target_node = nodes_by_opg_id_and_class_id.get(target_opg.id, {}).get(rel.target_class_config_id)
        if target_node is None:
            if rel.target_class_config_id in class_id_to_fqn:
                exception_class_ref = class_id_to_fqn[rel.target_class_config_id]
            else:
                exception_class_ref = f"class_config_id={rel.target_class_config_id}"
            raise ValueError(
                f"OPG portal: target {exception_class_ref} is not a member of projection {target_opg.name!r}; "
                + "add a root/member binding for the relationship target class"
            )

        key = (source_opg.id, rel.id, target_opg.id)
        if key in seen:
            raise ValueError(
                f"OPG portal: duplicate portal binding for {source_projection_name!r}::{portal.attribute_name} -> "
                + f"{portal.target_projection_name!r}"
            )
        seen.add(key)

        source_opg.object_projection_graph_relationships.append(
            ObjectProjectionGraphRelationship(
                id=stable_object_projection_graph_relationship_id(
                    source_opg_id=source_opg.id,
                    class_config_relationship_id=rel.id,
                    target_opg_id=target_opg.id,
                ),
                object_projection_graph_id=source_opg.id,
                object_projection_graph=source_opg,
                target_object_projection_graph_id=target_opg.id,
                target_object_projection_graph=target_opg,
                class_config_relationship_id=rel.id,
                class_config_relationship=rel,
                source_object_projection_graph_node_id=source_node.id,
                source_object_projection_graph_node=source_node,
                target_object_projection_graph_node_id=target_node.id,
                target_object_projection_graph_node=target_node,
            )
        )


def _recompute_opg_hashes_with_portals(
    *,
    ocg: ObjectConfigGraph,
    opgs: list[ObjectProjectionGraph],
    external_graphs: list[ObjectConfigGraph] | None,
    detached_relationships: list[ClassConfigRelationship] | None,
) -> None:
    """
    Recompute `projection_hash` for OPGs after second-pass provisioning (portals, etc.).

    v0 rule:
    - If an OPG has no portals, keep the original hash (membership-only, opgcanon:2).
    - If an OPG has portals, recompute using opgcanon:3 including portal entries.
    """
    for opg in opgs:
        if not opg.object_projection_graph_relationships:
            continue
        opg.projection_hash = calculate_hash(
            ocg=ocg,
            nodes=opg.object_projection_graph_nodes,
            edges=opg.object_projection_graph_edges,
            relationships=opg.object_projection_graph_relationships,
            external_graphs=external_graphs,
            additional_relationships=(detached_relationships or []),
        )


def _provision_object_projection_graph_constructors(
    *,
    ocg: ObjectConfigGraph,
    opgs: list[ObjectProjectionGraph],
    external_graphs: list[ObjectConfigGraph] | None,
) -> None:
    """
    Attach ObjectProjectionGraphConstructor entries onto each OPG instance.

    v0 rule (clarity > cleverness):
    - Constructor membership is derived from the root class's
      ClassConfigFunctionConfig entries where is_constructor=True.
    - No explicit constructor annotations are required.
    """
    graphs: list[ObjectConfigGraph] = [ocg, *(external_graphs or [])]
    class_by_id: dict[UUID, ClassConfig] = {}
    for g in graphs:
        for node in g.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
                continue
            class_by_id.setdefault(node.class_config.id, node.class_config)

    for opg in opgs:
        if not opg.supports_virtual_build:
            # Consumers can opt out of construction semantics.
            continue

        roots = [n for n in opg.object_projection_graph_nodes if n.is_root]
        if not roots:
            raise ValueError(f"OPG {opg.name!r} has no root nodes; cannot provision constructors")

        seen: set[tuple[UUID, UUID]] = set()  # (root_node_id, class_config_function_config_id)
        for root_node in roots:
            root_cc = class_by_id.get(root_node.class_config_id)
            if root_cc is None:
                raise ValueError(f"OPG {opg.name!r} root class_config_id={root_node.class_config_id} not found in OCG")

            for cc_fc in root_cc.class_config_function_configs:
                if not cc_fc.is_constructor:
                    continue
                key = (root_node.id, cc_fc.id)
                if key in seen:
                    continue
                seen.add(key)
                opg.object_projection_graph_constructors.append(
                    ObjectProjectionGraphConstructor(
                        object_projection_graph_id=opg.id,
                        root_node_id=root_node.id,
                        root_node=root_node,
                        function_constructor_id=cc_fc.id,
                        function_constructor=cc_fc,
                    )
                )


def build_object_config_graph_overlays_from_annotations(
    ocg: ObjectConfigGraph,
    *,
    namespace_bundle: ObjectConfigGraphNamespaceBundle | None = None,
) -> list[ObjectConfigGraphOverlay]:
    """
    Build ObjectConfigGraphOverlays for runtime consumption.

    Sources:
    - explicit overlays from `ann ... overlay ...` annotations
    - second-pass overlays generated by meta policies (e.g., reserved keywords)
    """
    overlays_by_language: dict[CodeLanguage, ObjectConfigGraphOverlay] = {}
    code_section_annotation_overlay: dict[CodeLanguage, list[CodeSectionAnnotationOverlay]] = {}

    # Get code section annotation overlays from OCG annotations and group by language.
    for ocg_annotation in ocg.object_config_graph_annotations:
        if ocg_annotation.kind == ObjectConfigGraphAnnotationKind.overlay:
            if ocg_annotation.code_section_annotation_overlay is None:
                logger.error(f"Code section annotation overlay not found for annotation {ocg_annotation.id}")
                raise ValueError(f"Code section annotation overlay not found for annotation {ocg_annotation.id}")
            if ocg_annotation.code_section_annotation_overlay.language not in code_section_annotation_overlay:
                code_section_annotation_overlay[ocg_annotation.code_section_annotation_overlay.language] = []
            code_section_annotation_overlay[ocg_annotation.code_section_annotation_overlay.language].append(
                ocg_annotation.code_section_annotation_overlay
            )

    # Explicit overlays from annotations
    if code_section_annotation_overlay:
        # Meta-time SSOT: overlays must compile using meta-ID namespaces, not code_id provenance.
        # When bundle is not provided, derive from canonical OCG FQN topology.
        if namespace_bundle is None:
            namespace_bundle = build_namespace_bundle_from_ocg_topology(ocg=ocg)

        # Pre-index canonical entities by simple keys
        index = index_ocg_for_overlay(
            ocg,
            namespace_by_class_config_id=namespace_bundle.namespace_by_class_config_id,
            namespace_by_enum_config_id=namespace_bundle.namespace_by_enum_config_id,
            namespace_by_function_config_id=namespace_bundle.namespace_by_function_config_id,
        )

        # Build ObjectConfigGraphOverlays for each language.
        for (
            language,
            code_section_annotation_overlays,
        ) in code_section_annotation_overlay.items():
            overlays_by_language[language] = build_object_config_graph_overlay_from_annotations(
                ocg=ocg,
                index=index,
                code_section_annotation_overlays=code_section_annotation_overlays,
                language=language,
            )

    # Second-pass policy overlays (reserved keywords, etc.)
    overlays_by_language = apply_reserved_keyword_overlays(ocg, overlays_by_language=overlays_by_language)

    # Deterministic order
    return [
        overlays_by_language[key]
        for key in sorted(overlays_by_language.keys(), key=lambda language_key: language_key.value)
    ]


def get_enum_configs(ocg: ObjectConfigGraph) -> list[EnumConfig]:
    return [n.enum_config for n in ocg.object_config_graph_nodes if n.enum_config is not None]


def get_function_configs(ocg: ObjectConfigGraph) -> list[FunctionConfig]:
    return [
        function_config
        for n in ocg.object_config_graph_nodes
        if (function_config := get_node_function_config(n)) is not None
    ]


def get_class_configs(ocg: ObjectConfigGraph) -> list[ClassConfig]:
    return [n.class_config for n in ocg.object_config_graph_nodes if n.class_config is not None]


def get_class_config_relationships(
    ocg: ObjectConfigGraph,
) -> list[ClassConfigRelationship]:
    return [
        n.class_config_relationship for n in ocg.object_config_graph_nodes if n.class_config_relationship is not None
    ]
