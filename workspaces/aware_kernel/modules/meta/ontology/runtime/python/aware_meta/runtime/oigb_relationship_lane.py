from __future__ import annotations

from collections.abc import Mapping
from typing import cast
from uuid import UUID

from aware_history_ontology.branch.branch import Branch
from aware_history_ontology.lane.lane import Lane
from aware_history_ontology.stable_ids import stable_lane_id
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.root import resolve_root_source_object_id
from aware_meta.runtime.commit.identity_lane import (
    resolve_object_instance_graph_identity_lane_context,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)
from aware_meta_ontology.graph.instance.object_instance_graph_branch_relationship import (
    ObjectInstanceGraphBranchRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.graph.instance.object_instance_graph_lane import (
    ObjectInstanceGraphLane,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_branch_relationship_id,
    stable_object_instance_graph_lane_id,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.execution_guard import allow_domain_create, disallow_push
from aware_orm.session.session import Session


def _optional_uuid_from_mapping(
    mapping: Mapping[str, object] | None,
    key: str,
) -> UUID | None:
    if mapping is None:
        return None
    raw = mapping.get(key)
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw)
    return None


def _required_uuid_from_mapping(
    mapping: Mapping[str, object] | None,
    key: str,
    *,
    context: str,
) -> UUID:
    value = _optional_uuid_from_mapping(mapping, key)
    if value is None:
        raise RuntimeError(f"Missing or invalid {key} ({context})")
    return value


def _append_unique_by_id(items: list[BaseORMModel], instance: BaseORMModel) -> None:
    instance_id = instance.id
    if all(existing.id != instance_id for existing in items):
        items.append(instance)


def _bind_new(session: Session, instance: BaseORMModel) -> BaseORMModel:
    session.imap_add(instance)
    return instance


def _ensure_branch_lane_shadow(
    *,
    session: Session,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    object_instance_graph_identity_id: UUID,
    branch_id: UUID,
    lane_hash: str,
    head_commit_id: UUID,
) -> ObjectInstanceGraphBranch:
    lane_id = stable_lane_id(branch_id=branch_id, lane_hash=lane_hash)

    branch = session.imap_get(Branch, branch_id)
    if branch is None:
        branch = cast(
            Branch,
            _bind_new(
                session,
                Branch(
                    id=branch_id,
                    key="default",
                    is_main=False,
                    name=None,
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
                    branch_id=branch_id,
                    lane_hash=lane_hash,
                ),
            ),
        )
    elif lane.branch_id != branch_id or lane.lane_hash != lane_hash:
        raise RuntimeError(
            "ObjectInstanceGraphBranch relationship lane mismatch: "
            + f"lane_id={lane_id} branch_id={lane.branch_id} lane_hash={lane.lane_hash!r}"
        )
    if lane.head_commit_id != head_commit_id:
        lane.head_commit_id = head_commit_id
    _append_unique_by_id(cast(list[BaseORMModel], branch.lanes), lane)

    oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=branch_id,
    )
    oigb = session.imap_get(ObjectInstanceGraphBranch, oigb_id)
    if oigb is None:
        oigb = cast(
            ObjectInstanceGraphBranch,
            _bind_new(
                session,
                ObjectInstanceGraphBranch(
                    id=oigb_id,
                    object_instance_graph_identity_id=object_instance_graph_identity_id,
                    branch=branch,
                    branch_id=branch_id,
                ),
            ),
        )
    elif oigb.object_instance_graph_identity_id != object_instance_graph_identity_id:
        raise RuntimeError(
            "ObjectInstanceGraphBranch relationship OIGB mismatch: "
            + f"oigb_id={oigb_id} have={oigb.object_instance_graph_identity_id} "
            + f"expected={object_instance_graph_identity_id}"
        )
    _append_unique_by_id(
        cast(
            list[BaseORMModel],
            object_instance_graph_identity.object_instance_graph_branches,
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
    _append_unique_by_id(
        cast(list[BaseORMModel], oigb.object_instance_graph_lanes), oigl
    )
    return oigb


def _ensure_branch_relationship(
    *,
    session: Session,
    source_oigb: ObjectInstanceGraphBranch,
    target_oigb: ObjectInstanceGraphBranch,
) -> ObjectInstanceGraphBranchRelationship:
    source_oigb_id = source_oigb.id
    target_oigb_id = target_oigb.id
    if source_oigb_id is None or target_oigb_id is None:
        raise RuntimeError(
            "ObjectInstanceGraphBranch relationship requires source and target ids"
        )

    for existing in source_oigb.object_instance_graph_branch_relationships:
        if existing.target_object_instance_graph_branch_id == target_oigb_id:
            return existing

    rel_id = stable_object_instance_graph_branch_relationship_id(
        object_instance_graph_branch_id=source_oigb_id,
        target_object_instance_graph_branch_id=target_oigb_id,
    )
    relationship = session.imap_get(ObjectInstanceGraphBranchRelationship, rel_id)
    if relationship is None:
        relationship = cast(
            ObjectInstanceGraphBranchRelationship,
            _bind_new(
                session,
                ObjectInstanceGraphBranchRelationship(
                    id=rel_id,
                    object_instance_graph_branch_id=source_oigb_id,
                    target_object_instance_graph_branch=target_oigb,
                    target_object_instance_graph_branch_id=target_oigb_id,
                ),
            ),
        )
    _append_unique_by_id(
        cast(
            list[BaseORMModel], source_oigb.object_instance_graph_branch_relationships
        ),
        relationship,
    )
    return relationship


async def attach_oigb_relationship(
    *,
    index: MetaGraphRuntimeIndex,
    author_id: UUID,
    source_domain_branch_id: UUID,
    source_projection_hash: str,
    target_domain_branch_id: UUID,
    target_projection_hash: str | None = None,
) -> None:
    """Attach a Branch-to-Branch relationship in the source OIGI lane."""

    ctx = resolve_object_instance_graph_identity_lane_context(index=index)
    if ctx is None:
        raise RuntimeError("Missing required projection: ObjectInstanceGraphIdentity")

    store = FSCommitStore()
    source_head = await store.head(
        branch_id=source_domain_branch_id,
        projection_hash=source_projection_hash,
    )
    source_head_mapping = source_head if isinstance(source_head, Mapping) else None
    if source_head_mapping is None or not source_head_mapping.get(
        "object_instance_graph_id"
    ):
        raise RuntimeError(
            "Missing source lane HEAD object_instance_graph_id (required to resolve identity lane): "
            + f"source_domain_branch_id={source_domain_branch_id} source_projection_hash={source_projection_hash}"
        )
    source_head_commit_id = _required_uuid_from_mapping(
        source_head_mapping,
        "commit_id",
        context=(
            "source lane HEAD commit_id (required to shadow source branch in source identity lane): "
            + f"source_domain_branch_id={source_domain_branch_id} source_projection_hash={source_projection_hash}"
        ),
    )
    source_oig_id = _required_uuid_from_mapping(
        source_head_mapping,
        "object_instance_graph_id",
        context=(
            "source lane HEAD object_instance_graph_id (required to resolve identity lane): "
            + f"source_domain_branch_id={source_domain_branch_id} source_projection_hash={source_projection_hash}"
        ),
    )

    identity_head = await store.head(
        branch_id=source_oig_id,
        projection_hash=ctx.projection_hash,
    )
    identity_head_mapping = (
        identity_head if isinstance(identity_head, Mapping) else None
    )
    if identity_head_mapping is None or not identity_head_mapping.get("commit_id"):
        raise RuntimeError(
            "Missing object_instance_graph_identity lane HEAD (commit-first invariant): "
            + f"object_instance_graph_id={source_oig_id} projection_hash={ctx.projection_hash}"
        )

    head_commit_id = _required_uuid_from_mapping(
        identity_head_mapping,
        "commit_id",
        context=(
            "object_instance_graph_identity lane HEAD (commit-first invariant): "
            + f"object_instance_graph_id={source_oig_id} projection_hash={ctx.projection_hash}"
        ),
    )
    head_oig_id = _required_uuid_from_mapping(
        identity_head_mapping,
        "object_instance_graph_id",
        context=(
            "object_instance_graph_identity lane HEAD object_instance_graph_id: "
            + f"object_instance_graph_id={source_oig_id} projection_hash={ctx.projection_hash}"
        ),
    )

    target_head_commit_id: UUID | None = None
    if target_projection_hash is not None:
        target_head = await store.head(
            branch_id=target_domain_branch_id,
            projection_hash=target_projection_hash,
        )
        target_head_mapping = target_head if isinstance(target_head, Mapping) else None
        target_head_commit_id = _required_uuid_from_mapping(
            target_head_mapping,
            "commit_id",
            context=(
                "target lane HEAD commit_id (required to shadow target branch in source identity lane): "
                + f"target_domain_branch_id={target_domain_branch_id} target_projection_hash={target_projection_hash}"
            ),
        )

    before_oig, _indexes = await CachedLaneMaterializer().get(
        branch_id=source_oig_id,
        ocg=index.ocg,
        opg=ctx.opg,
        commit_id=head_commit_id,
        oig_id=head_oig_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=ctx.opg,
        oig=before_oig,
        branch_id=source_oig_id,
    )
    source_oigi = session.imap_get(ObjectInstanceGraphIdentity, head_oig_id)
    if source_oigi is None:
        raise RuntimeError(
            "Source ObjectInstanceGraphIdentity missing from reified identity lane: "
            + f"object_instance_graph_identity_id={head_oig_id}"
        )

    with disallow_push(), allow_domain_create():
        source_oigb = _ensure_branch_lane_shadow(
            session=session,
            object_instance_graph_identity=source_oigi,
            object_instance_graph_identity_id=head_oig_id,
            branch_id=source_domain_branch_id,
            lane_hash=source_projection_hash,
            head_commit_id=source_head_commit_id,
        )
        target_oigb = session.imap_get(
            ObjectInstanceGraphBranch,
            stable_object_instance_graph_branch_id(
                object_instance_graph_identity_id=head_oig_id,
                branch_id=target_domain_branch_id,
            ),
        )
        if target_projection_hash is not None and target_head_commit_id is not None:
            target_oigb = _ensure_branch_lane_shadow(
                session=session,
                object_instance_graph_identity=source_oigi,
                object_instance_graph_identity_id=head_oig_id,
                branch_id=target_domain_branch_id,
                lane_hash=target_projection_hash,
                head_commit_id=target_head_commit_id,
            )
        if target_oigb is None:
            raise RuntimeError(
                "Target ObjectInstanceGraphBranch missing from source identity lane: "
                + f"target_domain_branch_id={target_domain_branch_id}"
            )
        _ = _ensure_branch_relationship(
            session=session,
            source_oigb=source_oigb,
            target_oigb=target_oigb,
        )

    after_oig = build_object_instance_graph(
        root_instance=source_oigi,
        object_config_graph=index.ocg,
        object_projection_graph=ctx.opg,
        key=before_oig.key,
        name=before_oig.name,
        description=before_oig.description or "",
        oig_id=before_oig.id,
        instance_registry=session.imap_all_objects(),
        enum_option_resolver=default_meta_enum_option_resolver,
    )
    changes = diff_object_instance_graph_changes(
        old=before_oig,
        new=after_oig,
        object_instance_graph_identity_id=head_oig_id,
    )
    if not changes:
        return

    function_id: UUID | None = None
    for node in index.ocg.object_config_graph_nodes:
        cc = node.class_config
        if cc is None or cc.name != "ObjectInstanceGraphBranch":
            continue
        for link in cc.class_config_function_configs:
            if link.function_config.name == "attach_branch_relationship":
                function_id = link.function_config.id
                break
        if function_id is not None:
            break
    if function_id is None:
        raise RuntimeError(
            "FunctionConfig not found in OCG: class=ObjectInstanceGraphBranch "
            "function=attach_branch_relationship"
        )

    commit_action = CommitActionDescriptor(
        operation_label="ObjectInstanceGraphBranch.attach_branch_relationship",
        call_target="instance",
        function_id=function_id,
        object_id=stable_object_instance_graph_branch_id(
            object_instance_graph_identity_id=head_oig_id,
            branch_id=source_domain_branch_id,
        ),
    )
    _ = await FSLaneCommitter().commit(
        branch_id=source_oig_id,
        projection_hash=ctx.projection_hash,
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


__all__ = ["attach_oigb_relationship"]
