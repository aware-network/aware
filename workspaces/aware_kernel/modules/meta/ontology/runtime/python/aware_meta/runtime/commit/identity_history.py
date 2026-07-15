"""Meta-owned OIGI history projection for runtime domain commits.

This module is the required commit reaction for the Meta history plane:
domain lane commits are projected into the `object_instance_graph_identity`
lane so consumers can resolve commit pins through OIGI truth instead of raw
filesystem paths.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID
import time
from typing import Final, cast

from aware_code.types import Json, JsonValue
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_history.stable_ids import stable_lane_id
from aware_history_ontology.branch.branch import Branch
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.stable_ids import (
    stable_commit_id,
    stable_commit_parent_id,
)
from aware_history_ontology.lane.lane import Lane

# Meta Ontology
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.graph.instance.object_instance_graph_lane import (
    ObjectInstanceGraphLane,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import (
    stable_class_instance_attribute_id,
    stable_class_instance_identity_id,
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_lane_id,
)

# Meta Runtime
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.builder import (
    extract_object_instance_graph_commit_root_metadata,
)
from aware_meta.graph.instance.commit.body_codec import (
    OigCommitBodyAttributeChangeDraft,
    OigCommitBodyAttributeValueChangeDraft,
    OigCommitBodyChangeRefDraft,
    OigCommitBodyDraft,
    OigCommitBodyFieldDeltaDraft,
    OigCommitBodyJsonValue,
    OigCommitBodyClassInstanceChangeDraft,
    OigCommitBodyRootChangeDraft,
    oig_commit_body_change_ref_draft_from_change,
    oig_commit_body_attribute_change_draft_from_change,
    oig_commit_body_class_instance_change_draft_from_change,
    oig_commit_body_relationship_change_draft_from_change,
)
from aware_meta.graph.instance.commit.contract import (
    CommitActionDescriptor,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitIdentitySidecar,
    ObjectInstanceGraphCommitPreStateEvidence,
    OigiHistoryDomainCommitProjection,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.stored_commit_records import (
    object_instance_graph_commit_envelope_from_commit,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
    apply_commit_state_index_row_changes,
    build_commit_state_index,
)
from aware_meta.graph.instance.builder import (
    OigBuildError,
    build_include_relationship_attribute_config_ids_by_class_config_id,
    build_relationship_attribute_config_ids_by_class_config_id,
)
from aware_meta.graph.instance.diff import (
    diff_object_instance_graph_changes,
)
from aware_meta.graph.instance.apply import OigChangeApplyError, OigDeltaApplyError
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.graph.instance.root import resolve_root_source_object_id
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import (
    default_meta_enum_option_resolver,
)
from aware_meta.attribute.instance.builder import (
    AttributeBuildError,
    build_attribute,
)
from aware_meta.attribute.instance.value.builder import fingerprint_attribute_value
from aware_meta.attribute.instance.value.stable_ids import stable_attribute_value_id
from aware_meta.class_.instance.builder import (
    ClassInstanceAttributeBuildPlan,
    ClassInstanceBuildError,
    build_class_instance,
    plan_class_instance_attribute_links,
)
from aware_meta.class_.instance.handlers import link_attribute
from aware_meta.graph.config.stable_ids import (
    stable_attribute_id,
    stable_class_instance_id,
)
from aware_meta.runtime.commit.identity_lane import (
    ensure_object_instance_graph_identity_lane_head,
    reset_invalid_object_instance_graph_identity_lane,
    resolve_object_instance_graph_identity_lane_context,
)
from aware_orm.session.execution_guard import (
    allow_domain_create,
    disallow_push,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.introspection import ModelIntrospection
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import ORMChangeSet
from aware_orm.session.change_collector import disable_change_tracking_hooks
from aware_orm.session.change_collector import scoped_change_collection
from aware_orm.session.session import Session
from pydantic import BaseModel


_OIGI_HISTORY_TRACE_CATEGORY = "meta.runtime.invoke_function"
_OIGI_HISTORY_TRACE_PHASE_PREFIX = (
    "runtime.invoke_function.required_commit_reactions.oigi_history"
)
_OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED: Final = object()
_OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED: Final = object()
_OIGI_PRIMITIVE_LEAF_PAYLOAD_UNSET: Final = object()
_OIGI_STATE_ROW_MISMATCH_SAMPLE_LIMIT: Final = 5
_OIGI_STATIC_DIRECT_CONTEXT_CACHE_LIMIT: Final = 32


class _OigiHistoryDirectProjectionUnsupported(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class _OigiHistoryProjectionResult:
    change_set: ORMChangeSet
    session: Session | None
    root_identity: ObjectInstanceGraphIdentity


@dataclass(frozen=True, slots=True)
class _OigiHistoryChangedClassInstanceTarget:
    source: ModelIntrospection
    class_config: ClassConfig
    class_instance: ClassInstance
    attribute_plan: ClassInstanceAttributeBuildPlan


@dataclass(frozen=True, slots=True)
class _OigiHistoryDirectClassInstanceTargets:
    changed_targets: tuple[_OigiHistoryChangedClassInstanceTarget, ...]
    deleted_class_instances: tuple[ClassInstance, ...]


@dataclass(frozen=True, slots=True)
class _OigiHistoryDirectProjectionContext:
    class_configs_by_id: Mapping[UUID, ClassConfig]
    relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    include_relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    opg_class_config_ids: frozenset[UUID]
    before_class_instances_by_id: dict[UUID, ClassInstance]


@dataclass(frozen=True, slots=True)
class _OigiHistoryStaticDirectProjectionContext:
    class_configs_by_id: Mapping[UUID, ClassConfig]
    relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    include_relationship_attribute_ids_by_cc_id: dict[UUID, set[UUID]]
    opg_class_config_ids: frozenset[UUID]


_OigiHistoryStaticDirectContextCacheKey = tuple[
    int,
    int,
    int,
    int,
    int,
    int,
    tuple[str, ...],
]
_OIGI_STATIC_DIRECT_CONTEXT_CACHE: OrderedDict[
    _OigiHistoryStaticDirectContextCacheKey,
    _OigiHistoryStaticDirectProjectionContext,
] = OrderedDict()


@dataclass(frozen=True, slots=True)
class _OigiHistoryProjectedChangedClassInstance:
    target: _OigiHistoryChangedClassInstanceTarget
    post_state_rows: tuple[CommitStateRow, ...]
    class_instance_change: ClassInstanceChange | None
    class_instance_body_draft: OigCommitBodyClassInstanceChangeDraft | None


@dataclass(frozen=True, slots=True)
class _OigiPrimitiveLeafSourceRowEmission:
    attribute_id: UUID
    attribute_config_id: UUID
    value_fingerprint: str
    attribute_change_draft: _OigiPrimitiveLeafAttributeChangeDraft | None
    reused_before_fingerprint: bool = False
    row_backed_before_attribute: bool = False


@dataclass(frozen=True, slots=True)
class _OigiPrimitiveLeafValueChangeDraft:
    attribute_value_id: UUID
    operation: ChangeType
    fields: tuple[tuple[str, object], ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class _OigiPrimitiveLeafAttributeChangeDraft:
    attribute_id: UUID
    attribute_config_id: UUID
    operation: ChangeType
    value_root_change: _OigiPrimitiveLeafValueChangeDraft
    created_at: datetime


@dataclass(frozen=True, slots=True)
class _OigiPrimitiveLeafAttributeChangeBuildResult:
    attribute_change: AttributeChange
    body_draft: OigCommitBodyAttributeChangeDraft


@dataclass(frozen=True, slots=True)
class _OigiPrimitiveLeafPayloadParts:
    primitive_payload: JsonValue
    fingerprint_primitive_value: JsonValue


@dataclass(frozen=True, slots=True)
class _OigiHistoryChangedTargetSourceProjection:
    post_state_rows: tuple[CommitStateRow, ...]
    class_instance_body_draft: OigCommitBodyClassInstanceChangeDraft


@dataclass(frozen=True, slots=True)
class _OigiHistoryChangeProjection:
    changes: list[ObjectInstanceGraphChange]
    graph_hash_post: str
    after_oig: ObjectInstanceGraph
    body_draft: OigCommitBodyDraft | None
    pre_state_evidence: ObjectInstanceGraphCommitPreStateEvidence | None = None
    pre_state_index: CommitStateIndex | None = None


@dataclass(frozen=True, slots=True)
class _OigiHistoryMaterializedHead:
    before_oig: ObjectInstanceGraph
    head_commit_id: UUID
    head_oig_id: UUID


def _oigi_history_trace_metadata(
    *,
    domain_oig_id: UUID | None = None,
    domain_branch_id: UUID | None = None,
    domain_projection_hash: str | None = None,
    domain_commit_id: UUID | None = None,
    oigi_projection_hash: str | None = None,
    oigi_lane_commit_id: UUID | None = None,
    history_commit_id: UUID | None = None,
    lane_id: UUID | None = None,
    projector_mode: str | None = None,
) -> dict[str, object]:
    return {
        "domain_oig_id": str(domain_oig_id) if domain_oig_id is not None else None,
        "domain_branch_id": (
            str(domain_branch_id) if domain_branch_id is not None else None
        ),
        "domain_projection_hash": domain_projection_hash,
        "domain_commit_id": (
            str(domain_commit_id) if domain_commit_id is not None else None
        ),
        "oigi_projection_hash": oigi_projection_hash,
        "oigi_lane_commit_id": (
            str(oigi_lane_commit_id) if oigi_lane_commit_id is not None else None
        ),
        "history_commit_id": (
            str(history_commit_id) if history_commit_id is not None else None
        ),
        "lane_id": str(lane_id) if lane_id is not None else None,
        "projector_mode": projector_mode,
    }


def _oigi_history_trace_phase(suffix: str) -> str:
    return f"{_OIGI_HISTORY_TRACE_PHASE_PREFIX}.{suffix}"


def _optional_uuid_from_mapping(
    mapping: Mapping[str, object] | None, key: str
) -> UUID | None:
    if mapping is None:
        return None
    raw = mapping.get(key)
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw)
    return None


def _record_perf(
    perf_ms: dict[str, int] | None,
    metric: str,
    *,
    started: float,
) -> None:
    if perf_ms is None:
        return
    perf_ms[metric] = max(int((time.monotonic() - started) * 1000), 0)


def _increment_perf(
    perf_ms: dict[str, int] | None,
    metric: str,
    *,
    value: int = 1,
) -> None:
    if perf_ms is None:
        return
    perf_ms[metric] = perf_ms.get(metric, 0) + value


def _record_commit_perf(
    perf_ms: dict[str, int] | None,
    *,
    prefix: str,
    committer: FSLaneCommitter,
) -> None:
    if perf_ms is None:
        return
    for (
        metric_name,
        metric_value,
    ) in committer.last_commit_perf_profile_snapshot().items():
        perf_ms[f"{prefix}_{metric_name}"] = max(metric_value, 0)


def _optional_string_from_mapping(
    mapping: Mapping[str, object] | None,
    key: str,
) -> str | None:
    if mapping is None:
        return None
    raw = mapping.get(key)
    if isinstance(raw, str) and raw.strip():
        return raw
    return None


def _record_oigi_history_projection_index_result(
    perf_ms: dict[str, int] | None,
    *,
    perf_metric_prefix: str,
    hit: bool,
) -> None:
    if perf_ms is None:
        return
    perf_ms[f"{perf_metric_prefix}_projection_index_head_hit_count"] = 1 if hit else 0
    perf_ms[f"{perf_metric_prefix}_projection_index_head_miss_count"] = 0 if hit else 1


async def _oigi_history_projection_head_index_hit(
    *,
    store: FSCommitStore,
    oigi_head: Mapping[str, object],
    domain_oig_id: UUID,
    oigi_projection_hash: str,
    object_instance_graph_identity_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    lane_id: UUID,
    domain_commit_id: UUID,
    history_commit_id: UUID,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "run_commit_reaction_oigi",
) -> bool:
    trace_metadata = _oigi_history_trace_metadata(
        domain_oig_id=domain_oig_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=domain_commit_id,
        oigi_projection_hash=oigi_projection_hash,
        oigi_lane_commit_id=_optional_uuid_from_mapping(oigi_head, "commit_id"),
        history_commit_id=history_commit_id,
        lane_id=lane_id,
    )
    read_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("projection_index_read"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        projection = await store.get_oigi_history_domain_commit_projection(
            branch_id=domain_oig_id,
            projection_hash=oigi_projection_hash,
            domain_commit_id=domain_commit_id,
        )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_projection_index_read_ms",
        started=read_started,
    )
    if projection is None:
        _record_oigi_history_projection_index_result(
            perf_ms,
            perf_metric_prefix=perf_metric_prefix,
            hit=False,
        )
        return False

    oigi_head_commit_id = _optional_uuid_from_mapping(oigi_head, "commit_id")
    oigi_head_hash = _optional_string_from_mapping(oigi_head, "graph_hash_post")
    with commit_perf_span(
        phase=_oigi_history_trace_phase("projection_index_validate"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        hit = (
            projection.domain_commit_id == domain_commit_id
            and projection.domain_branch_id == domain_branch_id
            and projection.domain_projection_hash == domain_projection_hash
            and projection.domain_lane_id == lane_id
            and projection.history_commit_id == history_commit_id
            and projection.object_instance_graph_identity_id
            == object_instance_graph_identity_id
            and projection.object_instance_graph_id == domain_oig_id
            and projection.oigi_projection_hash == oigi_projection_hash
            and projection.oigi_lane_commit_id == oigi_head_commit_id
            and oigi_head_hash is not None
            and projection.oigi_graph_hash_post == oigi_head_hash
        )
    _record_oigi_history_projection_index_result(
        perf_ms,
        perf_metric_prefix=perf_metric_prefix,
        hit=hit,
    )
    return hit


def _write_oigi_history_projection_index(
    *,
    store: FSCommitStore,
    domain_oig_id: UUID,
    oigi_projection_hash: str,
    object_instance_graph_identity_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    lane_id: UUID,
    domain_commit_id: UUID,
    history_commit_id: UUID,
    oigi_lane_commit_id: UUID,
    oigi_graph_hash_post: str,
) -> bool:
    if not oigi_graph_hash_post:
        return False
    return store.put_oigi_history_domain_commit_projection(
        branch_id=domain_oig_id,
        projection_hash=oigi_projection_hash,
        projection=OigiHistoryDomainCommitProjection(
            domain_commit_id=domain_commit_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            domain_lane_id=lane_id,
            history_commit_id=history_commit_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_id=domain_oig_id,
            oigi_projection_hash=oigi_projection_hash,
            oigi_lane_commit_id=oigi_lane_commit_id,
            oigi_graph_hash_post=oigi_graph_hash_post,
        ),
    )


def _oigi_history_head_state_hash_mismatch(
    *,
    before_oig: ObjectInstanceGraph,
) -> tuple[str, str] | None:
    state_index_hash = build_commit_state_index(before_oig).compute_hash()
    graph_hash = str(before_oig.hash or "")
    if state_index_hash == graph_hash:
        return None
    return state_index_hash, graph_hash


async def _materialize_oigi_history_head_with_recovery(
    *,
    materializer: CachedLaneMaterializer,
    lane_materializer: CachedLaneMaterializer | None,
    store: FSCommitStore,
    index: MetaGraphRuntimeIndex,
    oigi_opg: ObjectProjectionGraph,
    domain_oig_id: UUID,
    domain_projection_hash: str,
    oigi_projection_hash: str,
    head_commit_id: UUID,
    head_oig_id: UUID,
    author_id: UUID,
    perf_ms: dict[str, int] | None,
    perf_metric_prefix: str,
) -> _OigiHistoryMaterializedHead:
    def _materialization_error(
        *,
        state_index_hash: str,
        graph_hash: str,
    ) -> RuntimeError:
        return RuntimeError(
            "object_instance_graph_identity lane head violates the row-backed "
            "hash contract: "
            + f"object_instance_graph_id={domain_oig_id} "
            + f"projection_hash={oigi_projection_hash} "
            + f"state_index_hash={state_index_hash} "
            + f"graph_hash={graph_hash}"
        )

    try:
        before_oig, _indexes = await materializer.get(
            branch_id=domain_oig_id,
            ocg=index.ocg,
            opg=oigi_opg,
            commit_id=head_commit_id,
            oig_id=head_oig_id,
            attribute_configs_by_id=dict(index.attribute_configs_by_id),
            class_configs_by_id=dict(index.class_configs_by_id),
        )
    except (OigChangeApplyError, OigDeltaApplyError) as exc:
        if lane_materializer is not None:
            raise
        recovery_cause: BaseException = exc
        recovery_metric = "invalid_oigi_head_replay_reset_count"
    else:
        hash_mismatch = _oigi_history_head_state_hash_mismatch(before_oig=before_oig)
        if hash_mismatch is None:
            return _OigiHistoryMaterializedHead(
                before_oig=before_oig,
                head_commit_id=head_commit_id,
                head_oig_id=head_oig_id,
            )
        state_index_hash, graph_hash = hash_mismatch
        recovery_cause = _materialization_error(
            state_index_hash=state_index_hash,
            graph_hash=graph_hash,
        )
        recovery_metric = "invalid_oigi_head_state_hash_reset_count"
        if lane_materializer is not None:
            raise recovery_cause

    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_invalid_oigi_head_reset_count",
    )
    _increment_perf(perf_ms, f"{perf_metric_prefix}_{recovery_metric}")
    reset_invalid_object_instance_graph_identity_lane(
        aware_root=store.aware_root,
        branch_id=domain_oig_id,
        projection_hash=oigi_projection_hash,
    )
    await ensure_object_instance_graph_identity_lane_head(
        index=index,
        object_instance_graph_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
        author_id=author_id,
        label=f"oigi:{domain_oig_id.hex[:8]}:recovered",
        perf_ms=perf_ms,
        perf_metric_prefix=(f"{perf_metric_prefix}_reseed_invalid_oigi_lane"),
    )
    reseeded_head_raw = cast(
        object,
        await store.head(
            branch_id=domain_oig_id,
            projection_hash=oigi_projection_hash,
        ),
    )
    reseeded_head = (
        cast(Mapping[str, object], reseeded_head_raw)
        if isinstance(reseeded_head_raw, Mapping)
        else None
    )
    reseeded_head_commit_id = (
        _optional_uuid_from_mapping(reseeded_head, "commit_id")
        if reseeded_head is not None
        else None
    )
    reseeded_head_oig_id = (
        _optional_uuid_from_mapping(
            reseeded_head,
            "object_instance_graph_id",
        )
        if reseeded_head is not None
        else None
    )
    if reseeded_head_commit_id is None or reseeded_head_oig_id is None:
        raise RuntimeError(
            "Failed to reseed invalid object_instance_graph_identity lane: "
            + f"object_instance_graph_id={domain_oig_id} "
            + f"projection_hash={oigi_projection_hash}"
        ) from recovery_cause
    before_oig, _indexes = await materializer.get(
        branch_id=domain_oig_id,
        ocg=index.ocg,
        opg=oigi_opg,
        commit_id=reseeded_head_commit_id,
        oig_id=reseeded_head_oig_id,
        attribute_configs_by_id=dict(index.attribute_configs_by_id),
        class_configs_by_id=dict(index.class_configs_by_id),
    )
    hash_mismatch = _oigi_history_head_state_hash_mismatch(before_oig=before_oig)
    if hash_mismatch is not None:
        state_index_hash, graph_hash = hash_mismatch
        raise _materialization_error(
            state_index_hash=state_index_hash,
            graph_hash=graph_hash,
        ) from recovery_cause
    return _OigiHistoryMaterializedHead(
        before_oig=before_oig,
        head_commit_id=reseeded_head_commit_id,
        head_oig_id=reseeded_head_oig_id,
    )


def _bind_new(session: Session, instance: BaseORMModel) -> BaseORMModel:
    session.imap_add(instance)
    return instance


def _append_unique_by_id(items: list[object], instance: BaseORMModel) -> None:
    instance_id = instance.id
    if all(getattr(existing, "id", None) != instance_id for existing in items):
        items.append(instance)


def _history_commit_id(*, lane_id: UUID, domain_commit_id: UUID) -> UUID:
    return stable_commit_id(lane_id=lane_id, key=str(domain_commit_id))


def _ensure_oigi_branch_lane(
    *,
    session: Session,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    lane_id: UUID,
    branch_is_main: bool,
    branch_name: str | None,
) -> Lane:
    oigi_id = object_instance_graph_identity.id
    if oigi_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection requires OIGI id"
        )

    expected_lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    if lane_id != expected_lane_id:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection lane_id mismatch: "
            + f"have={lane_id} expected={expected_lane_id}"
        )

    branch = session.imap_get(Branch, domain_branch_id)
    if branch is None:
        branch = cast(
            Branch,
            _bind_new(
                session,
                Branch(
                    id=domain_branch_id,
                    key="default",
                    is_main=branch_is_main,
                    name=branch_name,
                ),
            ),
        )

    lane = session.imap_get(Lane, lane_id)
    if lane is None:
        lane = cast(
            Lane,
            _bind_new(
                session,
                Lane(
                    id=lane_id,
                    branch_id=domain_branch_id,
                    lane_hash=domain_projection_hash,
                ),
            ),
        )
    elif lane.branch_id != domain_branch_id or lane.lane_hash != domain_projection_hash:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection Lane mismatch: "
            + f"lane_id={lane_id} branch_id={lane.branch_id} lane_hash={lane.lane_hash!r}"
        )
    _append_unique_by_id(cast(list[object], branch.lanes), lane)

    oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=oigi_id,
        branch_id=domain_branch_id,
    )
    oigb = session.imap_get(ObjectInstanceGraphBranch, oigb_id)
    if oigb is None:
        oigb = cast(
            ObjectInstanceGraphBranch,
            _bind_new(
                session,
                ObjectInstanceGraphBranch(
                    id=oigb_id,
                    object_instance_graph_identity_id=oigi_id,
                    branch=branch,
                    branch_id=domain_branch_id,
                ),
            ),
        )
    elif oigb.object_instance_graph_identity_id != oigi_id:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection OIGB mismatch: "
            + f"oigb_id={oigb_id} have={oigb.object_instance_graph_identity_id} expected={oigi_id}"
        )
    _append_unique_by_id(
        cast(
            list[object], object_instance_graph_identity.object_instance_graph_branches
        ),
        oigb,
    )

    oigl_id = stable_object_instance_graph_lane_id(
        object_instance_graph_branch_id=oigb_id,
        lane_id=lane_id,
    )
    oigl = session.imap_get(ObjectInstanceGraphLane, oigl_id)
    if oigl is None:
        oigl = cast(
            ObjectInstanceGraphLane,
            _bind_new(
                session,
                ObjectInstanceGraphLane(
                    id=oigl_id,
                    object_instance_graph_branch_id=oigb_id,
                    lane=lane,
                    lane_id=lane_id,
                ),
            ),
        )
    _append_unique_by_id(cast(list[object], oigb.object_instance_graph_lanes), oigl)
    return lane


def _ensure_history_commit(
    *,
    session: Session,
    lane: Lane,
    lane_id: UUID,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope,
) -> Commit:
    domain_commit_id = domain_commit_envelope.commit_id
    commit_id = _history_commit_id(
        lane_id=lane_id,
        domain_commit_id=domain_commit_id,
    )
    commit = session.imap_get(Commit, commit_id)
    if commit is None:
        commit = cast(
            Commit,
            _bind_new(
                session,
                Commit(
                    id=commit_id,
                    lane_id=lane_id,
                    key=str(domain_commit_id),
                    author_id=resolve_meta_author_id(domain_commit_envelope.author_id),
                    created_at=domain_commit_envelope.created_at,
                    status=CommitStatus(domain_commit_envelope.status),
                ),
            ),
        )
    elif commit.lane_id != lane_id or commit.key != str(domain_commit_id):
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection Commit mismatch: "
            + f"commit_id={commit_id} lane_id={commit.lane_id} key={commit.key!r}"
        )
    _append_unique_by_id(cast(list[object], lane.commits), commit)

    for parent_domain_commit_id in domain_commit_envelope.parent_commit_ids:
        parent_commit_id = _history_commit_id(
            lane_id=lane_id,
            domain_commit_id=parent_domain_commit_id,
        )
        commit_parent_id = stable_commit_parent_id(
            commit_id=commit_id,
            parent_commit_id=parent_commit_id,
        )
        commit_parent = session.imap_get(CommitParent, commit_parent_id)
        if commit_parent is None:
            commit_parent = cast(
                CommitParent,
                _bind_new(
                    session,
                    CommitParent(
                        id=commit_parent_id,
                        commit_id=commit_id,
                        parent_commit_id=parent_commit_id,
                    ),
                ),
            )
        _append_unique_by_id(cast(list[object], commit.commit_parents), commit_parent)
    return commit


async def _canonicalize_domain_commit_identity_for_history(
    *,
    store: FSCommitStore,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_commit: ObjectInstanceGraphCommit,
) -> ObjectInstanceGraphCommit:
    oigi_id = object_instance_graph_identity.id
    if oigi_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection requires OIGI id"
        )
    if str(domain_commit.object_instance_graph_id) != str(
        object_instance_graph_identity.object_instance_graph_id
    ):
        return domain_commit
    if domain_commit.object_instance_graph_identity_id == oigi_id:
        return domain_commit

    canonical_commit = domain_commit.model_copy(
        update={
            "id": stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=oigi_id,
                commit_id=domain_commit.commit.id,
            ),
            "object_instance_graph_identity_id": oigi_id,
        }
    )
    _ = await store.put_commit_file(
        branch_id=domain_branch_id,
        projection_hash=domain_projection_hash,
        commit=canonical_commit,
    )
    return canonical_commit


async def _canonicalize_domain_commit_envelope_identity_for_history(
    *,
    store: FSCommitStore,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope,
) -> ObjectInstanceGraphCommitEnvelope:
    oigi_id = object_instance_graph_identity.id
    if oigi_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection requires OIGI id"
        )
    if str(domain_commit_envelope.object_instance_graph_id) != str(
        object_instance_graph_identity.object_instance_graph_id
    ):
        return domain_commit_envelope
    if domain_commit_envelope.object_instance_graph_identity_id == oigi_id:
        return domain_commit_envelope

    return replace(
        domain_commit_envelope,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=domain_commit_envelope.commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
    )


def _ensure_oigi_commit_wrapper(
    *,
    session: Session,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope,
    commit: Commit,
) -> ObjectInstanceGraphCommit:
    oigi_id = object_instance_graph_identity.id
    if oigi_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection requires OIGI id"
        )
    if str(domain_commit_envelope.object_instance_graph_id) != str(
        object_instance_graph_identity.object_instance_graph_id
    ):
        raise RuntimeError(
            "Domain commit object_instance_graph_id mismatch: "
            + f"commit_id={domain_commit_envelope.commit_id} "
            + f"have={domain_commit_envelope.object_instance_graph_id} "
            + f"expected_domain_oig_id={object_instance_graph_identity.object_instance_graph_id}"
        )
    if str(domain_commit_envelope.object_instance_graph_identity_id) != str(oigi_id):
        raise RuntimeError(
            "Domain commit object_instance_graph_identity_id mismatch: "
            + f"commit_id={domain_commit_envelope.commit_id} "
            + f"have={domain_commit_envelope.object_instance_graph_identity_id} "
            + f"expected_oigi_id={oigi_id}"
        )

    oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=oigi_id,
        commit_id=domain_commit_envelope.commit_id,
    )
    oig_commit = session.imap_get(ObjectInstanceGraphCommit, oig_commit_id)
    if oig_commit is None:
        oig_commit = cast(
            ObjectInstanceGraphCommit,
            _bind_new(
                session,
                ObjectInstanceGraphCommit(
                    id=oig_commit_id,
                    object_instance_graph_identity_id=oigi_id,
                    object_instance_graph_id=(
                        domain_commit_envelope.object_instance_graph_id
                    ),
                    commit=commit,
                    commit_id=commit.id,
                    object_instance_graph_key=(
                        domain_commit_envelope.object_instance_graph_key
                    ),
                    object_instance_graph_name=(
                        domain_commit_envelope.object_instance_graph_name
                    ),
                    object_instance_graph_description=(
                        domain_commit_envelope.object_instance_graph_description
                    ),
                    root_class_config_id=domain_commit_envelope.root_class_config_id,
                    root_source_object_id=(
                        domain_commit_envelope.root_source_object_id
                    ),
                    graph_hash_pre=domain_commit_envelope.graph_hash_pre,
                    graph_hash_post=domain_commit_envelope.graph_hash_post,
                    source_language=CodeLanguage(
                        domain_commit_envelope.source_language
                    ),
                    projection_hash=domain_commit_envelope.projection_hash,
                    object_instance_graph_changes=[],
                ),
            ),
        )
    else:
        oig_commit.commit = commit
        oig_commit.commit_id = commit.id
        oig_commit.object_instance_graph_identity_id = oigi_id
        oig_commit.object_instance_graph_id = (
            domain_commit_envelope.object_instance_graph_id
        )
        oig_commit.object_instance_graph_key = (
            domain_commit_envelope.object_instance_graph_key
        )
        oig_commit.object_instance_graph_name = (
            domain_commit_envelope.object_instance_graph_name
        )
        oig_commit.object_instance_graph_description = (
            domain_commit_envelope.object_instance_graph_description
        )
        oig_commit.root_class_config_id = domain_commit_envelope.root_class_config_id
        oig_commit.root_source_object_id = domain_commit_envelope.root_source_object_id
        oig_commit.graph_hash_pre = domain_commit_envelope.graph_hash_pre
        oig_commit.graph_hash_post = domain_commit_envelope.graph_hash_post
        oig_commit.source_language = CodeLanguage(
            domain_commit_envelope.source_language
        )
        oig_commit.projection_hash = domain_commit_envelope.projection_hash
    _append_unique_by_id(
        cast(
            list[object], object_instance_graph_identity.object_instance_graph_commits
        ),
        oig_commit,
    )
    return oig_commit


def _ensure_class_instance_identities(
    *,
    session: Session,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_commit: ObjectInstanceGraphCommit,
    existing_class_instance_ids: set[UUID],
) -> None:
    _ensure_class_instance_identities_from_ids(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        class_instance_ids=(
            class_change.class_instance_id
            for root_change in domain_commit.object_instance_graph_changes
            for class_change in root_change.class_instance_changes
        ),
        existing_class_instance_ids=existing_class_instance_ids,
    )


def _ensure_class_instance_identities_from_sidecar(
    *,
    session: Session,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope,
    identity_sidecar: ObjectInstanceGraphCommitIdentitySidecar,
    existing_class_instance_ids: set[UUID],
) -> bool:
    oigi_id = object_instance_graph_identity.id
    if oigi_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection requires OIGI id"
        )
    if identity_sidecar.commit_id != domain_commit_envelope.commit_id:
        return False
    if identity_sidecar.object_instance_graph_id != (
        domain_commit_envelope.object_instance_graph_id
    ):
        return False
    if (
        identity_sidecar.object_instance_graph_identity_id != oigi_id
        and identity_sidecar.object_instance_graph_id
        != domain_commit_envelope.object_instance_graph_id
    ):
        return False
    _ensure_class_instance_identities_from_ids(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        class_instance_ids=identity_sidecar.class_instance_ids,
        existing_class_instance_ids=existing_class_instance_ids,
    )
    return True


def _ensure_class_instance_identities_from_ids(
    *,
    session: Session,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    class_instance_ids: Iterable[UUID],
    existing_class_instance_ids: set[UUID],
) -> None:
    oigi_id = object_instance_graph_identity.id
    if oigi_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection requires OIGI id"
        )
    for class_instance_id in class_instance_ids:
        if class_instance_id in existing_class_instance_ids:
            continue
        class_instance_identity_id = stable_class_instance_identity_id(
            object_instance_graph_identity_id=oigi_id,
            class_instance_id=class_instance_id,
        )
        class_instance_identity = session.imap_get(
            ClassInstanceIdentity,
            class_instance_identity_id,
        )
        if class_instance_identity is None:
            class_instance_identity = cast(
                ClassInstanceIdentity,
                _bind_new(
                    session,
                    ClassInstanceIdentity(
                        id=class_instance_identity_id,
                        object_instance_graph_identity_id=oigi_id,
                        class_instance_id=class_instance_id,
                        label=None,
                    ),
                ),
            )
        _append_unique_by_id(
            cast(
                list[object],
                object_instance_graph_identity.class_instance_identities,
            ),
            class_instance_identity,
        )
        existing_class_instance_ids.add(class_instance_id)


def _root_identity_label_from_pre_oig(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    root_class_config_id: UUID,
) -> str | None:
    root_class_config = index.class_configs_by_id.get(root_class_config_id)
    if root_class_config is None:
        return None

    label_attribute_config_id: UUID | None = None
    for link in root_class_config.class_config_attribute_configs:
        attribute_config = link.attribute_config
        if attribute_config is None or attribute_config.name != "label":
            continue
        label_attribute_config_id = attribute_config.id
        break
    if label_attribute_config_id is None:
        return None

    root_class_instance = before_oig.root_class_instance
    if root_class_instance is None:
        root_class_instance_id = before_oig.root_class_instance_id
        root_class_instance = next(
            (
                class_instance
                for class_instance in before_oig.class_instances
                if class_instance.id == root_class_instance_id
            ),
            None,
        )
    if root_class_instance is None:
        return None

    for attribute in root_class_instance.attributes:
        if attribute.attribute_config_id != label_attribute_config_id:
            continue
        value_root = attribute.value_root
        primitive_value = value_root.primitive_value if value_root is not None else None
        if primitive_value is None:
            return None
        raw_value = primitive_value.get("value")
        return raw_value if isinstance(raw_value, str) else None
    return None


def _build_oigi_root_identity(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    root_class_config_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_projection_graph_identity_id: UUID,
    domain_oig_id: UUID,
) -> ObjectInstanceGraphIdentity:
    label = _root_identity_label_from_pre_oig(
        index=index,
        before_oig=before_oig,
        root_class_config_id=root_class_config_id,
    )
    with disable_change_tracking_hooks():
        with disable_autobind():
            return ObjectInstanceGraphIdentity(
                id=object_instance_graph_identity_id,
                label=label,
                object_projection_graph_identity_id=(
                    object_projection_graph_identity_id
                ),
                object_instance_graph_id=domain_oig_id,
            )


def _ensure_oigi_root_identity_boundary(
    *,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    object_projection_graph_identity_id: UUID,
    domain_oig_id: UUID,
) -> None:
    existing_opgi_id = getattr(
        object_instance_graph_identity,
        "object_projection_graph_identity_id",
        None,
    )
    existing_domain_oig_id = getattr(
        object_instance_graph_identity,
        "object_instance_graph_id",
        None,
    )
    if (
        existing_opgi_id is not None
        and existing_opgi_id != object_projection_graph_identity_id
    ):
        raise RuntimeError(
            "ObjectInstanceGraphIdentity root OPGI mismatch: "
            + f"object_instance_graph_identity_id={object_instance_graph_identity.id} "
            + f"have={existing_opgi_id} expected={object_projection_graph_identity_id}"
        )
    if existing_domain_oig_id is not None and existing_domain_oig_id != domain_oig_id:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity root domain OIG mismatch: "
            + f"object_instance_graph_identity_id={object_instance_graph_identity.id} "
            + f"have={existing_domain_oig_id} expected={domain_oig_id}"
        )
    if existing_opgi_id is None:
        object_instance_graph_identity.object_projection_graph_identity_id = (
            object_projection_graph_identity_id
        )
    if existing_domain_oig_id is None:
        object_instance_graph_identity.object_instance_graph_id = domain_oig_id


def _oigi_history_before_source_object_ids(
    before_oig: ObjectInstanceGraph,
) -> frozenset[UUID]:
    return frozenset(
        class_instance.source_object_id
        for class_instance in before_oig.class_instances
        if isinstance(class_instance.source_object_id, UUID)
    )


def _register_oigi_history_minimal_source_object(
    *,
    instance: BaseORMModel,
    before_source_object_ids: frozenset[UUID],
    created_ids: set[UUID],
    touched_ids: set[UUID],
    objects_by_id: dict[UUID, object],
    mark_touched: bool = False,
) -> None:
    if not isinstance(instance, ModelIntrospection):
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI minimal history projection requires ModelIntrospection: "
            f"source_type={type(instance)!r}"
        )
    source_object_id = instance.id
    if not isinstance(source_object_id, UUID):
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI minimal history projection source object lacks UUID id: "
            f"source_type={type(instance)!r}"
        )
    objects_by_id[source_object_id] = instance
    if source_object_id in before_source_object_ids:
        if mark_touched:
            touched_ids.add(source_object_id)
        else:
            touched_ids.discard(source_object_id)
        created_ids.discard(source_object_id)
    else:
        created_ids.add(source_object_id)
        touched_ids.discard(source_object_id)


def _oigi_history_domain_commit_class_instance_ids(
    domain_commit: ObjectInstanceGraphCommit,
) -> tuple[UUID, ...]:
    out: list[UUID] = []
    for root_change in domain_commit.object_instance_graph_changes:
        for class_change in root_change.class_instance_changes:
            if class_change.class_instance_id is not None:
                out.append(class_change.class_instance_id)
    return tuple(out)


def _oigi_history_sidecar_matches(
    *,
    object_instance_graph_identity_id: UUID,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope,
    identity_sidecar: ObjectInstanceGraphCommitIdentitySidecar,
) -> bool:
    if identity_sidecar.commit_id != domain_commit_envelope.commit_id:
        return False
    if identity_sidecar.object_instance_graph_id != (
        domain_commit_envelope.object_instance_graph_id
    ):
        return False
    if (
        identity_sidecar.object_instance_graph_identity_id
        != object_instance_graph_identity_id
        and identity_sidecar.object_instance_graph_id
        != domain_commit_envelope.object_instance_graph_id
    ):
        return False
    return True


async def _project_oigi_history_minimal_change_set(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    root_class_config_id: UUID,
    object_projection_graph_identity_id: UUID,
    object_instance_graph_identity_id: UUID,
    domain_oig_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    lane_id: UUID,
    head_commit_id: UUID,
    store: FSCommitStore,
    domain_commit: ObjectInstanceGraphCommit | None = None,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "run_commit_reaction_oigi",
) -> _OigiHistoryProjectionResult:
    if before_oig.id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI minimal history projection requires before OIG id."
        )
    expected_lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    if lane_id != expected_lane_id:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity history projection lane_id mismatch: "
            + f"have={lane_id} expected={expected_lane_id}"
        )
    if domain_commit_envelope is None:
        if domain_commit is None:
            raise RuntimeError(
                "OIGI minimal history projection requires a domain commit envelope"
            )
        domain_commit_envelope = object_instance_graph_commit_envelope_from_commit(
            branch_id=domain_branch_id,
            projection_hash=domain_projection_hash,
            commit=domain_commit,
        )

    before_source_object_ids = _oigi_history_before_source_object_ids(before_oig)
    created_ids: set[UUID] = set()
    touched_ids: set[UUID] = set()
    objects_by_id: dict[UUID, object] = {}

    def register(instance: BaseORMModel, *, mark_touched: bool = False) -> None:
        _register_oigi_history_minimal_source_object(
            instance=instance,
            before_source_object_ids=before_source_object_ids,
            created_ids=created_ids,
            touched_ids=touched_ids,
            objects_by_id=objects_by_id,
            mark_touched=mark_touched,
        )

    def is_projected_domain_commit(commit_id: UUID) -> bool:
        return (
            stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                commit_id=commit_id,
            )
            in before_source_object_ids
        )

    projected_identity_source_ids: set[UUID] = set()

    def project_class_instance_identities(class_instance_ids: Iterable[UUID]) -> None:
        for class_instance_id in class_instance_ids:
            class_instance_identity_id = stable_class_instance_identity_id(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                class_instance_id=class_instance_id,
            )
            if class_instance_identity_id in projected_identity_source_ids:
                continue
            projected_identity_source_ids.add(class_instance_identity_id)
            class_instance_identity = ClassInstanceIdentity(
                id=class_instance_identity_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                class_instance_id=class_instance_id,
                label=None,
            )
            object_instance_graph_identity.class_instance_identities.append(
                class_instance_identity
            )
            register(class_instance_identity)

    with disable_change_tracking_hooks():
        with disable_autobind():
            object_instance_graph_identity = _build_oigi_root_identity(
                index=index,
                before_oig=before_oig,
                root_class_config_id=root_class_config_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                domain_oig_id=domain_oig_id,
            )
            register(object_instance_graph_identity)

            branch = Branch(
                id=domain_branch_id,
                key="default",
                is_main=False,
                name=None,
            )
            register(branch)

            history_head_commit_id = _history_commit_id(
                lane_id=lane_id,
                domain_commit_id=head_commit_id,
            )
            lane = Lane(
                id=lane_id,
                branch_id=domain_branch_id,
                lane_hash=domain_projection_hash,
                head_commit_id=history_head_commit_id,
            )
            branch.lanes.append(lane)
            register(lane, mark_touched=True)

            oigb_id = stable_object_instance_graph_branch_id(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                branch_id=domain_branch_id,
            )
            oigb = ObjectInstanceGraphBranch(
                id=oigb_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                branch=branch,
                branch_id=domain_branch_id,
            )
            object_instance_graph_identity.object_instance_graph_branches.append(oigb)
            register(oigb)

            oigl_id = stable_object_instance_graph_lane_id(
                object_instance_graph_branch_id=oigb_id,
                lane_id=lane_id,
            )
            oigl = ObjectInstanceGraphLane(
                id=oigl_id,
                object_instance_graph_branch_id=oigb_id,
                lane=lane,
                lane_id=lane_id,
            )
            oigb.object_instance_graph_lanes.append(oigl)
            register(oigl)

    envelope_by_id: dict[UUID, ObjectInstanceGraphCommitEnvelope] = {
        domain_commit_envelope.commit_id: domain_commit_envelope,
    }
    provided_full_payload_by_id: dict[UUID, ObjectInstanceGraphCommit] = {}
    if domain_commit is not None:
        provided_full_payload_by_id[domain_commit.commit.id] = domain_commit
    full_payload_by_id: dict[UUID, ObjectInstanceGraphCommit] = {}
    identity_sidecar_by_id: dict[UUID, ObjectInstanceGraphCommitIdentitySidecar] = {}
    to_visit: list[UUID] = [head_commit_id]
    visited: set[UUID] = set()
    projected_head_commit: Commit | None = None
    identity_sidecar_hit_count = 0
    identity_sidecar_miss_count = 0
    identity_sidecar_inconsistent_count = 0
    full_body_identity_fallback_count = 0
    sidecar_read_started = time.monotonic()
    sidecar_read_elapsed_ms = 0
    full_body_fallback_elapsed_ms = 0

    while to_visit:
        commit_id = to_visit.pop()
        if commit_id in visited:
            continue
        visited.add(commit_id)

        if is_projected_domain_commit(commit_id):
            if commit_id == head_commit_id:
                projected_head_commit = None
            continue

        envelope = envelope_by_id.get(commit_id)
        if envelope is None:
            with commit_perf_span(
                phase=_oigi_history_trace_phase("minimal_read_domain_envelope"),
                category=_OIGI_HISTORY_TRACE_CATEGORY,
                metadata={"domain_commit_id": str(commit_id)},
            ):
                envelope = await store.get_commit_envelope(
                    branch_id=domain_branch_id,
                    projection_hash=domain_projection_hash,
                    commit_id=commit_id,
                )
            if envelope is None:
                with commit_perf_span(
                    phase=_oigi_history_trace_phase(
                        "minimal_read_domain_body_for_envelope"
                    ),
                    category=_OIGI_HISTORY_TRACE_CATEGORY,
                    metadata={"domain_commit_id": str(commit_id)},
                ):
                    payload = await store.get_commit(
                        branch_id=domain_branch_id,
                        projection_hash=domain_projection_hash,
                        commit_id=commit_id,
                    )
                if payload is None:
                    raise RuntimeError(
                        "Missing domain commit while projecting OIG identity "
                        + "history plane: "
                        + f"branch_id={domain_branch_id} "
                        + f"projection_hash={domain_projection_hash} "
                        + f"commit_id={commit_id}"
                    )
                full_payload_by_id[commit_id] = payload
                envelope = object_instance_graph_commit_envelope_from_commit(
                    branch_id=domain_branch_id,
                    projection_hash=domain_projection_hash,
                    commit=payload,
                )
            envelope_by_id[commit_id] = envelope

        envelope = await _canonicalize_domain_commit_envelope_identity_for_history(
            store=store,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            object_instance_graph_identity=object_instance_graph_identity,
            domain_commit_envelope=envelope,
        )
        envelope_by_id[commit_id] = envelope

        with disable_change_tracking_hooks():
            with disable_autobind():
                history_commit_id = _history_commit_id(
                    lane_id=lane_id,
                    domain_commit_id=commit_id,
                )
                history_commit = Commit(
                    id=history_commit_id,
                    lane_id=lane_id,
                    key=str(commit_id),
                    author_id=resolve_meta_author_id(envelope.author_id),
                    created_at=envelope.created_at,
                    status=CommitStatus(envelope.status),
                )
                lane.commits.append(history_commit)
                register(history_commit)

                for parent_domain_commit_id in envelope.parent_commit_ids:
                    parent_commit_id = _history_commit_id(
                        lane_id=lane_id,
                        domain_commit_id=parent_domain_commit_id,
                    )
                    commit_parent_id = stable_commit_parent_id(
                        commit_id=history_commit_id,
                        parent_commit_id=parent_commit_id,
                    )
                    commit_parent = CommitParent(
                        id=commit_parent_id,
                        commit_id=history_commit_id,
                        parent_commit_id=parent_commit_id,
                    )
                    history_commit.commit_parents.append(commit_parent)
                    register(commit_parent)

                oig_commit = ObjectInstanceGraphCommit(
                    id=stable_object_instance_graph_commit_id(
                        object_instance_graph_identity_id=(
                            object_instance_graph_identity_id
                        ),
                        commit_id=commit_id,
                    ),
                    object_instance_graph_identity_id=(
                        object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=envelope.object_instance_graph_id,
                    commit=history_commit,
                    commit_id=history_commit.id,
                    object_instance_graph_key=envelope.object_instance_graph_key,
                    object_instance_graph_name=envelope.object_instance_graph_name,
                    object_instance_graph_description=(
                        envelope.object_instance_graph_description
                    ),
                    root_class_config_id=envelope.root_class_config_id,
                    root_source_object_id=envelope.root_source_object_id,
                    graph_hash_pre=envelope.graph_hash_pre,
                    graph_hash_post=envelope.graph_hash_post,
                    source_language=CodeLanguage(envelope.source_language),
                    projection_hash=envelope.projection_hash,
                    object_instance_graph_changes=[],
                )
                object_instance_graph_identity.object_instance_graph_commits.append(
                    oig_commit
                )
                register(oig_commit)

        if commit_id == head_commit_id:
            projected_head_commit = history_commit

        full_payload = full_payload_by_id.get(commit_id)
        if full_payload is not None:
            project_class_instance_identities(
                _oigi_history_domain_commit_class_instance_ids(full_payload)
            )
        else:
            identity_sidecar = identity_sidecar_by_id.get(commit_id)
            if identity_sidecar is None:
                read_started = time.monotonic()
                with commit_perf_span(
                    phase=_oigi_history_trace_phase("minimal_read_identity_sidecar"),
                    category=_OIGI_HISTORY_TRACE_CATEGORY,
                    metadata={"domain_commit_id": str(commit_id)},
                ):
                    identity_sidecar = await store.get_commit_identity_sidecar(
                        branch_id=domain_branch_id,
                        projection_hash=domain_projection_hash,
                        commit_id=commit_id,
                    )
                sidecar_read_elapsed_ms += max(
                    int((time.monotonic() - read_started) * 1000),
                    0,
                )
                if identity_sidecar is not None:
                    identity_sidecar_by_id[commit_id] = identity_sidecar

            sidecar_projected = False
            if identity_sidecar is not None:
                sidecar_projected = _oigi_history_sidecar_matches(
                    object_instance_graph_identity_id=(
                        object_instance_graph_identity_id
                    ),
                    domain_commit_envelope=envelope,
                    identity_sidecar=identity_sidecar,
                )
                if sidecar_projected:
                    project_class_instance_identities(
                        identity_sidecar.class_instance_ids
                    )
                    identity_sidecar_hit_count += 1
                else:
                    identity_sidecar_inconsistent_count += 1
            else:
                identity_sidecar_miss_count += 1

            if not sidecar_projected:
                fallback_started = time.monotonic()
                full_payload = provided_full_payload_by_id.get(commit_id)
                if full_payload is None:
                    with commit_perf_span(
                        phase=_oigi_history_trace_phase(
                            "minimal_read_domain_body_for_identity"
                        ),
                        category=_OIGI_HISTORY_TRACE_CATEGORY,
                        metadata={"domain_commit_id": str(commit_id)},
                    ):
                        full_payload = await store.get_commit(
                            branch_id=domain_branch_id,
                            projection_hash=domain_projection_hash,
                            commit_id=commit_id,
                        )
                full_body_fallback_elapsed_ms += max(
                    int((time.monotonic() - fallback_started) * 1000),
                    0,
                )
                if full_payload is not None:
                    full_body_identity_fallback_count += 1
                    full_payload_by_id[commit_id] = full_payload
                    project_class_instance_identities(
                        _oigi_history_domain_commit_class_instance_ids(full_payload)
                    )

        for parent_id in envelope.parent_commit_ids:
            if parent_id not in visited:
                to_visit.append(parent_id)

    if projected_head_commit is not None:
        lane.head_commit = projected_head_commit
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_minimal_projection_fast_path_count"] = 1
        perf_ms[f"{perf_metric_prefix}_minimal_projection_fallback_count"] = 0
        perf_ms[f"{perf_metric_prefix}_minimal_projection_object_count"] = len(
            objects_by_id
        )
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_hit_count"] = (
            identity_sidecar_hit_count
        )
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_miss_count"] = (
            identity_sidecar_miss_count
        )
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_inconsistent_count"] = (
            identity_sidecar_inconsistent_count
        )
        perf_ms[f"{perf_metric_prefix}_full_body_identity_fallback_count"] = (
            full_body_identity_fallback_count
        )
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_read_ms"] = max(
            sidecar_read_elapsed_ms,
            0,
        )
        perf_ms[f"{perf_metric_prefix}_full_body_identity_fallback_ms"] = max(
            full_body_fallback_elapsed_ms,
            0,
        )
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_project_history_minimal_total_ms",
            started=sidecar_read_started,
        )
    return _OigiHistoryProjectionResult(
        change_set=ORMChangeSet(
            collected_at=datetime.now(timezone.utc),
            created_ids=frozenset(created_ids),
            touched_ids=frozenset(touched_ids),
            deleted_ids=frozenset(),
            objects_by_id=objects_by_id,
            scalar_fields_by_id={},
            list_fields_by_id={},
            scalar_baseline={},
            list_baseline={},
            list_added={},
            list_removed={},
        ),
        session=None,
        root_identity=object_instance_graph_identity,
    )


async def _project_oigi_history_projection(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    oigi_opg: ObjectProjectionGraph,
    root_class_config_id: UUID,
    object_projection_graph_identity_id: UUID,
    object_instance_graph_identity_id: UUID,
    domain_oig_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    lane_id: UUID,
    head_commit_id: UUID,
    store: FSCommitStore,
    domain_commit: ObjectInstanceGraphCommit | None = None,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "run_commit_reaction_oigi",
) -> _OigiHistoryProjectionResult:
    trace_metadata = _oigi_history_trace_metadata(
        domain_oig_id=domain_oig_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=(
            domain_commit_envelope.commit_id
            if domain_commit_envelope is not None
            else (domain_commit.commit.id if domain_commit is not None else None)
        ),
        lane_id=lane_id,
    )
    try:
        with commit_perf_span(
            phase=_oigi_history_trace_phase("project_history_minimal_change_set"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            return await _project_oigi_history_minimal_change_set(
                index=index,
                before_oig=before_oig,
                root_class_config_id=root_class_config_id,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                domain_oig_id=domain_oig_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                lane_id=lane_id,
                head_commit_id=head_commit_id,
                store=store,
                domain_commit=domain_commit,
                domain_commit_envelope=domain_commit_envelope,
                perf_ms=perf_ms,
                perf_metric_prefix=perf_metric_prefix,
            )
    except _OigiHistoryDirectProjectionUnsupported as exc:
        if perf_ms is not None:
            perf_ms[f"{perf_metric_prefix}_minimal_projection_fast_path_count"] = 0
            perf_ms[f"{perf_metric_prefix}_minimal_projection_fallback_count"] = 1
        with commit_perf_span(
            phase=_oigi_history_trace_phase("project_history_minimal_fallback"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={**trace_metadata, "reason": str(exc)},
        ):
            pass

    with commit_perf_span(
        phase=_oigi_history_trace_phase("reify_oigi_session"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        session = reify_oig_session(
            index=index,
            opg=oigi_opg,
            oig=before_oig,
            branch_id=domain_oig_id,
        )
    root_identity = session.imap_get(
        ObjectInstanceGraphIdentity,
        object_instance_graph_identity_id,
    )
    with scoped_change_collection() as collector:
        if root_identity is None:
            root_identity = _build_oigi_root_identity(
                index=index,
                before_oig=before_oig,
                root_class_config_id=root_class_config_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                domain_oig_id=domain_oig_id,
            )
            _ = _bind_new(session, root_identity)
        else:
            _ensure_oigi_root_identity_boundary(
                object_instance_graph_identity=root_identity,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                domain_oig_id=domain_oig_id,
            )

        with disallow_push(), allow_domain_create():
            with commit_perf_span(
                phase=_oigi_history_trace_phase("project_history_direct"),
                category=_OIGI_HISTORY_TRACE_CATEGORY,
                metadata=trace_metadata,
            ):
                await _project_oigi_history_direct(
                    session=session,
                    object_instance_graph_identity=root_identity,
                    domain_branch_id=domain_branch_id,
                    domain_projection_hash=domain_projection_hash,
                    lane_id=lane_id,
                    head_commit_id=head_commit_id,
                    store=store,
                    domain_commit=domain_commit,
                    domain_commit_envelope=domain_commit_envelope,
                    perf_ms=perf_ms,
                    perf_metric_prefix=perf_metric_prefix,
                )
        return _OigiHistoryProjectionResult(
            change_set=collector.snapshot(),
            session=session,
            root_identity=root_identity,
        )


def _opg_class_config_ids(*, opg: ObjectProjectionGraph) -> frozenset[UUID]:
    return frozenset(node.class_config_id for node in opg.object_projection_graph_nodes)


def _before_class_instances_by_id(
    before_oig: ObjectInstanceGraph,
) -> dict[UUID, ClassInstance]:
    out: dict[UUID, ClassInstance] = {}
    for class_instance in before_oig.class_instances:
        if class_instance.id is not None:
            out[class_instance.id] = class_instance
    return out


def _build_oigi_history_direct_projection_context(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    oigi_opg: ObjectProjectionGraph,
) -> _OigiHistoryDirectProjectionContext:
    static_context = _build_oigi_history_static_direct_projection_context(
        index=index,
        oigi_opg=oigi_opg,
    )
    return _OigiHistoryDirectProjectionContext(
        class_configs_by_id=static_context.class_configs_by_id,
        relationship_attribute_ids_by_cc_id=(
            static_context.relationship_attribute_ids_by_cc_id
        ),
        include_relationship_attribute_ids_by_cc_id=(
            static_context.include_relationship_attribute_ids_by_cc_id
        ),
        opg_class_config_ids=static_context.opg_class_config_ids,
        before_class_instances_by_id=_before_class_instances_by_id(before_oig),
    )


def _build_oigi_history_static_direct_projection_context(
    *,
    index: MetaGraphRuntimeIndex,
    oigi_opg: ObjectProjectionGraph,
) -> _OigiHistoryStaticDirectProjectionContext:
    opg_class_config_ids = _opg_class_config_ids(opg=oigi_opg)
    cache_key = _oigi_history_static_direct_projection_context_cache_key(
        index=index,
        oigi_opg=oigi_opg,
        opg_class_config_ids=opg_class_config_ids,
    )
    cached = _OIGI_STATIC_DIRECT_CONTEXT_CACHE.get(cache_key)
    if cached is not None:
        _OIGI_STATIC_DIRECT_CONTEXT_CACHE.move_to_end(cache_key)
        return cached

    class_configs_by_id = dict(index.class_configs_by_id)
    relationships_by_id = dict(index.relationships_by_id)
    static_context = _OigiHistoryStaticDirectProjectionContext(
        class_configs_by_id=class_configs_by_id,
        relationship_attribute_ids_by_cc_id=(
            build_relationship_attribute_config_ids_by_class_config_id(
                class_configs_by_id=class_configs_by_id,
                relationships_by_id=relationships_by_id,
            )
        ),
        include_relationship_attribute_ids_by_cc_id=(
            build_include_relationship_attribute_config_ids_by_class_config_id(
                object_projection_graph=oigi_opg,
                class_configs_by_id=class_configs_by_id,
                relationships_by_id=relationships_by_id,
            )
        ),
        opg_class_config_ids=opg_class_config_ids,
    )
    _OIGI_STATIC_DIRECT_CONTEXT_CACHE[cache_key] = static_context
    if len(_OIGI_STATIC_DIRECT_CONTEXT_CACHE) > _OIGI_STATIC_DIRECT_CONTEXT_CACHE_LIMIT:
        _OIGI_STATIC_DIRECT_CONTEXT_CACHE.popitem(last=False)
    return static_context


def _oigi_history_static_direct_projection_context_cache_key(
    *,
    index: MetaGraphRuntimeIndex,
    oigi_opg: ObjectProjectionGraph,
    opg_class_config_ids: frozenset[UUID],
) -> _OigiHistoryStaticDirectContextCacheKey:
    return (
        id(index),
        id(index.class_configs_by_id),
        id(index.relationships_by_id),
        id(oigi_opg),
        len(index.class_configs_by_id),
        len(index.relationships_by_id),
        tuple(sorted(str(item) for item in opg_class_config_ids)),
    )


def _build_oigi_history_changed_class_instances(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    oigi_opg: ObjectProjectionGraph,
    projection: _OigiHistoryProjectionResult,
) -> list[ClassInstance]:
    if before_oig.id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct projection requires before OIG id."
        )
    class_configs_by_id = dict(index.class_configs_by_id)
    relationship_attribute_ids_by_cc_id = (
        build_relationship_attribute_config_ids_by_class_config_id(
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=dict(index.relationships_by_id),
        )
    )
    include_relationship_attribute_ids_by_cc_id = (
        build_include_relationship_attribute_config_ids_by_class_config_id(
            object_projection_graph=oigi_opg,
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=dict(index.relationships_by_id),
        )
    )
    opg_class_config_ids = _opg_class_config_ids(opg=oigi_opg)
    changed_source_object_ids = (
        projection.change_set.created_ids | projection.change_set.touched_ids
    ) - projection.change_set.deleted_ids

    changed_class_instances: list[ClassInstance] = []
    for source_object_id in sorted(changed_source_object_ids, key=str):
        source = projection.change_set.objects_by_id.get(source_object_id)
        if source is None:
            continue
        try:
            class_config_id = source.try_class_config_id()
        except Exception as exc:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct projection source object lacks class_config_id: "
                f"source_object_id={source_object_id}"
            ) from exc
        if class_config_id is None or class_config_id not in opg_class_config_ids:
            continue
        class_config = class_configs_by_id.get(class_config_id)
        if class_config is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct projection ClassConfig missing from runtime index: "
                f"class_config_id={class_config_id}"
            )
        try:
            changed_class_instances.append(
                build_class_instance(
                    object_instance_graph_id=before_oig.id,
                    class_config=class_config,
                    class_configs_by_id=class_configs_by_id,
                    source=source,
                    enum_option_resolver=default_meta_enum_option_resolver,
                    relationship_attribute_config_ids=(
                        relationship_attribute_ids_by_cc_id.get(class_config_id)
                    ),
                    include_relationship_attribute_config_ids=(
                        include_relationship_attribute_ids_by_cc_id.get(class_config_id)
                    ),
                )
            )
        except ClassInstanceBuildError as exc:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct projection could not build changed class instance: "
                f"source_object_id={source_object_id} class_config_id={class_config_id}"
            ) from exc
    return changed_class_instances


def _build_oigi_history_changed_class_instance_targets(
    *,
    context: _OigiHistoryDirectProjectionContext,
    before_oig: ObjectInstanceGraph,
    projection: _OigiHistoryProjectionResult,
) -> _OigiHistoryDirectClassInstanceTargets:
    if before_oig.id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection requires before OIG id."
        )

    changed_source_object_ids = (
        projection.change_set.created_ids | projection.change_set.touched_ids
    ) - projection.change_set.deleted_ids
    deleted_class_instances = _build_oigi_history_deleted_class_instances(
        before_oig=before_oig,
        opg_class_config_ids=context.opg_class_config_ids,
        deleted_source_object_ids=projection.change_set.deleted_ids,
    )

    targets: list[_OigiHistoryChangedClassInstanceTarget] = []
    for source_object_id in sorted(changed_source_object_ids, key=str):
        source = projection.change_set.objects_by_id.get(source_object_id)
        if source is None:
            continue
        if not isinstance(source, ModelIntrospection):
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection requires ModelIntrospection: "
                f"source_object_id={source_object_id}"
            )
        try:
            class_config_id = source.try_class_config_id()
        except Exception as exc:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection source object lacks "
                f"class_config_id: source_object_id={source_object_id}"
            ) from exc
        if (
            class_config_id is None
            or class_config_id not in context.opg_class_config_ids
        ):
            continue
        class_config = context.class_configs_by_id.get(class_config_id)
        if class_config is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection ClassConfig missing from "
                f"runtime index: class_config_id={class_config_id}"
            )
        class_instance_id = stable_class_instance_id(
            object_instance_graph_id=before_oig.id,
            class_config_id=class_config.id,
            source_object_id=source.id,
        )
        with disable_change_tracking_hooks():
            with disable_autobind():
                class_instance = ClassInstance(
                    id=class_instance_id,
                    object_instance_graph_id=before_oig.id,
                    class_config_id=class_config.id,
                    source_object_id=source.id,
                    class_config=class_config,
                )
        targets.append(
            _OigiHistoryChangedClassInstanceTarget(
                source=source,
                class_config=class_config,
                class_instance=class_instance,
                attribute_plan=plan_class_instance_attribute_links(
                    class_config=class_config,
                    relationship_attribute_config_ids=(
                        context.relationship_attribute_ids_by_cc_id.get(class_config_id)
                    ),
                    include_relationship_attribute_config_ids=(
                        context.include_relationship_attribute_ids_by_cc_id.get(
                            class_config_id
                        )
                    ),
                ),
            )
        )
    return _OigiHistoryDirectClassInstanceTargets(
        changed_targets=tuple(targets),
        deleted_class_instances=deleted_class_instances,
    )


def _build_oigi_history_deleted_class_instances(
    *,
    before_oig: ObjectInstanceGraph,
    opg_class_config_ids: frozenset[UUID],
    deleted_source_object_ids: frozenset[UUID],
) -> tuple[ClassInstance, ...]:
    if not deleted_source_object_ids:
        return ()

    matches_by_source_id: dict[UUID, list[ClassInstance]] = {}
    for class_instance in before_oig.class_instances:
        source_object_id = class_instance.source_object_id
        class_config_id = class_instance.class_config_id
        if (
            source_object_id is None
            or source_object_id not in deleted_source_object_ids
        ):
            continue
        if class_config_id is None or class_config_id not in opg_class_config_ids:
            continue
        if class_instance.id is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection delete target lacks "
                f"ClassInstance.id: source_object_id={source_object_id}"
            )
        if class_instance.id == before_oig.root_class_instance_id:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection cannot delete the OIG root: "
                f"source_object_id={source_object_id}"
            )
        matches_by_source_id.setdefault(source_object_id, []).append(class_instance)

    deleted_class_instances: list[ClassInstance] = []
    for source_object_id in sorted(deleted_source_object_ids, key=str):
        matches = matches_by_source_id.get(source_object_id, [])
        if not matches:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection could not resolve deleted "
                f"source object from pre-state OIG: source_object_id={source_object_id}"
            )
        if len(matches) > 1:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection found ambiguous deleted "
                f"source object target: source_object_id={source_object_id}"
            )
        deleted_class_instances.append(matches[0])
    return tuple(deleted_class_instances)


def _project_oigi_history_changed_targets(
    *,
    targets: Iterable[_OigiHistoryChangedClassInstanceTarget],
    context: _OigiHistoryDirectProjectionContext,
    before_state_row_maps: Mapping[UUID, tuple[CommitStateRow, ...]],
    created_at: datetime,
    perf_ms: dict[str, int] | None,
    perf_metric_prefix: str,
) -> tuple[_OigiHistoryProjectedChangedClassInstance, ...]:
    projected: list[_OigiHistoryProjectedChangedClassInstance] = []
    for target in targets:
        projection = _project_oigi_history_changed_target(
            target=target,
            before_class_instance=context.before_class_instances_by_id.get(
                target.class_instance.id
            ),
            before_state_rows=before_state_row_maps.get(
                target.class_instance.id,
                (),
            ),
            class_configs_by_id=context.class_configs_by_id,
            created_at=created_at,
            perf_ms=perf_ms,
            perf_metric_prefix=perf_metric_prefix,
        )
        if projection is None:
            return ()
        projected.append(projection)
    return tuple(projected)


def _post_state_rows_by_changed_projection(
    projections: Iterable[_OigiHistoryProjectedChangedClassInstance],
) -> dict[UUID, tuple[CommitStateRow, ...]]:
    rows_by_id: dict[UUID, tuple[CommitStateRow, ...]] = {}
    for projection in projections:
        class_instance_id = projection.target.class_instance.id
        if class_instance_id is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection requires ClassInstance.id."
            )
        rows_by_id[class_instance_id] = projection.post_state_rows
    return rows_by_id


def _project_oigi_history_changed_target(
    *,
    target: _OigiHistoryChangedClassInstanceTarget,
    before_class_instance: ClassInstance | None,
    before_state_rows: tuple[CommitStateRow, ...],
    class_configs_by_id: Mapping[UUID, ClassConfig],
    created_at: datetime,
    perf_ms: dict[str, int] | None,
    perf_metric_prefix: str,
) -> _OigiHistoryProjectedChangedClassInstance | None:
    class_header = _build_oigi_history_class_instance_change_header(
        before_class_instance=before_class_instance,
        class_instance=target.class_instance,
        created_at=created_at,
    )
    if class_header is None:
        return None
    class_instance_change, operation = class_header
    with commit_perf_span(
        phase=_oigi_history_trace_phase(
            "build_direct_source_state_rows.before_attribute_fingerprints"
        ),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        before_attribute_fingerprints_by_config_id = (
            _attribute_fingerprints_by_config_id(before_state_rows)
        )
    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_source_row_before_attribute_fingerprint_count",
        value=len(before_attribute_fingerprints_by_config_id),
    )
    source_projection = _build_oigi_changed_target_source_state_rows_and_changes(
        target=target,
        before_class_instance=before_class_instance,
        before_attribute_fingerprints_by_config_id=before_attribute_fingerprints_by_config_id,
        class_instance_change=class_instance_change,
        class_configs_by_id=class_configs_by_id,
        created_at=created_at,
        perf_ms=perf_ms,
        perf_metric_prefix=perf_metric_prefix,
    )
    if source_projection is None:
        return None
    if (
        operation == ChangeType.update
        and not class_instance_change.change.change_deltas
        and not class_instance_change.attribute_changes
    ):
        return _OigiHistoryProjectedChangedClassInstance(
            target=target,
            post_state_rows=source_projection.post_state_rows,
            class_instance_change=None,
            class_instance_body_draft=None,
        )
    return _OigiHistoryProjectedChangedClassInstance(
        target=target,
        post_state_rows=source_projection.post_state_rows,
        class_instance_change=class_instance_change,
        class_instance_body_draft=source_projection.class_instance_body_draft,
    )


def _build_oigi_changed_target_source_state_rows_and_changes(
    *,
    target: _OigiHistoryChangedClassInstanceTarget,
    before_class_instance: ClassInstance | None,
    before_attribute_fingerprints_by_config_id: Mapping[UUID, str],
    class_instance_change: ClassInstanceChange,
    class_configs_by_id: Mapping[UUID, ClassConfig],
    created_at: datetime,
    perf_ms: dict[str, int] | None,
    perf_metric_prefix: str,
) -> _OigiHistoryChangedTargetSourceProjection | None:
    class_config = target.class_config
    class_instance = target.class_instance
    if class_config.id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection requires ClassConfig.id."
        )
    if class_instance.id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection requires ClassInstance.id."
        )
    with commit_perf_span(
        phase=_oigi_history_trace_phase(
            "build_direct_source_state_rows.before_attribute_index"
        ),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        before_attributes_by_id = (
            _oigi_attributes_by_id(before_class_instance.attributes)
            if before_class_instance is not None
            else {}
        )
    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_source_row_before_attribute_index_count",
        value=len(before_attributes_by_id),
    )
    rows: list[CommitStateRow] = [
        CommitStateRow(
            kind="NODE",
            key=str(class_config.id),
            value=str(class_instance.id),
        )
    ]
    attribute_rows: set[tuple[str, str]] = set()
    changed_attribute_ids: set[UUID] = set()
    direct_linked_edge_ids: set[UUID] = set()
    attribute_changes: list[tuple[tuple[str, str], AttributeChange]] = []
    attribute_change_body_drafts: list[
        tuple[tuple[str, str], OigCommitBodyAttributeChangeDraft]
    ] = []
    primitive_attribute_change_drafts: list[
        tuple[tuple[str, str], _OigiPrimitiveLeafAttributeChangeDraft]
    ] = []
    for link in target.attribute_plan.attribute_links:
        _increment_perf(
            perf_ms,
            f"{perf_metric_prefix}_source_row_attribute_link_count",
        )
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "build_direct_source_state_rows.attribute_plan_iteration"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
            attr_cfg = _oigi_attribute_config_from_link(link=link)
        if attr_cfg is None:
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_source_row_attribute_link_without_config_count",
            )
            continue
        if attr_cfg.id is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection requires AttributeConfig.id: "
                f"class_config_id={class_config.id} attribute_name={attr_cfg.name!r}"
            )
        if attr_cfg.is_virtual:
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_source_row_virtual_attribute_skip_count",
            )
            continue
        if attr_cfg.id in target.attribute_plan.relationship_attribute_config_ids:
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_source_row_relationship_attribute_skip_count",
            )
            continue

        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "build_direct_source_state_rows.source_value_resolution"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
            found, raw_value = target.source.try_attribute_value(attr_cfg)
        if not found:
            if attr_cfg.default_value is not None:
                _increment_perf(
                    perf_ms,
                    f"{perf_metric_prefix}_source_row_defaulted_attribute_count",
                )
                raw_value = _parse_oigi_default_attribute_value(attr_cfg)
            elif (
                attr_cfg.is_required
                or attr_cfg.id in target.attribute_plan.required_fk_attribute_config_ids
            ):
                raise _OigiHistoryDirectProjectionUnsupported(
                    "OIGI direct source-row projection source object is missing "
                    f"required attribute: class_config_id={class_config.id} "
                    f"attribute_name={attr_cfg.name!r}"
                )
            else:
                _increment_perf(
                    perf_ms,
                    f"{perf_metric_prefix}_source_row_optional_attribute_skip_count",
                )
                continue
        attribute_id = stable_attribute_id(
            owner_key=target.source.id,
            attribute_config_id=attr_cfg.id,
        )
        if (
            before_class_instance is not None
            and attribute_id not in before_attributes_by_id
            and attr_cfg.id not in before_attribute_fingerprints_by_config_id
        ):
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection cannot infer Attribute "
                "pre-state from ClassInstance existence alone: "
                f"class_instance_id={class_instance.id} "
                f"attribute_config_id={attr_cfg.id}"
            )
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "build_direct_source_state_rows.emit_primitive_leaf_source_row"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
            primitive_emission = _try_emit_oigi_model_free_primitive_leaf_source_row(
                owner_key=target.source.id,
                attribute_config=attr_cfg,
                value=raw_value,
                before_attributes_by_id=before_attributes_by_id,
                before_attribute_fingerprints_by_config_id=(
                    before_attribute_fingerprints_by_config_id
                ),
                created_at=created_at,
            )
        if primitive_emission is not _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED:
            emission = cast(
                _OigiPrimitiveLeafSourceRowEmission,
                primitive_emission,
            )
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_source_row_model_free_primitive_attribute_count",
            )
            changed_attribute_ids.add(emission.attribute_id)
            attribute_rows.add(
                (str(emission.attribute_config_id), emission.value_fingerprint)
            )
            if emission.attribute_change_draft is None:
                if emission.reused_before_fingerprint:
                    _increment_perf(
                        perf_ms,
                        (
                            f"{perf_metric_prefix}_source_row_model_free_primitive_"
                            "reused_before_fingerprint_count"
                        ),
                    )
                if (
                    emission.attribute_id not in before_attributes_by_id
                    and not emission.row_backed_before_attribute
                ):
                    _record_oigi_direct_source_row_projection_fallback(
                        perf_ms,
                        perf_metric_prefix=perf_metric_prefix,
                        reason="unreplayable_new_primitive_attribute_row",
                        class_config=class_config,
                        class_instance=class_instance,
                        attribute_config=attr_cfg,
                    )
                    return None
                _increment_perf(
                    perf_ms,
                    f"{perf_metric_prefix}_source_row_model_free_primitive_no_change_count",
                )
                continue
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_source_row_model_free_primitive_attribute_change_count",
            )
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_source_row_model_free_primitive_change_draft_count",
            )
            primitive_attribute_change_drafts.append(
                (
                    (str(emission.attribute_config_id), str(emission.attribute_id)),
                    emission.attribute_change_draft,
                )
            )
            continue
        try:
            with commit_perf_span(
                phase=_oigi_history_trace_phase(
                    "build_direct_source_state_rows.build_attribute_value"
                ),
                category=_OIGI_HISTORY_TRACE_CATEGORY,
                metadata={},
            ):
                attribute = _try_build_oigi_primitive_leaf_attribute(
                    owner_key=target.source.id,
                    attribute_config=attr_cfg,
                    value=raw_value,
                )
                if attribute is None:
                    _increment_perf(
                        perf_ms,
                        f"{perf_metric_prefix}_source_row_generic_attribute_builder_count",
                    )
                    attribute = build_attribute(
                        owner_key=target.source.id,
                        attribute_config=attr_cfg,
                        value=raw_value,
                        class_configs_by_id=dict(class_configs_by_id),
                        enum_option_resolver=default_meta_enum_option_resolver,
                    )
                else:
                    _increment_perf(
                        perf_ms,
                        f"{perf_metric_prefix}_source_row_primitive_attribute_fast_path_count",
                    )
        except AttributeBuildError as exc:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection could not build attribute "
                f"value: class_config_id={class_config.id} "
                f"attribute_name={attr_cfg.name!r}"
            ) from exc
        if attribute.id is None:
            _record_oigi_direct_source_row_projection_fallback(
                perf_ms,
                perf_metric_prefix=perf_metric_prefix,
                reason="built_attribute_without_id",
                class_config=class_config,
                class_instance=class_instance,
                attribute_config=attr_cfg,
            )
            return None
        _increment_perf(
            perf_ms,
            f"{perf_metric_prefix}_source_row_built_attribute_count",
        )
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "build_direct_source_state_rows.link_attribute"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
            edge = _try_append_oigi_direct_attribute_edge(
                class_instance=class_instance,
                attribute=attribute,
                direct_edge_ids=direct_linked_edge_ids,
            )
            if edge is None:
                _increment_perf(
                    perf_ms,
                    f"{perf_metric_prefix}_source_row_link_attribute_fallback_count",
                )
                _ = link_attribute(class_instance, attribute)
            else:
                _increment_perf(
                    perf_ms,
                    f"{perf_metric_prefix}_source_row_direct_attribute_link_count",
                )
        changed_attribute_ids.add(attribute.id)
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "build_direct_source_state_rows.fingerprint_current"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
            value_fingerprint = fingerprint_attribute_value(attribute.value_root)
        attribute_rows.add((str(attr_cfg.id), value_fingerprint))
        before_attribute = before_attributes_by_id.get(attribute.id)
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "build_direct_source_state_rows.fingerprint_before"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
            before_value_fingerprint = before_attribute_fingerprints_by_config_id.get(
                attribute.attribute_config_id
            )
            if before_value_fingerprint is None and before_attribute is not None:
                before_value_fingerprint = fingerprint_attribute_value(
                    before_attribute.value_root
                )
        row_backed_before_attribute = (
            before_attribute is None and before_value_fingerprint is not None
        )
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "build_direct_source_state_rows.build_attribute_change"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
            attribute_change_result = (
                _try_build_oigi_history_primitive_leaf_attribute_change(
                    before_attribute=before_attribute,
                    before_value_fingerprint=before_value_fingerprint,
                    attribute=attribute,
                    value_fingerprint=value_fingerprint,
                    parent=class_instance_change,
                    created_at=created_at,
                    row_backed_before_attribute=row_backed_before_attribute,
                )
            )
            if (
                attribute_change_result
                is _OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED
            ):
                _increment_perf(
                    perf_ms,
                    f"{perf_metric_prefix}_source_row_generic_attribute_change_builder_count",
                )
                attribute_change = (
                    None
                    if row_backed_before_attribute
                    else _build_oigi_history_attribute_change(
                        before_attribute=before_attribute,
                        before_value_fingerprint=before_value_fingerprint,
                        attribute=attribute,
                        value_fingerprint=value_fingerprint,
                        parent=class_instance_change,
                        created_at=created_at,
                    )
                )
            else:
                _increment_perf(
                    perf_ms,
                    f"{perf_metric_prefix}_source_row_primitive_attribute_change_fast_path_count",
                )
                attribute_change = cast(
                    AttributeChange | None,
                    attribute_change_result,
                )
        if attribute_change is None:
            if (
                before_attribute is None and not row_backed_before_attribute
            ) or before_value_fingerprint != value_fingerprint:
                _record_oigi_direct_source_row_projection_fallback(
                    perf_ms,
                    perf_metric_prefix=perf_metric_prefix,
                    reason="unreplayable_attribute_row",
                    class_config=class_config,
                    class_instance=class_instance,
                    attribute_config=attr_cfg,
                )
                return None
            continue
        attribute_changes.append(
            ((str(attribute.attribute_config_id), str(attribute.id)), attribute_change)
        )
        attribute_change_body_drafts.append(
            (
                (str(attribute.attribute_config_id), str(attribute.id)),
                oig_commit_body_attribute_change_draft_from_change(attribute_change),
            )
        )

    if set(before_attributes_by_id) - changed_attribute_ids:
        _record_oigi_direct_source_row_projection_fallback(
            perf_ms,
            perf_metric_prefix=perf_metric_prefix,
            reason="changed_target_missing_existing_attribute",
            class_config=class_config,
            class_instance=class_instance,
            attribute_config=None,
        )
        return None

    with commit_perf_span(
        phase=_oigi_history_trace_phase(
            "build_direct_source_state_rows.assemble_primitive_leaf_change_drafts"
        ),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        for sort_key, draft in sorted(
            primitive_attribute_change_drafts,
            key=lambda item: item[0],
        ):
            change_result = (
                _build_oigi_history_primitive_leaf_attribute_change_with_body_draft(
                    draft=draft,
                    parent=class_instance_change,
                )
            )
            attribute_changes.append((sort_key, change_result.attribute_change))
            attribute_change_body_drafts.append((sort_key, change_result.body_draft))
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_source_row_primitive_body_draft_direct_count",
            )
        _increment_perf(
            perf_ms,
            f"{perf_metric_prefix}_source_row_model_free_primitive_change_draft_assembled_count",
            value=len(primitive_attribute_change_drafts),
        )

    with commit_perf_span(
        phase=_oigi_history_trace_phase(
            "build_direct_source_state_rows.sort_rows_changes"
        ),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        class_instance_change.attribute_changes = [
            change
            for _sort_key, change in sorted(attribute_changes, key=lambda item: item[0])
        ]
        class_instance_body_draft = _build_oigi_commit_body_class_instance_change_draft(
            class_instance_change=class_instance_change,
            attribute_change_drafts=tuple(
                draft
                for _sort_key, draft in sorted(
                    attribute_change_body_drafts,
                    key=lambda item: item[0],
                )
            ),
        )
        _increment_perf(
            perf_ms,
            f"{perf_metric_prefix}_source_row_class_instance_body_draft_direct_count",
        )
        for attribute_config_id, value_fingerprint in sorted(attribute_rows):
            rows.append(
                CommitStateRow(
                    kind="ATTR",
                    key=str(class_instance.id),
                    value=f"{attribute_config_id}:{value_fingerprint}",
                )
            )
    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_source_row_state_row_count",
        value=len(rows),
    )
    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_source_row_attribute_change_count",
        value=len(class_instance_change.attribute_changes),
    )
    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_source_row_changed_target_direct_count",
    )
    return _OigiHistoryChangedTargetSourceProjection(
        post_state_rows=tuple(rows),
        class_instance_body_draft=class_instance_body_draft,
    )


def _record_oigi_direct_source_row_projection_fallback(
    perf_ms: dict[str, int] | None,
    *,
    perf_metric_prefix: str,
    reason: str,
    class_config: ClassConfig,
    class_instance: ClassInstance,
    attribute_config: AttributeConfig | None,
) -> None:
    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_source_row_{reason}_fallback_count",
    )
    _increment_perf(
        perf_ms,
        f"{perf_metric_prefix}_source_row_projection_fallback_count",
    )
    metadata: dict[str, object | None] = {
        "reason": reason,
        "class_config_id": (
            str(class_config.id) if class_config.id is not None else None
        ),
        "class_name": class_config.name,
        "class_fqn": class_config.class_fqn,
        "class_instance_id": (
            str(class_instance.id) if class_instance.id is not None else None
        ),
        "source_object_id": (
            str(class_instance.source_object_id)
            if class_instance.source_object_id is not None
            else None
        ),
    }
    if attribute_config is not None:
        metadata.update(
            {
                "attribute_config_id": (
                    str(attribute_config.id)
                    if attribute_config.id is not None
                    else None
                ),
                "attribute_name": attribute_config.name,
                "attribute_owner_key": attribute_config.owner_key,
                "attribute_type_kind": (
                    attribute_config.type_descriptor.kind.value
                    if attribute_config.type_descriptor is not None
                    and attribute_config.type_descriptor.kind is not None
                    else None
                ),
            }
        )
    with commit_perf_span(
        phase=_oigi_history_trace_phase("direct_source_row_projection_fallback"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=metadata,
    ):
        pass


def _try_build_oigi_primitive_leaf_attribute(
    *,
    owner_key: UUID,
    attribute_config: AttributeConfig,
    value: object,
) -> Attribute | None:
    type_descriptor = attribute_config.type_descriptor
    if (
        attribute_config.id is None
        or type_descriptor is None
        or type_descriptor.id is None
        or type_descriptor.kind != AttributeTypeDescriptorKind.primitive
        or type_descriptor.child_links
    ):
        return None

    attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config.id,
    )
    value_root_id = stable_attribute_value_id(
        parent_value_id=attribute_id,
        role="member",
        position=0,
        identity_key="root",
    )
    primitive_value = _oigi_primitive_leaf_json(value)
    with disable_change_tracking_hooks():
        with disable_autobind():
            value_root = AttributeValue(
                id=value_root_id,
                type_descriptor=type_descriptor,
                type_descriptor_id=type_descriptor.id,
                child_links=[],
                primitive_value=primitive_value,
            )
            return Attribute(
                id=attribute_id,
                owner_key=owner_key,
                attribute_config=attribute_config,
                attribute_config_id=attribute_config.id,
                value_root=value_root,
                value_root_id=value_root.id,
            )


def _try_emit_oigi_model_free_primitive_leaf_source_row(
    *,
    owner_key: UUID,
    attribute_config: AttributeConfig,
    value: object,
    before_attributes_by_id: Mapping[UUID, Attribute],
    before_attribute_fingerprints_by_config_id: Mapping[UUID, str],
    created_at: datetime,
) -> _OigiPrimitiveLeafSourceRowEmission | object:
    type_descriptor = attribute_config.type_descriptor
    attribute_config_id = attribute_config.id
    if (
        attribute_config_id is None
        or type_descriptor is None
        or type_descriptor.id is None
        or type_descriptor.kind != AttributeTypeDescriptorKind.primitive
        or type_descriptor.child_links
    ):
        return _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED

    attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config_id,
    )
    before_attribute = before_attributes_by_id.get(attribute_id)
    before_value = before_attribute.value_root if before_attribute is not None else None
    if before_value is not None and not _is_oigi_primitive_leaf_value(before_value):
        return _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED

    primitive_parts = _oigi_primitive_leaf_payload_parts(value)
    row_backed_before_fingerprint = before_attribute_fingerprints_by_config_id.get(
        attribute_config_id
    )
    row_backed_before_attribute = (
        before_attribute is None and row_backed_before_fingerprint is not None
    )
    operation = (
        ChangeType.update
        if (before_attribute is not None or row_backed_before_attribute)
        else ChangeType.create
    )
    if operation == ChangeType.update:
        if before_attribute is not None and before_value is None:
            return _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED
        if (
            before_attribute is not None
            and before_attribute.attribute_config_id != attribute_config_id
        ):
            return _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED
        before_fingerprint = before_attribute_fingerprints_by_config_id.get(
            attribute_config_id
        ) or (
            fingerprint_attribute_value(before_value)
            if before_value is not None
            else None
        )
        if before_fingerprint is None:
            return _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED
        if (
            before_fingerprint is not None
            and before_value is not None
            and _oigi_attribute_value_primitive_payload(before_value)
            == primitive_parts.primitive_payload
        ):
            return _OigiPrimitiveLeafSourceRowEmission(
                attribute_id=attribute_id,
                attribute_config_id=attribute_config_id,
                value_fingerprint=before_fingerprint,
                attribute_change_draft=None,
                reused_before_fingerprint=True,
                row_backed_before_attribute=row_backed_before_attribute,
            )

        value_fingerprint = _oigi_primitive_leaf_value_fingerprint(
            type_descriptor=type_descriptor,
            primitive_value=primitive_parts.fingerprint_primitive_value,
        )
        if value_fingerprint is None:
            return _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED
        if before_fingerprint is not None and before_fingerprint == value_fingerprint:
            return _OigiPrimitiveLeafSourceRowEmission(
                attribute_id=attribute_id,
                attribute_config_id=attribute_config_id,
                value_fingerprint=value_fingerprint,
                attribute_change_draft=None,
                reused_before_fingerprint=row_backed_before_attribute,
                row_backed_before_attribute=row_backed_before_attribute,
            )
        if row_backed_before_attribute:
            value_change_draft = _OigiPrimitiveLeafValueChangeDraft(
                attribute_value_id=stable_attribute_value_id(
                    parent_value_id=attribute_id,
                    role="member",
                    position=0,
                    identity_key="root",
                ),
                operation=ChangeType.update,
                fields=(("primitive_value", primitive_parts.primitive_payload),),
                created_at=created_at,
            )
            return _OigiPrimitiveLeafSourceRowEmission(
                attribute_id=attribute_id,
                attribute_config_id=attribute_config_id,
                value_fingerprint=value_fingerprint,
                attribute_change_draft=_OigiPrimitiveLeafAttributeChangeDraft(
                    attribute_id=attribute_id,
                    attribute_config_id=attribute_config_id,
                    operation=ChangeType.update,
                    value_root_change=value_change_draft,
                    created_at=created_at,
                ),
                row_backed_before_attribute=row_backed_before_attribute,
            )
    else:
        value_fingerprint = _oigi_primitive_leaf_value_fingerprint(
            type_descriptor=type_descriptor,
            primitive_value=primitive_parts.fingerprint_primitive_value,
        )
        if value_fingerprint is None:
            return _OIGI_MODEL_FREE_PRIMITIVE_SOURCE_ROW_UNSUPPORTED

    value_change_draft = _oigi_primitive_leaf_attribute_value_change_draft_from_parts(
        before_value=before_value,
        value_id=(
            stable_attribute_value_id(
                parent_value_id=attribute_id,
                role="member",
                position=0,
                identity_key="root",
            )
            if operation == ChangeType.create
            else None
        ),
        primitive_payload=primitive_parts.primitive_payload,
        operation=operation,
        created_at=created_at,
    )
    if value_change_draft is None:
        return _OigiPrimitiveLeafSourceRowEmission(
            attribute_id=attribute_id,
            attribute_config_id=attribute_config_id,
            value_fingerprint=value_fingerprint,
            attribute_change_draft=None,
        )

    return _OigiPrimitiveLeafSourceRowEmission(
        attribute_id=attribute_id,
        attribute_config_id=attribute_config_id,
        value_fingerprint=value_fingerprint,
        attribute_change_draft=_OigiPrimitiveLeafAttributeChangeDraft(
            attribute_id=attribute_id,
            attribute_config_id=attribute_config_id,
            operation=operation,
            value_root_change=value_change_draft,
            created_at=created_at,
        ),
    )


def _try_append_oigi_direct_attribute_edge(
    *,
    class_instance: ClassInstance,
    attribute: Attribute,
    direct_edge_ids: set[UUID],
) -> ClassInstanceAttribute | None:
    class_instance_id = class_instance.id
    attribute_id = attribute.id
    if class_instance_id is None or attribute_id is None:
        return None

    # This fast path is only valid for the fresh ClassInstance created by the
    # OIGI direct source-row projection. If any edge exists outside this local
    # walk, defer to the public linker so repair/dedupe behavior remains intact.
    if len(class_instance.class_instance_attributes) != len(direct_edge_ids):
        return None

    edge_id = stable_class_instance_attribute_id(
        class_instance_id=class_instance_id,
        attribute_id=attribute_id,
    )
    if edge_id in direct_edge_ids:
        return None

    with disable_autobind():
        edge = ClassInstanceAttribute(
            id=edge_id,
            class_instance_id=class_instance_id,
            attribute=attribute,
            attribute_id=attribute_id,
        )
    class_instance.class_instance_attributes.append(edge)
    direct_edge_ids.add(edge_id)
    return edge


def _oigi_primitive_leaf_json(value: object) -> Json | None:
    return _oigi_primitive_leaf_json_from_parts(
        _oigi_primitive_leaf_payload_parts(value)
    )


def _oigi_primitive_leaf_payload_parts(
    value: object,
) -> _OigiPrimitiveLeafPayloadParts:
    if value is None:
        return _OigiPrimitiveLeafPayloadParts(
            primitive_payload=None,
            fingerprint_primitive_value=None,
        )
    payload = _oigi_json_value(value)
    if isinstance(payload, dict):
        return _OigiPrimitiveLeafPayloadParts(
            primitive_payload=payload,
            fingerprint_primitive_value=payload,
        )
    return _OigiPrimitiveLeafPayloadParts(
        primitive_payload=payload,
        fingerprint_primitive_value={"value": payload},
    )


def _oigi_primitive_leaf_json_from_parts(
    parts: _OigiPrimitiveLeafPayloadParts,
) -> Json | None:
    primitive_value = parts.fingerprint_primitive_value
    if primitive_value is None:
        return None
    if not isinstance(primitive_value, dict):
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI primitive leaf payload parts must fingerprint as a JSON object."
        )
    return Json(cast(dict[str, JsonValue], primitive_value))


def _oigi_primitive_leaf_value_fingerprint(
    *,
    type_descriptor: object,
    primitive_value: object,
) -> str | None:
    descriptor_id = getattr(type_descriptor, "id", None)
    descriptor_kind = getattr(type_descriptor, "kind", None)
    child_links = getattr(type_descriptor, "child_links", None)
    if (
        descriptor_id is None
        or descriptor_kind != AttributeTypeDescriptorKind.primitive
        or child_links
    ):
        return None
    collection_kind = getattr(type_descriptor, "collection_kind", None)
    payload = {
        "descriptor_id": str(descriptor_id),
        "kind": descriptor_kind.value,
        "collection_kind": (
            collection_kind.value if collection_kind is not None else None
        ),
        "primitive_value": _oigi_fingerprint_jsonify(primitive_value),
        "enum_option_id": None,
        "class_instance_id": None,
        "inline_value_instance_id": None,
        "children": [],
    }
    blob = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _oigi_fingerprint_jsonify(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        iso = value.isoformat()
        return iso.replace("+00:00", "Z")
    if hasattr(value, "value"):
        return getattr(value, "value")
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_oigi_fingerprint_jsonify(item) for item in value]
    if isinstance(value, tuple):
        return [_oigi_fingerprint_jsonify(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _oigi_fingerprint_jsonify(item) for key, item in value.items()
        }
    return str(value)


def _try_build_oigi_history_primitive_leaf_attribute_change(
    *,
    before_attribute: Attribute | None,
    before_value_fingerprint: str | None,
    attribute: Attribute,
    value_fingerprint: str | None,
    parent: ClassInstanceChange,
    created_at: datetime,
    row_backed_before_attribute: bool = False,
) -> AttributeChange | None | object:
    attribute_id = attribute.id
    value = attribute.value_root
    if attribute_id is None or not _is_oigi_primitive_leaf_value(value):
        return _OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED

    before_value = before_attribute.value_root if before_attribute is not None else None
    if before_value is not None and not _is_oigi_primitive_leaf_value(before_value):
        return _OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED

    operation = (
        ChangeType.update
        if (before_attribute is not None or row_backed_before_attribute)
        else ChangeType.create
    )
    if operation == ChangeType.update:
        if before_attribute is None and not row_backed_before_attribute:
            return _OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED
        if before_attribute is not None and before_value is None:
            return _OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED
        if (
            before_attribute is not None
            and before_attribute.attribute_config_id != attribute.attribute_config_id
        ):
            return _OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED
        before_fingerprint = before_value_fingerprint or (
            fingerprint_attribute_value(before_value)
            if before_value is not None
            else None
        )
        if before_fingerprint is None:
            return _OIGI_PRIMITIVE_LEAF_ATTRIBUTE_CHANGE_UNSUPPORTED
        current_fingerprint = value_fingerprint or fingerprint_attribute_value(value)
        if before_fingerprint is not None and before_fingerprint == current_fingerprint:
            return None

    value_change = _build_oigi_history_primitive_leaf_attribute_value_change(
        before_value=before_value,
        value=value,
        operation=operation,
        created_at=created_at,
        row_backed_before_value_id=(
            stable_attribute_value_id(
                parent_value_id=attribute_id,
                role="member",
                position=0,
                identity_key="root",
            )
            if operation == ChangeType.update
            and row_backed_before_attribute
            and before_value is None
            else None
        ),
    )
    if value_change is None:
        return None

    change = _build_oigi_change(
        key=f"attribute:attr:{attribute.attribute_config_id}:{operation.value}",
        change_type=operation,
        fields=(("attribute_config_id", attribute.attribute_config_id),),
        created_at=created_at,
    )
    with disable_autobind():
        return AttributeChange(
            attribute_id=attribute_id,
            class_instance_change_id=parent.id,
            change=change,
            change_id=change.id,
            value_root_change=value_change,
            value_root_change_id=value_change.id,
        )


def _is_oigi_primitive_leaf_value(value: AttributeValue | None) -> bool:
    if value is None or value.child_links:
        return False
    type_descriptor = value.type_descriptor
    return (
        type_descriptor is not None
        and type_descriptor.kind == AttributeTypeDescriptorKind.primitive
    )


def _build_oigi_history_primitive_leaf_attribute_value_change(
    *,
    before_value: AttributeValue | None,
    value: AttributeValue,
    operation: ChangeType,
    created_at: datetime,
    row_backed_before_value_id: UUID | None = None,
) -> AttributeValueChange | None:
    return _build_oigi_history_primitive_leaf_attribute_value_change_from_parts(
        before_value=before_value,
        value_id=value.id,
        primitive_value=value.primitive_value,
        operation=operation,
        created_at=created_at,
        row_backed_before_value_id=row_backed_before_value_id,
    )


def _oigi_primitive_leaf_attribute_value_change_draft_from_parts(
    *,
    before_value: AttributeValue | None,
    value_id: UUID | None,
    primitive_payload: JsonValue,
    operation: ChangeType,
    created_at: datetime,
) -> _OigiPrimitiveLeafValueChangeDraft | None:
    if operation == ChangeType.update:
        if before_value is None:
            return None
        effective_value_id = before_value.id
        before_payload = _oigi_attribute_value_primitive_payload(before_value)
        if before_payload == primitive_payload:
            return None
        fields: tuple[tuple[str, object], ...] = (
            ("primitive_value", primitive_payload),
        )
    else:
        effective_value_id = value_id
        if primitive_payload is None:
            fields = ()
        else:
            fields = (("primitive_value", primitive_payload),)

    if effective_value_id is None:
        return None
    return _OigiPrimitiveLeafValueChangeDraft(
        attribute_value_id=effective_value_id,
        operation=operation,
        fields=fields,
        created_at=created_at,
    )


def _build_oigi_history_primitive_leaf_attribute_value_change_from_draft(
    *,
    draft: _OigiPrimitiveLeafValueChangeDraft,
) -> AttributeValueChange:
    change = _build_oigi_change_model_construct(
        key=f"attribute_value:value:{draft.operation.value}",
        change_type=draft.operation,
        fields=draft.fields,
        created_at=draft.created_at,
    )
    return AttributeValueChange.model_construct(
        attribute_value_id=draft.attribute_value_id,
        change=change,
        change_id=change.id,
        attribute_value_link_changes=[],
    )


def _build_oigi_history_primitive_leaf_attribute_change_from_draft(
    *,
    draft: _OigiPrimitiveLeafAttributeChangeDraft,
    parent: ClassInstanceChange,
) -> AttributeChange:
    return _build_oigi_history_primitive_leaf_attribute_change_with_body_draft(
        draft=draft,
        parent=parent,
    ).attribute_change


def _build_oigi_history_primitive_leaf_attribute_change_with_body_draft(
    *,
    draft: _OigiPrimitiveLeafAttributeChangeDraft,
    parent: ClassInstanceChange,
) -> _OigiPrimitiveLeafAttributeChangeBuildResult:
    value_change = _build_oigi_history_primitive_leaf_attribute_value_change_from_draft(
        draft=draft.value_root_change,
    )
    value_change_draft = OigCommitBodyAttributeValueChangeDraft(
        id=_required_oigi_direct_projection_uuid(
            value_change.id,
            "attribute_value_change.id",
        ),
        attribute_value_id=draft.value_root_change.attribute_value_id,
        change=_oigi_commit_body_change_ref_draft_from_fields(
            change=value_change.change,
            fields=draft.value_root_change.fields,
        ),
        attribute_value_link_changes=(),
    )
    change = _build_oigi_change_model_construct(
        key=f"attribute:attr:{draft.attribute_config_id}:{draft.operation.value}",
        change_type=draft.operation,
        fields=(("attribute_config_id", draft.attribute_config_id),),
        created_at=draft.created_at,
    )
    attribute_change = AttributeChange.model_construct(
        attribute_id=draft.attribute_id,
        class_instance_change_id=parent.id,
        change=change,
        change_id=change.id,
        value_root_change=value_change,
        value_root_change_id=value_change.id,
    )
    return _OigiPrimitiveLeafAttributeChangeBuildResult(
        attribute_change=attribute_change,
        body_draft=OigCommitBodyAttributeChangeDraft(
            id=_required_oigi_direct_projection_uuid(
                attribute_change.id,
                "attribute_change.id",
            ),
            attribute_id=draft.attribute_id,
            change=_oigi_commit_body_change_ref_draft_from_fields(
                change=change,
                fields=(("attribute_config_id", draft.attribute_config_id),),
            ),
            value_root_change=value_change_draft,
        ),
    )


def _oigi_commit_body_change_ref_draft_from_fields(
    *,
    change: Change,
    fields: Iterable[tuple[str, object]],
) -> OigCommitBodyChangeRefDraft:
    return OigCommitBodyChangeRefDraft(
        id=_required_oigi_direct_projection_uuid(change.id, "change.id"),
        key=change.key,
        type=change.type,
        created_at=change.created_at,
        fields=tuple(
            OigCommitBodyFieldDeltaDraft(
                position=position,
                property=property_name,
                kind=ChangeDeltaKind.scalar_set,
                payload=cast(
                    OigCommitBodyJsonValue,
                    {"value": _oigi_json_value(value)},
                ),
            )
            for position, (property_name, value) in enumerate(fields)
        ),
    )


def _build_oigi_commit_body_class_instance_change_draft(
    *,
    class_instance_change: ClassInstanceChange,
    attribute_change_drafts: tuple[OigCommitBodyAttributeChangeDraft, ...],
) -> OigCommitBodyClassInstanceChangeDraft:
    return OigCommitBodyClassInstanceChangeDraft(
        id=_required_oigi_direct_projection_uuid(
            class_instance_change.id,
            "class_instance_change.id",
        ),
        class_instance_id=_required_oigi_direct_projection_uuid(
            class_instance_change.class_instance_id,
            "class_instance_change.class_instance_id",
        ),
        change=oig_commit_body_change_ref_draft_from_change(
            class_instance_change.change,
            fields=class_instance_change.change.change_deltas,
        ),
        attribute_changes=attribute_change_drafts,
    )


def _required_oigi_direct_projection_uuid(value: object, name: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(value)
    raise _OigiHistoryDirectProjectionUnsupported(
        f"OIGI direct source-row projection missing required UUID: {name}"
    )


def _build_oigi_change_model_construct(
    *,
    key: str,
    change_type: ChangeType,
    fields: Iterable[tuple[str, object]],
    created_at: datetime,
) -> Change:
    change = Change.model_construct(
        key=key,
        type=change_type,
        change_deltas=[],
        created_at=created_at,
    )
    change.change_deltas = [
        ChangeDelta.model_construct(
            change_id=change.id,
            position=position,
            property=property_name,
            kind=ChangeDeltaKind.scalar_set,
            payload=Json({"value": _oigi_json_value(value)}),
        )
        for position, (property_name, value) in enumerate(fields)
    ]
    return change


def _build_oigi_history_primitive_leaf_attribute_value_change_from_parts(
    *,
    before_value: AttributeValue | None,
    value_id: UUID | None,
    primitive_value: Json | None,
    primitive_payload: JsonValue | object = _OIGI_PRIMITIVE_LEAF_PAYLOAD_UNSET,
    operation: ChangeType,
    created_at: datetime,
    row_backed_before_value_id: UUID | None = None,
) -> AttributeValueChange | None:
    payload = _oigi_primitive_leaf_payload_from_parts(
        primitive_value=primitive_value,
        primitive_payload=primitive_payload,
    )
    if operation == ChangeType.update:
        if before_value is None and row_backed_before_value_id is None:
            return None
        if before_value is None:
            effective_value_id = row_backed_before_value_id
        else:
            effective_value_id = before_value.id
            before_payload = _oigi_attribute_value_primitive_payload(before_value)
            if before_payload == payload:
                return None
        fields: tuple[tuple[str, object], ...] = (("primitive_value", payload),)
    else:
        effective_value_id = value_id
        fields = () if payload is None else (("primitive_value", payload),)

    if effective_value_id is None:
        return None

    change = _build_oigi_change(
        key=f"attribute_value:value:{operation.value}",
        change_type=operation,
        fields=fields,
        created_at=created_at,
    )
    with disable_autobind():
        return AttributeValueChange(
            attribute_value_id=effective_value_id,
            change=change,
            change_id=change.id,
            attribute_value_link_changes=[],
        )


def _oigi_primitive_leaf_payload_from_parts(
    *,
    primitive_value: Json | None,
    primitive_payload: JsonValue | object,
) -> JsonValue:
    if primitive_payload is not _OIGI_PRIMITIVE_LEAF_PAYLOAD_UNSET:
        return cast(JsonValue, primitive_payload)
    return _oigi_primitive_leaf_payload(primitive_value)


def _attribute_fingerprints_by_config_id(
    rows: Iterable[CommitStateRow],
) -> dict[UUID, str]:
    out: dict[UUID, str] = {}
    for row in rows:
        if row.kind != "ATTR":
            continue
        raw_attribute_config_id, separator, value_fingerprint = row.value.partition(":")
        if not separator:
            continue
        out[UUID(raw_attribute_config_id)] = value_fingerprint
    return out


def _populate_oigi_history_changed_targets_source_state_rows(
    *,
    targets: Iterable[_OigiHistoryChangedClassInstanceTarget],
    class_configs_by_id: dict[UUID, ClassConfig],
) -> dict[UUID, tuple[CommitStateRow, ...]]:
    state_rows_by_id: dict[UUID, tuple[CommitStateRow, ...]] = {}
    for target in targets:
        state_rows_by_id[target.class_instance.id] = (
            _populate_oigi_changed_target_source_state_rows(
                target=target,
                class_configs_by_id=class_configs_by_id,
            )
        )
    return state_rows_by_id


def _populate_oigi_changed_target_source_state_rows(
    *,
    target: _OigiHistoryChangedClassInstanceTarget,
    class_configs_by_id: dict[UUID, ClassConfig],
) -> tuple[CommitStateRow, ...]:
    class_config = target.class_config
    class_instance = target.class_instance
    if class_config.id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection requires ClassConfig.id."
        )
    if class_instance.id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection requires ClassInstance.id."
        )
    rows: list[CommitStateRow] = [
        CommitStateRow(
            kind="NODE",
            key=str(class_config.id),
            value=str(class_instance.id),
        )
    ]
    attribute_rows: set[tuple[str, str]] = set()
    for link in target.attribute_plan.attribute_links:
        attr_cfg = _oigi_attribute_config_from_link(link=link)
        if attr_cfg is None:
            continue
        if attr_cfg.id is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection requires AttributeConfig.id: "
                f"class_config_id={class_config.id} attribute_name={attr_cfg.name!r}"
            )
        if attr_cfg.is_virtual:
            continue
        if attr_cfg.id in target.attribute_plan.relationship_attribute_config_ids:
            continue

        found, raw_value = target.source.try_attribute_value(attr_cfg)
        if not found:
            if attr_cfg.default_value is not None:
                raw_value = _parse_oigi_default_attribute_value(attr_cfg)
            elif (
                attr_cfg.is_required
                or attr_cfg.id in target.attribute_plan.required_fk_attribute_config_ids
            ):
                raise _OigiHistoryDirectProjectionUnsupported(
                    "OIGI direct source-row projection source object is missing "
                    f"required attribute: class_config_id={class_config.id} "
                    f"attribute_name={attr_cfg.name!r}"
                )
            else:
                continue
        try:
            attribute = build_attribute(
                owner_key=target.source.id,
                attribute_config=attr_cfg,
                value=raw_value,
                class_configs_by_id=class_configs_by_id,
                enum_option_resolver=default_meta_enum_option_resolver,
            )
        except AttributeBuildError as exc:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection could not build attribute "
                f"value: class_config_id={class_config.id} "
                f"attribute_name={attr_cfg.name!r}"
            ) from exc
        _ = link_attribute(class_instance, attribute)
        attribute_rows.add(
            (
                str(attr_cfg.id),
                fingerprint_attribute_value(attribute.value_root),
            )
        )

    for attribute_config_id, value_fingerprint in sorted(attribute_rows):
        rows.append(
            CommitStateRow(
                kind="ATTR",
                key=str(class_instance.id),
                value=f"{attribute_config_id}:{value_fingerprint}",
            )
        )
    return tuple(rows)


def _oigi_attribute_config_from_link(*, link: object) -> AttributeConfig | None:
    attr_cfg = getattr(link, "attribute_config", None)
    if attr_cfg is None:
        return None
    if not isinstance(attr_cfg, AttributeConfig):
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection expected AttributeConfig link: "
            f"attribute_config_type={type(attr_cfg)!r}"
        )
    return attr_cfg


def _parse_oigi_default_attribute_value(attribute_config: AttributeConfig) -> object:
    default_value = attribute_config.default_value
    if default_value is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection cannot parse empty default value: "
            f"attribute_name={attribute_config.name!r}"
        )
    try:
        return json.loads(default_value)
    except Exception as exc:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection found invalid default JSON: "
            f"attribute_name={attribute_config.name!r} default_value={default_value!r}"
        ) from exc


def _build_oigi_history_changes_from_direct_targets(
    *,
    before_oig: ObjectInstanceGraph,
    object_instance_graph_identity_id: UUID,
    direct_targets: _OigiHistoryDirectClassInstanceTargets,
    changed_projections: Iterable[_OigiHistoryProjectedChangedClassInstance],
    created_at: datetime,
) -> tuple[list[ObjectInstanceGraphChange], OigCommitBodyDraft] | None:
    changed_class_instance_ids: set[UUID] = set()
    deleted_class_instance_ids = frozenset(
        class_instance.id
        for class_instance in direct_targets.deleted_class_instances
        if class_instance.id is not None
    )
    class_instance_changes: list[ClassInstanceChange] = []
    class_instance_body_drafts: list[OigCommitBodyClassInstanceChangeDraft] = []
    with commit_perf_span(
        phase=_oigi_history_trace_phase(
            "emit_changed_class_instance_changes.collect_changed_projection_changes"
        ),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        for projection in changed_projections:
            class_instance = projection.target.class_instance
            class_instance_id = class_instance.id
            if class_instance_id is None:
                return None
            changed_class_instance_ids.add(class_instance_id)
            if projection.class_instance_change is not None:
                class_instance_changes.append(projection.class_instance_change)
                if projection.class_instance_body_draft is None:
                    return None
                class_instance_body_drafts.append(projection.class_instance_body_draft)

    with commit_perf_span(
        phase=_oigi_history_trace_phase(
            "emit_changed_class_instance_changes.build_deleted_changes"
        ),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        for deleted_class_instance in sorted(
            direct_targets.deleted_class_instances,
            key=lambda item: (str(item.class_config_id), str(item.id)),
        ):
            deleted_class_instance_id = deleted_class_instance.id
            if deleted_class_instance_id is None:
                return None
            if deleted_class_instance_id in changed_class_instance_ids:
                raise _OigiHistoryDirectProjectionUnsupported(
                    "OIGI direct source-row projection cannot both change and "
                    f"delete ClassInstance {deleted_class_instance_id}"
                )
            deleted_change = _build_oigi_history_class_instance_delete_change(
                class_instance=deleted_class_instance,
                created_at=created_at,
            )
            class_instance_changes.append(deleted_change)
            class_instance_body_drafts.append(
                oig_commit_body_class_instance_change_draft_from_change(deleted_change)
            )

    with commit_perf_span(
        phase=_oigi_history_trace_phase(
            "emit_changed_class_instance_changes.build_deleted_relationship_changes"
        ),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        relationship_changes = _build_oigi_history_deleted_relationship_changes(
            before_oig=before_oig,
            deleted_class_instance_ids=deleted_class_instance_ids,
            created_at=created_at,
        )

    if not class_instance_changes and not relationship_changes:
        return [], OigCommitBodyDraft(roots=())
    out: list[ObjectInstanceGraphChange] = []
    body_roots: list[OigCommitBodyRootChangeDraft] = []
    root_change = _build_oigi_change(
        key="root:object_instance:update",
        change_type=ChangeType.update,
        fields=(),
        created_at=created_at,
    )
    with disable_autobind():
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "emit_changed_class_instance_changes.build_root_compat_change"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={},
        ):
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
        with commit_perf_span(
            phase=_oigi_history_trace_phase(
                "emit_changed_class_instance_changes.build_root_body_draft"
            ),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={
                "class_instance_body_draft_count": len(class_instance_body_drafts)
            },
        ):
            body_roots.append(
                OigCommitBodyRootChangeDraft(
                    id=out[-1].id,
                    type=ObjectInstanceGraphChangeType.object_instance,
                    change=oig_commit_body_change_ref_draft_from_change(root_change),
                    class_instance_changes=tuple(class_instance_body_drafts),
                    class_instance_relationship_changes=(),
                )
            )
        if relationship_changes:
            relationship_root_change = _build_oigi_change(
                key="root:object_instance_relationship:update",
                change_type=ChangeType.update,
                fields=(),
                created_at=created_at,
            )
            out.append(
                ObjectInstanceGraphChange(
                    object_instance_graph_identity_id=(
                        object_instance_graph_identity_id
                    ),
                    object_instance_graph_id=before_oig.id,
                    type=ObjectInstanceGraphChangeType.object_instance_relationship,
                    change=relationship_root_change,
                    change_id=relationship_root_change.id,
                    class_instance_changes=[],
                    class_instance_relationship_changes=relationship_changes,
                )
            )
            with commit_perf_span(
                phase=_oigi_history_trace_phase(
                    "emit_changed_class_instance_changes."
                    "build_relationship_body_draft"
                ),
                category=_OIGI_HISTORY_TRACE_CATEGORY,
                metadata={"relationship_change_count": len(relationship_changes)},
            ):
                body_roots.append(
                    OigCommitBodyRootChangeDraft(
                        id=out[-1].id,
                        type=ObjectInstanceGraphChangeType.object_instance_relationship,
                        change=oig_commit_body_change_ref_draft_from_change(
                            relationship_root_change
                        ),
                        class_instance_changes=(),
                        class_instance_relationship_changes=tuple(
                            oig_commit_body_relationship_change_draft_from_change(item)
                            for item in relationship_changes
                        ),
                    )
                )
    return out, OigCommitBodyDraft(roots=tuple(body_roots))


def _build_oigi_history_class_instance_delete_change(
    *,
    class_instance: ClassInstance,
    created_at: datetime,
) -> ClassInstanceChange:
    class_instance_id = class_instance.id
    if class_instance_id is None:
        raise _OigiHistoryDirectProjectionUnsupported(
            "OIGI direct source-row projection delete target lacks ClassInstance.id."
        )
    change = _build_oigi_change(
        key=(
            "class_instance:"
            f"{class_instance.class_config_id}:{class_instance.id}:delete"
        ),
        change_type=ChangeType.delete,
        fields=(),
        created_at=created_at,
    )
    with disable_autobind():
        return ClassInstanceChange(
            class_instance_id=class_instance_id,
            change=change,
            change_id=change.id,
            attribute_changes=[],
        )


def _build_oigi_history_deleted_relationship_changes(
    *,
    before_oig: ObjectInstanceGraph,
    deleted_class_instance_ids: frozenset[UUID],
    created_at: datetime,
) -> list[ClassInstanceRelationshipChange]:
    if not deleted_class_instance_ids:
        return []

    out: list[ClassInstanceRelationshipChange] = []
    for relationship in sorted(
        before_oig.class_instance_relationships,
        key=lambda item: (
            str(item.class_config_relationship_id),
            str(item.source_class_instance_id),
            str(item.target_class_instance_id),
        ),
    ):
        relationship_id = relationship.class_config_relationship_id
        source_id = relationship.source_class_instance_id
        target_id = relationship.target_class_instance_id
        if (
            source_id not in deleted_class_instance_ids
            and target_id not in deleted_class_instance_ids
        ):
            continue
        if relationship_id is None or source_id is None or target_id is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection cannot delete malformed "
                f"relationship for deleted ClassInstance ids={deleted_class_instance_ids}"
            )
        change = _build_oigi_change(
            key=(
                "class_instance_relationship:"
                f"{relationship_id}:{source_id}->{target_id}:delete"
            ),
            change_type=ChangeType.delete,
            fields=(),
            created_at=created_at,
        )
        with disable_autobind():
            out.append(
                ClassInstanceRelationshipChange(
                    class_config_relationship_id=relationship_id,
                    source_class_instance_id=source_id,
                    target_class_instance_id=target_id,
                    change=change,
                    change_id=change.id,
                )
            )
    return out


def _build_oigi_history_class_instance_change(
    *,
    before_class_instance: ClassInstance | None,
    class_instance: ClassInstance,
    created_at: datetime,
) -> ClassInstanceChange | None:
    class_header = _build_oigi_history_class_instance_change_header(
        before_class_instance=before_class_instance,
        class_instance=class_instance,
        created_at=created_at,
    )
    if class_header is None:
        return None
    class_instance_change, operation = class_header
    attribute_changes = _build_oigi_history_attribute_changes(
        before_class_instance=before_class_instance,
        class_instance=class_instance,
        parent=class_instance_change,
        created_at=created_at,
    )
    if attribute_changes is None:
        return None
    if (
        operation == ChangeType.update
        and not class_instance_change.change.change_deltas
        and not attribute_changes
    ):
        return None
    class_instance_change.attribute_changes = attribute_changes
    return class_instance_change


def _build_oigi_history_class_instance_change_header(
    *,
    before_class_instance: ClassInstance | None,
    class_instance: ClassInstance,
    created_at: datetime,
) -> tuple[ClassInstanceChange, ChangeType] | None:
    class_instance_id = class_instance.id
    if class_instance_id is None:
        return None
    operation = (
        ChangeType.create if before_class_instance is None else ChangeType.update
    )
    fields: list[tuple[str, object]] = []
    if operation == ChangeType.create:
        fields.extend(
            (
                ("class_config_id", class_instance.class_config_id),
                ("source_object_id", class_instance.source_object_id),
            )
        )

    change = _build_oigi_change(
        key=(
            "class_instance:"
            f"{class_instance.class_config_id}:{class_instance.id}:{operation.value}"
        ),
        change_type=operation,
        fields=fields,
        created_at=created_at,
    )
    with disable_autobind():
        class_instance_change = ClassInstanceChange(
            class_instance_id=class_instance_id,
            change=change,
            change_id=change.id,
            attribute_changes=[],
        )
    return class_instance_change, operation


def _build_oigi_history_attribute_changes(
    *,
    before_class_instance: ClassInstance | None,
    class_instance: ClassInstance,
    parent: ClassInstanceChange,
    created_at: datetime,
) -> list[AttributeChange] | None:
    before_attributes_by_id = (
        _oigi_attributes_by_id(before_class_instance.attributes)
        if before_class_instance is not None
        else {}
    )
    changed_attributes_by_id = _oigi_attributes_by_id(class_instance.attributes)
    if set(before_attributes_by_id) - set(changed_attributes_by_id):
        return None

    out: list[AttributeChange] = []
    for attribute in sorted(
        changed_attributes_by_id.values(),
        key=lambda item: (str(item.attribute_config_id), str(item.id)),
    ):
        attribute_change = _build_oigi_history_attribute_change(
            before_attribute=before_attributes_by_id.get(attribute.id),
            attribute=attribute,
            parent=parent,
            created_at=created_at,
        )
        if attribute_change is None:
            continue
        out.append(attribute_change)
    return out


def _build_oigi_history_attribute_change(
    *,
    before_attribute: Attribute | None,
    before_value_fingerprint: str | None = None,
    attribute: Attribute,
    value_fingerprint: str | None = None,
    parent: ClassInstanceChange,
    created_at: datetime,
) -> AttributeChange | None:
    attribute_id = attribute.id
    if attribute_id is None:
        return None
    operation = ChangeType.create if before_attribute is None else ChangeType.update
    if operation == ChangeType.update and before_attribute is not None:
        if before_attribute.attribute_config_id != attribute.attribute_config_id:
            return None
        before_fingerprint = before_value_fingerprint or fingerprint_attribute_value(
            before_attribute.value_root
        )
        current_fingerprint = value_fingerprint or fingerprint_attribute_value(
            attribute.value_root
        )
        if before_fingerprint == current_fingerprint:
            return None

    value_change = _build_oigi_history_attribute_value_change(
        before_value=(
            before_attribute.value_root if before_attribute is not None else None
        ),
        value=attribute.value_root,
        operation=operation,
        created_at=created_at,
    )
    if value_change is None:
        return None

    change = _build_oigi_change(
        key=f"attribute:attr:{attribute.attribute_config_id}:{operation.value}",
        change_type=operation,
        fields=(("attribute_config_id", attribute.attribute_config_id),),
        created_at=created_at,
    )
    with disable_autobind():
        return AttributeChange(
            attribute_id=attribute_id,
            class_instance_change_id=parent.id,
            change=change,
            change_id=change.id,
            value_root_change=value_change,
            value_root_change_id=value_change.id,
        )


def _build_oigi_history_attribute_value_change(
    *,
    before_value: AttributeValue | None,
    value: AttributeValue | None,
    operation: ChangeType,
    created_at: datetime,
) -> AttributeValueChange | None:
    if value is None:
        return None
    if value.child_links or (before_value is not None and before_value.child_links):
        return _build_oigi_history_union_attribute_value_change(
            before_value=before_value,
            value=value,
            operation=operation,
            created_at=created_at,
        )
    if operation == ChangeType.update and before_value is None:
        return None
    if operation == ChangeType.update:
        if before_value is None:
            return None
        value_id = before_value.id
    else:
        value_id = value.id
    if value_id is None:
        return None
    fields = _oigi_history_attribute_value_fields(
        before_value=before_value,
        value=value,
        operation=operation,
    )
    if operation == ChangeType.update and not fields:
        return None
    change = _build_oigi_change(
        key=f"attribute_value:value:{operation.value}",
        change_type=operation,
        fields=fields,
        created_at=created_at,
    )
    with disable_autobind():
        return AttributeValueChange(
            attribute_value_id=value_id,
            change=change,
            change_id=change.id,
            attribute_value_link_changes=[],
        )


def _build_oigi_history_union_attribute_value_change(
    *,
    before_value: AttributeValue | None,
    value: AttributeValue,
    operation: ChangeType,
    created_at: datetime,
) -> AttributeValueChange | None:
    if (
        _oigi_attribute_value_descriptor_kind(value)
        != AttributeTypeDescriptorKind.union
    ):
        return None
    if before_value is not None:
        return None
    if operation != ChangeType.create:
        return None
    return _build_oigi_history_attribute_value_tree_create_change(
        value=value,
        created_at=created_at,
    )


def _build_oigi_history_attribute_value_tree_create_change(
    *,
    value: AttributeValue,
    created_at: datetime,
) -> AttributeValueChange | None:
    value_id = value.id
    if value_id is None:
        return None
    if value.child_links and (
        _oigi_attribute_value_descriptor_kind(value)
        != AttributeTypeDescriptorKind.union
    ):
        return None
    fields = _oigi_history_attribute_value_fields(
        before_value=None,
        value=value,
        operation=ChangeType.create,
    )
    change = _build_oigi_change(
        key="attribute_value:value:create",
        change_type=ChangeType.create,
        fields=fields,
        created_at=created_at,
    )
    with disable_autobind():
        value_change = AttributeValueChange(
            attribute_value_id=value_id,
            change=change,
            change_id=change.id,
            attribute_value_link_changes=[],
        )
    for link in sorted(value.child_links, key=_oigi_attribute_value_link_sort_key):
        link_change = _build_oigi_history_attribute_value_link_create_change(
            link=link,
            parent=value_change,
            created_at=created_at,
        )
        if link_change is None:
            return None
        value_change.attribute_value_link_changes.append(link_change)
    return value_change


def _build_oigi_history_attribute_value_link_create_change(
    *,
    link: AttributeValueLink,
    parent: AttributeValueChange,
    created_at: datetime,
) -> AttributeValueLinkChange | None:
    link_id = link.id
    if link_id is None:
        return None
    child = link.child
    if child is None:
        return None
    child_change = _build_oigi_history_attribute_value_tree_create_change(
        value=child,
        created_at=created_at,
    )
    if child_change is None:
        return None
    fields: list[tuple[str, object]] = [("role", link.role.value)]
    if link.position is not None:
        fields.append(("position", link.position))
    if link.identity_key is not None:
        fields.append(("identity_key", link.identity_key))
    change = _build_oigi_change(
        key=(
            "attribute_value_link:"
            f"{link.role.value}:"
            f"{link.position if link.position is not None else ''}:"
            f"{link.identity_key or ''}:create"
        ),
        change_type=ChangeType.create,
        fields=fields,
        created_at=created_at,
    )
    with disable_autobind():
        return AttributeValueLinkChange(
            attribute_value_change_id=parent.id,
            attribute_value_link_id=link_id,
            change=change,
            change_id=change.id,
            child_attribute_value_change=child_change,
            child_attribute_value_change_id=child_change.id,
        )


def _oigi_attribute_value_descriptor_kind(
    value: AttributeValue,
) -> AttributeTypeDescriptorKind | None:
    descriptor = value.type_descriptor
    return None if descriptor is None else descriptor.kind


def _oigi_attribute_value_link_sort_key(
    link: AttributeValueLink,
) -> tuple[str, int, str, str]:
    return (
        link.role.value,
        link.position if link.position is not None else -1,
        link.identity_key or "",
        str(link.id),
    )


def _oigi_history_attribute_value_fields(
    *,
    before_value: AttributeValue | None,
    value: AttributeValue,
    operation: ChangeType,
) -> tuple[tuple[str, object], ...]:
    candidate_fields = (
        ("primitive_value", _oigi_attribute_value_primitive_payload(value)),
        ("enum_option_id", value.enum_option_id),
        ("inline_value_instance_id", value.inline_value_instance_id),
        ("class_instance_id", value.class_instance_id),
    )
    if operation == ChangeType.create or before_value is None:
        return tuple((key, item) for key, item in candidate_fields if item is not None)
    before_fields = {
        "primitive_value": _oigi_attribute_value_primitive_payload(before_value),
        "enum_option_id": before_value.enum_option_id,
        "inline_value_instance_id": before_value.inline_value_instance_id,
        "class_instance_id": before_value.class_instance_id,
    }
    return tuple(
        (key, item) for key, item in candidate_fields if before_fields.get(key) != item
    )


def _oigi_attributes_by_id(attributes: Iterable[Attribute]) -> dict[UUID, Attribute]:
    out: dict[UUID, Attribute] = {}
    for attribute in attributes:
        attribute_id = attribute.id
        if attribute_id is None:
            continue
        previous = out.get(attribute_id)
        if previous is not None:
            return {}
        out[attribute_id] = attribute
    return out


def _oigi_attribute_value_primitive_payload(value: AttributeValue | None) -> JsonValue:
    if value is None:
        return None
    raw = value.primitive_value
    return _oigi_primitive_leaf_payload(raw)


def _oigi_primitive_leaf_payload(raw: Json | None) -> JsonValue:
    if isinstance(raw, dict) and set(raw.keys()) == {"value"}:
        return _oigi_json_value(raw.get("value"))
    return _oigi_json_value(raw)


def _build_oigi_change(
    *,
    key: str,
    change_type: ChangeType,
    fields: Iterable[tuple[str, object]],
    created_at: datetime,
) -> Change:
    change = Change(
        key=key,
        type=change_type,
        change_deltas=[],
        created_at=created_at,
    )
    deltas: list[ChangeDelta] = []
    for position, (property_name, value) in enumerate(fields):
        deltas.append(
            ChangeDelta(
                change_id=change.id,
                position=position,
                property=property_name,
                kind=ChangeDeltaKind.scalar_set,
                payload=Json({"value": _oigi_json_value(value)}),
            )
        )
    change.change_deltas = deltas
    return change


def _oigi_json_value(value: object) -> JsonValue:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return str(value.value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_oigi_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_oigi_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _oigi_json_value(item) for key, item in value.items()}
    if isinstance(value, BaseModel):
        dumped = value.model_dump(mode="json", exclude_none=True)
        return _oigi_json_value(dumped)
    return str(value)


def _build_oigi_history_after_oig_from_direct_targets(
    *,
    before_oig: ObjectInstanceGraph,
    changed_class_instances: list[ClassInstance],
    deleted_class_instance_ids: frozenset[UUID],
    graph_hash_post: str,
) -> ObjectInstanceGraph:
    before_positions = {
        class_instance.id: position
        for position, class_instance in enumerate(before_oig.class_instances)
        if class_instance.id is not None
    }
    class_instances = [
        class_instance
        for class_instance in before_oig.class_instances
        if class_instance.id not in deleted_class_instance_ids
    ]
    for changed_class_instance in changed_class_instances:
        if changed_class_instance.id in deleted_class_instance_ids:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct source-row projection cannot cache a changed "
                f"deleted ClassInstance: {changed_class_instance.id}"
            )
        position = before_positions.get(changed_class_instance.id)
        if position is None or position >= len(class_instances):
            class_instances.append(changed_class_instance)
            continue
        replaced = False
        for current_position, current in enumerate(class_instances):
            if current.id != changed_class_instance.id:
                continue
            class_instances[current_position] = changed_class_instance
            replaced = True
            break
        if not replaced:
            class_instances.append(changed_class_instance)

    with disable_autobind():
        return ObjectInstanceGraph(
            id=before_oig.id,
            key=before_oig.key,
            name=before_oig.name,
            description=before_oig.description,
            object_projection_graph_id=before_oig.object_projection_graph_id,
            root_class_instance_id=before_oig.root_class_instance_id,
            root_class_instance=before_oig.root_class_instance,
            class_instances=class_instances,
            class_instance_relationships=[
                relationship
                for relationship in before_oig.class_instance_relationships
                if relationship.source_class_instance_id
                not in deleted_class_instance_ids
                and relationship.target_class_instance_id
                not in deleted_class_instance_ids
            ],
            hash=graph_hash_post,
        )


def _derive_oigi_post_oig_from_changes(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    changes: list[ObjectInstanceGraphChange],
    trusted_graph_hash_post: str | None = None,
) -> ObjectInstanceGraph:
    return materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
        trusted_graph_hash_post=trusted_graph_hash_post,
    )


def _derive_oigi_post_oig_from_direct_projection(
    *,
    before_oig: ObjectInstanceGraph,
    changed_projections: Iterable[_OigiHistoryProjectedChangedClassInstance],
    direct_targets: _OigiHistoryDirectClassInstanceTargets,
    graph_hash_post: str,
) -> ObjectInstanceGraph:
    changed_class_instances_by_id: dict[UUID, ClassInstance] = {}
    for projection in changed_projections:
        class_instance = projection.target.class_instance
        class_instance_id = class_instance.id
        if class_instance_id is None:
            raise _OigiHistoryDirectProjectionUnsupported(
                "OIGI direct post graph requires changed ClassInstance.id."
            )
        changed_class_instances_by_id[class_instance_id] = class_instance

    deleted_class_instance_ids = frozenset(
        class_instance.id
        for class_instance in direct_targets.deleted_class_instances
        if class_instance.id is not None
    )
    post_class_instances: list[ClassInstance] = []
    for class_instance in before_oig.class_instances:
        class_instance_id = class_instance.id
        if class_instance_id is None:
            continue
        if class_instance_id in deleted_class_instance_ids:
            continue
        post_class_instances.append(
            changed_class_instances_by_id.pop(class_instance_id, class_instance)
        )
    post_class_instances.extend(
        sorted(
            changed_class_instances_by_id.values(),
            key=lambda item: (str(item.class_config_id), str(item.id)),
        )
    )

    post_relationships = [
        relationship
        for relationship in before_oig.class_instance_relationships
        if relationship.source_class_instance_id not in deleted_class_instance_ids
        and relationship.target_class_instance_id not in deleted_class_instance_ids
    ]

    with disable_autobind():
        return ObjectInstanceGraph(
            id=before_oig.id,
            key=before_oig.key,
            name=before_oig.name,
            description=before_oig.description,
            object_projection_graph_id=before_oig.object_projection_graph_id,
            root_class_instance_id=before_oig.root_class_instance_id,
            root_class_instance=before_oig.root_class_instance,
            class_instances=post_class_instances,
            class_instance_relationships=post_relationships,
            hash=graph_hash_post,
        )


def _build_oigi_history_changes_from_projection(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    oigi_opg: ObjectProjectionGraph,
    object_instance_graph_identity_id: UUID,
    projection: _OigiHistoryProjectionResult,
    perf_ms: dict[str, int] | None,
    perf_metric_prefix: str,
) -> _OigiHistoryChangeProjection:
    context_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("build_direct_projection_context"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        direct_context = _build_oigi_history_direct_projection_context(
            index=index,
            before_oig=before_oig,
            oigi_opg=oigi_opg,
        )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_build_direct_projection_context_ms",
        started=context_started,
    )
    class_instances_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("build_direct_compat_class_instances"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        direct_targets = _build_oigi_history_changed_class_instance_targets(
            context=direct_context,
            before_oig=before_oig,
            projection=projection,
        )
        changed_targets = direct_targets.changed_targets
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_build_direct_compat_class_instances_ms",
        started=class_instances_started,
    )
    pre_state_index = build_commit_state_index(before_oig)
    pre_state_row_maps = pre_state_index.row_maps(include_relationship_keys=False)
    source_state_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("build_direct_source_state_rows"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        changed_projections = _project_oigi_history_changed_targets(
            targets=changed_targets,
            context=direct_context,
            before_state_row_maps=pre_state_row_maps.class_state_rows_by_id,
            created_at=projection.change_set.collected_at,
            perf_ms=perf_ms,
            perf_metric_prefix=perf_metric_prefix,
        )
        projection_changes_supported = len(changed_projections) == len(changed_targets)
        if projection_changes_supported:
            post_class_state_rows_by_id = _post_state_rows_by_changed_projection(
                projections=changed_projections
            )
            changed_class_instances = [
                projection.target.class_instance for projection in changed_projections
            ]
        else:
            post_class_state_rows_by_id = (
                _populate_oigi_history_changed_targets_source_state_rows(
                    targets=changed_targets,
                    class_configs_by_id=dict(index.class_configs_by_id),
                )
            )
            changed_class_instances = [
                target.class_instance for target in changed_targets
            ]
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_build_direct_source_state_rows_ms",
        started=source_state_started,
    )
    pre_state_evidence: ObjectInstanceGraphCommitPreStateEvidence | None = None
    changes_started = time.monotonic()
    body_draft: OigCommitBodyDraft | None = None
    with commit_perf_span(
        phase=_oigi_history_trace_phase("emit_changed_class_instance_changes"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        change_projection = (
            _build_oigi_history_changes_from_direct_targets(
                before_oig=before_oig,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                direct_targets=direct_targets,
                changed_projections=changed_projections,
                created_at=projection.change_set.collected_at,
            )
            if projection_changes_supported
            else None
        )
        if change_projection is not None:
            changes, body_draft = change_projection
        else:
            changes = None
        if changes is None:
            if direct_targets.deleted_class_instances:
                if perf_ms is not None:
                    perf_ms[f"{perf_metric_prefix}_row_shaped_change_builder_count"] = 0
                    perf_ms[
                        f"{perf_metric_prefix}_row_shaped_change_fallback_count"
                    ] = 1
                raise _OigiHistoryDirectProjectionUnsupported(
                    "OIGI direct source-row projection could not emit "
                    "row-shaped create/delete changes."
                )
            old_class_instances: list[ClassInstance] = []
            for class_instance in changed_class_instances:
                class_instance_id = class_instance.id
                if class_instance_id is None:
                    continue
                before_class_instance = direct_context.before_class_instances_by_id.get(
                    class_instance_id
                )
                if before_class_instance is not None:
                    old_class_instances.append(before_class_instance)
            with disable_autobind():
                old_graph = ObjectInstanceGraph(
                    id=before_oig.id,
                    key=before_oig.key,
                    name=before_oig.name,
                    description=before_oig.description,
                    object_projection_graph_id=before_oig.object_projection_graph_id,
                    root_class_instance_id=before_oig.root_class_instance_id,
                    root_class_instance=before_oig.root_class_instance,
                    class_instances=old_class_instances,
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
                    root_class_instance=before_oig.root_class_instance,
                    class_instances=changed_class_instances,
                    class_instance_relationships=[],
                    hash=before_oig.hash,
                )
            changes = diff_object_instance_graph_changes(
                old=old_graph,
                new=new_graph,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                created_at=projection.change_set.collected_at,
            )
            if perf_ms is not None:
                perf_ms[f"{perf_metric_prefix}_row_shaped_change_builder_count"] = 0
                perf_ms[f"{perf_metric_prefix}_row_shaped_change_fallback_count"] = 1
                perf_ms[f"{perf_metric_prefix}_row_shaped_body_draft_count"] = 0
        elif perf_ms is not None:
            perf_ms[f"{perf_metric_prefix}_row_shaped_change_builder_count"] = 1
            perf_ms[f"{perf_metric_prefix}_row_shaped_change_fallback_count"] = 0
            perf_ms[f"{perf_metric_prefix}_row_shaped_body_draft_count"] = (
                1 if body_draft is not None and body_draft.roots else 0
            )
            perf_ms[f"{perf_metric_prefix}_row_native_body_draft_root_count"] = (
                len(body_draft.roots) if body_draft is not None else 0
            )
            perf_ms[
                f"{perf_metric_prefix}_row_native_body_draft_class_instance_count"
            ] = (
                sum(len(root.class_instance_changes) for root in body_draft.roots)
                if body_draft is not None
                else 0
            )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_build_direct_class_instance_changes_ms",
        started=changes_started,
    )
    post_state_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("apply_direct_state_rows"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={},
    ):
        post_state_index = apply_commit_state_index_row_changes(
            pre_state_index=pre_state_index,
            changes=changes,
            post_class_state_rows_by_id=post_class_state_rows_by_id,
        )
        state_row_graph_hash_post = post_state_index.compute_hash()
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_apply_direct_state_rows_ms",
        started=post_state_started,
    )
    graph_hash_post = state_row_graph_hash_post
    if projection_changes_supported:
        post_graph_started = time.monotonic()
        with commit_perf_span(
            phase=_oigi_history_trace_phase("build_direct_post_graph_cache"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={
                "mode": "row_backed_direct_graph",
                "trusted_hash_candidate": True,
            },
        ):
            after_oig = _derive_oigi_post_oig_from_direct_projection(
                before_oig=before_oig,
                changed_projections=changed_projections,
                direct_targets=direct_targets,
                graph_hash_post=state_row_graph_hash_post,
            )
            _increment_perf(
                perf_ms,
                f"{perf_metric_prefix}_direct_post_graph_cache_row_backed_graph_count",
            )
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_build_direct_post_graph_cache_ms",
            started=post_graph_started,
        )
        _increment_perf(
            perf_ms,
            f"{perf_metric_prefix}_direct_post_graph_cache_trusted_hash_count",
        )
        pre_state_evidence = ObjectInstanceGraphCommitPreStateEvidence(
            state_hash=before_oig.hash,
            row_count=len(pre_state_index.rows),
            source_contract="aware.meta.oigi.direct_projection.pre_state.v1",
            source_ref="oigi_history_direct_projection",
        )
    else:
        post_graph_started = time.monotonic()
        with commit_perf_span(
            phase=_oigi_history_trace_phase("build_direct_post_graph_cache"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={
                "mode": "compat_replay",
                "trusted_hash_candidate": False,
            },
        ):
            after_oig = _derive_oigi_post_oig_from_changes(
                index=index,
                before_oig=before_oig,
                changes=changes,
                trusted_graph_hash_post=None,
            )
            graph_hash_post = after_oig.hash
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_build_direct_post_graph_cache_ms",
            started=post_graph_started,
        )

    if (
        not projection_changes_supported
        and state_row_graph_hash_post != graph_hash_post
    ):
        _increment_perf(
            perf_ms,
            f"{perf_metric_prefix}_direct_state_row_replay_hash_mismatch_count",
        )
        _record_oigi_direct_state_row_replay_mismatch_diagnostics(
            perf_ms=perf_ms,
            perf_metric_prefix=perf_metric_prefix,
            direct_post_state_index=post_state_index,
            replayed_after_oig=after_oig,
            direct_state_hash_post=state_row_graph_hash_post,
            replay_graph_hash_post=graph_hash_post,
        )
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_direct_change_count"] = len(changes)
        perf_ms[f"{perf_metric_prefix}_compat_change_builder_fallback_count"] = 0
    return _OigiHistoryChangeProjection(
        changes=changes,
        graph_hash_post=graph_hash_post,
        after_oig=after_oig,
        body_draft=body_draft,
        pre_state_evidence=pre_state_evidence,
        pre_state_index=pre_state_index,
    )


def _record_oigi_direct_state_row_replay_mismatch_diagnostics(
    *,
    perf_ms: dict[str, int] | None,
    perf_metric_prefix: str,
    direct_post_state_index: CommitStateIndex,
    replayed_after_oig: ObjectInstanceGraph,
    direct_state_hash_post: str,
    replay_graph_hash_post: str,
) -> None:
    replay_state_index = build_commit_state_index(replayed_after_oig)
    direct_rows = frozenset(direct_post_state_index.rows)
    replay_rows = frozenset(replay_state_index.rows)
    direct_only_rows = tuple(sorted(direct_rows - replay_rows))
    replay_only_rows = tuple(sorted(replay_rows - direct_rows))

    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_direct_state_row_replay_direct_row_count"] = len(
            direct_rows
        )
        perf_ms[f"{perf_metric_prefix}_direct_state_row_replay_replay_row_count"] = len(
            replay_rows
        )
        perf_ms[
            f"{perf_metric_prefix}_direct_state_row_replay_direct_only_row_count"
        ] = len(direct_only_rows)
        perf_ms[
            f"{perf_metric_prefix}_direct_state_row_replay_replay_only_row_count"
        ] = len(replay_only_rows)
        for row_kind in ("NODE", "ATTR", "EDGE"):
            perf_ms[
                f"{perf_metric_prefix}_direct_state_row_replay_"
                f"direct_only_{row_kind.lower()}_row_count"
            ] = sum(1 for row in direct_only_rows if row.kind == row_kind)
            perf_ms[
                f"{perf_metric_prefix}_direct_state_row_replay_"
                f"replay_only_{row_kind.lower()}_row_count"
            ] = sum(1 for row in replay_only_rows if row.kind == row_kind)

    with commit_perf_span(
        phase=_oigi_history_trace_phase("direct_state_row_replay_mismatch"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={
            "direct_state_hash_post": direct_state_hash_post,
            "replay_graph_hash_post": replay_graph_hash_post,
            "replay_state_hash_post": replay_state_index.compute_hash(),
            "direct_row_count": len(direct_rows),
            "replay_row_count": len(replay_rows),
            "direct_only_row_count": len(direct_only_rows),
            "replay_only_row_count": len(replay_only_rows),
            "direct_only_sample": _oigi_state_row_sample(direct_only_rows),
            "replay_only_sample": _oigi_state_row_sample(replay_only_rows),
        },
    ):
        pass


def _oigi_state_row_sample(rows: tuple[CommitStateRow, ...]) -> str:
    return ";".join(
        f"{row.kind}|{row.key}|{row.value}"
        for row in rows[:_OIGI_STATE_ROW_MISMATCH_SAMPLE_LIMIT]
    )


def _build_oigi_history_changes_from_compat_change_set(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    oigi_opg: ObjectProjectionGraph,
    object_instance_graph_identity_id: UUID,
    projection: _OigiHistoryProjectionResult,
    perf_ms: dict[str, int] | None,
    perf_metric_prefix: str,
) -> tuple[list[ObjectInstanceGraphChange], ObjectInstanceGraph]:
    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        ocg=index.ocg,
        opg=oigi_opg,
        change_set=projection.change_set,
        class_configs_by_id=dict(index.class_configs_by_id),
        relationships_by_id=dict(index.relationships_by_id),
        enum_option_resolver=default_meta_enum_option_resolver,
    )
    after_oig = (
        _derive_oigi_post_oig_from_changes(
            index=index,
            before_oig=before_oig,
            changes=changes,
        )
        if changes
        else before_oig
    )
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_compat_change_builder_fallback_count"] = 1
        perf_ms[f"{perf_metric_prefix}_direct_change_count"] = 0
    return changes, after_oig


async def _project_oigi_history_direct(
    *,
    session: Session,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    lane_id: UUID,
    head_commit_id: UUID,
    store: FSCommitStore,
    domain_commit: ObjectInstanceGraphCommit | None = None,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "run_commit_reaction_oigi",
) -> None:
    trace_metadata = _oigi_history_trace_metadata(
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=head_commit_id,
        lane_id=lane_id,
    )
    if domain_commit_envelope is None:
        if domain_commit is None:
            raise RuntimeError(
                "OIGI history projection requires a domain commit envelope"
            )
        domain_commit_envelope = object_instance_graph_commit_envelope_from_commit(
            branch_id=domain_branch_id,
            projection_hash=domain_projection_hash,
            commit=domain_commit,
        )

    with commit_perf_span(
        phase=_oigi_history_trace_phase("ensure_branch_lane"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        lane = _ensure_oigi_branch_lane(
            session=session,
            object_instance_graph_identity=object_instance_graph_identity,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            lane_id=lane_id,
            branch_is_main=False,
            branch_name=None,
        )

    with commit_perf_span(
        phase=_oigi_history_trace_phase("scan_existing_history"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        existing_commit_ids: set[UUID] = set()
        for existing in object_instance_graph_identity.object_instance_graph_commits:
            if existing.commit is None:
                continue
            commit_key = existing.commit.key
            try:
                existing_commit_ids.add(UUID(commit_key))
            except (TypeError, ValueError):
                continue

        existing_class_instance_ids = {
            existing.class_instance_id
            for existing in object_instance_graph_identity.class_instance_identities
        }

    to_visit: list[UUID] = [head_commit_id]
    visited: set[UUID] = set()
    envelope_by_id: dict[UUID, ObjectInstanceGraphCommitEnvelope] = {
        domain_commit_envelope.commit_id: domain_commit_envelope,
    }
    provided_full_payload_by_id: dict[UUID, ObjectInstanceGraphCommit] = {}
    if domain_commit is not None:
        provided_full_payload_by_id[domain_commit.commit.id] = domain_commit
    full_payload_by_id: dict[UUID, ObjectInstanceGraphCommit] = {}
    identity_sidecar_by_id: dict[UUID, ObjectInstanceGraphCommitIdentitySidecar] = {}
    projected_head_commit: Commit | None = None
    identity_sidecar_hit_count = 0
    identity_sidecar_miss_count = 0
    identity_sidecar_inconsistent_count = 0
    full_body_identity_fallback_count = 0
    sidecar_read_started = time.monotonic()
    sidecar_read_elapsed_ms = 0
    full_body_fallback_elapsed_ms = 0

    while to_visit:
        commit_id = to_visit.pop()
        if commit_id in visited:
            continue
        visited.add(commit_id)

        commit_already_projected = commit_id in existing_commit_ids
        if commit_already_projected:
            history_commit_id = _history_commit_id(
                lane_id=lane_id,
                domain_commit_id=commit_id,
            )
            commit = session.imap_get(Commit, history_commit_id)
            if commit_id == head_commit_id:
                projected_head_commit = commit
            if commit is not None:
                _append_unique_by_id(cast(list[object], lane.commits), commit)
            continue

        envelope = envelope_by_id.get(commit_id)
        if envelope is None:
            with commit_perf_span(
                phase=_oigi_history_trace_phase("read_domain_envelope"),
                category=_OIGI_HISTORY_TRACE_CATEGORY,
                metadata={
                    **trace_metadata,
                    "domain_commit_id": str(commit_id),
                },
            ):
                envelope = await store.get_commit_envelope(
                    branch_id=domain_branch_id,
                    projection_hash=domain_projection_hash,
                    commit_id=commit_id,
                )
            if envelope is None:
                with commit_perf_span(
                    phase=_oigi_history_trace_phase("read_domain_body_for_envelope"),
                    category=_OIGI_HISTORY_TRACE_CATEGORY,
                    metadata={
                        **trace_metadata,
                        "domain_commit_id": str(commit_id),
                    },
                ):
                    payload = await store.get_commit(
                        branch_id=domain_branch_id,
                        projection_hash=domain_projection_hash,
                        commit_id=commit_id,
                    )
                if payload is None:
                    raise RuntimeError(
                        "Missing domain commit while projecting OIG identity history plane: "
                        + f"branch_id={domain_branch_id} projection_hash={domain_projection_hash} "
                        + f"commit_id={commit_id}"
                    )
                full_payload_by_id[commit_id] = payload
                envelope = object_instance_graph_commit_envelope_from_commit(
                    branch_id=domain_branch_id,
                    projection_hash=domain_projection_hash,
                    commit=payload,
                )
            envelope_by_id[commit_id] = envelope
        with commit_perf_span(
            phase=_oigi_history_trace_phase("canonicalize_envelope_identity"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata={
                **trace_metadata,
                "domain_commit_id": str(commit_id),
            },
        ):
            envelope = await _canonicalize_domain_commit_envelope_identity_for_history(
                store=store,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                object_instance_graph_identity=object_instance_graph_identity,
                domain_commit_envelope=envelope,
            )
        envelope_by_id[commit_id] = envelope

        commit: Commit | None = None
        if not commit_already_projected:
            with commit_perf_span(
                phase=_oigi_history_trace_phase("ensure_history_commit_wrapper"),
                category=_OIGI_HISTORY_TRACE_CATEGORY,
                metadata={
                    **trace_metadata,
                    "domain_commit_id": str(commit_id),
                },
            ):
                commit = _ensure_history_commit(
                    session=session,
                    lane=lane,
                    lane_id=lane_id,
                    domain_commit_envelope=envelope,
                )
                _ensure_oigi_commit_wrapper(
                    session=session,
                    object_instance_graph_identity=object_instance_graph_identity,
                    domain_commit_envelope=envelope,
                    commit=commit,
                )
            existing_commit_ids.add(commit_id)

        if commit_id == head_commit_id:
            projected_head_commit = commit

        full_payload = full_payload_by_id.get(commit_id)
        if full_payload is not None:
            _ensure_class_instance_identities(
                session=session,
                object_instance_graph_identity=object_instance_graph_identity,
                domain_commit=full_payload,
                existing_class_instance_ids=existing_class_instance_ids,
            )
        else:
            identity_sidecar = identity_sidecar_by_id.get(commit_id)
            if identity_sidecar is None:
                read_started = time.monotonic()
                with commit_perf_span(
                    phase=_oigi_history_trace_phase("read_identity_sidecar"),
                    category=_OIGI_HISTORY_TRACE_CATEGORY,
                    metadata={
                        **trace_metadata,
                        "domain_commit_id": str(commit_id),
                    },
                ):
                    identity_sidecar = await store.get_commit_identity_sidecar(
                        branch_id=domain_branch_id,
                        projection_hash=domain_projection_hash,
                        commit_id=commit_id,
                    )
                sidecar_read_elapsed_ms += max(
                    int((time.monotonic() - read_started) * 1000),
                    0,
                )
                if identity_sidecar is not None:
                    identity_sidecar_by_id[commit_id] = identity_sidecar
            sidecar_projected = False
            if identity_sidecar is not None:
                with commit_perf_span(
                    phase=_oigi_history_trace_phase("project_identity_sidecar"),
                    category=_OIGI_HISTORY_TRACE_CATEGORY,
                    metadata={
                        **trace_metadata,
                        "domain_commit_id": str(commit_id),
                    },
                ):
                    sidecar_projected = _ensure_class_instance_identities_from_sidecar(
                        session=session,
                        object_instance_graph_identity=object_instance_graph_identity,
                        domain_commit_envelope=envelope,
                        identity_sidecar=identity_sidecar,
                        existing_class_instance_ids=existing_class_instance_ids,
                    )
                if sidecar_projected:
                    identity_sidecar_hit_count += 1
                else:
                    identity_sidecar_inconsistent_count += 1
            else:
                identity_sidecar_miss_count += 1
            if not sidecar_projected:
                fallback_started = time.monotonic()
                full_payload = provided_full_payload_by_id.get(commit_id)
                if full_payload is None:
                    with commit_perf_span(
                        phase=_oigi_history_trace_phase(
                            "read_domain_body_for_identity"
                        ),
                        category=_OIGI_HISTORY_TRACE_CATEGORY,
                        metadata={
                            **trace_metadata,
                            "domain_commit_id": str(commit_id),
                        },
                    ):
                        full_payload = await store.get_commit(
                            branch_id=domain_branch_id,
                            projection_hash=domain_projection_hash,
                            commit_id=commit_id,
                        )
                full_body_fallback_elapsed_ms += max(
                    int((time.monotonic() - fallback_started) * 1000),
                    0,
                )
                if full_payload is not None:
                    full_body_identity_fallback_count += 1
                    full_payload_by_id[commit_id] = full_payload
                    with commit_perf_span(
                        phase=_oigi_history_trace_phase("project_identity_from_body"),
                        category=_OIGI_HISTORY_TRACE_CATEGORY,
                        metadata={
                            **trace_metadata,
                            "domain_commit_id": str(commit_id),
                        },
                    ):
                        _ensure_class_instance_identities(
                            session=session,
                            object_instance_graph_identity=(
                                object_instance_graph_identity
                            ),
                            domain_commit=full_payload,
                            existing_class_instance_ids=existing_class_instance_ids,
                        )
        for parent_id in envelope.parent_commit_ids:
            if parent_id not in visited:
                to_visit.append(parent_id)

    history_head_commit_id = _history_commit_id(
        lane_id=lane_id,
        domain_commit_id=head_commit_id,
    )
    if projected_head_commit is None:
        projected_head_commit = session.imap_get(Commit, history_head_commit_id)
    if projected_head_commit is None:
        raise RuntimeError(
            "Missing projected history Commit while advancing OIGI lane head: "
            + f"history_commit_id={history_head_commit_id} domain_head_commit_id={head_commit_id}"
        )
    with commit_perf_span(
        phase=_oigi_history_trace_phase("advance_history_lane_head"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        if lane.head_commit_id != history_head_commit_id:
            lane.head_commit_id = history_head_commit_id
        if lane.head_commit is None or lane.head_commit.id != history_head_commit_id:
            lane.head_commit = projected_head_commit
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_hit_count"] = (
            identity_sidecar_hit_count
        )
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_miss_count"] = (
            identity_sidecar_miss_count
        )
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_inconsistent_count"] = (
            identity_sidecar_inconsistent_count
        )
        perf_ms[f"{perf_metric_prefix}_full_body_identity_fallback_count"] = (
            full_body_identity_fallback_count
        )
        perf_ms[f"{perf_metric_prefix}_identity_sidecar_read_ms"] = max(
            sidecar_read_elapsed_ms,
            0,
        )
        perf_ms[f"{perf_metric_prefix}_full_body_identity_fallback_ms"] = max(
            full_body_fallback_elapsed_ms,
            0,
        )
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_project_history_direct_total_ms",
            started=sidecar_read_started,
        )


async def upsert_object_instance_graph_identity_history_from_domain_commit(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    domain_commit: ObjectInstanceGraphCommit | None = None,
    domain_commit_envelope: ObjectInstanceGraphCommitEnvelope | None = None,
    source_class_instance_identity_id: UUID | None = None,
    perf_ms: dict[str, int] | None = None,
    perf_metric_prefix: str = "run_commit_reaction_oigi",
    projector_mode: str = "handler",
    store: FSCommitStore | None = None,
    lane_materializer: CachedLaneMaterializer | None = None,
) -> UUID:
    """Upsert the OIGI history plane for a domain commit."""
    total_started = time.monotonic()
    if domain_commit_envelope is None:
        if domain_commit is None:
            raise RuntimeError(
                "ObjectInstanceGraphIdentity history upsert requires a domain commit envelope"
            )
        domain_commit_envelope = object_instance_graph_commit_envelope_from_commit(
            branch_id=domain_branch_id,
            projection_hash=domain_projection_hash,
            commit=domain_commit,
        )
    domain_oig_id: UUID | None = None
    oigi_ctx = resolve_object_instance_graph_identity_lane_context(index=index)
    if oigi_ctx is None:
        raise RuntimeError("Missing required OPG: object_instance_graph_identity")

    oigi_opg = oigi_ctx.opg
    oigi_projection_hash = oigi_ctx.projection_hash
    if not (oigi_projection_hash or "").strip():
        raise RuntimeError(
            "object_instance_graph_identity OPG has empty projection_hash"
        )

    author_id = resolve_meta_author_id(actor_id)
    domain_oig_id = domain_commit_envelope.object_instance_graph_id
    store = store or FSCommitStore()
    trace_metadata = _oigi_history_trace_metadata(
        domain_oig_id=domain_oig_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=domain_commit_envelope.commit_id,
        oigi_projection_hash=oigi_projection_hash,
        projector_mode=projector_mode,
    )

    head_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("head_read"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        oigi_head_raw = cast(
            object,
            await store.head(
                branch_id=domain_oig_id,
                projection_hash=oigi_projection_hash,
            ),
        )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_head_read_ms",
        started=head_started,
    )
    oigi_head = (
        cast(Mapping[str, object], oigi_head_raw)
        if isinstance(oigi_head_raw, Mapping)
        else None
    )
    if oigi_head is None or not oigi_head.get("commit_id"):
        raise RuntimeError(
            "Missing object_instance_graph_identity lane HEAD (commit-first invariant): "
            + f"object_instance_graph_id={domain_oig_id} projection_hash={oigi_projection_hash}"
        )

    head_commit_id = _optional_uuid_from_mapping(oigi_head, "commit_id")
    if head_commit_id is None:
        raise RuntimeError(
            "Invalid object_instance_graph_identity HEAD commit_id (commit-first invariant): "
            + f"object_instance_graph_id={domain_oig_id} projection_hash={oigi_projection_hash}"
        )
    head_oig_id = _optional_uuid_from_mapping(oigi_head, "object_instance_graph_id")
    if head_oig_id is None:
        raise RuntimeError(
            "Invalid object_instance_graph_identity HEAD object_instance_graph_id (commit-first invariant): "
            + f"object_instance_graph_id={domain_oig_id} projection_hash={oigi_projection_hash}"
        )

    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    history_head_commit_id = _history_commit_id(
        lane_id=lane_id,
        domain_commit_id=domain_commit_envelope.commit_id,
    )
    with commit_perf_span(
        phase=_oigi_history_trace_phase("projection_index_check"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={
            **trace_metadata,
            "oigi_lane_commit_id": str(head_commit_id),
            "history_commit_id": str(history_head_commit_id),
            "lane_id": str(lane_id),
        },
    ):
        projection_index_hit = await _oigi_history_projection_head_index_hit(
            store=store,
            oigi_head=oigi_head,
            domain_oig_id=domain_oig_id,
            oigi_projection_hash=oigi_projection_hash,
            object_instance_graph_identity_id=head_oig_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            lane_id=lane_id,
            domain_commit_id=domain_commit_envelope.commit_id,
            history_commit_id=history_head_commit_id,
            perf_ms=perf_ms,
            perf_metric_prefix=perf_metric_prefix,
        )
    if projection_index_hit:
        if perf_ms is not None:
            perf_ms[f"{perf_metric_prefix}_projection_index_fast_path_count"] = 1
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_total_ms",
            started=total_started,
        )
        return head_oig_id
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_projection_index_fast_path_count"] = 0

    materialize_started = time.monotonic()
    materializer = lane_materializer or CachedLaneMaterializer()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("materialize_head"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={
            **trace_metadata,
            "oigi_lane_commit_id": str(head_commit_id),
        },
    ):
        materialized_head = await _materialize_oigi_history_head_with_recovery(
            materializer=materializer,
            lane_materializer=lane_materializer,
            store=store,
            index=index,
            oigi_opg=oigi_opg,
            domain_oig_id=domain_oig_id,
            domain_projection_hash=domain_projection_hash,
            oigi_projection_hash=oigi_projection_hash,
            head_commit_id=head_commit_id,
            head_oig_id=head_oig_id,
            author_id=author_id,
            perf_ms=perf_ms,
            perf_metric_prefix=perf_metric_prefix,
        )
        before_oig = materialized_head.before_oig
        head_commit_id = materialized_head.head_commit_id
        head_oig_id = materialized_head.head_oig_id
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_materialize_head_ms",
        started=materialize_started,
    )

    with commit_perf_span(
        phase=_oigi_history_trace_phase("resolve_root_context"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        actual_root_object_id = resolve_root_source_object_id(before_oig)
        if actual_root_object_id != head_oig_id:
            raise RuntimeError(
                "object_instance_graph_identity lane root mismatch: "
                + f"expected_root={head_oig_id} got_root={actual_root_object_id}"
            )

        root_cc_id: UUID | None = None
        for node in oigi_opg.object_projection_graph_nodes:
            if node.is_root:
                root_cc_id = node.class_config_id
                break
        if root_cc_id is None:
            if not oigi_opg.object_projection_graph_nodes:
                raise RuntimeError("object_instance_graph_identity OPG has no nodes")
            root_cc_id = oigi_opg.object_projection_graph_nodes[0].class_config_id

    function_name = "upsert_history_from_lane_head"
    function_id: UUID | None = None
    with commit_perf_span(
        phase=_oigi_history_trace_phase("resolve_function_config"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        for node in index.ocg.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_:
                continue
            cc = node.class_config
            if cc is None or cc.id != root_cc_id:
                continue
            for link in cc.class_config_function_configs:
                fc = link.function_config
                if fc.name == function_name:
                    function_id = fc.id
                    break
            if function_id is not None:
                break
    if function_id is None:
        raise RuntimeError(
            "FunctionConfig not found in OCG for ObjectInstanceGraphIdentity history upsert: "
            + f"class_config_id={root_cc_id} function_name={function_name}"
        )

    if projector_mode not in {"handler", "direct"}:
        raise ValueError(
            "Unsupported OIGI history projector mode: " + repr(projector_mode)
        )

    with commit_perf_span(
        phase=_oigi_history_trace_phase("resolve_domain_opgi"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=domain_projection_hash,
        )
    if opgi is None:
        raise RuntimeError(
            f"Missing required OPGI on runtime bundle: projection_hash={domain_projection_hash}"
        )

    execute_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("project_change_set"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        projection = await _project_oigi_history_projection(
            index=index,
            before_oig=before_oig,
            oigi_opg=oigi_opg,
            root_class_config_id=root_cc_id,
            object_projection_graph_identity_id=opgi.id,
            object_instance_graph_identity_id=head_oig_id,
            domain_oig_id=domain_oig_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            lane_id=lane_id,
            head_commit_id=domain_commit_envelope.commit_id,
            domain_commit=domain_commit,
            domain_commit_envelope=domain_commit_envelope,
            store=store,
            perf_ms=perf_ms,
            perf_metric_prefix=perf_metric_prefix,
        )
    _record_perf(
        perf_ms,
        (
            f"{perf_metric_prefix}_execute_history_handler_ms"
            if projector_mode == "handler"
            else f"{perf_metric_prefix}_project_history_direct_ms"
        ),
        started=execute_started,
    )

    build_changes_started = time.monotonic()
    pre_state_evidence: ObjectInstanceGraphCommitPreStateEvidence | None = None
    pre_state_index: CommitStateIndex | None = None
    try:
        with commit_perf_span(
            phase=_oigi_history_trace_phase("build_direct_oig_changes"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            change_projection = _build_oigi_history_changes_from_projection(
                index=index,
                before_oig=before_oig,
                oigi_opg=oigi_opg,
                object_instance_graph_identity_id=head_oig_id,
                projection=projection,
                perf_ms=perf_ms,
                perf_metric_prefix=perf_metric_prefix,
            )
            changes = change_projection.changes
            after_oig = change_projection.after_oig
            graph_hash_post = change_projection.graph_hash_post
            body_draft = change_projection.body_draft
            pre_state_evidence = change_projection.pre_state_evidence
            pre_state_index = change_projection.pre_state_index
    except (OigBuildError, _OigiHistoryDirectProjectionUnsupported):
        with commit_perf_span(
            phase=_oigi_history_trace_phase("build_oig_changes_compat_fallback"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            changes, after_oig = _build_oigi_history_changes_from_compat_change_set(
                index=index,
                before_oig=before_oig,
                oigi_opg=oigi_opg,
                object_instance_graph_identity_id=head_oig_id,
                projection=projection,
                perf_ms=perf_ms,
                perf_metric_prefix=perf_metric_prefix,
            )
            graph_hash_post = after_oig.hash
            body_draft = None
            pre_state_evidence = None
            pre_state_index = None
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_build_changes_ms",
        started=build_changes_started,
    )
    if not changes:
        with commit_perf_span(
            phase=_oigi_history_trace_phase("projection_index_write"),
            category=_OIGI_HISTORY_TRACE_CATEGORY,
            metadata=trace_metadata,
        ):
            wrote_projection_index = _write_oigi_history_projection_index(
                store=store,
                domain_oig_id=domain_oig_id,
                oigi_projection_hash=oigi_projection_hash,
                object_instance_graph_identity_id=head_oig_id,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
                lane_id=lane_id,
                domain_commit_id=domain_commit_envelope.commit_id,
                history_commit_id=history_head_commit_id,
                oigi_lane_commit_id=head_commit_id,
                oigi_graph_hash_post=before_oig.hash,
            )
        if perf_ms is not None:
            perf_ms[f"{perf_metric_prefix}_projection_index_written_count"] = (
                1 if wrote_projection_index else 0
            )
        _record_perf(
            perf_ms,
            f"{perf_metric_prefix}_total_ms",
            started=total_started,
        )
        return head_oig_id

    commit_action = CommitActionDescriptor(
        operation_label="ObjectInstanceGraphIdentity.upsert_history_from_lane_head",
        call_target="instance",
        function_id=function_id,
        object_id=head_oig_id,
        class_instance_identity_id=source_class_instance_identity_id,
    )

    committer = FSLaneCommitter(store=store)
    fs_commit_started = time.monotonic()
    with commit_perf_span(
        phase=_oigi_history_trace_phase("build_pre_state_index"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={
            **trace_metadata,
            "change_count": len(changes),
            "pre_state_evidence_hit": pre_state_evidence is not None,
        },
    ):
        root_metadata = extract_object_instance_graph_commit_root_metadata(
            graph=before_oig,
        )
        if pre_state_index is None:
            pre_state_index = build_commit_state_index(before_oig)
    with commit_perf_span(
        phase=_oigi_history_trace_phase("append_oigi_commit"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata={
            **trace_metadata,
            "change_count": len(changes),
            "append_mode": (
                "record_native_shallow_pre_state_evidence"
                if pre_state_evidence is not None
                else "record_native_shallow"
            ),
        },
    ):
        if pre_state_evidence is not None:
            oigi_lane_commit_record = (
                await committer.commit_record_shallow_from_pre_state_evidence(
                    branch_id=domain_oig_id,
                    projection_hash=oigi_projection_hash,
                    object_projection_graph_identity_id=opgi.id,
                    object_instance_graph_identity_id=head_oig_id,
                    object_instance_graph_id=before_oig.id,
                    pre_state_evidence=pre_state_evidence,
                    pre_state_index=pre_state_index,
                    root_metadata=root_metadata,
                    root_object_id=resolve_root_source_object_id(before_oig),
                    changes=changes,
                    body_draft=body_draft,
                    graph_hash_pre=before_oig.hash,
                    graph_hash_post=graph_hash_post,
                    author_id=author_id,
                    commit_action=commit_action,
                    write_health_index=False,
                )
            )
        else:
            if pre_state_index is None:
                raise RuntimeError(
                    "OIGI history append requires pre_state_index without "
                    "pre-state evidence."
                )
            oigi_lane_commit_record = await committer.commit_record_shallow(
                branch_id=domain_oig_id,
                projection_hash=oigi_projection_hash,
                object_projection_graph_identity_id=opgi.id,
                object_instance_graph_identity_id=head_oig_id,
                object_instance_graph_id=before_oig.id,
                pre_state_index=pre_state_index,
                root_metadata=root_metadata,
                root_object_id=resolve_root_source_object_id(before_oig),
                changes=changes,
                body_draft=body_draft,
                graph_hash_pre=before_oig.hash,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                commit_action=commit_action,
            )
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_record_native_append_count"] = 1
        perf_ms[f"{perf_metric_prefix}_record_native_pre_state_evidence_count"] = (
            1 if pre_state_evidence is not None else 0
        )
        perf_ms[f"{perf_metric_prefix}_record_native_body_draft_append_count"] = (
            1 if body_draft is not None and body_draft.roots else 0
        )
    with commit_perf_span(
        phase=_oigi_history_trace_phase("prime_materialization_cache"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        materializer.prime(
            branch_id=domain_oig_id,
            opg=oigi_opg,
            commit_id=oigi_lane_commit_record.commit_id,
            oig_id=head_oig_id,
            graph=after_oig,
        )
    with commit_perf_span(
        phase=_oigi_history_trace_phase("projection_index_write"),
        category=_OIGI_HISTORY_TRACE_CATEGORY,
        metadata=trace_metadata,
    ):
        wrote_projection_index = _write_oigi_history_projection_index(
            store=store,
            domain_oig_id=domain_oig_id,
            oigi_projection_hash=oigi_projection_hash,
            object_instance_graph_identity_id=head_oig_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            lane_id=lane_id,
            domain_commit_id=domain_commit_envelope.commit_id,
            history_commit_id=history_head_commit_id,
            oigi_lane_commit_id=oigi_lane_commit_record.commit_id,
            oigi_graph_hash_post=oigi_lane_commit_record.envelope.graph_hash_post,
        )
    if perf_ms is not None:
        perf_ms[f"{perf_metric_prefix}_projection_index_written_count"] = (
            1 if wrote_projection_index else 0
        )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_fs_commit_ms",
        started=fs_commit_started,
    )
    _record_commit_perf(
        perf_ms,
        prefix=f"{perf_metric_prefix}_fs_commit",
        committer=committer,
    )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_total_ms",
        started=total_started,
    )
    return head_oig_id


__all__ = ["upsert_object_instance_graph_identity_history_from_domain_commit"]
