from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
from aware_experience_ontology.invocation.experience_invocation_action_commit import ExperienceInvocationActionCommit
from aware_experience_ontology.invocation.experience_invocation_action_propagation import (
    ExperienceInvocationActionPropagation,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_experience_invocation_action_id
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    experience_invocation_action_config_id: UUID,
    invocation_key: UUID,
    actor_id: UUID | None = None,
    api_call_id: UUID | None = None,
    sdk_operation_call_id: UUID | None = None,
    request_ref: str | None = None,
    receipt_ref: str | None = None,
    status: str = "pending",
) -> ExperienceInvocationAction:
    """
    Create one deterministic standalone invocation receipt.

    Contract:
    - Stable identity is `(experience_invocation_action_config, invocation_key)`.
    - `invocation_key` is stable for one dispatch attempt.
    - `actor_id` links to Identity-owned Actor provenance.
    - `api_call_id` and `sdk_operation_call_id` are optional module-owned
      receipts for the same dispatch.
    """

    # --- AWARE: LOGIC START build
    normalized_request_ref = (request_ref or "").strip() or None
    normalized_receipt_ref = (receipt_ref or "").strip() or None
    normalized_status = (status or "").strip() or "pending"
    action_id = stable_experience_invocation_action_id(
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        invocation_key=invocation_key,
    )

    session = current_handler_session()
    experience_invocation_action_config = session.imap_get(
        ExperienceInvocationActionConfig,
        experience_invocation_action_config_id,
    )
    existing = session.imap_get(ExperienceInvocationAction, action_id)
    if existing is not None:
        if (
            existing.experience_invocation_action_config_id != experience_invocation_action_config_id
            or existing.invocation_key != invocation_key
            or existing.actor_id != actor_id
            or existing.api_call_id != api_call_id
            or existing.sdk_operation_call_id != sdk_operation_call_id
            or existing.request_ref != normalized_request_ref
            or existing.receipt_ref != normalized_receipt_ref
            or existing.status != normalized_status
        ):
            raise RuntimeError(
                "ExperienceInvocationAction field mismatch for existing action: "
                + f"experience_invocation_action_id={action_id}"
            )
        return existing

    if experience_invocation_action_config is not None:
        return ExperienceInvocationAction(
            id=action_id,
            experience_invocation_action_config_id=experience_invocation_action_config_id,
            experience_invocation_action_config=experience_invocation_action_config,
            invocation_key=invocation_key,
            actor_id=actor_id,
            api_call_id=api_call_id,
            sdk_operation_call_id=sdk_operation_call_id,
            request_ref=normalized_request_ref,
            receipt_ref=normalized_receipt_ref,
            status=normalized_status,
        )
    return ExperienceInvocationAction(
        id=action_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        invocation_key=invocation_key,
        actor_id=actor_id,
        api_call_id=api_call_id,
        sdk_operation_call_id=sdk_operation_call_id,
        request_ref=normalized_request_ref,
        receipt_ref=normalized_receipt_ref,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build


async def add_commit(
    experience_invocation_action: ExperienceInvocationAction,
    object_instance_graph_commit_id: UUID,
    commit_role: str = "mutation",
    description: str | None = None,
) -> ExperienceInvocationActionCommit:
    """
    Link one graph commit produced or consumed by this invocation action.

    Contract:
    - The commit wrapper remains Meta-owned.
    - Events emitted from that commit are linked through child commit-event edges.
    """

    # --- AWARE: LOGIC START add_commit
    commit = await ExperienceInvocationActionCommit.build_via_experience_invocation_action(
        experience_invocation_action_id=experience_invocation_action.id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        commit_role=commit_role,
        description=description,
    )
    for existing in experience_invocation_action.commits:
        if existing.id == commit.id:
            return existing
    experience_invocation_action.commits.append(commit)
    return commit
    # --- AWARE: LOGIC END add_commit


async def add_propagation(
    experience_invocation_action: ExperienceInvocationAction,
    target_invocation_action_id: UUID,
    propagation_kind: str = "invokes",
    description: str | None = None,
) -> ExperienceInvocationActionPropagation:
    """
    Link this invocation action to another invocation action it caused.

    Contract:
    - SDK actions can point to API actions, service actions, or future
      adapter-specific actions without collapsing their receipts.
    - Commit and event provenance stays on the action that produced it.
    """

    # --- AWARE: LOGIC START add_propagation
    propagation = await ExperienceInvocationActionPropagation.build_via_experience_invocation_action(
        experience_invocation_action_id=experience_invocation_action.id,
        target_invocation_action_id=target_invocation_action_id,
        propagation_kind=propagation_kind,
        description=description,
    )
    for existing in experience_invocation_action.propagations:
        if existing.id == propagation.id:
            return existing
    experience_invocation_action.propagations.append(propagation)
    return propagation
    # --- AWARE: LOGIC END add_propagation
