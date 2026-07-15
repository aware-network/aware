from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.actor.actor_commit import ActorCommit

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_identity_ontology.stable_ids import stable_actor_commit_id

# --- AWARE: USER_IMPORTS END


async def create_via_actor(
    actor_id: UUID,
    domain_branch_id: UUID,
    domain_projection_hash: str,
    domain_commit_id: UUID,
    object_instance_graph_commit_id: UUID,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    receipt_actor_id: UUID | None = None,
    created_at_unix_ms: int | None = None,
    operation_label: str | None = None,
    call_target: str | None = None,
    function_id: UUID | None = None,
    object_id: UUID | None = None,
    class_instance_identity_id: UUID | None = None,
    graph_hash_post: str | None = None,
    object_instance_graph_id: UUID | None = None,
    root_object_id: UUID | None = None,
    head_version: int | None = None,
    source: str = "environment_lane_commit_receipt",
) -> ActorCommit:
    """
    Create or ensure one ActorCommit personal-history binding.

    This is the post-commit reaction record for Environment lane commit fanout.
    It does not rewrite History Commit authorship; it binds the actor whose
    personal history should include the durable commit.
    """

    # --- AWARE: LOGIC START create_via_actor
    projection_hash = (domain_projection_hash or "").strip()
    if not projection_hash:
        raise ValueError("ActorCommit.create_via_actor requires a domain_projection_hash")

    actor_commit_id = stable_actor_commit_id(
        actor_id=actor_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=projection_hash,
        domain_commit_id=domain_commit_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_oig_commit = (
        session.imap_get(ObjectInstanceGraphCommit, object_instance_graph_commit_id) if session is not None else None
    )

    existing = session.imap_get(ActorCommit, actor_commit_id) if session is not None else None
    if existing is not None:
        if (
            existing.actor_id != actor_id
            or existing.domain_branch_id != domain_branch_id
            or existing.domain_projection_hash != projection_hash
            or existing.domain_commit_id != domain_commit_id
        ):
            raise RuntimeError(
                "ActorCommit.create_via_actor payload mismatch for existing personal-history binding: "
                f"actor_commit_id={actor_commit_id}"
            )
        existing.object_instance_graph_commit_id = object_instance_graph_commit_id
        existing.object_instance_graph_commit = resolved_oig_commit
        existing.environment_id = environment_id
        existing.process_id = process_id
        existing.thread_id = thread_id
        existing.receipt_actor_id = receipt_actor_id
        existing.created_at_unix_ms = created_at_unix_ms
        existing.operation_label = operation_label
        existing.call_target = call_target
        existing.function_id = function_id
        existing.object_id = object_id
        existing.class_instance_identity_id = class_instance_identity_id
        existing.graph_hash_post = graph_hash_post
        existing.object_instance_graph_id = object_instance_graph_id
        existing.root_object_id = root_object_id
        existing.head_version = head_version
        existing.source = source
        return existing

    return ActorCommit(
        id=actor_commit_id,
        actor_id=actor_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=projection_hash,
        domain_commit_id=domain_commit_id,
        object_instance_graph_commit=resolved_oig_commit,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        receipt_actor_id=receipt_actor_id,
        created_at_unix_ms=created_at_unix_ms,
        operation_label=operation_label,
        call_target=call_target,
        function_id=function_id,
        object_id=object_id,
        class_instance_identity_id=class_instance_identity_id,
        graph_hash_post=graph_hash_post,
        object_instance_graph_id=object_instance_graph_id,
        root_object_id=root_object_id,
        head_version=head_version,
        source=source,
    )
    # --- AWARE: LOGIC END create_via_actor
