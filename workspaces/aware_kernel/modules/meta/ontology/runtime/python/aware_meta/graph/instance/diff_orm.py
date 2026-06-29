"""ORM delta → canonical OIG change graphs (delta-first, v0).

Runtime goal
------------
The production commit pipeline must be **delta-first**:

`OIG(pre) + ORM-collected in-memory changes → ObjectInstanceGraphChange[] → OIG Commit`

OIG(post) is a derived materialization by applying the change graph (and may be
used for validation/debug), but it must not be the SSOT for commits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from aware_orm.models.introspection import ModelIntrospection
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import ORMChangeSet, snapshot_list, stable_ref

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import stable_class_instance_id

from aware_meta.attribute.instance.value.builder import (
    ClassInstanceResolver,
    EnumOptionResolver,
    UnionSelection,
)
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes


class OrmChangeTranslationError(ValueError):
    pass


@dataclass(frozen=True)
class _RelationshipFieldSpec:
    relationship_id: UUID
    direction: ClassConfigRelationshipDirection


@dataclass(frozen=True)
class _OcgIndex:
    class_configs_by_id: dict[UUID, ClassConfig]
    relationships_by_id: dict[UUID, ClassConfigRelationship]
    attribute_names_by_id: dict[UUID, str]
    owner_class_config_by_attribute_id: dict[UUID, UUID]
    relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    portal_include_relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    soft_ref_include_relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    required_fk_include_relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    opg_class_config_ids: frozenset[UUID]
    opg_relationship_ids: frozenset[UUID]
    relationship_field_specs_by_cc_id: dict[UUID, dict[str, _RelationshipFieldSpec]]


@dataclass(frozen=True)
class _RelationshipContextSource(ModelIntrospection):
    source: ModelIntrospection
    values_by_name: dict[str, object]

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


_OCG_INDEX_CACHE: dict[tuple[UUID, UUID], _OcgIndex] = {}


def _resolve_root_class_instance_snapshot(
    *,
    class_instances: list[Any],
    expected_root_class_instance_id: UUID | None,
    fallback_root_class_instance: Any | None,
) -> Any | None:
    if expected_root_class_instance_id is None:
        return fallback_root_class_instance
    for class_instance in class_instances:
        if getattr(class_instance, "id", None) == expected_root_class_instance_id:
            return class_instance
    if (
        getattr(fallback_root_class_instance, "id", None)
        == expected_root_class_instance_id
    ):
        return fallback_root_class_instance
    raise OrmChangeTranslationError(
        "Root ClassInstance missing from ObjectInstanceGraph diff snapshot: "
        + f"root_class_instance_id={expected_root_class_instance_id}"
    )


def build_object_instance_graph_changes_from_orm_change_set(
    *,
    before_oig: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    change_set: ORMChangeSet,
    class_configs_by_id: dict[UUID, ClassConfig] | None = None,
    relationships_by_id: dict[UUID, ClassConfigRelationship] | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
) -> list[ObjectInstanceGraphChange]:
    """Translate ORM-collected mutations into canonical OIG change graphs.

    Notes
    -----
    - This function intentionally does not build OIG(post) from ORM.
    - ClassInstance attribute changes are produced by diffing a *subset* of OIG members:
      - old snapshot members are taken from `before_oig` (SSOT),
      - new snapshot members are rebuilt from the mutated ORM objects.
      This avoids accidental deletes when ORM views are partial/unhydrated.
    - Relationship changes are derived from the ORM change collector baselines
      (append/remove semantics), then applied against OIG(pre) by the applier.
    """
    if before_oig.id is None:
        raise OrmChangeTranslationError("before_oig.id is required")

    created_at = change_set.collected_at

    index = _build_ocg_index(
        ocg=ocg,
        opg=opg,
        class_configs_by_id=class_configs_by_id,
        relationships_by_id=relationships_by_id,
    )

    # ---- ClassInstance changes (attributes/value trees) ------------------- #
    class_instance_changes = _build_class_instance_changes(
        before_oig=before_oig,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        change_set=change_set,
        index=index,
        created_at=created_at,
        enum_option_resolver=enum_option_resolver,
        class_instance_resolver=class_instance_resolver,
        union_selections=union_selections,
    )

    # ---- Relationship changes (structural edges) -------------------------- #
    relationship_changes = _build_relationship_changes(
        before_oig=before_oig,
        change_set=change_set,
        index=index,
        created_at=created_at,
    )

    if not class_instance_changes and not relationship_changes:
        return []

    out: list[ObjectInstanceGraphChange] = []
    if class_instance_changes:
        with disable_autobind():
            root_change = Change(
                key="root:object_instance:update",
                type=ChangeType.update,
                change_deltas=[],
                created_at=created_at,
            )
            out.append(
                ObjectInstanceGraphChange(
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    object_instance_graph_id=before_oig.id,
                    type=ObjectInstanceGraphChangeType.object_instance,
                    change=root_change,
                    change_id=root_change.id,
                    class_instance_changes=class_instance_changes,
                    class_instance_relationship_changes=[],
                )
            )
    if relationship_changes:
        with disable_autobind():
            root_change = Change(
                key="root:object_instance_relationship:update",
                type=ChangeType.update,
                change_deltas=[],
                created_at=created_at,
            )
            out.append(
                ObjectInstanceGraphChange(
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    object_instance_graph_id=before_oig.id,
                    type=ObjectInstanceGraphChangeType.object_instance_relationship,
                    change=root_change,
                    change_id=root_change.id,
                    class_instance_changes=[],
                    class_instance_relationship_changes=relationship_changes,
                )
            )
    return out


def _build_ocg_index(
    *,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    class_configs_by_id: dict[UUID, ClassConfig] | None = None,
    relationships_by_id: dict[UUID, ClassConfigRelationship] | None = None,
) -> _OcgIndex:
    cache_key: tuple[UUID, UUID] | None = None
    # Cache only when deriving from the OCG itself. Callers can inject broader indexes
    # (e.g., cross-module projections) whose dependency installation state may differ
    # across tests or harness runs in the same process.
    if class_configs_by_id is None and relationships_by_id is None:
        if ocg.id is not None and opg.id is not None:
            cache_key = (ocg.id, opg.id)
            cached = _OCG_INDEX_CACHE.get(cache_key)
            if cached is not None:
                return cached

    resolved_class_configs_by_id: dict[UUID, ClassConfig] = {}
    resolved_relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
    attribute_names_by_id: dict[UUID, str] = {}

    if class_configs_by_id is None or relationships_by_id is None:
        for node in ocg.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                resolved_class_configs_by_id[node.class_config.id] = node.class_config
            elif (
                node.type == ObjectConfigGraphNodeType.relationship
                and node.class_config_relationship is not None
            ):
                resolved_relationships_by_id[node.class_config_relationship.id] = (
                    node.class_config_relationship
                )
        # Include detached cross-OCG relationships when present on the OCG payload.
        for ocg_rel in ocg.object_config_graph_relationships:
            for rel_class in ocg_rel.object_config_graph_relationship_classes:
                cc = rel_class.class_config
                if cc is None:
                    continue
                resolved_class_configs_by_id.setdefault(cc.id, cc)
            for rel in ocg_rel.class_config_relationships:
                resolved_relationships_by_id.setdefault(rel.id, rel)
    else:
        resolved_class_configs_by_id.update(class_configs_by_id)
        resolved_relationships_by_id.update(relationships_by_id)

    # Ensure OPG membership is resolvable in the provided index.
    missing_cc_ids = [
        cc_id
        for cc_id in (n.class_config_id for n in opg.object_projection_graph_nodes)
        if cc_id not in resolved_class_configs_by_id
    ]
    if missing_cc_ids:
        raise OrmChangeTranslationError(
            "ClassConfig(s) missing for OPG membership: "
            f"object_projection_graph_id={opg.id} missing={missing_cc_ids}"
        )

    missing_rel_ids = [
        rel_id
        for rel_id in (
            e.class_config_relationship_id for e in opg.object_projection_graph_edges
        )
        if rel_id not in resolved_relationships_by_id
    ]
    if missing_rel_ids:
        raise OrmChangeTranslationError(
            "ClassConfigRelationship(s) missing for OPG edges: "
            f"object_projection_graph_id={opg.id} missing={missing_rel_ids}"
        )

    owner_cc_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in resolved_class_configs_by_id.items():
        for link in cc.class_config_attribute_configs:
            ac = link.attribute_config
            if ac is None:
                continue
            prev = owner_cc_by_attr_id.get(ac.id)
            if prev is not None and prev != cc_id:
                raise OrmChangeTranslationError(
                    f"AttributeConfig {ac.id} owned by multiple ClassConfigs ({prev} vs {cc_id})"
                )
            owner_cc_by_attr_id[ac.id] = cc_id

            # Prefer direct wiring for name resolution when available.
            attribute_names_by_id.setdefault(ac.id, ac.name)

    relationship_attr_ids_by_cc: dict[UUID, set[UUID]] = {
        cc_id: set() for cc_id in resolved_class_configs_by_id
    }
    for rel in resolved_relationships_by_id.values():
        for rel_attr in rel.class_config_relationship_attributes:
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            owner_cc_id = owner_cc_by_attr_id.get(attr_id)
            if owner_cc_id is None:
                continue
            relationship_attr_ids_by_cc.setdefault(owner_cc_id, set()).add(attr_id)

    opg_class_config_ids = frozenset(
        {n.class_config_id for n in opg.object_projection_graph_nodes}
    )
    opg_relationship_ids = frozenset(
        {e.class_config_relationship_id for e in opg.object_projection_graph_edges}
    )

    portal_include_by_cc: dict[UUID, set[UUID]] = {}
    portals = opg.object_projection_graph_relationships
    for portal in portals:
        rel = (
            resolved_relationships_by_id.get(portal.class_config_relationship_id)
            or portal.class_config_relationship
        )
        if rel is None:
            raise OrmChangeTranslationError(
                "Portal relationship missing ClassConfigRelationship binding: "
                f"object_projection_graph_id={opg.id} class_config_relationship_id={portal.class_config_relationship_id}"
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
            continue

        owner_cc_id = owner_cc_by_attr_id.get(fk_attr_id)
        if owner_cc_id is None:
            raise OrmChangeTranslationError(
                "Portal relationship FOREIGN_KEY attribute_config_id not found on any ClassConfig: "
                f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
            )
        if owner_cc_id != rel.class_config_id:
            raise OrmChangeTranslationError(
                "Portal relationship FOREIGN_KEY attribute must be owned by the relationship source ClassConfig: "
                f"class_config_relationship_id={rel.id} owner_class_config_id={owner_cc_id} expected={rel.class_config_id}"
            )

        portal_include_by_cc.setdefault(owner_cc_id, set()).add(fk_attr_id)

    # SoftRef retention (projection frontier):
    # - If a relationship is NOT represented as an OPG edge (StrongRef),
    # - preserve any explicit FOREIGN_KEY binding whose owner class is in this OPG.
    #
    # Direction is intentionally ignored (forward or reverse): the deterministic
    # primitive FK value must remain commit-tracked on the owning class instance.
    # Without this, required FK columns can be dropped from OIG snapshots and later
    # fail DB projection (for example reverse-owned FK shapes such as ActorRole.actor_id).
    soft_ref_include_by_cc: dict[UUID, set[UUID]] = {}
    for rel in resolved_relationships_by_id.values():
        if rel.id is None:
            continue
        # Relationship analysis may retain detached cross-graph relationships
        # whose endpoints are not present in this OCG dependency closure.
        # Those are irrelevant for this projection's soft-ref retention.
        if (
            rel.class_config_id not in resolved_class_configs_by_id
            or rel.target_class_config_id not in resolved_class_configs_by_id
        ):
            continue
        if rel.id in opg_relationship_ids:
            # StrongRef: FK values come from relationship edges, not from committed FK attributes.
            continue
        for rel_attr in rel.class_config_relationship_attributes:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            fk_attr_id = rel_attr.attribute_config_id
            if fk_attr_id is None:
                continue

            owner_cc_id = owner_cc_by_attr_id.get(fk_attr_id)
            if owner_cc_id is None:
                raise OrmChangeTranslationError(
                    "SoftRef FOREIGN_KEY attribute_config_id not found on any ClassConfig: "
                    f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
                )
            if owner_cc_id not in {
                rel.class_config_id,
                rel.target_class_config_id,
            }:
                continue
            if owner_cc_id not in opg_class_config_ids:
                continue

            soft_ref_include_by_cc.setdefault(owner_cc_id, set()).add(fk_attr_id)

    # Required FK retention (commit truth):
    # - Keep required FK primitives as data attributes even when relationships are represented
    #   as edges, so commit payloads stay self-contained across portal/hard-boundary contexts.
    # - Requiredness is derived from relationship schema semantics (not AttributeConfig.is_required).
    required_fk_include_by_cc: dict[UUID, set[UUID]] = {}

    def _is_required_fk(
        rel: ClassConfigRelationship, *, direction: ClassConfigRelationshipDirection
    ) -> bool:
        if rel.class_config_relationship_association_edge is not None:
            return True
        return bool(rel.forward_required)

    for rel in resolved_relationships_by_id.values():
        # Relationship analysis may retain detached cross-graph relationships
        # whose endpoints are not present in this OCG dependency closure.
        # Those are irrelevant for this projection's required-FK retention.
        if (
            rel.class_config_id not in resolved_class_configs_by_id
            or rel.target_class_config_id not in resolved_class_configs_by_id
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

            owner_cc_id = owner_cc_by_attr_id.get(fk_attr_id)
            if owner_cc_id is None:
                raise OrmChangeTranslationError(
                    "Required FK attribute_config_id not found on any ClassConfig: "
                    f"class_config_relationship_id={rel.id} attribute_config_id={fk_attr_id}"
                )
            if owner_cc_id not in opg_class_config_ids:
                continue
            required_fk_include_by_cc.setdefault(owner_cc_id, set()).add(fk_attr_id)

    relationship_field_specs_by_cc_id: dict[UUID, dict[str, _RelationshipFieldSpec]] = (
        {}
    )
    for rel in resolved_relationships_by_id.values():
        if rel.id not in opg_relationship_ids:
            continue
        if rel.class_config_relationship_association_edge is not None:
            raise OrmChangeTranslationError(
                "Association-edge relationships must be reified in runtime OCG (A→Edge→B) before diff_orm translation: "
                f"class_config_relationship_id={rel.id}"
            )
        for rel_attr in rel.class_config_relationship_attributes:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                continue
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            owner_cc_id = owner_cc_by_attr_id.get(attr_id)
            if owner_cc_id is None:
                continue
            name = attribute_names_by_id.get(attr_id)
            if not name:
                continue
            relationship_field_specs_by_cc_id.setdefault(owner_cc_id, {})[name] = (
                _RelationshipFieldSpec(
                    relationship_id=rel.id,
                    direction=rel_attr.direction,
                )
            )

    # Foreign-key scalar fields can encode relationship intent when reverse reference
    # fields are not annotated in `.aware`. Commit truth remains relationship edges;
    # FK values are used only to derive those edges deterministically.
    for rel in resolved_relationships_by_id.values():
        if rel.id not in opg_relationship_ids:
            continue
        if rel.class_config_relationship_association_edge is not None:
            raise OrmChangeTranslationError(
                "Association-edge relationships must be reified in runtime OCG (A→Edge→B) before diff_orm translation: "
                f"class_config_relationship_id={rel.id}"
            )
        for rel_attr in rel.class_config_relationship_attributes:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            owner_cc_id = owner_cc_by_attr_id.get(attr_id)
            if owner_cc_id is None:
                continue
            if owner_cc_id not in {rel.class_config_id, rel.target_class_config_id}:
                continue
            name = attribute_names_by_id.get(attr_id)
            if not name:
                continue
            relationship_field_specs_by_cc_id.setdefault(owner_cc_id, {}).setdefault(
                name,
                _RelationshipFieldSpec(
                    relationship_id=rel.id,
                    direction=rel_attr.direction,
                ),
            )

    out = _OcgIndex(
        class_configs_by_id=resolved_class_configs_by_id,
        relationships_by_id=resolved_relationships_by_id,
        attribute_names_by_id=attribute_names_by_id,
        owner_class_config_by_attribute_id=owner_cc_by_attr_id,
        relationship_attribute_ids_by_cc_id=relationship_attr_ids_by_cc,
        portal_include_relationship_attribute_ids_by_cc_id=portal_include_by_cc,
        soft_ref_include_relationship_attribute_ids_by_cc_id=soft_ref_include_by_cc,
        required_fk_include_relationship_attribute_ids_by_cc_id=required_fk_include_by_cc,
        opg_class_config_ids=opg_class_config_ids,
        opg_relationship_ids=opg_relationship_ids,
        relationship_field_specs_by_cc_id=relationship_field_specs_by_cc_id,
    )
    if cache_key is not None:
        _OCG_INDEX_CACHE[cache_key] = out
    return out


def _build_class_instance_changes(
    *,
    before_oig: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    change_set: ORMChangeSet,
    index: _OcgIndex,
    created_at: datetime,
    enum_option_resolver: EnumOptionResolver | None,
    class_instance_resolver: ClassInstanceResolver | None,
    union_selections: dict[str, UnionSelection] | None,
) -> list[Any]:
    # Map pre-state class instances for quick lookup (SSOT baseline).
    before_by_source_id = {
        ci.source_object_id: ci
        for ci in before_oig.class_instances
        if ci is not None and ci.id is not None and ci.source_object_id is not None
    }

    candidate_ids: set[UUID] = set(change_set.touched_ids) | set(change_set.deleted_ids)
    if not candidate_ids:
        return []

    old_instances = [
        before_by_source_id[cid]
        for cid in sorted(candidate_ids, key=str)
        if cid in before_by_source_id
    ]
    new_instances = []
    relationship_context_values_by_id = _relationship_context_values_by_object_id(
        change_set=change_set,
        index=index,
    )

    for cid in sorted(candidate_ids, key=str):
        obj = change_set.objects_by_id.get(cid)
        if obj is None:
            continue

        class_config_id = None
        before_ci = before_by_source_id.get(cid)
        if before_ci is not None and before_ci.class_config_id is not None:
            class_config_id = before_ci.class_config_id
        else:
            try:
                class_config_id = getattr(obj, "try_class_config_id")()
            except Exception:
                class_config_id = None

        if class_config_id is None:
            continue

        if class_config_id not in index.opg_class_config_ids:
            continue

        class_config = index.class_configs_by_id.get(class_config_id)
        if class_config is None:
            raise OrmChangeTranslationError(
                f"ClassConfig not found: {class_config_id} (instance_id={cid})"
            )

        rel_attr_ids = index.relationship_attribute_ids_by_cc_id.get(class_config_id)
        include_attr_ids: set[UUID] = set()
        include_attr_ids |= (
            index.portal_include_relationship_attribute_ids_by_cc_id.get(
                class_config_id, set()
            )
        )
        include_attr_ids |= (
            index.soft_ref_include_relationship_attribute_ids_by_cc_id.get(
                class_config_id, set()
            )
        )
        include_attr_ids |= (
            index.required_fk_include_relationship_attribute_ids_by_cc_id.get(
                class_config_id, set()
            )
        )

        source = _with_relationship_context_values(
            source=obj,
            values_by_name=relationship_context_values_by_id.get(cid),
        )

        new_instances.append(
            build_class_instance(
                object_instance_graph_id=before_oig.id,
                class_config=class_config,
                class_configs_by_id=index.class_configs_by_id,
                source=source,
                enum_option_resolver=enum_option_resolver,
                class_instance_resolver=class_instance_resolver,
                union_selections=union_selections,
                relationship_attribute_config_ids=rel_attr_ids,
                include_relationship_attribute_config_ids=include_attr_ids or None,
            )
        )

    if not old_instances and not new_instances:
        return []

    old_root_class_instance = _resolve_root_class_instance_snapshot(
        class_instances=old_instances,
        expected_root_class_instance_id=before_oig.root_class_instance_id,
        fallback_root_class_instance=before_oig.root_class_instance,
    )
    new_root_class_instance = _resolve_root_class_instance_snapshot(
        class_instances=new_instances,
        expected_root_class_instance_id=before_oig.root_class_instance_id,
        fallback_root_class_instance=before_oig.root_class_instance,
    )

    with disable_autobind():
        old_graph = ObjectInstanceGraph(
            id=before_oig.id,
            key=before_oig.key,
            name=before_oig.name,
            description=before_oig.description,
            object_projection_graph_id=before_oig.object_projection_graph_id,
            root_class_instance_id=before_oig.root_class_instance_id,
            root_class_instance=old_root_class_instance,
            class_instances=list(old_instances),
            class_instance_relationships=[],
            hash=before_oig.hash,
        )
        new_graph = ObjectInstanceGraph(
            id=before_oig.id,
            key=before_oig.key,
            name=before_oig.name,
            description=before_oig.description,
            object_projection_graph_id=before_oig.object_projection_graph_id,
            root_class_instance_id=before_oig.root_class_instance_id,
            root_class_instance=new_root_class_instance,
            class_instances=list(new_instances),
            class_instance_relationships=[],
            hash=before_oig.hash,
        )

    with disable_autobind():
        diffs = diff_object_instance_graph_changes(
            old=old_graph,
            new=new_graph,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            created_at=created_at,
        )
    out = []
    for root in diffs:
        out.extend(root.class_instance_changes)
    return out


def _with_relationship_context_values(
    *,
    source: ModelIntrospection,
    values_by_name: dict[str, object] | None,
) -> ModelIntrospection:
    if not values_by_name:
        return source
    return _RelationshipContextSource(
        source=source, values_by_name=dict(values_by_name)
    )


def _relationship_context_values_by_object_id(
    *,
    change_set: ORMChangeSet,
    index: _OcgIndex,
) -> dict[UUID, dict[str, object]]:
    """Infer missing FK scalar values from relationship fields captured in the change set.

    Runtime-generated ontology models may omit propagation FK fields while ClassConfig
    still requires those attributes as commit truth. The relationship object graph is
    the SSOT in that case: source-owned FKs point at the relationship target, and
    target-owned FKs point back at the relationship source.
    """

    class_config_id_by_object_id: dict[UUID, UUID] = {}
    for obj_id, obj in change_set.objects_by_id.items():
        cc_id = _try_object_class_config_id(obj)
        if cc_id is not None:
            class_config_id_by_object_id[obj_id] = cc_id

    out: dict[UUID, dict[str, object]] = {}
    for rel in index.relationships_by_id.values():
        if rel.id not in index.opg_relationship_ids:
            continue

        reference_attrs = [
            rel_attr
            for rel_attr in rel.class_config_relationship_attributes or []
            if rel_attr.role == ClassConfigRelationshipAttributeRole.reference
            and rel_attr.attribute_config_id is not None
        ]
        foreign_key_attrs = [
            rel_attr
            for rel_attr in rel.class_config_relationship_attributes or []
            if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
            and rel_attr.attribute_config_id is not None
        ]
        if not reference_attrs or not foreign_key_attrs:
            continue

        for ref_attr in reference_attrs:
            ref_attr_id = ref_attr.attribute_config_id
            if ref_attr_id is None:
                continue
            owner_cc_id = index.owner_class_config_by_attribute_id.get(ref_attr_id)
            ref_name = index.attribute_names_by_id.get(ref_attr_id)
            if owner_cc_id is None or not ref_name:
                continue

            for obj_id, obj in change_set.objects_by_id.items():
                if class_config_id_by_object_id.get(obj_id) != owner_cc_id:
                    continue

                related_ids = _read_relationship_reference_ids(obj, ref_name)
                if not related_ids:
                    continue

                for related_id in related_ids:
                    if ref_attr.direction == ClassConfigRelationshipDirection.forward:
                        source_object_id = obj_id
                        target_object_id = related_id
                    else:
                        source_object_id = related_id
                        target_object_id = obj_id

                    _record_foreign_key_context_values(
                        out=out,
                        index=index,
                        relationship=rel,
                        foreign_key_attrs=foreign_key_attrs,
                        source_object_id=source_object_id,
                        target_object_id=target_object_id,
                    )

    return out


def _record_foreign_key_context_values(
    *,
    out: dict[UUID, dict[str, object]],
    index: _OcgIndex,
    relationship: ClassConfigRelationship,
    foreign_key_attrs: list[Any],
    source_object_id: UUID,
    target_object_id: UUID,
) -> None:
    for fk_attr in foreign_key_attrs:
        fk_attr_id = fk_attr.attribute_config_id
        if fk_attr_id is None:
            continue
        owner_cc_id = index.owner_class_config_by_attribute_id.get(fk_attr_id)
        if owner_cc_id is None:
            continue
        fk_name = index.attribute_names_by_id.get(fk_attr_id)
        if not fk_name:
            continue

        if owner_cc_id == relationship.class_config_id:
            out.setdefault(source_object_id, {}).setdefault(fk_name, target_object_id)
        elif owner_cc_id == relationship.target_class_config_id:
            out.setdefault(target_object_id, {}).setdefault(fk_name, source_object_id)


def _try_object_class_config_id(obj: Any) -> UUID | None:
    try:
        class_config_id = getattr(obj, "try_class_config_id")()
    except Exception:
        return None
    return class_config_id if isinstance(class_config_id, UUID) else None


def _read_relationship_reference_ids(obj: Any, field_name: str) -> list[UUID]:
    try:
        declared, value = obj.try_field_value(field_name, include_unset=True)
    except Exception:
        declared = hasattr(obj, field_name)
        value = getattr(obj, field_name, None) if declared else None
    if not declared:
        return []

    if isinstance(value, list):
        return [
            value_id for value_id in snapshot_list(value) if isinstance(value_id, UUID)
        ]

    value_id = stable_ref(value)
    return [value_id] if isinstance(value_id, UUID) else []


def _build_relationship_changes(
    *,
    before_oig: ObjectInstanceGraph,
    change_set: ORMChangeSet,
    index: _OcgIndex,
    created_at: datetime,
) -> list[ClassInstanceRelationshipChange]:
    specs_by_cc_id = index.relationship_field_specs_by_cc_id
    deleted_ids = set(change_set.deleted_ids)
    before_ci_by_source_id = {
        ci.source_object_id: ci
        for ci in before_oig.class_instances
        if ci is not None and ci.id is not None and ci.source_object_id is not None
    }
    before_relationship_keys = {
        (
            rel.class_config_relationship_id,
            rel.source_class_instance_id,
            rel.target_class_instance_id,
        )
        for rel in before_oig.class_instance_relationships
        if rel.class_config_relationship_id in index.opg_relationship_ids
    }

    out: list[ClassInstanceRelationshipChange] = []
    seen: set[tuple[UUID, UUID, UUID]] = set()

    def emit(op: ChangeType, rel_id: UUID, src_id: UUID, tgt_id: UUID) -> None:
        key = (rel_id, src_id, tgt_id)
        if op == ChangeType.create and key in before_relationship_keys:
            return
        if op == ChangeType.delete and key not in before_relationship_keys:
            return
        if key in seen:
            return
        seen.add(key)
        with disable_autobind():
            ch = Change(
                key=f"relationship:{rel_id}:{src_id}:{tgt_id}:{op.value}",
                type=op,
                change_deltas=[],
                created_at=created_at,
            )
            out.append(
                ClassInstanceRelationshipChange(
                    change=ch,
                    change_id=ch.id,
                    class_config_relationship_id=rel_id,
                    source_class_instance_id=src_id,
                    target_class_instance_id=tgt_id,
                )
            )

    def resolve_class_config_id(instance_id: UUID, obj: Any | None) -> UUID | None:
        # Prefer SSOT from pre-state graph.
        before_ci = before_ci_by_source_id.get(instance_id)
        if before_ci is not None:
            return before_ci.class_config_id
        if obj is None:
            return None
        try:
            return getattr(obj, "try_class_config_id")()
        except Exception:
            return None

    def resolve_class_instance_id(
        instance_source_id: UUID, obj: Any | None
    ) -> UUID | None:
        before_ci = before_ci_by_source_id.get(instance_source_id)
        if before_ci is not None and before_ci.id is not None:
            return before_ci.id
        class_config_id = resolve_class_config_id(instance_source_id, obj)
        if class_config_id is None:
            return None
        return stable_class_instance_id(
            object_instance_graph_id=before_oig.id,
            class_config_id=class_config_id,
            source_object_id=instance_source_id,
        )

    # Created instances: emit relationship edges for any populated relationship
    # reference fields (initial constructor state), even when the field wasn't
    # mutated after instantiation.
    for obj_id in sorted(change_set.created_ids, key=str):
        if obj_id in deleted_ids:
            continue
        obj = change_set.objects_by_id.get(obj_id)
        cc_id = resolve_class_config_id(obj_id, obj)
        if cc_id is None or obj is None or cc_id not in index.opg_class_config_ids:
            continue

        for field_name, spec in (specs_by_cc_id.get(cc_id, {}) or {}).items():
            value = getattr(obj, field_name, None)
            if isinstance(value, list):
                for other_id in snapshot_list(value):
                    if not isinstance(other_id, UUID):
                        continue
                    src_ci_id = resolve_class_instance_id(obj_id, obj)
                    tgt_ci_id = resolve_class_instance_id(
                        other_id, change_set.objects_by_id.get(other_id)
                    )
                    if src_ci_id is None or tgt_ci_id is None:
                        continue
                    if spec.direction == ClassConfigRelationshipDirection.forward:
                        emit(
                            ChangeType.create,
                            spec.relationship_id,
                            src_ci_id,
                            tgt_ci_id,
                        )
                    else:
                        emit(
                            ChangeType.create,
                            spec.relationship_id,
                            tgt_ci_id,
                            src_ci_id,
                        )
                continue

            other_id = stable_ref(value)
            if not isinstance(other_id, UUID):
                continue
            src_ci_id = resolve_class_instance_id(obj_id, obj)
            tgt_ci_id = resolve_class_instance_id(
                other_id, change_set.objects_by_id.get(other_id)
            )
            if src_ci_id is None or tgt_ci_id is None:
                continue
            if spec.direction == ClassConfigRelationshipDirection.forward:
                emit(ChangeType.create, spec.relationship_id, src_ci_id, tgt_ci_id)
            else:
                emit(ChangeType.create, spec.relationship_id, tgt_ci_id, src_ci_id)

    # List/collection relationship deltas: prefer incremental membership deltas
    # collected by the ORM (O(Δ)), and fall back to baseline vs current snapshot
    # when deltas are unavailable.
    list_keys = (
        set(change_set.list_baseline.keys())
        | set(change_set.list_added.keys())
        | set(change_set.list_removed.keys())
    )
    for obj_id, field_name in sorted(list_keys, key=lambda k: (str(k[0]), k[1])):
        if obj_id in deleted_ids:
            continue
        before_list = change_set.list_baseline.get((obj_id, field_name), [])
        obj = change_set.objects_by_id.get(obj_id)
        cc_id = resolve_class_config_id(obj_id, obj)
        if cc_id is None or cc_id not in index.opg_class_config_ids:
            continue

        spec = specs_by_cc_id.get(cc_id, {}).get(field_name)
        if spec is None:
            continue

        key = (obj_id, field_name)
        delta_added = change_set.list_added.get(key)
        delta_removed = change_set.list_removed.get(key)

        added: list[UUID]
        removed: list[UUID]
        if delta_added is not None or delta_removed is not None:
            added = sorted(
                {v for v in (delta_added or set()) if isinstance(v, UUID)}, key=str
            )
            removed = sorted(
                {v for v in (delta_removed or set()) if isinstance(v, UUID)}, key=str
            )
        else:
            after_list = (
                snapshot_list(getattr(obj, field_name, None)) if obj is not None else []
            )
            before_ids = {v for v in before_list if isinstance(v, UUID)}
            after_ids = {v for v in after_list if isinstance(v, UUID)}
            added = sorted(after_ids - before_ids, key=str)
            removed = sorted(before_ids - after_ids, key=str)

        for other_id in added:
            src_ci_id = resolve_class_instance_id(obj_id, obj)
            tgt_ci_id = resolve_class_instance_id(
                other_id, change_set.objects_by_id.get(other_id)
            )
            if src_ci_id is None or tgt_ci_id is None:
                continue
            if spec.direction == ClassConfigRelationshipDirection.forward:
                emit(ChangeType.create, spec.relationship_id, src_ci_id, tgt_ci_id)
            else:
                emit(ChangeType.create, spec.relationship_id, tgt_ci_id, src_ci_id)

        for other_id in removed:
            src_ci_id = resolve_class_instance_id(obj_id, obj)
            tgt_ci_id = resolve_class_instance_id(
                other_id, change_set.objects_by_id.get(other_id)
            )
            if src_ci_id is None or tgt_ci_id is None:
                continue
            if spec.direction == ClassConfigRelationshipDirection.forward:
                emit(ChangeType.delete, spec.relationship_id, src_ci_id, tgt_ci_id)
            else:
                emit(ChangeType.delete, spec.relationship_id, tgt_ci_id, src_ci_id)

    # Scalar relationship deltas: SET semantics against collector scalar baseline.
    for (obj_id, field_name), before_value in change_set.scalar_baseline.items():
        if obj_id in deleted_ids:
            continue
        obj = change_set.objects_by_id.get(obj_id)
        cc_id = resolve_class_config_id(obj_id, obj)
        if cc_id is None or cc_id not in index.opg_class_config_ids:
            continue

        spec = specs_by_cc_id.get(cc_id, {}).get(field_name)
        if spec is None:
            continue

        after_value = (
            stable_ref(getattr(obj, field_name, None)) if obj is not None else None
        )

        if before_value == after_value:
            continue

        if isinstance(before_value, UUID):
            src_ci_id = resolve_class_instance_id(obj_id, obj)
            tgt_ci_id = resolve_class_instance_id(
                before_value, change_set.objects_by_id.get(before_value)
            )
            if src_ci_id is not None and tgt_ci_id is not None:
                if spec.direction == ClassConfigRelationshipDirection.forward:
                    emit(ChangeType.delete, spec.relationship_id, src_ci_id, tgt_ci_id)
                else:
                    emit(ChangeType.delete, spec.relationship_id, tgt_ci_id, src_ci_id)

        if isinstance(after_value, UUID):
            src_ci_id = resolve_class_instance_id(obj_id, obj)
            tgt_ci_id = resolve_class_instance_id(
                after_value, change_set.objects_by_id.get(after_value)
            )
            if src_ci_id is not None and tgt_ci_id is not None:
                if spec.direction == ClassConfigRelationshipDirection.forward:
                    emit(ChangeType.create, spec.relationship_id, src_ci_id, tgt_ci_id)
                else:
                    emit(ChangeType.create, spec.relationship_id, tgt_ci_id, src_ci_id)

    # Explicit class-instance deletes must remove all pre-existing OPG relationships
    # touching the deleted endpoint(s). This keeps OIG structural integrity strict
    # without relying on FK nulling side effects.
    if deleted_ids:
        deleted_ci_ids = {
            ci_id
            for deleted_source_id in deleted_ids
            for ci_id in [
                resolve_class_instance_id(
                    deleted_source_id, change_set.objects_by_id.get(deleted_source_id)
                )
            ]
            if ci_id is not None
        }
        for rel in before_oig.class_instance_relationships:
            rel_id = rel.class_config_relationship_id
            if rel_id not in index.opg_relationship_ids:
                continue
            src_id = rel.source_class_instance_id
            tgt_id = rel.target_class_instance_id
            if src_id in deleted_ci_ids or tgt_id in deleted_ci_ids:
                emit(ChangeType.delete, rel_id, src_id, tgt_id)

    return out


__all__ = [
    "OrmChangeTranslationError",
    "build_object_instance_graph_changes_from_orm_change_set",
]
