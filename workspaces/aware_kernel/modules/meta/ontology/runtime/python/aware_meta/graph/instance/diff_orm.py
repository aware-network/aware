"""ORM delta → canonical OIG change graphs (delta-first, v0).

Runtime goal
------------
The production commit pipeline must be **delta-first**:

`OIG(pre) + ORM-collected in-memory changes → ObjectInstanceGraphChange[] → OIG Commit`

OIG(post) is a derived materialization by applying the change graph (and may be
used for validation/debug), but it must not be the SSOT for commits.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast
from uuid import UUID, uuid4

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

from aware_orm.models.introspection import ModelIntrospection
from aware_orm.models.constructor_profile import (
    ORMConstructorProfile,
    capture_orm_constructor_profile,
)
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import (
    ORMChangeSet,
    disable_change_tracking_hooks,
    snapshot_list,
    stable_ref,
)

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
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
    coerce_primitive_attribute_value,
)
from aware_meta.class_.instance.builder import (
    ClassInstanceBuildProfile,
    build_class_instance,
    plan_class_instance_attribute_links,
)
from aware_meta.attribute.instance.value.stable_ids import (
    stable_attribute_value_id,
    stable_attribute_value_link_id,
)
from aware_meta.graph.config.stable_ids import stable_attribute_id
from aware_meta.graph.instance.commit.perf_trace import (
    commit_perf_span,
    current_commit_perf_trace,
)
from aware_meta.graph.instance.commit.body_codec import (
    OigCommitBodyAttributeChangeDraft,
    OigCommitBodyAttributeValueChangeDraft,
    OigCommitBodyAttributeValueLinkChangeDraft,
    OigCommitBodyChangeRefDraft,
    OigCommitBodyDraft,
    OigCommitBodyFieldDeltaDraft,
    OigCommitBodyJsonValue,
)
from aware_meta.graph.instance.diff import (
    ClassInstanceChangeBuildProfile,
    build_class_instance_changes_from_iterables,
    build_class_instance_create_body_draft_from_attributes,
    build_object_instance_graph_create_body_draft,
    build_object_instance_graph_dirty_class_instance_changes,
)


class OrmChangeTranslationError(ValueError):
    pass


def _direct_change_ref(
    *,
    key: str,
    change_type: ChangeType,
    fields: tuple[tuple[str, object], ...],
    created_at: datetime,
) -> OigCommitBodyChangeRefDraft:
    return OigCommitBodyChangeRefDraft(
        id=uuid4(),
        key=key,
        type=change_type,
        created_at=created_at,
        fields=tuple(
            OigCommitBodyFieldDeltaDraft(
                position=position,
                property=property_name,
                kind=ChangeDeltaKind.scalar_set,
                payload=cast(
                    OigCommitBodyJsonValue,
                    {"value": str(value) if isinstance(value, UUID) else value},
                ),
            )
            for position, (property_name, value) in enumerate(fields)
        ),
    )


@dataclass(frozen=True, slots=True)
class OrmChangeTranslationEvidence:
    changes: tuple[ObjectInstanceGraphChange, ...] = ()
    body_draft: OigCommitBodyDraft | None = None

    def __post_init__(self) -> None:
        if self.changes and self.body_draft is not None:
            raise ValueError("ORM change evidence cannot mix changes and body draft")


@dataclass(frozen=True, slots=True)
class OrmChangeTranslationRelationshipProjectionContext:
    relationship_attribute_ids_by_cc_id: Mapping[UUID, set[UUID]]
    include_relationship_attribute_ids_by_cc_id: Mapping[UUID, set[UUID]]
    opg_class_config_ids: frozenset[UUID]


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
    include_relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    opg_class_config_ids: frozenset[UUID]
    opg_relationship_ids: frozenset[UUID]
    relationship_field_specs_by_cc_id: dict[UUID, dict[str, _RelationshipFieldSpec]]


@dataclass(slots=True)
class OrmChangeTranslationIndexCache:
    """Runtime-index-owned cache for static ORM translation context."""

    object_config_graph: ObjectConfigGraph
    class_configs_by_id: Mapping[UUID, ClassConfig]
    relationships_by_id: Mapping[UUID, ClassConfigRelationship]
    _indexes_by_projection_identity: dict[tuple[UUID, str], _OcgIndex] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def get(
        self,
        *,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
    ) -> _OcgIndex | None:
        self._require_owner(ocg=ocg)
        return self._indexes_by_projection_identity.get(
            self._projection_identity(opg=opg)
        )

    def build(
        self,
        *,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
    ) -> _OcgIndex:
        self._require_owner(ocg=ocg)
        projection_identity = self._projection_identity(opg=opg)
        cached = self._indexes_by_projection_identity.get(projection_identity)
        if cached is not None:
            return cached
        built = _build_ocg_index(
            ocg=ocg,
            opg=opg,
            class_configs_by_id=self.class_configs_by_id,
            relationships_by_id=self.relationships_by_id,
        )
        self._indexes_by_projection_identity[projection_identity] = built
        return built

    def relationship_projection_context(
        self,
        *,
        ocg: ObjectConfigGraph,
        opg: ObjectProjectionGraph,
    ) -> OrmChangeTranslationRelationshipProjectionContext | None:
        index = self.get(ocg=ocg, opg=opg)
        if index is None:
            return None
        return OrmChangeTranslationRelationshipProjectionContext(
            relationship_attribute_ids_by_cc_id=(
                index.relationship_attribute_ids_by_cc_id
            ),
            include_relationship_attribute_ids_by_cc_id=(
                index.include_relationship_attribute_ids_by_cc_id
            ),
            opg_class_config_ids=index.opg_class_config_ids,
        )

    def _require_owner(self, *, ocg: ObjectConfigGraph) -> None:
        if ocg is self.object_config_graph:
            return
        raise OrmChangeTranslationError(
            "ORM translation index cache belongs to a different ObjectConfigGraph: "
            f"expected_id={self.object_config_graph.id} actual_id={ocg.id}"
        )

    @staticmethod
    def _projection_identity(*, opg: ObjectProjectionGraph) -> tuple[UUID, str]:
        if not opg.projection_hash:
            raise OrmChangeTranslationError(
                "ORM translation index cache requires ObjectProjectionGraph "
                f"projection_hash: object_projection_graph_id={opg.id}"
            )
        return (opg.id, opg.projection_hash)


@dataclass(frozen=True)
class _ClassInstanceCandidateSelection:
    input_ids: frozenset[UUID]
    selected_ids: frozenset[UUID]
    pruned_relationship_only_ids: frozenset[UUID]
    ignored_out_of_projection_ids: frozenset[UUID]


@dataclass
class _RelationshipContextSource:
    source: ModelIntrospection
    values_by_name: dict[str, object]
    id: UUID = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", self.source.id)

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


def build_object_instance_graph_changes_from_orm_change_set(
    *,
    before_oig: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    change_set: ORMChangeSet,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    relationships_by_id: Mapping[UUID, ClassConfigRelationship] | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
    index_cache: OrmChangeTranslationIndexCache | None = None,
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
    with disable_autobind(), disable_change_tracking_hooks():
        evidence = _build_object_instance_graph_changes_from_orm_change_set(
            before_oig=before_oig,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            ocg=ocg,
            opg=opg,
            change_set=change_set,
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=relationships_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union_selections=union_selections,
            index_cache=index_cache,
            record_native_creates=False,
        )
        return list(evidence.changes)


def build_object_instance_graph_evidence_from_orm_change_set(
    *,
    before_oig: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    change_set: ORMChangeSet,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    relationships_by_id: Mapping[UUID, ClassConfigRelationship] | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
    index_cache: OrmChangeTranslationIndexCache | None = None,
) -> OrmChangeTranslationEvidence:
    with disable_autobind(), disable_change_tracking_hooks():
        return _build_object_instance_graph_changes_from_orm_change_set(
            before_oig=before_oig,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            ocg=ocg,
            opg=opg,
            change_set=change_set,
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=relationships_by_id,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union_selections=union_selections,
            index_cache=index_cache,
            record_native_creates=True,
        )


def _build_object_instance_graph_changes_from_orm_change_set(
    *,
    before_oig: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    change_set: ORMChangeSet,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    relationships_by_id: Mapping[UUID, ClassConfigRelationship] | None = None,
    enum_option_resolver: EnumOptionResolver | None = None,
    class_instance_resolver: ClassInstanceResolver | None = None,
    union_selections: dict[str, UnionSelection] | None = None,
    index_cache: OrmChangeTranslationIndexCache | None = None,
    record_native_creates: bool,
) -> OrmChangeTranslationEvidence:
    if before_oig.id is None:
        raise OrmChangeTranslationError("before_oig.id is required")

    created_at = change_set.collected_at

    trace_metadata = _orm_change_translation_trace_metadata(
        before_oig=before_oig,
        opg=opg,
        change_set=change_set,
    )
    with commit_perf_span(
        phase="handler_execution.orm_change_translation.build_ocg_index",
        category="meta.runtime.handler_execution",
        metadata=trace_metadata,
    ):
        cached_index = (
            None if index_cache is None else index_cache.get(ocg=ocg, opg=opg)
        )
        if cached_index is not None:
            with commit_perf_span(
                phase=(
                    "handler_execution.orm_change_translation."
                    "build_ocg_index.cache_reuse"
                ),
                category="meta.runtime.handler_execution",
                metadata=trace_metadata,
            ):
                index = cached_index
        elif index_cache is not None:
            with commit_perf_span(
                phase=(
                    "handler_execution.orm_change_translation."
                    "build_ocg_index.cache_build"
                ),
                category="meta.runtime.handler_execution",
                metadata=trace_metadata,
            ):
                index = index_cache.build(ocg=ocg, opg=opg)
        else:
            index = _build_ocg_index(
                ocg=ocg,
                opg=opg,
                class_configs_by_id=class_configs_by_id,
                relationships_by_id=relationships_by_id,
            )

    # ---- ClassInstance changes (attributes/value trees) ------------------- #
    with commit_perf_span(
        phase="handler_execution.orm_change_translation.build_class_instance_changes",
        category="meta.runtime.handler_execution",
        metadata=trace_metadata,
    ):
        created_class_instances: list[Any] | None = (
            [] if record_native_creates else None
        )
        created_class_instance_drafts: list[Any] | None = (
            [] if record_native_creates else None
        )
        class_instance_changes = _build_class_instance_changes(
            before_oig=before_oig,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            change_set=change_set,
            index=index,
            created_at=created_at,
            enum_option_resolver=enum_option_resolver,
            class_instance_resolver=class_instance_resolver,
            union_selections=union_selections,
            created_class_instance_sink=created_class_instances,
            created_class_instance_draft_sink=created_class_instance_drafts,
        )

    # ---- Relationship changes (structural edges) -------------------------- #
    with commit_perf_span(
        phase="handler_execution.orm_change_translation.build_relationship_changes",
        category="meta.runtime.handler_execution",
        metadata=trace_metadata,
    ):
        relationship_changes = _build_relationship_changes(
            before_oig=before_oig,
            change_set=change_set,
            index=index,
            created_at=created_at,
        )

    detached_metadata: dict[str, object] = {
        **trace_metadata,
        "relationship_change_count": len(relationship_changes),
    }
    with commit_perf_span(
        phase=(
            "handler_execution.orm_change_translation."
            "build_detached_class_instance_changes"
        ),
        category="meta.runtime.handler_execution",
        metadata=detached_metadata,
    ):
        detached_projection_changes = _build_detached_class_instance_delete_changes(
            before_oig=before_oig,
            object_instance_graph_identity_id=(object_instance_graph_identity_id),
            opg=opg,
            relationship_changes=relationship_changes,
            created_at=created_at,
        )
        detached_class_instance_changes: list[ClassInstanceChange] = [
            class_instance_change
            for root_change in detached_projection_changes
            for class_instance_change in root_change.class_instance_changes
        ]
        detached_relationship_changes = [
            relationship_change
            for root_change in detached_projection_changes
            for relationship_change in root_change.class_instance_relationship_changes
        ]
        detached_metadata["detached_class_instance_count"] = len(
            detached_class_instance_changes
        )
        detached_metadata["detached_relationship_count"] = len(
            detached_relationship_changes
        )
    if detached_class_instance_changes:
        detached_class_instance_ids = {
            change.class_instance_id for change in detached_class_instance_changes
        }
        class_instance_changes = [
            change
            for change in class_instance_changes
            if change.class_instance_id not in detached_class_instance_ids
        ]
        class_instance_changes.extend(detached_class_instance_changes)
        _record_detached_class_instance_delete_count(
            class_instance_ids=detached_class_instance_ids,
        )
    if detached_relationship_changes:
        existing_relationship_change_signatures = {
            _relationship_change_signature(change) for change in relationship_changes
        }
        additional_detached_relationship_changes = [
            change
            for change in detached_relationship_changes
            if _relationship_change_signature(change)
            not in existing_relationship_change_signatures
        ]
        relationship_changes.extend(additional_detached_relationship_changes)
        _record_detached_relationship_delete_count(
            relationship_changes=additional_detached_relationship_changes,
        )

    if (
        not class_instance_changes
        and not relationship_changes
        and not created_class_instances
        and not created_class_instance_drafts
    ):
        return OrmChangeTranslationEvidence()

    if created_class_instances or created_class_instance_drafts:
        with commit_perf_span(
            phase=(
                "handler_execution.orm_change_translation."
                "assemble_record_native_create_evidence"
            ),
            category="meta.runtime.handler_execution",
            metadata={
                **trace_metadata,
                "created_class_instance_count": len(created_class_instances or ()),
                "direct_created_class_instance_count": len(
                    created_class_instance_drafts or ()
                ),
                "semantic_class_instance_change_count": len(class_instance_changes),
                "relationship_change_count": len(relationship_changes),
            },
        ):
            body_draft = build_object_instance_graph_create_body_draft(
                class_instances=created_class_instances or (),
                class_instance_create_drafts=(created_class_instance_drafts or ()),
                class_instance_changes=class_instance_changes,
                relationship_changes=relationship_changes,
                created_at=created_at,
            )
        return OrmChangeTranslationEvidence(body_draft=body_draft)

    with commit_perf_span(
        phase="handler_execution.orm_change_translation.assemble_root_changes",
        category="meta.runtime.handler_execution",
        metadata={
            **trace_metadata,
            "class_instance_change_count": len(class_instance_changes),
            "relationship_change_count": len(relationship_changes),
        },
    ):
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
                        object_instance_graph_identity_id=(
                            object_instance_graph_identity_id
                        ),
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
                        object_instance_graph_identity_id=(
                            object_instance_graph_identity_id
                        ),
                        object_instance_graph_id=before_oig.id,
                        type=ObjectInstanceGraphChangeType.object_instance_relationship,
                        change=root_change,
                        change_id=root_change.id,
                        class_instance_changes=[],
                        class_instance_relationship_changes=relationship_changes,
                    )
                )
    return OrmChangeTranslationEvidence(changes=tuple(out))


def _orm_change_translation_trace_metadata(
    *,
    before_oig: ObjectInstanceGraph,
    opg: ObjectProjectionGraph,
    change_set: ORMChangeSet,
) -> dict[str, object]:
    return {
        "object_instance_graph_id": before_oig.id,
        "projection_hash": opg.projection_hash,
        "created_count": len(change_set.created_ids),
        "touched_count": len(change_set.touched_ids),
        "deleted_count": len(change_set.deleted_ids),
        "scalar_field_object_count": len(change_set.scalar_fields_by_id),
        "list_field_object_count": len(change_set.list_fields_by_id),
        "list_added_count": sum(
            len(values) for values in change_set.list_added.values()
        ),
        "list_removed_count": sum(
            len(values) for values in change_set.list_removed.values()
        ),
    }


def _build_ocg_index(
    *,
    ocg: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None = None,
    relationships_by_id: Mapping[UUID, ClassConfigRelationship] | None = None,
) -> _OcgIndex:
    opg_class_config_ids = frozenset(
        node.class_config_id for node in opg.object_projection_graph_nodes
    )
    opg_relationship_ids = frozenset(
        edge.class_config_relationship_id for edge in opg.object_projection_graph_edges
    )
    portal_relationship_ids = frozenset(
        portal.class_config_relationship_id
        for portal in opg.object_projection_graph_relationships
    )
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

    attribute_names_by_id: dict[UUID, str] = {}

    if class_configs_by_id is None or relationships_by_id is None:
        resolved_class_configs_by_id: dict[UUID, ClassConfig] = {}
        resolved_relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
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
        resolved_class_configs_by_id = (
            class_configs_by_id
            if isinstance(class_configs_by_id, dict)
            else dict(class_configs_by_id)
        )
        resolved_relationships_by_id = (
            relationships_by_id
            if isinstance(relationships_by_id, dict)
            else dict(relationships_by_id)
        )

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

    projection_relationships_by_id = {
        relationship_id: relationship
        for relationship_id, relationship in resolved_relationships_by_id.items()
        if relationship_id in opg_relationship_ids
        or relationship_id in portal_relationship_ids
        or relationship.class_config_id in opg_class_config_ids
        or relationship.target_class_config_id in opg_class_config_ids
    }
    for portal in opg.object_projection_graph_relationships:
        relationship = portal.class_config_relationship
        if relationship is not None:
            projection_relationships_by_id.setdefault(relationship.id, relationship)

    metadata_class_config_ids = set(opg_class_config_ids)
    for relationship in projection_relationships_by_id.values():
        metadata_class_config_ids.add(relationship.class_config_id)
        metadata_class_config_ids.add(relationship.target_class_config_id)
    metadata_class_configs_by_id = {
        class_config_id: resolved_class_configs_by_id[class_config_id]
        for class_config_id in metadata_class_config_ids
        if class_config_id in resolved_class_configs_by_id
    }

    owner_cc_by_attr_id: dict[UUID, UUID] = {}
    for cc_id, cc in metadata_class_configs_by_id.items():
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
        cc_id: set() for cc_id in opg_class_config_ids
    }
    for rel in projection_relationships_by_id.values():
        for rel_attr in rel.class_config_relationship_attributes:
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            owner_cc_id = owner_cc_by_attr_id.get(attr_id)
            if owner_cc_id is None:
                continue
            relationship_attr_ids_by_cc.setdefault(owner_cc_id, set()).add(attr_id)

    portal_include_by_cc: dict[UUID, set[UUID]] = {}
    portals = opg.object_projection_graph_relationships
    for portal in portals:
        rel = (
            projection_relationships_by_id.get(portal.class_config_relationship_id)
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
    for rel in projection_relationships_by_id.values():
        if rel.id is None:
            continue
        # Relationship analysis may retain detached cross-graph relationships
        # whose endpoints are not present in this OCG dependency closure.
        # Those are irrelevant for this projection's soft-ref retention.
        if (
            rel.class_config_id not in opg_class_config_ids
            and rel.target_class_config_id not in opg_class_config_ids
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

    for rel in projection_relationships_by_id.values():
        # Relationship analysis may retain detached cross-graph relationships
        # whose endpoints are not present in this OCG dependency closure.
        # Those are irrelevant for this projection's required-FK retention.
        if (
            rel.class_config_id not in opg_class_config_ids
            and rel.target_class_config_id not in opg_class_config_ids
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

    include_relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]] = {}
    for source in (
        portal_include_by_cc,
        soft_ref_include_by_cc,
        required_fk_include_by_cc,
    ):
        for class_config_id, attribute_config_ids in source.items():
            include_relationship_attribute_ids_by_cc_id.setdefault(
                class_config_id, set()
            ).update(attribute_config_ids)

    relationship_field_specs_by_cc_id: dict[UUID, dict[str, _RelationshipFieldSpec]] = (
        {}
    )
    for rel in projection_relationships_by_id.values():
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
    for rel in projection_relationships_by_id.values():
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
        relationships_by_id=projection_relationships_by_id,
        attribute_names_by_id=attribute_names_by_id,
        owner_class_config_by_attribute_id=owner_cc_by_attr_id,
        relationship_attribute_ids_by_cc_id=relationship_attr_ids_by_cc,
        portal_include_relationship_attribute_ids_by_cc_id=portal_include_by_cc,
        soft_ref_include_relationship_attribute_ids_by_cc_id=soft_ref_include_by_cc,
        required_fk_include_relationship_attribute_ids_by_cc_id=required_fk_include_by_cc,
        include_relationship_attribute_ids_by_cc_id=(
            include_relationship_attribute_ids_by_cc_id
        ),
        opg_class_config_ids=opg_class_config_ids,
        opg_relationship_ids=opg_relationship_ids,
        relationship_field_specs_by_cc_id=relationship_field_specs_by_cc_id,
    )
    if cache_key is not None:
        _OCG_INDEX_CACHE[cache_key] = out
    return out


def _descriptor_is_null(descriptor: AttributeTypeDescriptor) -> bool:
    if (
        descriptor.kind != AttributeTypeDescriptorKind.primitive
        or descriptor.primitive_config is None
    ):
        return False
    primitive_type = CodePrimitiveType.model_validate(
        descriptor.primitive_config.primitive_type
    )
    return primitive_type.base_type == CodePrimitiveBaseType.null


def _try_direct_value_create_draft(
    *,
    descriptor: AttributeTypeDescriptor,
    value: object,
    value_id: UUID,
    created_at: datetime,
    enum_option_resolver: EnumOptionResolver | None,
    union: UnionSelection | None = None,
) -> OigCommitBodyAttributeValueChangeDraft | None:
    fields: tuple[tuple[str, object], ...]
    links: tuple[OigCommitBodyAttributeValueLinkChangeDraft, ...] = ()
    if descriptor.id is None:
        return None
    if descriptor.kind == AttributeTypeDescriptorKind.primitive:
        if descriptor.child_links:
            return None
        primitive_value = coerce_primitive_attribute_value(
            value,
            type_descriptor=descriptor,
        )
        fields = (
            () if primitive_value is None else (("primitive_value", primitive_value),)
        )
    elif descriptor.kind == AttributeTypeDescriptorKind.enum:
        if descriptor.child_links:
            return None
        if isinstance(value, UUID):
            enum_option_id = value
        elif isinstance(value, EnumOption):
            enum_option_id = value.id
        elif enum_option_resolver is not None:
            try:
                enum_option_id = enum_option_resolver(descriptor, value)
            except Exception:
                return None
        else:
            return None
        if not isinstance(enum_option_id, UUID):
            return None
        fields = (("enum_option_id", enum_option_id),)
    elif descriptor.kind == AttributeTypeDescriptorKind.union:
        members = {
            link.position: link.child
            for link in descriptor.child_links
            if link.role == AttributeTypeDescriptorRole.member
            and link.position is not None
            and link.child is not None
        }
        if len(members) != len(descriptor.child_links):
            return None
        if union is not None:
            selected_position = union.position
            selected_value = union.value
        elif value is None:
            null_positions = [
                position
                for position, member in members.items()
                if _descriptor_is_null(member)
            ]
            if len(null_positions) != 1:
                return None
            selected_position = null_positions[0]
            selected_value = None
        else:
            non_null_positions = [
                position
                for position, member in members.items()
                if not _descriptor_is_null(member)
            ]
            if len(non_null_positions) != 1:
                return None
            selected_position = non_null_positions[0]
            selected_value = value
        selected_descriptor = members.get(selected_position)
        if selected_descriptor is None:
            return None
        role = AttributeTypeDescriptorRole.member.value
        child_value_id = stable_attribute_value_id(
            parent_value_id=value_id,
            role=role,
            position=selected_position,
            identity_key=None,
        )
        child_draft = _try_direct_value_create_draft(
            descriptor=selected_descriptor,
            value=selected_value,
            value_id=child_value_id,
            created_at=created_at,
            enum_option_resolver=enum_option_resolver,
        )
        if child_draft is None:
            return None
        link_id = stable_attribute_value_link_id(
            parent_value_id=value_id,
            role=role,
            position=selected_position,
            identity_key=None,
        )
        links = (
            OigCommitBodyAttributeValueLinkChangeDraft(
                id=uuid4(),
                attribute_value_link_id=link_id,
                change=_direct_change_ref(
                    key=(
                        f"attribute_value_link:{role}:" f"{selected_position}::create"
                    ),
                    change_type=ChangeType.create,
                    fields=(("role", role), ("position", selected_position)),
                    created_at=created_at,
                ),
                child_attribute_value_change=child_draft,
            ),
        )
        fields = ()
    else:
        return None
    return OigCommitBodyAttributeValueChangeDraft(
        id=uuid4(),
        attribute_value_id=value_id,
        change=_direct_change_ref(
            key="attribute_value:value:create",
            change_type=ChangeType.create,
            fields=fields,
            created_at=created_at,
        ),
        attribute_value_link_changes=links,
    )


def _try_direct_class_instance_create_draft(
    *,
    object_instance_graph_id: UUID,
    class_config: ClassConfig,
    source: ModelIntrospection,
    relationship_attribute_config_ids: set[UUID] | None,
    include_relationship_attribute_config_ids: set[UUID] | None,
    enum_option_resolver: EnumOptionResolver | None,
    union_selections: dict[str, UnionSelection] | None,
    created_at: datetime,
) -> Any | None:
    if class_config.id is None:
        return None
    plan = plan_class_instance_attribute_links(
        class_config=class_config,
        relationship_attribute_config_ids=relationship_attribute_config_ids,
        include_relationship_attribute_config_ids=(
            include_relationship_attribute_config_ids
        ),
    )
    class_instance_id = stable_class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=source.id,
    )
    attribute_drafts: list[tuple[UUID, OigCommitBodyAttributeChangeDraft]] = []
    for link in plan.attribute_links:
        attribute_config: AttributeConfig | None = getattr(
            link, "attribute_config", None
        )
        if attribute_config is None or attribute_config.is_virtual:
            continue
        if attribute_config.id in plan.relationship_attribute_config_ids:
            continue
        found, raw_value = source.try_attribute_value(attribute_config)
        if not found:
            if attribute_config.default_value is not None:
                return None
            if (
                attribute_config.is_required
                or attribute_config.id in plan.required_fk_attribute_config_ids
            ):
                return None
            continue
        if attribute_config.id is None or attribute_config.type_descriptor is None:
            return None
        attribute_id = stable_attribute_id(
            owner_key=source.id,
            attribute_config_id=attribute_config.id,
        )
        value_root_id = stable_attribute_value_id(
            parent_value_id=attribute_id,
            role="member",
            position=0,
            identity_key="root",
        )
        value_draft = _try_direct_value_create_draft(
            descriptor=attribute_config.type_descriptor,
            value=raw_value,
            value_id=value_root_id,
            created_at=created_at,
            enum_option_resolver=enum_option_resolver,
            union=(
                union_selections.get(attribute_config.name)
                if union_selections
                else None
            ),
        )
        if value_draft is None:
            return None
        attribute_drafts.append(
            (
                attribute_config.id,
                OigCommitBodyAttributeChangeDraft(
                    id=uuid4(),
                    attribute_id=attribute_id,
                    change=_direct_change_ref(
                        key=f"attribute:attr:{attribute_config.id}:create",
                        change_type=ChangeType.create,
                        fields=(("attribute_config_id", attribute_config.id),),
                        created_at=created_at,
                    ),
                    value_root_change=value_draft,
                ),
            )
        )
    return build_class_instance_create_body_draft_from_attributes(
        class_instance_id=class_instance_id,
        class_config_id=class_config.id,
        source_object_id=source.id,
        attribute_changes=(
            draft
            for _, draft in sorted(attribute_drafts, key=lambda item: str(item[0]))
        ),
        created_at=created_at,
    )


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
    created_class_instance_sink: list[Any] | None = None,
    created_class_instance_draft_sink: list[Any] | None = None,
) -> list[Any]:
    selection_metadata: dict[str, object] = {
        "created_count": len(change_set.created_ids),
        "touched_count": len(change_set.touched_ids),
        "deleted_count": len(change_set.deleted_ids),
    }
    with commit_perf_span(
        phase=(
            "handler_execution.orm_change_translation."
            "class_instance_changes.classify_candidates"
        ),
        category="meta.runtime.handler_execution",
        metadata=selection_metadata,
    ):
        before_by_source_id = {
            ci.source_object_id: ci
            for ci in before_oig.class_instances
            if ci is not None and ci.id is not None and ci.source_object_id is not None
        }
        selection = _select_class_instance_change_candidates(
            change_set=change_set,
            index=index,
            before_by_source_id=before_by_source_id,
        )
        selection_metadata.update(
            {
                "input_count": len(selection.input_ids),
                "selected_count": len(selection.selected_ids),
                "pruned_relationship_only_count": len(
                    selection.pruned_relationship_only_ids
                ),
                "ignored_out_of_projection_count": len(
                    selection.ignored_out_of_projection_ids
                ),
            }
        )
    _record_class_instance_candidate_counts(selection=selection)
    candidate_ids = selection.selected_ids
    if not candidate_ids:
        return []
    profile_enabled = current_commit_perf_trace() is not None
    class_instance_build_profile = (
        ClassInstanceBuildProfile() if profile_enabled else None
    )
    class_instance_build_metadata: dict[str, object] = {
        "selected_count": len(candidate_ids),
    }

    with commit_perf_span(
        phase=(
            "handler_execution.orm_change_translation."
            "class_instance_changes.build_relationship_context"
        ),
        category="meta.runtime.handler_execution",
        metadata={"selected_count": len(candidate_ids)},
    ):
        relationship_context_values_by_id = _relationship_context_values_by_object_id(
            change_set=change_set,
            index=index,
        )

    with commit_perf_span(
        phase=(
            "handler_execution.orm_change_translation."
            "class_instance_changes.build_class_instances"
        ),
        category="meta.runtime.handler_execution",
        metadata=class_instance_build_metadata,
    ):
        old_instances = [
            before_by_source_id[cid]
            for cid in sorted(candidate_ids, key=str)
            if cid in before_by_source_id
        ]
        new_instances = []
        for cid in sorted(candidate_ids, key=str):
            obj = change_set.objects_by_id.get(cid)
            if obj is None:
                continue

            class_config_id = _change_object_class_config_id(
                source_object_id=cid,
                obj=obj,
                before_by_source_id=before_by_source_id,
            )
            if class_config_id is None:
                continue
            if class_config_id not in index.opg_class_config_ids:
                continue

            class_config = index.class_configs_by_id.get(class_config_id)
            if class_config is None:
                raise OrmChangeTranslationError(
                    f"ClassConfig not found: {class_config_id} (instance_id={cid})"
                )

            rel_attr_ids = index.relationship_attribute_ids_by_cc_id.get(
                class_config_id
            )
            include_attr_ids = _retained_relationship_attribute_ids(
                index=index,
                class_config_id=class_config_id,
            )
            source = _with_relationship_context_values(
                source=obj,
                values_by_name=relationship_context_values_by_id.get(cid),
            )
            if (
                cid not in before_by_source_id
                and created_class_instance_draft_sink is not None
            ):
                _record_direct_create_result(result="attempt", source_object_id=cid)
                direct_draft = _try_direct_class_instance_create_draft(
                    object_instance_graph_id=before_oig.id,
                    class_config=class_config,
                    source=source,
                    relationship_attribute_config_ids=rel_attr_ids,
                    include_relationship_attribute_config_ids=(
                        include_attr_ids or None
                    ),
                    enum_option_resolver=enum_option_resolver,
                    union_selections=union_selections,
                    created_at=created_at,
                )
                if direct_draft is not None:
                    created_class_instance_draft_sink.append(direct_draft)
                    _record_direct_create_result(
                        result="admitted", source_object_id=cid
                    )
                    continue
                _record_direct_create_result(result="fallback", source_object_id=cid)
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
                    include_relationship_attribute_config_ids=(
                        include_attr_ids or None
                    ),
                    build_profile=class_instance_build_profile,
                )
            )
    _record_class_instance_build_profile(profile=class_instance_build_profile)

    if created_class_instance_sink is not None:
        old_instance_ids = {item.id for item in old_instances}
        created_instances = [
            item for item in new_instances if item.id not in old_instance_ids
        ]
        created_class_instance_sink.extend(created_instances)
        if created_instances:
            created_ids = {item.id for item in created_instances}
            new_instances = [
                item for item in new_instances if item.id not in created_ids
            ]

    if not old_instances and not new_instances:
        return []

    change_build_profile = (
        ClassInstanceChangeBuildProfile() if profile_enabled else None
    )
    constructor_profile_context = (
        capture_orm_constructor_profile(model_names=("Change", "ChangeDelta"))
        if profile_enabled
        else nullcontext(None)
    )
    with commit_perf_span(
        phase=(
            "handler_execution.orm_change_translation."
            "class_instance_changes.emit_changes"
        ),
        category="meta.runtime.handler_execution",
        metadata={
            "old_class_instance_count": len(old_instances),
            "new_class_instance_count": len(new_instances),
        },
    ):
        with disable_autobind(), constructor_profile_context as constructor_profile:
            changes = build_class_instance_changes_from_iterables(
                graph=before_oig,
                old_class_instances=old_instances,
                new_class_instances=new_instances,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                created_at=created_at,
                build_profile=change_build_profile,
            )
    _record_class_instance_change_build_profile(
        profile=change_build_profile,
        constructor_profile=constructor_profile,
    )
    return changes


def _record_class_instance_build_profile(
    *,
    profile: ClassInstanceBuildProfile | None,
) -> None:
    recorder = current_commit_perf_trace()
    if recorder is None or profile is None:
        return
    prefix = (
        "handler_execution.orm_change_translation."
        "class_instance_changes.build_profile"
    )
    durations_s = {
        "construct_shell": profile.construct_shell_s,
        "plan_attributes": profile.plan_attributes_s,
        "materialize_attributes": profile.materialize_attributes_s,
        "source_attribute_values": profile.source_attribute_values_s,
        "build_attributes": profile.build_attributes_s,
        "link_attributes": profile.link_attributes_s,
    }
    metadata = {
        "attribute_link_input_count": profile.attr_links_total,
        "source_attribute_lookup_count": profile.source_attribute_lookups,
        "attribute_built_count": profile.attributes_built,
        "virtual_attribute_skipped_count": profile.virtual_attributes_skipped,
        "relationship_attribute_skipped_count": (
            profile.relationship_attributes_skipped
        ),
        "optional_attribute_omitted_count": profile.optional_attributes_omitted,
        "default_value_used_count": profile.default_values_used,
    }
    for name, duration_s in durations_s.items():
        recorder.record(
            phase=f"{prefix}.{name}",
            duration_ms=duration_s * 1000.0,
            category="meta.runtime.handler_execution",
            metadata=metadata,
        )
    _record_profile_count(
        phase=f"{prefix}.attribute_link_input",
        count=profile.attr_links_total,
    )
    _record_profile_count(
        phase=f"{prefix}.source_attribute_lookup",
        count=profile.source_attribute_lookups,
    )
    _record_profile_count(
        phase=f"{prefix}.attribute_built",
        count=profile.attributes_built,
    )


def _record_class_instance_change_build_profile(
    *,
    profile: ClassInstanceChangeBuildProfile | None,
    constructor_profile: ORMConstructorProfile | None,
) -> None:
    recorder = current_commit_perf_trace()
    if recorder is None or profile is None:
        return
    prefix = (
        "handler_execution.orm_change_translation."
        "class_instance_changes.emission_profile"
    )
    durations_s = {
        "index_inputs": profile.index_inputs_s,
        "classify_candidates": profile.classify_candidates_s,
        "create_changes": profile.create_changes_s,
        "update_attribute_membership": (profile.update_attribute_membership_s),
        "update_graph_diff": profile.update_graph_diff_s,
        "delete_changes": profile.delete_changes_s,
        "create_field_plan": profile.create_field_plan_s,
        "create_change_shell": profile.create_change_shell_s,
        "create_change_deltas": profile.create_change_deltas_s,
        "create_change_delta_payload_value": (
            profile.create_change_delta_payload_value_s
        ),
        "create_change_delta_json_wrapper": (
            profile.create_change_delta_json_wrapper_s
        ),
        "create_change_delta_model": profile.create_change_delta_model_s,
        "create_class_instance_wrapper": profile.create_class_instance_wrapper_s,
        "create_attribute_index": profile.create_attribute_index_s,
        "create_attribute_sort": profile.create_attribute_sort_s,
        "create_attribute_wrapper": profile.create_attribute_wrapper_s,
        "create_attribute_value_wrapper": (profile.create_attribute_value_wrapper_s),
        "create_attribute_value_link_sort": (
            profile.create_attribute_value_link_sort_s
        ),
        "create_attribute_value_link_wrapper": (
            profile.create_attribute_value_link_wrapper_s
        ),
    }
    metadata = {
        "old_class_instance_count": profile.old_class_instance_count,
        "new_class_instance_count": profile.new_class_instance_count,
        "candidate_count": profile.candidate_count,
        "create_candidate_count": profile.create_candidate_count,
        "update_candidate_count": profile.update_candidate_count,
        "delete_candidate_count": profile.delete_candidate_count,
        "update_attribute_membership_count": (
            profile.update_attribute_membership_count
        ),
        "update_graph_diff_count": profile.update_graph_diff_count,
        "emitted_change_count": profile.emitted_change_count,
        "create_change_shell_count": profile.create_change_shell_count,
        "create_change_delta_count": profile.create_change_delta_count,
        "create_change_delta_payload_value_count": (
            profile.create_change_delta_payload_value_count
        ),
        "create_change_delta_json_wrapper_count": (
            profile.create_change_delta_json_wrapper_count
        ),
        "create_change_delta_model_count": (profile.create_change_delta_model_count),
        "create_class_instance_wrapper_count": (
            profile.create_class_instance_wrapper_count
        ),
        "create_attribute_input_count": profile.create_attribute_input_count,
        "create_attribute_unique_count": profile.create_attribute_unique_count,
        "create_attribute_wrapper_count": profile.create_attribute_wrapper_count,
        "create_attribute_value_wrapper_count": (
            profile.create_attribute_value_wrapper_count
        ),
        "create_attribute_value_link_wrapper_count": (
            profile.create_attribute_value_link_wrapper_count
        ),
    }
    if constructor_profile is not None:
        for metric_prefix, model_name in (
            ("orm_change", "Change"),
            ("orm_change_delta", "ChangeDelta"),
        ):
            model_profile = constructor_profile.models.get(model_name)
            if model_profile is None:
                continue
            model_validation_residual_s = max(
                0.0,
                model_profile.model_validation_s
                - model_profile.relationship_pre_validator_s,
            )
            relationship_pre_validator_residual_s = max(
                0.0,
                model_profile.relationship_pre_validator_s
                - model_profile.relationship_hook_guard_s
                - model_profile.relationship_processing_s,
            )
            relationship_hook_guard_residual_s = max(
                0.0,
                model_profile.relationship_hook_guard_s - model_profile.uuid_default_s,
            )
            durations_s.update(
                {
                    f"{metric_prefix}_model_validation": (
                        model_profile.model_validation_s
                    ),
                    f"{metric_prefix}_model_validation_residual": (
                        model_validation_residual_s
                    ),
                    f"{metric_prefix}_relationship_pre_validator": (
                        model_profile.relationship_pre_validator_s
                    ),
                    f"{metric_prefix}_relationship_pre_validator_residual": (
                        relationship_pre_validator_residual_s
                    ),
                    f"{metric_prefix}_relationship_hook_guard": (
                        model_profile.relationship_hook_guard_s
                    ),
                    f"{metric_prefix}_relationship_hook_guard_residual": (
                        relationship_hook_guard_residual_s
                    ),
                    f"{metric_prefix}_uuid_default": (model_profile.uuid_default_s),
                    f"{metric_prefix}_relationship_processing": (
                        model_profile.relationship_processing_s
                    ),
                    f"{metric_prefix}_post_init_hook_guard": (
                        model_profile.post_init_hook_guard_s
                    ),
                }
            )
            metadata.update(
                {
                    f"{metric_prefix}_model_validation_count": (
                        model_profile.model_validation_count
                    ),
                    f"{metric_prefix}_relationship_pre_validator_count": (
                        model_profile.relationship_pre_validator_count
                    ),
                    f"{metric_prefix}_relationship_hook_guard_count": (
                        model_profile.relationship_hook_guard_count
                    ),
                    f"{metric_prefix}_uuid_default_count": (
                        model_profile.uuid_default_count
                    ),
                    f"{metric_prefix}_relationship_processing_count": (
                        model_profile.relationship_processing_count
                    ),
                    f"{metric_prefix}_post_init_hook_guard_count": (
                        model_profile.post_init_hook_guard_count
                    ),
                }
            )
    for name, duration_s in durations_s.items():
        recorder.record(
            phase=f"{prefix}.{name}",
            duration_ms=duration_s * 1000.0,
            category="meta.runtime.handler_execution",
            metadata=metadata,
        )
    for name, count in (
        ("candidate_input", profile.candidate_count),
        ("create_candidate", profile.create_candidate_count),
        ("update_candidate", profile.update_candidate_count),
        ("delete_candidate", profile.delete_candidate_count),
        (
            "update_attribute_membership_path",
            profile.update_attribute_membership_count,
        ),
        ("update_graph_diff_path", profile.update_graph_diff_count),
        ("change_emitted", profile.emitted_change_count),
        ("create_change_object", profile.create_change_shell_count),
        ("create_change_delta", profile.create_change_delta_count),
        (
            "create_change_delta_payload_value",
            profile.create_change_delta_payload_value_count,
        ),
        (
            "create_change_delta_json_wrapper",
            profile.create_change_delta_json_wrapper_count,
        ),
        (
            "create_change_delta_model",
            profile.create_change_delta_model_count,
        ),
        (
            "create_class_instance_wrapper_object",
            profile.create_class_instance_wrapper_count,
        ),
        ("create_attribute_input", profile.create_attribute_input_count),
        ("create_attribute_unique", profile.create_attribute_unique_count),
        (
            "create_attribute_wrapper_object",
            profile.create_attribute_wrapper_count,
        ),
        (
            "create_attribute_value_wrapper_object",
            profile.create_attribute_value_wrapper_count,
        ),
        (
            "create_attribute_value_link_wrapper_object",
            profile.create_attribute_value_link_wrapper_count,
        ),
    ):
        _record_profile_count(phase=f"{prefix}.{name}", count=count)
    if constructor_profile is None:
        return
    for metric_prefix, model_name in (
        ("orm_change", "Change"),
        ("orm_change_delta", "ChangeDelta"),
    ):
        model_profile = constructor_profile.models.get(model_name)
        if model_profile is None:
            continue
        for name, count in (
            ("model_validation_attempt", model_profile.model_validation_count),
            (
                "relationship_pre_validator_call",
                model_profile.relationship_pre_validator_count,
            ),
            (
                "relationship_hook_guard_call",
                model_profile.relationship_hook_guard_count,
            ),
            ("uuid_default_generated", model_profile.uuid_default_count),
            (
                "relationship_processing_call",
                model_profile.relationship_processing_count,
            ),
            (
                "post_init_hook_guard_call",
                model_profile.post_init_hook_guard_count,
            ),
        ):
            _record_profile_count(
                phase=f"{prefix}.{metric_prefix}_{name}",
                count=count,
            )


def _record_profile_count(*, phase: str, count: int) -> None:
    recorder = current_commit_perf_trace()
    if recorder is None:
        return
    for position in range(count):
        recorder.record(
            phase=phase,
            duration_ms=0.0,
            category="meta.runtime.handler_execution",
            metadata={"position": position},
        )


def _select_class_instance_change_candidates(
    *,
    change_set: ORMChangeSet,
    index: _OcgIndex,
    before_by_source_id: Mapping[UUID, Any],
) -> _ClassInstanceCandidateSelection:
    input_ids = frozenset(
        set(change_set.created_ids)
        | set(change_set.touched_ids)
        | set(change_set.deleted_ids)
    )
    mandatory_ids = set(change_set.created_ids) | set(change_set.deleted_ids)
    selected_ids: set[UUID] = set()
    pruned_ids: set[UUID] = set()
    ignored_ids: set[UUID] = set()

    for source_object_id in sorted(input_ids, key=str):
        obj = change_set.objects_by_id.get(source_object_id)
        class_config_id = _change_object_class_config_id(
            source_object_id=source_object_id,
            obj=obj,
            before_by_source_id=before_by_source_id,
        )
        if (
            class_config_id is not None
            and class_config_id not in index.opg_class_config_ids
        ):
            ignored_ids.add(source_object_id)
            continue
        if source_object_id in mandatory_ids:
            selected_ids.add(source_object_id)
            continue
        if class_config_id is None or not _is_relationship_only_change(
            source_object_id=source_object_id,
            class_config_id=class_config_id,
            change_set=change_set,
            index=index,
        ):
            selected_ids.add(source_object_id)
            continue
        pruned_ids.add(source_object_id)

    return _ClassInstanceCandidateSelection(
        input_ids=input_ids,
        selected_ids=frozenset(selected_ids),
        pruned_relationship_only_ids=frozenset(pruned_ids),
        ignored_out_of_projection_ids=frozenset(ignored_ids),
    )


def _is_relationship_only_change(
    *,
    source_object_id: UUID,
    class_config_id: UUID,
    change_set: ORMChangeSet,
    index: _OcgIndex,
) -> bool:
    scalar_fields = set(change_set.scalar_fields_by_id.get(source_object_id, set()))
    scalar_fields.update(
        field_name
        for object_id, field_name in change_set.scalar_baseline
        if object_id == source_object_id
    )
    list_fields = set(change_set.list_fields_by_id.get(source_object_id, set()))
    for evidence in (
        change_set.list_baseline,
        change_set.list_added,
        change_set.list_removed,
    ):
        list_fields.update(
            field_name
            for object_id, field_name in evidence
            if object_id == source_object_id
        )
    if not scalar_fields and not list_fields:
        return False

    relationship_fields = index.relationship_field_specs_by_cc_id.get(
        class_config_id,
        {},
    )
    retained_field_names = {
        index.attribute_names_by_id[attribute_id]
        for attribute_id in _retained_relationship_attribute_ids(
            index=index,
            class_config_id=class_config_id,
        )
        if attribute_id in index.attribute_names_by_id
    }
    for field_name in scalar_fields:
        if (
            field_name not in relationship_fields
            or field_name in retained_field_names
            or (source_object_id, field_name) not in change_set.scalar_baseline
        ):
            return False
    for field_name in list_fields:
        evidence_key = (source_object_id, field_name)
        if (
            field_name not in relationship_fields
            or field_name in retained_field_names
            or not any(
                evidence_key in evidence
                for evidence in (
                    change_set.list_baseline,
                    change_set.list_added,
                    change_set.list_removed,
                )
            )
        ):
            return False
    return True


def _change_object_class_config_id(
    *,
    source_object_id: UUID,
    obj: Any | None,
    before_by_source_id: Mapping[UUID, Any],
) -> UUID | None:
    before_class_instance = before_by_source_id.get(source_object_id)
    before_class_config_id = getattr(before_class_instance, "class_config_id", None)
    object_class_config_id = (
        _try_object_class_config_id(obj) if obj is not None else None
    )
    if isinstance(before_class_config_id, UUID):
        if (
            object_class_config_id is not None
            and object_class_config_id != before_class_config_id
        ):
            raise OrmChangeTranslationError(
                "Collected ORM object class does not match pre-state identity: "
                f"source_object_id={source_object_id} "
                f"expected_class_config_id={before_class_config_id} "
                f"actual_class_config_id={object_class_config_id} "
                f"object_type={type(obj).__module__}.{type(obj).__name__}"
            )
        return before_class_config_id
    return object_class_config_id


def _retained_relationship_attribute_ids(
    *,
    index: _OcgIndex,
    class_config_id: UUID,
) -> set[UUID]:
    return (
        set(
            index.portal_include_relationship_attribute_ids_by_cc_id.get(
                class_config_id,
                set(),
            )
        )
        | set(
            index.soft_ref_include_relationship_attribute_ids_by_cc_id.get(
                class_config_id,
                set(),
            )
        )
        | set(
            index.required_fk_include_relationship_attribute_ids_by_cc_id.get(
                class_config_id,
                set(),
            )
        )
    )


def _record_class_instance_candidate_counts(
    *,
    selection: _ClassInstanceCandidateSelection,
) -> None:
    for source_object_id in selection.input_ids:
        with commit_perf_span(
            phase=(
                "handler_execution.orm_change_translation."
                "class_instance_changes.candidate_input"
            ),
            category="meta.runtime.handler_execution",
            metadata={"source_object_id": source_object_id},
        ):
            pass
    for source_object_id in selection.selected_ids:
        with commit_perf_span(
            phase=(
                "handler_execution.orm_change_translation."
                "class_instance_changes.candidate_selected"
            ),
            category="meta.runtime.handler_execution",
            metadata={"source_object_id": source_object_id},
        ):
            pass
    for source_object_id in selection.pruned_relationship_only_ids:
        with commit_perf_span(
            phase=(
                "handler_execution.orm_change_translation."
                "class_instance_changes.candidate_pruned_relationship_only"
            ),
            category="meta.runtime.handler_execution",
            metadata={"source_object_id": source_object_id},
        ):
            pass
    for source_object_id in selection.ignored_out_of_projection_ids:
        with commit_perf_span(
            phase=(
                "handler_execution.orm_change_translation."
                "class_instance_changes.candidate_ignored_out_of_projection"
            ),
            category="meta.runtime.handler_execution",
            metadata={"source_object_id": source_object_id},
        ):
            pass


def _record_direct_create_result(*, result: str, source_object_id: UUID) -> None:
    with commit_perf_span(
        phase=(
            "handler_execution.orm_change_translation."
            f"class_instance_changes.direct_create_{result}"
        ),
        category="meta.runtime.handler_execution",
        metadata={"source_object_id": source_object_id},
    ):
        pass


def _build_detached_class_instance_delete_changes(
    *,
    before_oig: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    opg: ObjectProjectionGraph,
    relationship_changes: list[ClassInstanceRelationshipChange],
    created_at: datetime,
) -> list[ObjectInstanceGraphChange]:
    if not any(
        change.change.type == ChangeType.delete for change in relationship_changes
    ):
        return []

    traversal_direction_by_relationship_id: dict[
        UUID, ClassConfigRelationshipDirection
    ] = {}
    for edge in opg.object_projection_graph_edges:
        relationship_id = edge.class_config_relationship_id
        previous_direction = traversal_direction_by_relationship_id.get(relationship_id)
        if (
            previous_direction is not None
            and previous_direction != edge.traversal_direction
        ):
            raise OrmChangeTranslationError(
                "OPG uses one relationship with conflicting traversal directions: "
                f"relationship_id={relationship_id}"
            )
        traversal_direction_by_relationship_id[relationship_id] = (
            edge.traversal_direction
        )

    baseline_relationship_keys = {
        (
            relationship.class_config_relationship_id,
            relationship.source_class_instance_id,
            relationship.target_class_instance_id,
        )
        for relationship in before_oig.class_instance_relationships
        if relationship.class_config_relationship_id
        in traversal_direction_by_relationship_id
    }
    post_relationship_keys = set(baseline_relationship_keys)
    for relationship_change in relationship_changes:
        relationship_key = (
            relationship_change.class_config_relationship_id,
            relationship_change.source_class_instance_id,
            relationship_change.target_class_instance_id,
        )
        if relationship_key[0] not in traversal_direction_by_relationship_id:
            continue
        if relationship_change.change.type == ChangeType.create:
            post_relationship_keys.add(relationship_key)
        elif relationship_change.change.type == ChangeType.delete:
            post_relationship_keys.discard(relationship_key)

    root_class_instance_id = before_oig.root_class_instance_id
    if root_class_instance_id is None:
        return []
    baseline_reachable_ids = _reachable_class_instance_ids(
        root_class_instance_id=root_class_instance_id,
        relationship_keys=baseline_relationship_keys,
        traversal_direction_by_relationship_id=(traversal_direction_by_relationship_id),
    )
    post_reachable_ids = _reachable_class_instance_ids(
        root_class_instance_id=root_class_instance_id,
        relationship_keys=post_relationship_keys,
        traversal_direction_by_relationship_id=(traversal_direction_by_relationship_id),
    )
    detached_class_instance_ids = baseline_reachable_ids - post_reachable_ids
    if not detached_class_instance_ids:
        return []

    post_oig = before_oig.model_copy(deep=False)
    post_oig.class_instances = [
        class_instance
        for class_instance in before_oig.class_instances
        if class_instance.id not in detached_class_instance_ids
    ]
    post_oig.class_instance_relationships = [
        relationship
        for relationship in before_oig.class_instance_relationships
        if relationship.source_class_instance_id not in detached_class_instance_ids
        and relationship.target_class_instance_id not in detached_class_instance_ids
        and (
            relationship.class_config_relationship_id,
            relationship.source_class_instance_id,
            relationship.target_class_instance_id,
        )
        in post_relationship_keys
    ]
    return build_object_instance_graph_dirty_class_instance_changes(
        old=before_oig,
        new=post_oig,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        dirty_class_instance_ids=detached_class_instance_ids,
        created_at=created_at,
    )


def _relationship_change_signature(
    change: ClassInstanceRelationshipChange,
) -> tuple[ChangeType, UUID, UUID, UUID]:
    return (
        change.change.type,
        change.class_config_relationship_id,
        change.source_class_instance_id,
        change.target_class_instance_id,
    )


def _reachable_class_instance_ids(
    *,
    root_class_instance_id: UUID,
    relationship_keys: set[tuple[UUID, UUID, UUID]],
    traversal_direction_by_relationship_id: Mapping[
        UUID, ClassConfigRelationshipDirection
    ],
) -> set[UUID]:
    targets_by_source_id: dict[UUID, set[UUID]] = {}
    for relationship_id, source_id, target_id in relationship_keys:
        direction = traversal_direction_by_relationship_id.get(relationship_id)
        if direction == ClassConfigRelationshipDirection.forward:
            traversal_source_id, traversal_target_id = source_id, target_id
        elif direction == ClassConfigRelationshipDirection.reverse:
            traversal_source_id, traversal_target_id = target_id, source_id
        else:
            continue
        targets_by_source_id.setdefault(traversal_source_id, set()).add(
            traversal_target_id
        )

    reachable_ids = {root_class_instance_id}
    pending_ids = [root_class_instance_id]
    while pending_ids:
        source_id = pending_ids.pop()
        for target_id in targets_by_source_id.get(source_id, set()):
            if target_id in reachable_ids:
                continue
            reachable_ids.add(target_id)
            pending_ids.append(target_id)
    return reachable_ids


def _record_detached_class_instance_delete_count(
    *,
    class_instance_ids: set[UUID],
) -> None:
    for class_instance_id in class_instance_ids:
        with commit_perf_span(
            phase=(
                "handler_execution.orm_change_translation."
                "detached_class_instance_delete"
            ),
            category="meta.runtime.handler_execution",
            metadata={"class_instance_id": class_instance_id},
        ):
            pass


def _record_detached_relationship_delete_count(
    *,
    relationship_changes: list[ClassInstanceRelationshipChange],
) -> None:
    for relationship_change in relationship_changes:
        with commit_perf_span(
            phase=(
                "handler_execution.orm_change_translation."
                "detached_relationship_delete"
            ),
            category="meta.runtime.handler_execution",
            metadata={
                "class_config_relationship_id": (
                    relationship_change.class_config_relationship_id
                ),
                "source_class_instance_id": (
                    relationship_change.source_class_instance_id
                ),
                "target_class_instance_id": (
                    relationship_change.target_class_instance_id
                ),
            },
        ):
            pass


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

    reference_specs_by_cc_id, foreign_key_attrs_by_relationship_id = (
        _relationship_context_specs_by_class_config(index=index)
    )

    out: dict[UUID, dict[str, object]] = {}
    created_ids = set(change_set.created_ids)
    for rel in index.relationships_by_id.values():
        if rel.id not in index.opg_relationship_ids:
            continue
        foreign_key_attrs = foreign_key_attrs_by_relationship_id.get(rel.id, ())
        if not foreign_key_attrs:
            continue

        for obj_id, obj in change_set.objects_by_id.items():
            owner_cc_id = class_config_id_by_object_id.get(obj_id)
            if owner_cc_id is None:
                continue
            reference_specs = reference_specs_by_cc_id.get(owner_cc_id)
            if not reference_specs:
                continue

            if obj_id in created_ids:
                candidate_field_names = set(reference_specs)
            else:
                changed_fields = set(change_set.scalar_fields_by_id.get(obj_id, set()))
                changed_fields.update(change_set.list_fields_by_id.get(obj_id, set()))
                candidate_field_names = changed_fields & set(reference_specs)
            if not candidate_field_names:
                continue

            for ref_name in sorted(candidate_field_names):
                spec = reference_specs.get(ref_name)
                if spec is None or spec.relationship_id != rel.id:
                    continue

                related_ids = _read_relationship_reference_ids(obj, ref_name)
                if not related_ids:
                    continue

                for related_id in related_ids:
                    if spec.direction == ClassConfigRelationshipDirection.forward:
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


def _relationship_context_specs_by_class_config(
    *,
    index: _OcgIndex,
) -> tuple[
    dict[UUID, dict[str, _RelationshipFieldSpec]],
    dict[UUID, tuple[ClassConfigRelationshipAttribute, ...]],
]:
    reference_specs_by_cc_id: dict[UUID, dict[str, _RelationshipFieldSpec]] = {}
    foreign_key_attrs_by_relationship_id: dict[
        UUID, tuple[ClassConfigRelationshipAttribute, ...]
    ] = {}

    for rel in index.relationships_by_id.values():
        if rel.id not in index.opg_relationship_ids:
            continue

        foreign_key_attrs = tuple(
            rel_attr
            for rel_attr in rel.class_config_relationship_attributes or []
            if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
            and rel_attr.attribute_config_id is not None
        )
        if not foreign_key_attrs:
            continue
        foreign_key_attrs_by_relationship_id[rel.id] = foreign_key_attrs

        for rel_attr in rel.class_config_relationship_attributes or []:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.reference:
                continue
            attr_id = rel_attr.attribute_config_id
            if attr_id is None:
                continue
            owner_cc_id = index.owner_class_config_by_attribute_id.get(attr_id)
            ref_name = index.attribute_names_by_id.get(attr_id)
            if owner_cc_id is None or not ref_name:
                continue
            reference_specs_by_cc_id.setdefault(owner_cc_id, {})[ref_name] = (
                _RelationshipFieldSpec(
                    relationship_id=rel.id,
                    direction=rel_attr.direction,
                )
            )

    return reference_specs_by_cc_id, foreign_key_attrs_by_relationship_id


def _record_foreign_key_context_values(
    *,
    out: dict[UUID, dict[str, object]],
    index: _OcgIndex,
    relationship: ClassConfigRelationship,
    foreign_key_attrs: tuple[ClassConfigRelationshipAttribute, ...],
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

    def require_relationship_endpoints(
        *,
        owner_source_id: UUID,
        owner: Any | None,
        related_source_id: UUID,
        related: Any | None,
        field_name: str,
        relationship_id: UUID,
        operation: str,
    ) -> tuple[UUID, UUID]:
        owner_class_instance_id = resolve_class_instance_id(owner_source_id, owner)
        related_class_instance_id = resolve_class_instance_id(
            related_source_id,
            related,
        )
        if owner_class_instance_id is None or related_class_instance_id is None:
            unresolved_role = "owner" if owner_class_instance_id is None else "related"
            unresolved_source_id = (
                owner_source_id
                if owner_class_instance_id is None
                else related_source_id
            )
            raise OrmChangeTranslationError(
                "Cannot resolve OPG relationship endpoint for direct ORM change "
                f"translation: operation={operation} "
                f"relationship_id={relationship_id} "
                f"owner_source_object_id={owner_source_id} "
                f"field_name={field_name} "
                f"unresolved_role={unresolved_role} "
                f"unresolved_source_object_id={unresolved_source_id}"
            )
        return owner_class_instance_id, related_class_instance_id

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
                    src_ci_id, tgt_ci_id = require_relationship_endpoints(
                        owner_source_id=obj_id,
                        owner=obj,
                        related_source_id=other_id,
                        related=change_set.objects_by_id.get(other_id),
                        field_name=field_name,
                        relationship_id=spec.relationship_id,
                        operation="create_initial_list_member",
                    )
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
            src_ci_id, tgt_ci_id = require_relationship_endpoints(
                owner_source_id=obj_id,
                owner=obj,
                related_source_id=other_id,
                related=change_set.objects_by_id.get(other_id),
                field_name=field_name,
                relationship_id=spec.relationship_id,
                operation="create_initial_scalar_target",
            )
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
            src_ci_id, tgt_ci_id = require_relationship_endpoints(
                owner_source_id=obj_id,
                owner=obj,
                related_source_id=other_id,
                related=change_set.objects_by_id.get(other_id),
                field_name=field_name,
                relationship_id=spec.relationship_id,
                operation="add_list_member",
            )
            if spec.direction == ClassConfigRelationshipDirection.forward:
                emit(ChangeType.create, spec.relationship_id, src_ci_id, tgt_ci_id)
            else:
                emit(ChangeType.create, spec.relationship_id, tgt_ci_id, src_ci_id)

        for other_id in removed:
            src_ci_id, tgt_ci_id = require_relationship_endpoints(
                owner_source_id=obj_id,
                owner=obj,
                related_source_id=other_id,
                related=change_set.objects_by_id.get(other_id),
                field_name=field_name,
                relationship_id=spec.relationship_id,
                operation="remove_list_member",
            )
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
            src_ci_id, tgt_ci_id = require_relationship_endpoints(
                owner_source_id=obj_id,
                owner=obj,
                related_source_id=before_value,
                related=change_set.objects_by_id.get(before_value),
                field_name=field_name,
                relationship_id=spec.relationship_id,
                operation="delete_scalar_target",
            )
            if spec.direction == ClassConfigRelationshipDirection.forward:
                emit(ChangeType.delete, spec.relationship_id, src_ci_id, tgt_ci_id)
            else:
                emit(ChangeType.delete, spec.relationship_id, tgt_ci_id, src_ci_id)

        if isinstance(after_value, UUID):
            src_ci_id, tgt_ci_id = require_relationship_endpoints(
                owner_source_id=obj_id,
                owner=obj,
                related_source_id=after_value,
                related=change_set.objects_by_id.get(after_value),
                field_name=field_name,
                relationship_id=spec.relationship_id,
                operation="create_scalar_target",
            )
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
    "OrmChangeTranslationEvidence",
    "OrmChangeTranslationIndexCache",
    "OrmChangeTranslationRelationshipProjectionContext",
    "build_object_instance_graph_changes_from_orm_change_set",
    "build_object_instance_graph_evidence_from_orm_change_set",
]
