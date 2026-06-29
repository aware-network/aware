"""Meta-owned OIGI history projection for runtime domain commits.

This module is the required commit reaction for the Meta history plane:
domain lane commits are projected into the `object_instance_graph_identity`
lane so consumers can resolve commit pins through OIGI truth instead of raw
filesystem paths.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from uuid import UUID
import time
from typing import cast

from aware_code_ontology.code.code_enums import CodeLanguage
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
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
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
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import (
    stable_class_instance_identity_id,
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_lane_id,
)

# Meta Runtime
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitIdentitySidecar,
    OigiHistoryDomainCommitProjection,
    object_instance_graph_commit_envelope_from_commit,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
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
from aware_meta.runtime.commit.identity_lane import (
    resolve_object_instance_graph_identity_lane_context,
)
from aware_orm.session.execution_guard import (
    allow_domain_create,
    disallow_push,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import ORMChangeSet
from aware_orm.session.change_collector import disable_change_tracking_hooks
from aware_orm.session.change_collector import scoped_change_collection
from aware_orm.session.session import Session


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
    read_started = time.monotonic()
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


def _bind_new(session: Session, instance: BaseORMModel) -> BaseORMModel:
    session.imap_add(instance)
    return instance


def _append_unique_by_id(items: list[BaseORMModel], instance: BaseORMModel) -> None:
    instance_id = instance.id
    if all(existing.id != instance_id for existing in items):
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
        oig_commit.source_language = CodeLanguage(domain_commit_envelope.source_language)
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


async def _project_oigi_history_change_set(
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
) -> ORMChangeSet:
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
        return collector.snapshot()


def _derive_oigi_post_oig_from_changes(
    *,
    index: MetaGraphRuntimeIndex,
    before_oig: ObjectInstanceGraph,
    changes: list[ObjectInstanceGraphChange],
) -> ObjectInstanceGraph:
    return materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )


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

    lane = _ensure_oigi_branch_lane(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        branch_is_main=False,
        branch_name=None,
    )

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
            envelope = await store.get_commit_envelope(
                branch_id=domain_branch_id,
                projection_hash=domain_projection_hash,
                commit_id=commit_id,
            )
            if envelope is None:
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
        envelope = await _canonicalize_domain_commit_envelope_identity_for_history(
            store=store,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            object_instance_graph_identity=object_instance_graph_identity,
            domain_commit_envelope=envelope,
        )
        envelope_by_id[commit_id] = envelope

        if not commit_already_projected:
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
                    _ensure_class_instance_identities(
                        session=session,
                        object_instance_graph_identity=object_instance_graph_identity,
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

    head_started = time.monotonic()
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
    if await _oigi_history_projection_head_index_hit(
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
    ):
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
    before_oig, _indexes = await materializer.get(
        branch_id=domain_oig_id,
        ocg=index.ocg,
        opg=oigi_opg,
        commit_id=head_commit_id,
        oig_id=head_oig_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_materialize_head_ms",
        started=materialize_started,
    )

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

    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=domain_projection_hash,
    )
    if opgi is None:
        raise RuntimeError(
            f"Missing required OPGI on runtime bundle: projection_hash={domain_projection_hash}"
        )

    execute_started = time.monotonic()
    change_set = await _project_oigi_history_change_set(
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
    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=head_oig_id,
        ocg=index.ocg,
        opg=oigi_opg,
        change_set=change_set,
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
    _record_perf(
        perf_ms,
        f"{perf_metric_prefix}_build_changes_ms",
        started=build_changes_started,
    )
    if not changes:
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

    committer = FSLaneCommitter()
    fs_commit_started = time.monotonic()
    oigi_lane_commit = await committer.commit(
        branch_id=domain_oig_id,
        projection_hash=oigi_projection_hash,
        object_instance_graph_identity_id=head_oig_id,
        object_instance_graph_id=before_oig.id,
        before_oig=before_oig,
        root_object_id=resolve_root_source_object_id(before_oig),
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=author_id,
        commit_action=commit_action,
    )
    if oigi_lane_commit is not None:
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
            oigi_lane_commit_id=oigi_lane_commit.commit.id,
            oigi_graph_hash_post=oigi_lane_commit.graph_hash_post,
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
