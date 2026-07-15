from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_history_ontology.lane.lane import Lane
from aware_meta.graph.projection.branching import stable_portal_target_branch_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.commit.identity_lane import (
    resolve_object_instance_graph_identity_lane_context,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oigb_relationship_lane import attach_oigb_relationship
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_branch_id
from aware_orm.session.session import Session


@dataclass(frozen=True, slots=True)
class MetaPortalResolvedLaneRef:
    source_object_instance_graph_id: UUID
    source_object_instance_graph_identity_id: UUID
    source_object_instance_graph_branch_id: UUID
    relationship_id: UUID
    target_object_instance_graph_branch_id: UUID
    target_branch_id: UUID
    target_projection_hash: str
    target_lane_id: UUID
    target_head_commit_id: UUID
    target_object_instance_graph_id: UUID
    target_root_object_id: UUID | None
    target_graph_hash_post: str


@dataclass(frozen=True, slots=True)
class MetaPortalTargetBranchRef:
    source_object_instance_graph_id: UUID
    target_object_projection_graph_identity_id: UUID
    target_object_id: UUID
    target_branch_id: UUID
    target_projection_hash: str


@dataclass(frozen=True, slots=True)
class _TargetLaneHeadRef:
    branch_id: UUID
    projection_hash: str
    head_commit_id: UUID
    object_instance_graph_id: UUID
    root_object_id: UUID | None
    graph_hash_post: str


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


def _required_string_from_mapping(
    mapping: Mapping[str, object] | None,
    key: str,
    *,
    context: str,
) -> str:
    if mapping is None:
        raise RuntimeError(f"Missing or invalid {key} ({context})")
    raw = mapping.get(key)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    raise RuntimeError(f"Missing or invalid {key} ({context})")


def _required_uuid_attr(instance: object, field_name: str, *, context: str) -> UUID:
    value = getattr(instance, field_name, None)
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    raise RuntimeError(f"Missing or invalid {field_name} ({context})")


def _optional_uuid_attr(instance: object, field_name: str) -> UUID | None:
    value = getattr(instance, field_name, None)
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return None


def _required_string_attr(instance: object, field_name: str, *, context: str) -> str:
    value = getattr(instance, field_name, None)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise RuntimeError(f"Missing or invalid {field_name} ({context})")


def _list_attr(instance: object, field_name: str) -> tuple[object, ...]:
    value = getattr(instance, field_name, None)
    if value is None:
        return ()
    if isinstance(value, list | tuple):
        return tuple(value)
    raise RuntimeError(f"Invalid {field_name}: expected list")


async def resolve_portal_target_lane_ref(
    *,
    index: MetaGraphRuntimeIndex,
    source_domain_branch_id: UUID,
    source_projection_hash: str,
    target_domain_branch_id: UUID | None = None,
    target_projection_hash: str | None = None,
    target_class_config_id: UUID | None = None,
    target_object_id: UUID | None = None,
    source_store: FSCommitStore | None = None,
    target_store: FSCommitStore | None = None,
) -> MetaPortalResolvedLaneRef:
    """Resolve one target lane from committed OIGB relationship truth.

    The resolver is intentionally read-only. It does not synthesize branches,
    inspect package manifests, or infer target ids from semantic naming.
    """

    candidates = await resolve_portal_target_lane_refs(
        index=index,
        source_domain_branch_id=source_domain_branch_id,
        source_projection_hash=source_projection_hash,
        target_domain_branch_id=target_domain_branch_id,
        target_projection_hash=target_projection_hash,
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
        source_store=source_store,
        target_store=target_store,
    )
    if len(candidates) > 1:
        details = ", ".join(
            f"{candidate.target_branch_id}:{candidate.target_projection_hash}"
            for candidate in candidates
        )
        raise RuntimeError(
            "Ambiguous committed portal target lane relationships: " + details
        )
    return candidates[0]


async def resolve_portal_target_lane_refs(
    *,
    index: MetaGraphRuntimeIndex,
    source_domain_branch_id: UUID,
    source_projection_hash: str,
    target_domain_branch_id: UUID | None = None,
    target_projection_hash: str | None = None,
    target_class_config_id: UUID | None = None,
    target_object_id: UUID | None = None,
    source_store: FSCommitStore | None = None,
    target_store: FSCommitStore | None = None,
) -> tuple[MetaPortalResolvedLaneRef, ...]:
    """Resolve matching target lanes from committed OIGB relationship truth."""

    if (target_class_config_id is None) != (target_object_id is None):
        raise ValueError(
            "target_class_config_id and target_object_id must be provided together"
        )

    ctx = resolve_object_instance_graph_identity_lane_context(index=index)
    if ctx is None:
        raise RuntimeError("Missing required projection: ObjectInstanceGraphIdentity")

    store = source_store or FSCommitStore()
    target_commit_store = target_store or store
    source_head = await store.head(
        branch_id=source_domain_branch_id,
        projection_hash=source_projection_hash,
    )
    source_head_mapping = source_head if isinstance(source_head, Mapping) else None
    source_oig_id = _required_uuid_from_mapping(
        source_head_mapping,
        "object_instance_graph_id",
        context=(
            "source lane HEAD object_instance_graph_id "
            "(required to resolve portal source identity): "
            + f"source_domain_branch_id={source_domain_branch_id} "
            + f"source_projection_hash={source_projection_hash}"
        ),
    )

    identity_head = await store.head(
        branch_id=source_oig_id,
        projection_hash=ctx.projection_hash,
    )
    identity_head_mapping = (
        identity_head if isinstance(identity_head, Mapping) else None
    )
    identity_commit_id = _required_uuid_from_mapping(
        identity_head_mapping,
        "commit_id",
        context=(
            "source ObjectInstanceGraphIdentity lane HEAD commit_id "
            "(required to resolve portal branch relationships): "
            + f"object_instance_graph_id={source_oig_id} "
            + f"projection_hash={ctx.projection_hash}"
        ),
    )
    source_oigi_id = _required_uuid_from_mapping(
        identity_head_mapping,
        "object_instance_graph_id",
        context=(
            "source ObjectInstanceGraphIdentity lane HEAD object_instance_graph_id: "
            + f"object_instance_graph_id={source_oig_id} "
            + f"projection_hash={ctx.projection_hash}"
        ),
    )

    before_oig, _indexes = await OIGMaterializer(commits=store).get(
        branch_id=source_oig_id,
        ocg=index.ocg,
        opg=ctx.opg,
        commit_id=identity_commit_id,
        oig_id=source_oigi_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=ctx.opg,
        oig=before_oig,
        branch_id=source_oig_id,
    )
    source_oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=source_oigi_id,
        branch_id=source_domain_branch_id,
    )
    source_oigb = session.imap_get(ObjectInstanceGraphBranch, source_oigb_id)
    if source_oigb is None:
        raise RuntimeError(
            "Source ObjectInstanceGraphBranch missing from committed "
            "ObjectInstanceGraphIdentity lane: "
            + f"source_object_instance_graph_branch_id={source_oigb_id}"
        )

    return await _resolve_target_lane_refs(
        index=index,
        target_store=target_commit_store,
        session=session,
        source_oig_id=source_oig_id,
        source_oigi_id=source_oigi_id,
        source_oigb=source_oigb,
        source_oigb_id=source_oigb_id,
        target_domain_branch_id=target_domain_branch_id,
        target_projection_hash=target_projection_hash,
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
    )


async def resolve_portal_target_branch_ref_for_object(
    *,
    index: MetaGraphRuntimeIndex,
    source_domain_branch_id: UUID,
    source_projection_hash: str,
    target_projection_hash: str,
    target_object_id: UUID,
    source_object_instance_graph_id: UUID | None = None,
    source_store: FSCommitStore | None = None,
) -> MetaPortalTargetBranchRef:
    """Resolve the deterministic target branch for a portal target object."""

    if not target_projection_hash.strip():
        raise ValueError("target_projection_hash is required")

    source_oig_id = source_object_instance_graph_id
    if source_oig_id is None:
        store = source_store or FSCommitStore()
        source_head = await store.head(
            branch_id=source_domain_branch_id,
            projection_hash=source_projection_hash,
        )
        source_oig_id = _required_uuid_from_mapping(
            source_head if isinstance(source_head, Mapping) else None,
            "object_instance_graph_id",
            context=(
                "source lane HEAD object_instance_graph_id "
                "(required to derive portal target branch): "
                + f"source_domain_branch_id={source_domain_branch_id} "
                + f"source_projection_hash={source_projection_hash}"
            ),
        )

    _target_ocgi, target_opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=target_projection_hash,
    )
    if target_opgi is None:
        raise RuntimeError(
            "Portal target ObjectProjectionGraphIdentity missing: "
            + f"target_projection_hash={target_projection_hash}"
        )

    target_branch_id = stable_portal_target_branch_id(
        object_instance_graph_id=source_oig_id,
        object_projection_graph_identity_id=target_opgi.id,
        target_object_id=target_object_id,
    )
    return MetaPortalTargetBranchRef(
        source_object_instance_graph_id=source_oig_id,
        target_object_projection_graph_identity_id=target_opgi.id,
        target_object_id=target_object_id,
        target_branch_id=target_branch_id,
        target_projection_hash=target_projection_hash,
    )


async def attach_portal_target_branch_relationship_for_object(
    *,
    index: MetaGraphRuntimeIndex,
    author_id: UUID,
    source_domain_branch_id: UUID,
    source_projection_hash: str,
    target_projection_hash: str,
    target_object_id: UUID,
    source_object_instance_graph_id: UUID | None = None,
    target_domain_branch_id: UUID | None = None,
    source_store: FSCommitStore | None = None,
    target_store: FSCommitStore | None = None,
) -> MetaPortalTargetBranchRef:
    """Attach a source->target OIGB relation for a deterministic portal target."""

    branch_ref = await resolve_portal_target_branch_ref_for_object(
        index=index,
        source_domain_branch_id=source_domain_branch_id,
        source_projection_hash=source_projection_hash,
        source_object_instance_graph_id=source_object_instance_graph_id,
        source_store=source_store,
        target_projection_hash=target_projection_hash,
        target_object_id=target_object_id,
    )
    if (
        target_domain_branch_id is not None
        and target_domain_branch_id != branch_ref.target_branch_id
    ):
        raise RuntimeError(
            "Portal target branch mismatch for object relationship attach: "
            + f"expected={branch_ref.target_branch_id} "
            + f"actual={target_domain_branch_id} "
            + f"target_projection_hash={target_projection_hash} "
            + f"target_object_id={target_object_id}"
        )

    await attach_oigb_relationship(
        index=index,
        author_id=author_id,
        source_domain_branch_id=source_domain_branch_id,
        source_projection_hash=source_projection_hash,
        target_domain_branch_id=branch_ref.target_branch_id,
        target_projection_hash=target_projection_hash,
        source_store=source_store,
        target_store=target_store,
    )
    return branch_ref


async def resolve_portal_target_lane_ref_for_object(
    *,
    index: MetaGraphRuntimeIndex,
    source_domain_branch_id: UUID,
    source_projection_hash: str,
    target_projection_hash: str,
    target_class_config_id: UUID,
    target_object_id: UUID,
    target_domain_branch_id: UUID | None = None,
    source_store: FSCommitStore | None = None,
    target_store: FSCommitStore | None = None,
) -> MetaPortalResolvedLaneRef:
    """Resolve a committed portal target lane and verify it contains an object."""

    lane_ref = await resolve_portal_target_lane_ref(
        index=index,
        source_domain_branch_id=source_domain_branch_id,
        source_projection_hash=source_projection_hash,
        target_domain_branch_id=target_domain_branch_id,
        target_projection_hash=target_projection_hash,
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
        source_store=source_store,
        target_store=target_store,
    )
    return lane_ref


async def ensure_portal_target_lane_ref_for_object(
    *,
    index: MetaGraphRuntimeIndex,
    author_id: UUID,
    source_domain_branch_id: UUID,
    source_projection_hash: str,
    target_projection_hash: str,
    target_class_config_id: UUID,
    target_object_id: UUID,
    target_domain_branch_id: UUID | None = None,
    source_store: FSCommitStore | None = None,
    target_store: FSCommitStore | None = None,
) -> MetaPortalResolvedLaneRef:
    """Ensure and resolve a portal relationship to an existing target object.

    This is a Meta-owned write facade. Callers provide explicit portal/object
    coordinates; Meta resolves the target branch from committed lane truth and
    owns the OIGB relationship append.
    """

    if not target_projection_hash.strip():
        raise ValueError("target_projection_hash is required")

    source_commit_store = source_store or FSCommitStore()
    target_commit_store = target_store or source_commit_store
    resolved_target_branch_id = await _resolve_target_domain_branch_id_for_object(
        index=index,
        store=target_commit_store,
        target_projection_hash=target_projection_hash,
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
        requested_target_branch_id=target_domain_branch_id,
    )
    await attach_oigb_relationship(
        index=index,
        author_id=author_id,
        source_domain_branch_id=source_domain_branch_id,
        source_projection_hash=source_projection_hash,
        target_domain_branch_id=resolved_target_branch_id,
        target_projection_hash=target_projection_hash,
        source_store=source_commit_store,
        target_store=target_commit_store,
    )
    return await resolve_portal_target_lane_ref_for_object(
        index=index,
        source_domain_branch_id=source_domain_branch_id,
        source_projection_hash=source_projection_hash,
        target_domain_branch_id=resolved_target_branch_id,
        target_projection_hash=target_projection_hash,
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
        source_store=source_commit_store,
        target_store=target_commit_store,
    )


async def _resolve_target_domain_branch_id_for_object(
    *,
    index: MetaGraphRuntimeIndex,
    store: FSCommitStore,
    target_projection_hash: str,
    target_class_config_id: UUID,
    target_object_id: UUID,
    requested_target_branch_id: UUID | None,
) -> UUID:
    candidate_branch_ids: list[UUID] = []
    async for branch_id, _head in store.iter_lane_heads_by_projection(
        projection_hash=target_projection_hash
    ):
        candidate_branch_ids.append(branch_id)
    candidate_branch_ids = sorted(set(candidate_branch_ids), key=str)
    if not candidate_branch_ids:
        raise RuntimeError(
            "No committed lane heads found for portal target projection: "
            + f"target_projection_hash={target_projection_hash}"
        )

    if requested_target_branch_id is not None:
        if requested_target_branch_id not in candidate_branch_ids:
            raise RuntimeError(
                "Requested portal target branch is not reachable via committed "
                "target projection heads: "
                + f"requested_target_branch_id={requested_target_branch_id} "
                + f"target_projection_hash={target_projection_hash} "
                + f"candidate_branch_ids={sorted([str(v) for v in candidate_branch_ids])}"
            )
        lane_ref = await _target_lane_head_ref_from_head(
            store=store,
            branch_id=requested_target_branch_id,
            projection_hash=target_projection_hash,
        )
        if not await _target_lane_contains_object_by_ref(
            index=index,
            store=store,
            target_branch_id=lane_ref.branch_id,
            target_projection_hash=lane_ref.projection_hash,
            target_head_commit_id=lane_ref.head_commit_id,
            target_object_instance_graph_id=lane_ref.object_instance_graph_id,
            target_root_object_id=lane_ref.root_object_id,
            target_class_config_id=target_class_config_id,
            target_object_id=target_object_id,
        ):
            raise RuntimeError(
                "Requested portal target branch does not contain the requested "
                "target object: "
                + f"requested_target_branch_id={requested_target_branch_id} "
                + f"target_projection_hash={target_projection_hash} "
                + f"target_class_config_id={target_class_config_id} "
                + f"target_object_id={target_object_id}"
            )
        return requested_target_branch_id

    root_matches: list[UUID] = []
    for candidate_branch_id in candidate_branch_ids:
        head = await store.head(
            branch_id=candidate_branch_id,
            projection_hash=target_projection_hash,
        )
        root_id = _optional_uuid_from_mapping(
            head if isinstance(head, Mapping) else None,
            "root_object_id",
        )
        if root_id == target_object_id:
            root_matches.append(candidate_branch_id)
    if len(root_matches) == 1:
        return root_matches[0]
    if len(root_matches) > 1:
        raise RuntimeError(
            "Ambiguous portal target branch routing: multiple branches share "
            "the requested root_object_id. Pass target_domain_branch_id "
            "explicitly. "
            + f"target_object_id={target_object_id} "
            + f"target_projection_hash={target_projection_hash} "
            + f"candidate_branch_ids={sorted([str(v) for v in root_matches])}"
        )

    deep_matches: list[UUID] = []
    for candidate_branch_id in candidate_branch_ids:
        lane_ref = await _target_lane_head_ref_from_head(
            store=store,
            branch_id=candidate_branch_id,
            projection_hash=target_projection_hash,
        )
        if await _target_lane_contains_object_by_ref(
            index=index,
            store=store,
            target_branch_id=lane_ref.branch_id,
            target_projection_hash=lane_ref.projection_hash,
            target_head_commit_id=lane_ref.head_commit_id,
            target_object_instance_graph_id=lane_ref.object_instance_graph_id,
            target_root_object_id=lane_ref.root_object_id,
            target_class_config_id=target_class_config_id,
            target_object_id=target_object_id,
        ):
            deep_matches.append(candidate_branch_id)
    if len(deep_matches) == 1:
        return deep_matches[0]
    if len(deep_matches) > 1:
        raise RuntimeError(
            "Ambiguous portal target branch routing: requested target object "
            "exists in multiple branches. Pass target_domain_branch_id "
            "explicitly. "
            + f"target_object_id={target_object_id} "
            + f"target_projection_hash={target_projection_hash} "
            + f"candidate_branch_ids={sorted([str(v) for v in deep_matches])}"
        )

    raise RuntimeError(
        "Portal target object not found in any committed target lane: "
        + f"target_object_id={target_object_id} "
        + f"target_projection_hash={target_projection_hash} "
        + f"candidate_branch_ids={sorted([str(v) for v in candidate_branch_ids])}"
    )


async def _target_lane_head_ref_from_head(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
) -> _TargetLaneHeadRef:
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    head_mapping = head if isinstance(head, Mapping) else None
    commit_id = _required_uuid_from_mapping(
        head_mapping,
        "commit_id",
        context=(
            "portal target lane HEAD commit_id: "
            + f"target_branch_id={branch_id} "
            + f"target_projection_hash={projection_hash}"
        ),
    )
    oig_id = _required_uuid_from_mapping(
        head_mapping,
        "object_instance_graph_id",
        context=(
            "portal target lane HEAD object_instance_graph_id: "
            + f"target_branch_id={branch_id} "
            + f"target_projection_hash={projection_hash}"
        ),
    )
    graph_hash_post = _required_string_from_mapping(
        head_mapping,
        "graph_hash_post",
        context=(
            "portal target lane HEAD graph_hash_post: "
            + f"target_branch_id={branch_id} "
            + f"target_projection_hash={projection_hash}"
        ),
    )
    return _TargetLaneHeadRef(
        branch_id=branch_id,
        projection_hash=projection_hash,
        head_commit_id=commit_id,
        object_instance_graph_id=oig_id,
        root_object_id=_optional_uuid_from_mapping(
            head_mapping,
            "root_object_id",
        ),
        graph_hash_post=graph_hash_post,
    )


async def _target_lane_contains_object_by_ref(
    *,
    index: MetaGraphRuntimeIndex,
    store: FSCommitStore,
    target_branch_id: UUID,
    target_projection_hash: str,
    target_head_commit_id: UUID,
    target_object_instance_graph_id: UUID,
    target_root_object_id: UUID | None,
    target_class_config_id: UUID,
    target_object_id: UUID,
) -> bool:
    if target_root_object_id == target_object_id:
        return True
    target_opg = index.opg_by_hash.get(target_projection_hash)
    if target_opg is None:
        raise RuntimeError(
            "ObjectProjectionGraph not found for resolved portal target lane: "
            + f"projection_hash={target_projection_hash}"
        )
    target_oig, _indexes = await OIGMaterializer(commits=store).get(
        branch_id=target_branch_id,
        ocg=index.ocg,
        opg=target_opg,
        commit_id=target_head_commit_id,
        oig_id=target_object_instance_graph_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return _lane_contains_target_object(
        oig=target_oig,
        target_class_config_id=target_class_config_id,
        target_object_id=target_object_id,
    )


def _lane_contains_target_object(
    *,
    oig: object,
    target_class_config_id: UUID,
    target_object_id: UUID,
) -> bool:
    class_instances = getattr(oig, "class_instances", None) or []
    for class_instance in class_instances:
        if getattr(class_instance, "class_config_id", None) != target_class_config_id:
            continue
        if getattr(class_instance, "id", None) == target_object_id:
            return True
        if getattr(class_instance, "source_object_id", None) == target_object_id:
            return True
    return False


async def _resolve_target_lane_refs(
    *,
    index: MetaGraphRuntimeIndex,
    target_store: FSCommitStore,
    session: Session,
    source_oig_id: UUID,
    source_oigi_id: UUID,
    source_oigb: object,
    source_oigb_id: UUID,
    target_domain_branch_id: UUID | None,
    target_projection_hash: str | None,
    target_class_config_id: UUID | None,
    target_object_id: UUID | None,
) -> MetaPortalResolvedLaneRef:
    candidates: list[MetaPortalResolvedLaneRef] = []
    relationships = _list_attr(
        source_oigb, "object_instance_graph_branch_relationships"
    )
    for relationship in relationships:
        relationship_id = _required_uuid_attr(
            relationship,
            "id",
            context="ObjectInstanceGraphBranchRelationship id",
        )
        relationship_source_oigb_id = getattr(
            relationship, "object_instance_graph_branch_id", None
        )
        if (
            relationship_source_oigb_id is not None
            and relationship_source_oigb_id != source_oigb_id
        ):
            raise RuntimeError(
                "Portal branch relationship source mismatch: "
                + f"relationship_id={relationship_id} "
                + f"have={relationship_source_oigb_id} expected={source_oigb_id}"
            )
        target_oigb_id = _required_uuid_attr(
            relationship,
            "target_object_instance_graph_branch_id",
            context=(
                "ObjectInstanceGraphBranchRelationship target "
                + f"relationship_id={relationship_id}"
            ),
        )
        target_oigb = getattr(relationship, "target_object_instance_graph_branch", None)
        if target_oigb is None:
            target_oigb = session.imap_get(ObjectInstanceGraphBranch, target_oigb_id)
        if target_oigb is None:
            raise RuntimeError(
                "Portal target ObjectInstanceGraphBranch missing from committed "
                "OIGI lane: "
                + f"relationship_id={relationship_id} "
                + f"target_object_instance_graph_branch_id={target_oigb_id}"
            )
        target_branch_id = _required_uuid_attr(
            target_oigb,
            "branch_id",
            context=(
                "portal target ObjectInstanceGraphBranch branch_id "
                + f"target_object_instance_graph_branch_id={target_oigb_id}"
            ),
        )
        if (
            target_domain_branch_id is not None
            and target_branch_id != target_domain_branch_id
        ):
            continue
        for candidate in await _target_lane_refs_for_oigb(
            store=target_store,
            source_oig_id=source_oig_id,
            source_oigi_id=source_oigi_id,
            source_oigb_id=source_oigb_id,
            relationship_id=relationship_id,
            target_oigb=target_oigb,
            target_oigb_id=target_oigb_id,
            target_branch_id=target_branch_id,
            target_projection_hash=target_projection_hash,
        ):
            candidates.append(candidate)

    if target_class_config_id is not None and target_object_id is not None:
        matching_candidates: list[MetaPortalResolvedLaneRef] = []
        for candidate in candidates:
            if await _target_lane_contains_object_by_ref(
                index=index,
                store=target_store,
                target_branch_id=candidate.target_branch_id,
                target_projection_hash=candidate.target_projection_hash,
                target_head_commit_id=candidate.target_head_commit_id,
                target_object_instance_graph_id=(
                    candidate.target_object_instance_graph_id
                ),
                target_root_object_id=candidate.target_root_object_id,
                target_class_config_id=target_class_config_id,
                target_object_id=target_object_id,
            ):
                matching_candidates.append(candidate)
        candidates = matching_candidates

    if not candidates:
        raise RuntimeError(
            "No committed portal target lane relationship matched source lane: "
            + f"source_object_instance_graph_branch_id={source_oigb_id} "
            + f"target_domain_branch_id={target_domain_branch_id} "
            + f"target_projection_hash={target_projection_hash} "
            + f"target_object_id={target_object_id}"
        )
    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.target_projection_hash,
                str(candidate.target_branch_id),
                str(candidate.relationship_id),
            ),
        )
    )


async def _target_lane_refs_for_oigb(
    *,
    store: FSCommitStore,
    source_oig_id: UUID,
    source_oigi_id: UUID,
    source_oigb_id: UUID,
    relationship_id: UUID,
    target_oigb: object,
    target_oigb_id: UUID,
    target_branch_id: UUID,
    target_projection_hash: str | None,
) -> tuple[MetaPortalResolvedLaneRef, ...]:
    lane_refs: list[MetaPortalResolvedLaneRef] = []
    object_instance_graph_lanes = _list_attr(target_oigb, "object_instance_graph_lanes")
    if not object_instance_graph_lanes:
        raise RuntimeError(
            "Portal target ObjectInstanceGraphBranch has no lane refs: "
            + f"target_object_instance_graph_branch_id={target_oigb_id}"
        )

    for oig_lane in object_instance_graph_lanes:
        lane_id = _required_uuid_attr(
            oig_lane,
            "lane_id",
            context=(
                "portal target ObjectInstanceGraphLane lane_id "
                + f"target_object_instance_graph_branch_id={target_oigb_id}"
            ),
        )
        lane = getattr(oig_lane, "lane", None)
        if lane is None:
            raise RuntimeError(
                "Portal target ObjectInstanceGraphLane missing Lane object: "
                + f"lane_id={lane_id}"
            )
        if not isinstance(lane, Lane) and not hasattr(lane, "lane_hash"):
            raise RuntimeError(f"Invalid portal target lane object: lane_id={lane_id}")
        lane_branch_id = _required_uuid_attr(
            lane,
            "branch_id",
            context=f"portal target Lane branch_id lane_id={lane_id}",
        )
        if lane_branch_id != target_branch_id:
            raise RuntimeError(
                "Portal target OIGB/Lane branch mismatch: "
                + f"target_oigb_id={target_oigb_id} "
                + f"target_branch_id={target_branch_id} lane_branch_id={lane_branch_id}"
            )
        projection_hash = _required_string_attr(
            lane,
            "lane_hash",
            context=f"portal target Lane lane_hash lane_id={lane_id}",
        )
        if (
            target_projection_hash is not None
            and projection_hash != target_projection_hash
        ):
            continue
        lane_head_commit_id = _optional_uuid_attr(lane, "head_commit_id")
        target_head = await store.head(
            branch_id=target_branch_id,
            projection_hash=projection_hash,
        )
        target_head_mapping = target_head if isinstance(target_head, Mapping) else None
        target_head_commit_id = _required_uuid_from_mapping(
            target_head_mapping,
            "commit_id",
            context=(
                "portal target lane HEAD commit_id: "
                + f"target_branch_id={target_branch_id} "
                + f"target_projection_hash={projection_hash}"
            ),
        )
        if (
            lane_head_commit_id is not None
            and target_head_commit_id != lane_head_commit_id
        ):
            raise RuntimeError(
                "Portal target Lane head does not match commit-store HEAD: "
                + f"lane_id={lane_id} lane_head_commit_id={lane_head_commit_id} "
                + f"store_head_commit_id={target_head_commit_id}"
            )
        target_oig_id = _required_uuid_from_mapping(
            target_head_mapping,
            "object_instance_graph_id",
            context=(
                "portal target lane HEAD object_instance_graph_id: "
                + f"target_branch_id={target_branch_id} "
                + f"target_projection_hash={projection_hash}"
            ),
        )
        target_root_object_id = _optional_uuid_from_mapping(
            target_head_mapping,
            "root_object_id",
        )
        target_graph_hash_post = _required_string_from_mapping(
            target_head_mapping,
            "graph_hash_post",
            context=(
                "portal target lane HEAD graph_hash_post: "
                + f"target_branch_id={target_branch_id} "
                + f"target_projection_hash={projection_hash}"
            ),
        )
        lane_refs.append(
            MetaPortalResolvedLaneRef(
                source_object_instance_graph_id=source_oig_id,
                source_object_instance_graph_identity_id=source_oigi_id,
                source_object_instance_graph_branch_id=source_oigb_id,
                relationship_id=relationship_id,
                target_object_instance_graph_branch_id=target_oigb_id,
                target_branch_id=target_branch_id,
                target_projection_hash=projection_hash,
                target_lane_id=lane_id,
                target_head_commit_id=target_head_commit_id,
                target_object_instance_graph_id=target_oig_id,
                target_root_object_id=target_root_object_id,
                target_graph_hash_post=target_graph_hash_post,
            )
        )
    return tuple(lane_refs)


__all__ = [
    "attach_portal_target_branch_relationship_for_object",
    "ensure_portal_target_lane_ref_for_object",
    "MetaPortalTargetBranchRef",
    "MetaPortalResolvedLaneRef",
    "resolve_portal_target_branch_ref_for_object",
    "resolve_portal_target_lane_ref",
    "resolve_portal_target_lane_refs",
    "resolve_portal_target_lane_ref_for_object",
]
