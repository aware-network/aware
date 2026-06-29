from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)

# History Ontology
from aware_history_ontology.stable_ids import stable_commit_id, stable_lane_id
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_history_ontology.lane.lane import Lane

# Meta
from aware_meta.graph.instance.commit.fs_store import FSCommitStore

# Meta Runtime
from aware_meta.runtime.author import resolve_author_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_object_instance_graph_identity(
    object_instance_graph_identity_id: UUID, commit_id: UUID, domain_branch_id: UUID, domain_projection_hash: str
) -> ObjectInstanceGraphCommit:
    """
    Materialize a history-plane OIG commit wrapper for a domain commit.

    Canonical v0:
    - Reads the domain commit payload from the commit store (SSOT).
    - Creates (or reuses) the underlying history Commit + CommitParent objects.
    - Parent ObjectInstanceGraphIdentity ownership is propagated by traversal lowering.
    - Deterministic identity is constructor-keyed on `(commit_id)` plus parent path.
    - Domain commit payload must carry rooted OIG bootstrap metadata so materialization
      never synthesizes an empty ObjectInstanceGraph.
    """

    # --- AWARE: LOGIC START create_via_object_instance_graph_identity
    session = current_handler_session()

    # `commit_id` here is the domain OIG commit id.
    # The wrapped History Commit remains lane-owned and therefore resolves from
    # `(lane_id, key=str(domain_commit_id))`.
    oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        commit_id=commit_id,
    )

    existing = session.imap_get(ObjectInstanceGraphCommit, oig_commit_id)
    if existing is not None:
        return existing

    store = FSCommitStore()
    payload = await store.get_commit(
        branch_id=domain_branch_id,
        projection_hash=domain_projection_hash,
        commit_id=commit_id,
    )
    if payload is None:
        raise RuntimeError(
            "Missing domain commit while materializing OIG history plane: "
            + f"branch_id={domain_branch_id} projection_hash={domain_projection_hash} commit_id={commit_id}"
        )

    parent_identity = session.imap_get(ObjectInstanceGraphIdentity, object_instance_graph_identity_id)
    if parent_identity is None:
        raise RuntimeError(
            "ObjectInstanceGraphCommit.create_via_object_instance_graph_identity requires existing "
            + f"ObjectInstanceGraphIdentity: object_instance_graph_identity_id={object_instance_graph_identity_id}"
        )

    expected_domain_oig_id = parent_identity.object_instance_graph_id

    if str(payload.object_instance_graph_id) != str(expected_domain_oig_id):
        raise RuntimeError(
            "Domain commit object_instance_graph_id mismatch: "
            + f"commit_id={commit_id} have={payload.object_instance_graph_id} "
            + f"expected_domain_oig_id={expected_domain_oig_id}"
        )
    if str(payload.object_instance_graph_identity_id) != str(object_instance_graph_identity_id):
        raise RuntimeError(
            "Domain commit object_instance_graph_identity_id mismatch: "
            + f"commit_id={commit_id} have={payload.object_instance_graph_identity_id} "
            + f"expected_oigi_id={object_instance_graph_identity_id}"
        )
    if payload.commit.id != commit_id:
        raise RuntimeError(
            "Domain commit payload mismatch: " + f"commit_id={commit_id} payload_commit_id={payload.commit.id}"
        )

    # Commit DAG nodes.
    lane_id = stable_lane_id(branch_id=domain_branch_id, lane_hash=domain_projection_hash)
    history_commit_id = stable_commit_id(lane_id=lane_id, key=str(commit_id))
    commit = session.imap_get(Commit, history_commit_id)
    parent_ids = [
        stable_commit_id(lane_id=lane_id, key=str(parent.parent_commit_id)) for parent in payload.commit.commit_parents
    ]
    lane = session.imap_get(Lane, lane_id)
    if lane is None:
        raise RuntimeError(
            "Missing Lane while materializing OIG history Commit wrapper: "
            + f"lane_id={lane_id} domain_branch_id={domain_branch_id} "
            + f"projection_hash={domain_projection_hash}"
        )
    if commit is None:
        created_at = payload.commit.created_at
        commit = await Commit.create_via_lane(
            lane_id=lane_id,
            key=str(commit_id),
            # Legacy tolerance: some historical commit payloads may be missing author_id.
            # Canonical behavior: treat as SYSTEM_ACTOR_ID rather than emitting null UUIDs.
            author_id=resolve_author_id(payload.commit.author_id),
            created_at=created_at,
            status=payload.commit.status,
        )
        if commit.id != history_commit_id:
            raise RuntimeError(
                "Commit.create produced unexpected id (commit id stability invariant): "
                + f"expected={history_commit_id} domain_commit_id={commit_id} got={commit.id}"
            )
    if all(existing.id != commit.id for existing in lane.commits):
        lane.commits.append(commit)

    for parent_id in parent_ids:
        if any(existing.parent_commit_id == parent_id for existing in commit.commit_parents):
            continue
        created_parent = await CommitParent.create_via_commit(
            commit_id=commit.id,
            parent_commit_id=parent_id,
        )
        if all(existing.parent_commit_id != parent_id for existing in commit.commit_parents):
            commit.commit_parents.append(created_parent)

    return ObjectInstanceGraphCommit(
        id=oig_commit_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=payload.object_instance_graph_id,
        commit=commit,
        commit_id=commit.id,
        object_instance_graph_key=payload.object_instance_graph_key,
        object_instance_graph_name=payload.object_instance_graph_name,
        object_instance_graph_description=payload.object_instance_graph_description,
        root_class_config_id=payload.root_class_config_id,
        root_source_object_id=payload.root_source_object_id,
        graph_hash_pre=payload.graph_hash_pre,
        graph_hash_post=payload.graph_hash_post,
        source_language=payload.source_language,
        projection_hash=domain_projection_hash,
        object_instance_graph_changes=payload.object_instance_graph_changes,
    )
    # --- AWARE: LOGIC END create_via_object_instance_graph_identity
