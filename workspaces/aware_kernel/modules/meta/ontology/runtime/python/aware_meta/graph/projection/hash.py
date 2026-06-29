import hashlib
import json
from uuid import UUID

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
    ObjectProjectionGraphRelationship,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipReifiedRole,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship

from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id


def calculate_hash(
    *,
    ocg: ObjectConfigGraph,
    nodes: list[ObjectProjectionGraphNode],
    edges: list[ObjectProjectionGraphEdge],
    relationships: list[ObjectProjectionGraphRelationship] | None = None,
    external_graphs: list[ObjectConfigGraph] | None = None,
    additional_relationships: list[ClassConfigRelationship] | None = None,
) -> str:
    """
    Returns lowercase hex SHA-256 over canonical membership rules,
    recursively substituting subgraph hashes (composition-aware).
    Raises if a referenced subgraph is missing.
    """

    # -----------------------------
    # Build stable keys from OCG (+ externals)
    # -----------------------------
    graphs: list[ObjectConfigGraph] = [ocg, *(external_graphs or [])]
    class_id_to_fqn: dict[UUID, str] = {}
    rel_id_to_key: dict[UUID, str] = {}
    rel_by_id: dict[UUID, ClassConfigRelationship] = {}

    class_by_id: dict[UUID, ClassConfig] = {}
    fqn_to_class_id: dict[str, UUID] = {}
    # Index classes by id + compute class fqn from topology.
    for g in graphs:
        ns_by_node_id = build_node_namespace_by_node_id(g)
        for n in g.object_config_graph_nodes:
            if n.type != ObjectConfigGraphNodeType.class_ or n.class_config is None:
                continue
            prev = class_by_id.get(n.class_config.id)
            if prev is None:
                class_by_id[n.class_config.id] = n.class_config
            ns = ns_by_node_id.get(n.id)
            explicit_fqn = (getattr(n.class_config, "class_fqn", None) or "").strip()
            if not explicit_fqn and ns is None:
                continue
            fqn = explicit_fqn or ns.fqn(n.class_config.name)
            prev_id = fqn_to_class_id.get(fqn)
            if prev_id is not None and prev_id != n.class_config.id:
                raise ValueError(f"OPG hash: duplicate class FQN {fqn!r} maps to {prev_id} and {n.class_config.id}")
            fqn_to_class_id[fqn] = n.class_config.id
            prev_fqn = class_id_to_fqn.get(n.class_config.id)
            if prev_fqn is not None and prev_fqn != fqn:
                raise ValueError(
                    f"OPG hash: class_config_id={n.class_config.id} maps to multiple FQNs: {prev_fqn!r} and {fqn!r}"
                )
            class_id_to_fqn[n.class_config.id] = fqn

    # AttributeConfig.id -> (owner_class_id, attr_name)
    attr_name_by_id: dict[UUID, tuple[UUID, str]] = {}
    for c in class_by_id.values():
        for link in c.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_name_by_id[link.attribute_config.id] = (
                c.id,
                link.attribute_config.name,
            )

    def _index_relationship(rel: ClassConfigRelationship) -> None:
        rel_by_id[rel.id] = rel
        src_fqn = class_id_to_fqn.get(rel.class_config_id)
        if src_fqn is None:
            raise ValueError(f"OPG hash: missing source class_fqn for relationship {rel.id}")
        attr_name = _declaring_attr_name(rel=rel, attr_name_by_id=attr_name_by_id)
        assoc_name = None
        if rel.class_config_relationship_association_edge is not None:
            assoc_id = rel.class_config_relationship_association_edge.class_config_id
            if assoc_id is not None:
                assoc_cls = class_by_id.get(assoc_id)
                assoc_name = assoc_cls.name if assoc_cls is not None else None
        key = f"{src_fqn}::{attr_name}"
        if assoc_name:
            key = f"{key}::{assoc_name}"
        prev = rel_id_to_key.get(rel.id)
        if prev is not None and prev != key:
            raise ValueError(f"OPG hash: relationship_id={rel.id} maps to multiple keys: {prev!r} and {key!r}")
        rel_id_to_key[rel.id] = key

    # Compute stable relationship key: {source_class_fqn}::{declaring_attr}(::{association_class_name})?
    for g in graphs:
        for n in g.object_config_graph_nodes:
            if n.type != ObjectConfigGraphNodeType.relationship or n.class_config_relationship is None:
                continue
            _index_relationship(n.class_config_relationship)
    for class_config in class_by_id.values():
        for rel in class_config.class_config_relationships or []:
            _index_relationship(rel)

    # Canonical: detached cross-OCG relationships are not embedded as RELATIONSHIP nodes, but still
    # participate in projection hashing when referenced by membership edges or portals.
    for rel in additional_relationships or []:
        # Detached candidates may come from a wider dependency catalog; referenced
        # relationships still fail later if they are genuinely required.
        if rel.class_config_id not in class_id_to_fqn:
            continue
        _index_relationship(rel)

    # Build canonical lists first (stable across rebuilds)
    node_entries = [canon_node(node=r, class_id_to_fqn=class_id_to_fqn) for r in nodes]
    edge_entries = [canon_edge(edge=r, rel_id_to_key=rel_id_to_key) for r in edges]

    nodes_sorted = sorted(node_entries, key=lambda x: str(x["class_fqn"]))
    edges_sorted = sorted(edge_entries, key=lambda x: str(x["relationship_key"]))

    relationships_entries = None
    if relationships:
        # Cross-OPG portals must be hashed by projection identity, not user-facing names.
        #
        # We intentionally avoid hashing the target projection's full projection_hash here
        # to prevent cycles (A -> B and B -> A). Instead we hash the target membership only
        # (nodes + edges), which is stable and name-insensitive.
        membership_hash_by_opg_id: dict[UUID, str] = {}

        relationships_entries = []
        for rel in relationships:
            target_opg = rel.target_object_projection_graph
            if target_opg is None:
                raise ValueError(
                    "OPG hash: portal relationship missing target_object_projection_graph binding; "
                    "ensure relationships are provisioned with in-memory target bindings before hashing"
                )
            target_membership_hash = membership_hash_by_opg_id.get(target_opg.id)
            if target_membership_hash is None:
                target_membership_hash = calculate_hash(
                    ocg=ocg,
                    nodes=target_opg.object_projection_graph_nodes,
                    edges=target_opg.object_projection_graph_edges,
                    relationships=None,
                    external_graphs=external_graphs,
                    additional_relationships=additional_relationships,
                )
                membership_hash_by_opg_id[target_opg.id] = target_membership_hash

            cfg_rel = rel_by_id.get(rel.class_config_relationship_id)
            if cfg_rel is None:
                raise ValueError(
                    "OPG hash: portal relationship references unknown "
                    f"class_config_relationship_id={rel.class_config_relationship_id}"
                )
            target_class_fqn = class_id_to_fqn.get(cfg_rel.target_class_config_id) or str(
                cfg_rel.target_class_config_id
            )

            relationships_entries.append(
                {
                    "relationship_key": rel_id_to_key.get(rel.class_config_relationship_id)
                    or str(rel.class_config_relationship_id),
                    "target_membership_hash": target_membership_hash,
                    "target_class_fqn": target_class_fqn,
                }
            )

        relationships_entries = sorted(
            relationships_entries,
            key=lambda x: (
                x["relationship_key"],
                x["target_membership_hash"],
                x["target_class_fqn"],
            ),
        )

    canonical = {
        "canon_version": "opgcanon:3" if relationships_entries else "opgcanon:2",
        "nodes": nodes_sorted,
        "edges": edges_sorted,
    }
    if relationships_entries:
        canonical["relationships"] = relationships_entries

    payload = json.dumps(canonical, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canon_node(*, node: ObjectProjectionGraphNode, class_id_to_fqn: dict[UUID, str]):
    sub = None
    # Prefer attached subgraph instance when present to avoid premature DB lookups

    # !! TODO: add SUBGRAPHS
    # Track visited to prevent cycles in composed OPGs
    # visited: set = set()
    # if rule.subgraph_opg is not None:
    #     sub_opg = rule.subgraph_opg
    #     if sub_opg.id in visited:
    #         sub = sub_opg.projection_hash
    #     else:
    #         visited.add(sub_opg.id)
    #         sub = sub_opg.projection_hash or await sub_opg.calculate_hash()
    # elif rule.subgraph_opg_id:
    #     sub_opg = await ObjectProjectionGraph.get_by_id(rule.subgraph_opg_id, eager=False)
    #     if sub_opg is None:
    #         raise ValueError(f"OPG {self.id}: missing subgraph {rule.subgraph_opg_id}")
    #     if sub_opg.id in visited:
    #         sub = sub_opg.projection_hash
    #     else:
    #         visited.add(sub_opg.id)
    #         sub = sub_opg.projection_hash or await sub_opg.calculate_hash()
    return {
        "class_fqn": class_id_to_fqn.get(node.class_config_id) or str(node.class_config_id),
        "selection": node.selection.value,  # normalized string
        "top_n": (node.top_n if node.selection == ObjectProjectionGraphNodeSelection.top_n else None),
        "required_for_validity": bool(node.required_for_validity),
        "subgraph_hash": sub,
    }


def canon_edge(*, edge: ObjectProjectionGraphEdge, rel_id_to_key: dict[UUID, str]):
    return {
        "relationship_key": rel_id_to_key.get(edge.class_config_relationship_id)
        or str(edge.class_config_relationship_id),
        "include": edge.include.value,
        "multiplicity": edge.multiplicity.value,
        "traversal_direction": edge.traversal_direction.value,
        "depth_limit": edge.depth_limit if edge.depth_limit is not None else None,
        "attribute_role": (edge.attribute_role.value if edge.attribute_role is not None else None),
    }


def _declaring_attr_name(*, rel: ClassConfigRelationship, attr_name_by_id: dict[UUID, tuple[UUID, str]]) -> str:
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
            return rel.relationship_key
        raise ValueError(f"OPG hash: relationship {rel.id} missing FORWARD+REFERENCE attribute binding")
    owner_and_name = attr_name_by_id.get(ref_attr_id)
    if owner_and_name is None:
        raise ValueError(f"OPG hash: relationship {rel.id} reference attribute_config_id={ref_attr_id} not found")
    owner_class_id, attr_name = owner_and_name
    if owner_class_id != rel.class_config_id:
        raise ValueError(
            f"OPG hash: relationship {rel.id} reference attribute_config_id={ref_attr_id} not owned by source"
        )
    return attr_name
