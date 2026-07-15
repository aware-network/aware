from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.thread.thread_object_instance_graph_branch import ThreadObjectInstanceGraphBranch

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta.runtime.graph_identity import (
    resolve_meta_graph_ocgi_opgi as resolve_ocgi_opgi,
)

# Environment
from aware_environment.stable_ids import stable_thread_oigb_assoc_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_index,
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_for_lane(
    thread_id: UUID, domain_branch_id: UUID, projection_hash: str, title: str | None = None, is_active: bool = True
) -> ThreadObjectInstanceGraphBranch:
    """
    Create an attachment edge for an existing global lane (branch_id, projection_hash).

    Canonical v0 intent:
    - OS lane metadata only: creates deterministic Branch/Lane/OIGB objects if missing.
    - Does not author domain commits; lane HEAD comes from the commit store (SSOT).
    """

    # --- AWARE: LOGIC START create_for_lane
    if not projection_hash.strip():
        raise RuntimeError("ThreadObjectInstanceGraphBranch.create_for_lane requires non-empty projection_hash")

    # SSOT: lane HEAD is commits, not OS metadata.
    store = FSCommitStore()
    head = await store.head(branch_id=domain_branch_id, projection_hash=projection_hash)
    if head is None or not head.get("commit_id") or not head.get("object_instance_graph_id"):
        raise RuntimeError(
            "Cannot attach lane with no HEAD commit (commit-first invariant): "
            f"domain_branch_id={domain_branch_id} projection_hash={projection_hash}"
        )
    head_commit_id = UUID(str(head["commit_id"]))
    head_commit = await store.get_commit(
        branch_id=domain_branch_id,
        projection_hash=projection_hash,
        commit_id=head_commit_id,
    )
    if head_commit is None or head_commit.commit is None:
        raise RuntimeError(
            "Cannot attach lane with missing HEAD commit payload (commit-first invariant): "
            f"domain_branch_id={domain_branch_id} projection_hash={projection_hash}"
        )

    index = current_handler_index()
    opg = next(
        (
            candidate
            for candidate in index.ocg.object_projection_graphs
            if (candidate.projection_hash or "").strip() == projection_hash
        ),
        None,
    )
    if opg is None:
        raise RuntimeError(
            "Cannot attach lane without ObjectProjectionGraphIdentity binding: "
            f"domain_branch_id={domain_branch_id} projection_hash={projection_hash}"
        )
    _ocgi, opgi = resolve_ocgi_opgi(index=index, projection_hash=projection_hash)
    if opgi is None:
        raise RuntimeError(
            "Cannot attach lane without ObjectProjectionGraphIdentity binding: "
            f"domain_branch_id={domain_branch_id} projection_hash={projection_hash}"
        )

    object_instance_graph_id = UUID(str(head["object_instance_graph_id"]))
    object_instance_graph_identity_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=object_instance_graph_id,
    )
    oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        branch_id=domain_branch_id,
    )
    assoc_id = stable_thread_oigb_assoc_id(thread_id=thread_id, oigb_id=oigb_id)

    session = current_handler_session()

    existing_assoc = session.imap_get(ThreadObjectInstanceGraphBranch, assoc_id)
    if existing_assoc is not None:
        # Idempotent + upgrade-safe:
        # - Never mutate an existing association from a constructor handler (mutate-self-only).
        # - If the OIGI anchor is missing (legacy env projection), backfill it via an
        #   instance handler on the association itself.
        if existing_assoc.object_instance_graph_identity_id is None:
            existing_assoc = await existing_assoc.backfill_identity_anchor(
                object_instance_graph_identity_id=object_instance_graph_identity_id
            )
        return existing_assoc

    assoc = ThreadObjectInstanceGraphBranch(
        id=assoc_id,
        thread_id=thread_id,
        object_instance_graph_branch_id=oigb_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        is_active=is_active,
        title=title,
    )
    return assoc
    # --- AWARE: LOGIC END create_for_lane


async def backfill_identity_anchor(
    thread_object_instance_graph_branch: ThreadObjectInstanceGraphBranch, object_instance_graph_identity_id: UUID
) -> ThreadObjectInstanceGraphBranch:
    """
    Backfill `object_instance_graph_identity_id` for legacy associations.

    Why:
    - Older OS commits were created before the environment projection included the
      `object_instance_graph_identity` portal, so the association may be missing the
      OIGI anchor on replay/materialization.

    Canonical rules:
    - Mutates only this association instance (mutate-self-only invariant).
    - Idempotent: no-op when already set.
    """

    # --- AWARE: LOGIC START backfill_identity_anchor
    if thread_object_instance_graph_branch.object_instance_graph_identity_id is None:
        thread_object_instance_graph_branch.object_instance_graph_identity_id = object_instance_graph_identity_id
    return thread_object_instance_graph_branch
    # --- AWARE: LOGIC END backfill_identity_anchor
