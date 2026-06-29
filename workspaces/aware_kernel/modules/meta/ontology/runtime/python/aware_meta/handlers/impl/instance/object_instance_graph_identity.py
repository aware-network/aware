from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import ObjectInstanceGraphChangeType
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_meta_ontology.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity
from aware_meta_ontology.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange
from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# History Ontology
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.lane.lane import Lane
from aware_history_ontology.stable_ids import stable_commit_id

# History
from aware_history.stable_ids import stable_lane_id

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_identity_id

# Meta
from aware_meta.graph.instance.commit.fs_store import FSCommitStore

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def upsert_history_from_lane_head(
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    lane_id: UUID,
    head_commit_id: UUID,
    branch_is_main: bool = False,
    branch_name: str | None = None,
) -> ObjectInstanceGraphIdentity:
    """
    Upsert the SSOT history plane for a domain lane head.

    Writes (in the `object_instance_graph_identity` projection):
    - OIGB (deterministic id) anchored to this OIGI
    - Branch + Lane(lane_hash=domain_projection_hash) with updated head_commit pointer
    - Commit DAG objects + OIGCommit wrappers for the head commit and any missing ancestors

    IMPORTANT:
    - Reads domain commit payloads from the node commit store (commit-first invariant).
    - Never authors domain commits.
    """

    # --- AWARE: LOGIC START upsert_history_from_lane_head
    oig_id = object_instance_graph_identity.id

    # Deterministic lane identity consistency guard.
    expected_lane_id = stable_lane_id(branch_id=domain_branch_id, lane_hash=domain_projection_hash)
    if lane_id != expected_lane_id:
        raise RuntimeError(
            "ObjectInstanceGraphIdentity.upsert_history_from_lane_head lane_id mismatch: "
            + f"have={lane_id} expected={expected_lane_id}"
        )

    # Ensure OIGB + history Branch/Lane exist (idempotent).
    oigb = await ObjectInstanceGraphBranch.create_with_lane_and_branch_via_object_instance_graph_identity(
        object_instance_graph_identity_id=oig_id,
        branch_id=domain_branch_id,
        lane_id=lane_id,
        commit_id=head_commit_id,
        lane_hash=domain_projection_hash,
        is_main=branch_is_main,
        name=branch_name,
    )
    if all(b.id != oigb.id for b in object_instance_graph_identity.object_instance_graph_branches):
        object_instance_graph_identity.object_instance_graph_branches.append(oigb)

    # Determine existing commit ledger coverage for this identity.
    existing_commit_ids: set[UUID] = set()
    for existing in object_instance_graph_identity.object_instance_graph_commits:
        commit_key = existing.commit.key
        try:
            existing_commit_ids.add(UUID(commit_key))
        except (TypeError, ValueError):
            continue
    existing_class_instance_ids: set[UUID] = set()
    for existing in object_instance_graph_identity.class_instance_identities:
        existing_class_instance_ids.add(existing.class_instance_id)

    store = FSCommitStore()
    to_visit: list[UUID] = [head_commit_id]
    visited: set[UUID] = set()

    while to_visit:
        cid = to_visit.pop()
        if cid in visited:
            continue
        visited.add(cid)

        if cid not in existing_commit_ids:
            oig_commit = await ObjectInstanceGraphCommit.create_via_object_instance_graph_identity(
                object_instance_graph_identity_id=oig_id,
                commit_id=cid,
                domain_branch_id=domain_branch_id,
                domain_projection_hash=domain_projection_hash,
            )
            if all(c.id != oig_commit.id for c in object_instance_graph_identity.object_instance_graph_commits):
                object_instance_graph_identity.object_instance_graph_commits.append(oig_commit)
            existing_commit_ids.add(cid)

        payload = await store.get_commit(
            branch_id=domain_branch_id,
            projection_hash=domain_projection_hash,
            commit_id=cid,
        )
        if payload is None:
            raise RuntimeError(
                "Missing domain commit while projecting OIG identity history plane: "
                + f"branch_id={domain_branch_id} projection_hash={domain_projection_hash} commit_id={cid}"
            )

        # Propagate class-instance identity rows under this OIGI from commit payload.
        for root_change in payload.object_instance_graph_changes:
            for class_change in root_change.class_instance_changes:
                class_instance_id = class_change.class_instance_id
                if class_instance_id in existing_class_instance_ids:
                    continue
                created = await object_instance_graph_identity.create_class_instance_identity(
                    class_instance_id=class_instance_id
                )
                existing_class_instance_ids.add(created.class_instance_id)

        for parent in payload.commit.commit_parents:
            parent_id = parent.parent_commit_id
            if parent_id in visited:
                continue
            to_visit.append(parent_id)

    # Advance the lane head pointer to match SSOT.
    session = current_handler_session()
    lane = session.imap_get(Lane, lane_id)
    if lane is None:
        raise RuntimeError(
            "Missing Lane after upserting OIGB history objects: "
            + f"domain_branch_id={domain_branch_id} lane_id={lane_id}"
        )

    history_head_commit_id = stable_commit_id(lane_id=lane_id, key=str(head_commit_id))
    projected_head_commit = session.imap_get(Commit, history_head_commit_id)
    if projected_head_commit is None:
        for existing in object_instance_graph_identity.object_instance_graph_commits:
            commit = existing.commit
            if commit is None or commit.id != history_head_commit_id:
                continue
            projected_head_commit = commit
            break
    if projected_head_commit is None:
        raise RuntimeError(
            "Missing projected history Commit while advancing OIGI lane head: "
            + f"history_commit_id={history_head_commit_id} domain_head_commit_id={head_commit_id}"
        )

    if lane.head_commit_id != history_head_commit_id or lane.head_commit is None:
        _ = await lane.advance_head(commit_id=history_head_commit_id)
    if lane.head_commit is None or lane.head_commit.id != history_head_commit_id:
        lane.head_commit = projected_head_commit

    return object_instance_graph_identity
    # --- AWARE: LOGIC END upsert_history_from_lane_head


async def create_class_instance_identity(
    object_instance_graph_identity: ObjectInstanceGraphIdentity, class_instance_id: UUID, label: str | None = None
) -> ClassInstanceIdentity:
    """
    Create one deterministic ClassInstanceIdentity under this ObjectInstanceGraphIdentity.

    Contract:
    - Parent-owned propagation edge for projection inclusion (`OIGI -> CII`).
    - Idempotent per `(object_instance_graph_identity_id, class_instance_id)`.
    """

    # --- AWARE: LOGIC START create_class_instance_identity
    oig_id = object_instance_graph_identity.id

    for existing in object_instance_graph_identity.class_instance_identities:
        if existing.class_instance_id != class_instance_id:
            continue
        if label is not None and existing.label != label:
            existing.label = label
        return existing

    created = await ClassInstanceIdentity.create_via_object_instance_graph_identity(
        object_instance_graph_identity_id=oig_id,
        class_instance_id=class_instance_id,
        label=label,
    )
    if all(existing.id != created.id for existing in object_instance_graph_identity.class_instance_identities):
        object_instance_graph_identity.class_instance_identities.append(created)
    return created
    # --- AWARE: LOGIC END create_class_instance_identity


async def create_class_instance_relationship_identity(
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    class_instance_relationship_id: UUID,
    label: str | None = None,
) -> ClassInstanceRelationshipIdentity:
    """
    Create one deterministic ClassInstanceRelationshipIdentity under this ObjectInstanceGraphIdentity.

    Contract:
    - Parent-owned propagation edge for projection inclusion (`OIGI -> CIRI`).
    - Idempotent per `(object_instance_graph_identity_id, class_instance_relationship_id)`.
    """

    # --- AWARE: LOGIC START create_class_instance_relationship_identity
    oig_id = object_instance_graph_identity.id

    for existing in object_instance_graph_identity.class_instance_relationship_identities:
        if existing.class_instance_relationship_id != class_instance_relationship_id:
            continue
        if label is not None and existing.label != label:
            existing.label = label
        return existing

    created = await ClassInstanceRelationshipIdentity.create_via_object_instance_graph_identity(
        object_instance_graph_identity_id=oig_id,
        class_instance_relationship_id=class_instance_relationship_id,
        label=label,
    )
    if all(
        existing.id != created.id for existing in object_instance_graph_identity.class_instance_relationship_identities
    ):
        object_instance_graph_identity.class_instance_relationship_identities.append(created)
    return created
    # --- AWARE: LOGIC END create_class_instance_relationship_identity


async def create_change(
    object_instance_graph_identity: ObjectInstanceGraphIdentity, change_id: UUID, type: ObjectInstanceGraphChangeType
) -> ObjectInstanceGraphChange:
    """
    Create one deterministic ObjectInstanceGraphChange under this ObjectInstanceGraphIdentity.

    Contract:
    - Parent-owned propagation edge for history-plane inclusion (`OIGI -> OIGChange`).
    - The change payload still targets the canonical OIG worldline referenced by this OIGI.
    - Deterministic identity resolves from `(object_instance_graph_identity_id via path, change_id)`.
    """

    # --- AWARE: LOGIC START create_change
    oig_id = object_instance_graph_identity.id

    for existing in object_instance_graph_identity.object_instance_graph_changes:
        if existing.change_id != change_id:
            continue
        if existing.type != type:
            raise RuntimeError(
                "ObjectInstanceGraphIdentity.create_change encountered mismatched existing change tree type: "
                + f"change_id={change_id} existing={existing.type} requested={type}"
            )
        return existing

    created = await ObjectInstanceGraphChange.create_via_object_instance_graph_identity(
        object_instance_graph_identity_id=oig_id,
        change_id=change_id,
        type=type,
    )
    if all(existing.id != created.id for existing in object_instance_graph_identity.object_instance_graph_changes):
        object_instance_graph_identity.object_instance_graph_changes.append(created)
    return created
    # --- AWARE: LOGIC END create_change


async def create_via_object_projection_graph_identity(
    object_projection_graph_identity_id: UUID, object_instance_graph_id: UUID, label: str | None = None
) -> ObjectInstanceGraphIdentity:
    """
    Create deterministic ObjectInstanceGraphIdentity for one ObjectInstanceGraph worldline.

    Contract:
    - `ObjectInstanceGraphIdentity.id` is compiler/runtime derived from
      `(object_projection_graph_identity_id via path, object_instance_graph_id)`.
    - `object_instance_graph` is a boundary pointer to the canonical OIG worldline and
      must not be traversed inside the identity projection payload.
    """

    # --- AWARE: LOGIC START create_via_object_projection_graph_identity
    object_instance_graph_identity_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ObjectInstanceGraphIdentity, object_instance_graph_identity_id)
    if existing is not None:
        if (
            existing.object_projection_graph_identity_id != object_projection_graph_identity_id
            or existing.object_instance_graph_id != object_instance_graph_id
            or (existing.label or None) != (label or None)
        ):
            raise RuntimeError(
                "ObjectInstanceGraphIdentity.create_via_object_projection_graph_identity "
                + "payload mismatch for existing identity: "
                + f"object_instance_graph_identity_id={object_instance_graph_identity_id}"
            )
        return existing

    return ObjectInstanceGraphIdentity(
        id=object_instance_graph_identity_id,
        label=label,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
    )
    # --- AWARE: LOGIC END create_via_object_projection_graph_identity
