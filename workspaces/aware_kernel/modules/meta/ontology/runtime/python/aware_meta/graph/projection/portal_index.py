from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


@dataclass(frozen=True)
class ObjectProjectionGraphPortal:
    """
    Canonical "portal" derived from ObjectProjectionGraphRelationship.

    This is the SSOT runtime needs to:
    - authorize cross-projection propagation
    - resolve the target lane (projection_hash / opg_id)
    - resolve relationship binding (reference field name) without heuristics.
    """

    object_projection_graph_relationship_id: UUID

    source_object_projection_graph_id: UUID
    source_projection_hash: str

    target_object_projection_graph_id: UUID
    target_projection_hash: str

    class_config_relationship_id: UUID
    source_class_config_id: UUID
    target_class_config_id: UUID

    reference_attribute_config_id: UUID
    reference_field_name: str


class ObjectProjectionGraphPortalIndex(BaseModel):
    """
    Fast lookup indexes for cross-OPG portal relationships.

    NOTE: This is an in-memory index only (not a wire artifact). It is intended to
    be computed once per loaded environment bundle and reused across function calls.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    portals: list[ObjectProjectionGraphPortal] = Field(default_factory=list)

    portals_by_source_projection_hash: dict[str, list[ObjectProjectionGraphPortal]] = Field(default_factory=dict)
    portals_by_source_projection_hash_and_relationship_id: dict[str, dict[UUID, list[ObjectProjectionGraphPortal]]] = (
        Field(default_factory=dict)
    )

    reference_attribute_config_id_by_relationship_id: dict[UUID, UUID] = Field(default_factory=dict)
    reference_field_name_by_relationship_id: dict[UUID, str] = Field(default_factory=dict)
    foreign_key_attribute_config_id_by_relationship_id: dict[UUID, UUID] = Field(default_factory=dict)
    foreign_key_field_name_by_relationship_id: dict[UUID, str] = Field(default_factory=dict)


@dataclass(frozen=True)
class ObjectProjectionGraphPortalClosureContext:
    """
    Prepared cross-graph portal metadata for one runtime graph closure.

    The context contains only stable OCG/OPG metadata keyed by UUID. Callers still
    build a per-graph portal index so source graph filtering and output ordering
    remain identical to the direct `build_portal_index` path.
    """

    opg_by_id: Mapping[UUID, ObjectProjectionGraph]
    relationships_by_id: Mapping[UUID, ClassConfigRelationship]
    class_by_id: Mapping[UUID, ClassConfig]
    attr_name_by_id: Mapping[UUID, tuple[UUID, str]]
    graph_count: int


def build_portal_closure_context(
    ocg: ObjectConfigGraph,
    *,
    external_graphs: list[ObjectConfigGraph] | None = None,
) -> ObjectProjectionGraphPortalClosureContext:
    """Build reusable cross-graph metadata for portal index construction."""

    graphs: list[ObjectConfigGraph] = [ocg, *(external_graphs or [])]

    opg_by_id: dict[UUID, ObjectProjectionGraph] = {}
    for g in graphs:
        for opg in g.object_projection_graphs:
            opg_by_id.setdefault(opg.id, opg)

    relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
    class_by_id: dict[UUID, ClassConfig] = {}
    for g in graphs:
        for node in g.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                class_by_id[node.class_config.id] = node.class_config
                _merge_class_config_metadata(
                    class_config=node.class_config,
                    class_by_id=class_by_id,
                    relationships_by_id=relationships_by_id,
                )
            if node.type == ObjectConfigGraphNodeType.relationship and node.class_config_relationship is not None:
                relationships_by_id[node.class_config_relationship.id] = node.class_config_relationship
        # cross ocg relationships (to allow cross-ocg / opg resolution)
        for rel in g.object_config_graph_relationships:
            for rel_class in rel.object_config_graph_relationship_classes:
                if rel_class.class_config is not None:
                    class_by_id.setdefault(
                        rel_class.class_config.id,
                        rel_class.class_config,
                    )
            for class_config_relationship in rel.class_config_relationships:
                relationships_by_id[class_config_relationship.id] = class_config_relationship

    _merge_installed_binding_metadata(
        class_by_id=class_by_id,
        relationships_by_id=relationships_by_id,
    )

    attr_name_by_id: dict[UUID, tuple[UUID, str]] = {}
    for c in class_by_id.values():
        for link in c.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_name_by_id[link.attribute_config.id] = (
                c.id,
                link.attribute_config.name,
            )

    return ObjectProjectionGraphPortalClosureContext(
        opg_by_id=opg_by_id,
        relationships_by_id=relationships_by_id,
        class_by_id=class_by_id,
        attr_name_by_id=attr_name_by_id,
        graph_count=len(graphs),
    )


def build_portal_index(
    ocg: ObjectConfigGraph,
    *,
    external_graphs: list[ObjectConfigGraph] | None = None,
    closure_context: ObjectProjectionGraphPortalClosureContext | None = None,
) -> ObjectProjectionGraphPortalIndex:
    """
    Build a portal index from an OCG that already has OPGs attached.

    Invariants:
    - All referenced OPG relationships must be resolvable from in-memory OCG(+externals).
    - No DB lookups: missing links are hard errors (clarity > cleverness).
    """
    if closure_context is None:
        closure_context = build_portal_closure_context(
            ocg,
            external_graphs=external_graphs,
        )
    opg_by_id = closure_context.opg_by_id

    # This index exists to support cross-OPG routing, so we intentionally restrict
    # relationship binding analysis to only the relationships referenced by OPG portals.
    #
    # Kernel OCGs may contain many relationships (including MANY_TO_MANY association
    # edges) whose FK bindings are not represented as source-owned fields; attempting
    # to derive FK field names for *all* relationships would make runtime startup
    # brittle and is out of scope for portal middleware.
    portal_relationship_ids: set[UUID] = set()
    for source_opg in ocg.object_projection_graphs:
        for rel in source_opg.object_projection_graph_relationships:
            if rel.class_config_relationship_id is not None:
                portal_relationship_ids.add(rel.class_config_relationship_id)

    relationships_by_id = closure_context.relationships_by_id
    attr_name_by_id = closure_context.attr_name_by_id

    reference_attribute_config_id_by_relationship_id: dict[UUID, UUID] = {}
    reference_field_name_by_relationship_id: dict[UUID, str] = {}
    foreign_key_attribute_config_id_by_relationship_id: dict[UUID, UUID] = {}
    foreign_key_field_name_by_relationship_id: dict[UUID, str] = {}
    for rel in relationships_by_id.values():
        if rel.id not in portal_relationship_ids:
            continue
        ref_attr_id: UUID | None = None
        fk_attr_id: UUID | None = None
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
            ):
                ref_attr_id = ra.attribute_config_id
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.foreign_key
            ):
                fk_attr_id = ra.attribute_config_id
        if ref_attr_id is None:
            raise ValueError(f"Portal index: relationship {rel.id} missing FORWARD+REFERENCE attribute binding")
        owner_and_name = attr_name_by_id.get(ref_attr_id)
        if owner_and_name is None:
            raise ValueError(
                "Portal index: relationship "
                f"{rel.id} reference attribute_config_id={ref_attr_id} "
                "not found on any class"
            )
        owner_class_id, field_name = owner_and_name
        if owner_class_id != rel.class_config_id:
            raise ValueError(
                f"Portal index: relationship {rel.id} reference attribute_config_id={ref_attr_id} "
                f"is not owned by the relationship source class_id={rel.class_config_id}"
            )
        reference_attribute_config_id_by_relationship_id[rel.id] = ref_attr_id
        reference_field_name_by_relationship_id[rel.id] = field_name

        # v0: only record FK bindings that are owned by the relationship source class.
        # Reverse / auxiliary relationship bindings are not lane-routing primitives.
        if fk_attr_id is None:
            continue
        fk_owner_and_name = attr_name_by_id.get(fk_attr_id)
        if fk_owner_and_name is None:
            raise ValueError(
                "Portal index: relationship "
                f"{rel.id} foreign_key attribute_config_id={fk_attr_id} "
                "not found on any class"
            )
        fk_owner_class_id, fk_field_name = fk_owner_and_name
        if fk_owner_class_id != rel.class_config_id:
            continue
        foreign_key_attribute_config_id_by_relationship_id[rel.id] = fk_attr_id
        foreign_key_field_name_by_relationship_id[rel.id] = fk_field_name

    portals: list[ObjectProjectionGraphPortal] = []
    for source_opg in ocg.object_projection_graphs:
        for opg_rel in source_opg.object_projection_graph_relationships:
            target_opg = opg_rel.target_object_projection_graph
            if target_opg is None:
                target_opg = opg_by_id.get(opg_rel.target_object_projection_graph_id)
            if target_opg is None:
                raise ValueError(
                    "Portal index: ObjectProjectionGraphRelationship missing target OPG binding: "
                    f"opg_relationship_id={opg_rel.id} "
                    "target_object_projection_graph_id="
                    f"{opg_rel.target_object_projection_graph_id}"
                )

            cfg_rel = opg_rel.class_config_relationship or relationships_by_id.get(
                opg_rel.class_config_relationship_id
            )
            if cfg_rel is None:
                raise ValueError(
                    "Portal index: ObjectProjectionGraphRelationship missing ClassConfigRelationship binding: "
                    f"opg_relationship_id={opg_rel.id} "
                    "class_config_relationship_id="
                    f"{opg_rel.class_config_relationship_id}"
                )

            ref_attr_id = reference_attribute_config_id_by_relationship_id.get(cfg_rel.id)
            ref_field_name = reference_field_name_by_relationship_id.get(cfg_rel.id)
            if ref_attr_id is None or ref_field_name is None:
                raise ValueError(
                    "Portal index: missing reference field binding for relationship: "
                    f"class_config_relationship_id={cfg_rel.id}"
                )

            portals.append(
                ObjectProjectionGraphPortal(
                    object_projection_graph_relationship_id=opg_rel.id,
                    source_object_projection_graph_id=source_opg.id,
                    source_projection_hash=source_opg.projection_hash,
                    target_object_projection_graph_id=target_opg.id,
                    target_projection_hash=target_opg.projection_hash,
                    class_config_relationship_id=cfg_rel.id,
                    source_class_config_id=cfg_rel.class_config_id,
                    target_class_config_id=cfg_rel.target_class_config_id,
                    reference_attribute_config_id=ref_attr_id,
                    reference_field_name=ref_field_name,
                )
            )

    portals.sort(
        key=lambda p: (
            p.source_projection_hash,
            str(p.class_config_relationship_id),
            p.target_projection_hash,
            str(p.object_projection_graph_relationship_id),
        )
    )

    portals_by_source_hash: dict[str, list[ObjectProjectionGraphPortal]] = {}
    portals_by_source_hash_and_rel: dict[str, dict[UUID, list[ObjectProjectionGraphPortal]]] = {}
    for portal in portals:
        portals_by_source_hash.setdefault(portal.source_projection_hash, []).append(portal)
        portals_by_source_hash_and_rel.setdefault(portal.source_projection_hash, {}).setdefault(
            portal.class_config_relationship_id, []
        ).append(portal)

    # Ensure deterministic ordering for all group lists.
    for items in portals_by_source_hash.values():
        items.sort(
            key=lambda p: (
                str(p.class_config_relationship_id),
                p.target_projection_hash,
            )
        )
    for rel_map in portals_by_source_hash_and_rel.values():
        for items in rel_map.values():
            items.sort(key=lambda p: p.target_projection_hash)

    return ObjectProjectionGraphPortalIndex(
        portals=portals,
        portals_by_source_projection_hash=portals_by_source_hash,
        portals_by_source_projection_hash_and_relationship_id=portals_by_source_hash_and_rel,
        reference_attribute_config_id_by_relationship_id=reference_attribute_config_id_by_relationship_id,
        reference_field_name_by_relationship_id=reference_field_name_by_relationship_id,
        foreign_key_attribute_config_id_by_relationship_id=foreign_key_attribute_config_id_by_relationship_id,
        foreign_key_field_name_by_relationship_id=foreign_key_field_name_by_relationship_id,
    )


def _merge_class_config_metadata(
    *,
    class_config: object,
    class_by_id: dict[UUID, ClassConfig],
    relationships_by_id: dict[UUID, ClassConfigRelationship],
) -> None:
    if not isinstance(class_config, ClassConfig):
        return
    existing = class_by_id.get(class_config.id)
    if existing is None:
        class_by_id[class_config.id] = class_config
    else:
        existing_function_ids = {
            link.function_config_id
            for link in existing.class_config_function_configs
            if link.function_config_id is not None
        }
        existing_function_names = {
            (link.function_config.name or "").strip()
            for link in existing.class_config_function_configs
            if link.function_config is not None and (link.function_config.name or "").strip()
        }
        for link in class_config.class_config_function_configs:
            function_id = link.function_config_id
            function_name = (
                (link.function_config.name or "").strip()
                if link.function_config is not None
                else ""
            )
            if function_id is not None and function_id in existing_function_ids:
                continue
            if function_name and function_name in existing_function_names:
                continue
            existing.class_config_function_configs.append(link)
            if function_id is not None:
                existing_function_ids.add(function_id)
            if function_name:
                existing_function_names.add(function_name)
    for rel in class_config.class_config_relationships:
        relationships_by_id.setdefault(rel.id, rel)


def _merge_installed_binding_metadata(
    *,
    class_by_id: dict[UUID, ClassConfig],
    relationships_by_id: dict[UUID, ClassConfigRelationship],
) -> None:
    try:
        from aware_orm.registry import ORMModelRegistry  # noqa: WPS433

        for model_class in ORMModelRegistry.get_all_fqn_to_class().values():
            try:
                class_config = model_class.get_class_config()  # type: ignore[attr-defined]
            except Exception:
                class_config = None
            _merge_class_config_metadata(
                class_config=class_config,
                class_by_id=class_by_id,
                relationships_by_id=relationships_by_id,
            )
    except Exception:
        pass

    try:
        from aware_utils.pydantic.class_config_registry import (  # noqa: WPS433
            iter_registered_class_config_payloads,
        )

        for entry in iter_registered_class_config_payloads():
            try:
                class_config = ClassConfig.model_validate(entry.payload)
            except Exception:
                continue
            _merge_class_config_metadata(
                class_config=class_config,
                class_by_id=class_by_id,
                relationships_by_id=relationships_by_id,
            )
    except Exception:
        pass


__all__ = [
    "ObjectProjectionGraphPortal",
    "ObjectProjectionGraphPortalClosureContext",
    "ObjectProjectionGraphPortalIndex",
    "build_portal_closure_context",
    "build_portal_index",
]
