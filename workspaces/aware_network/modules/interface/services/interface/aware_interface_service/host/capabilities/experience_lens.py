from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
)
from aware_interface import InterfaceRuntimeFocusState

from aware_interface_service.host.capabilities.experience import (
    ExperienceSectionGraphBindingActivationResolution,
)
from aware_interface_service.models import (
    InterfaceEnvironmentNavigationState,
    InterfaceEnvironmentSessionState,
    InterfaceExperienceLensActionState,
    InterfaceExperienceLensState,
)


def environment_session_state_from_join_receipt(
    *,
    receipt: EnvironmentSessionJoinReceipt,
    updated_at: str,
) -> InterfaceEnvironmentSessionState:
    identity_evidence = receipt.identity_evidence
    identity_session = (
        identity_evidence.identity_session if identity_evidence is not None else None
    )
    identity_member = (
        identity_evidence.identity_member if identity_evidence is not None else None
    )
    identity_roles = (
        tuple(identity_evidence.identity_actor_roles)
        if identity_evidence is not None
        else ()
    )
    return InterfaceEnvironmentSessionState(
        status=receipt.status,
        accepted=receipt.accepted,
        actor_id=receipt.actor_id,
        environment_id=receipt.environment_id,
        environment_profile_id=receipt.environment_profile_id,
        environment_session_id=receipt.environment_session_id,
        environment_session_key=receipt.environment_session_key,
        identity_session_id=(
            identity_session.session_id if identity_session is not None else None
        ),
        identity_member_id=(
            identity_member.session_member_id if identity_member is not None else None
        ),
        identity_actor_role_count=len(identity_roles),
        blockers=tuple(str(item) for item in receipt.blockers),
        error=receipt.error,
        reason=receipt.reason,
        updated_at=updated_at,
        evidence=_jsonish_mapping(receipt.evidence),
    )


def environment_navigation_state_from_context(
    *,
    context: EnvironmentNavigationContextView,
    actor_id: UUID | None,
    updated_at: str,
) -> InterfaceEnvironmentNavigationState:
    return InterfaceEnvironmentNavigationState(
        status=context.status,
        accepted=context.status == "active",
        actor_id=actor_id,
        environment_id=context.environment_id,
        environment_session_id=context.environment_session_id,
        environment_navigation_context_id=context.environment_navigation_context_id,
        key=context.key,
        process_id=context.selected_process_id,
        thread_id=context.selected_thread_id,
        branch_id=context.branch_id,
        projection_hash=context.projection_hash,
        root_object_id=context.root_object_id,
        commit_id=context.commit_id,
        object_instance_graph_commit_id=context.object_instance_graph_commit_id,
        updated_at=updated_at,
        evidence=_jsonish_mapping(context.evidence),
    )


def experience_lens_state_from_blocker(
    *,
    blocker: str,
    actor_id: UUID | None,
    environment_session: InterfaceEnvironmentSessionState | None,
    environment_navigation: InterfaceEnvironmentNavigationState | None,
    updated_at: str,
) -> InterfaceExperienceLensState:
    return InterfaceExperienceLensState(
        status="blocked",
        accepted=False,
        actor_id=actor_id,
        environment_id=(
            environment_navigation.environment_id
            if environment_navigation is not None
            else (
                environment_session.environment_id
                if environment_session is not None
                else None
            )
        ),
        environment_session_id=(
            environment_session.environment_session_id
            if environment_session is not None
            else None
        ),
        environment_navigation_context_id=(
            environment_navigation.environment_navigation_context_id
            if environment_navigation is not None
            else None
        ),
        blockers=(blocker,),
        error=blocker,
        updated_at=updated_at,
        evidence={"source": "interface_experience_lens", "blocker": blocker},
    )


def experience_lens_state_from_activation(
    *,
    activation: ExperienceSectionGraphBindingActivationResolution,
    actor_id: UUID,
    environment_session: InterfaceEnvironmentSessionState,
    environment_navigation: InterfaceEnvironmentNavigationState,
    view_ref: str | None,
    active_focus: InterfaceRuntimeFocusState | None,
    updated_at: str,
    evidence: Mapping[str, object] | None = None,
) -> InterfaceExperienceLensState:
    actions = tuple(
        InterfaceExperienceLensActionState(
            action_key=item.action_key,
            action_kind=item.action_kind,
            target_ref=item.target_ref,
            view_invocation_action_config_id=item.view_invocation_action_config_id,
        )
        for item in activation.view_actions
    )
    return InterfaceExperienceLensState(
        status="resolved",
        accepted=True,
        actor_id=actor_id,
        environment_id=environment_navigation.environment_id,
        environment_session_id=environment_session.environment_session_id,
        environment_navigation_context_id=(
            environment_navigation.environment_navigation_context_id
        ),
        experience_name=activation.experience_name,
        view_ref=view_ref,
        section_key=activation.section_key,
        observable_id=activation.projection_observable_id,
        section_graph_binding_key=activation.binding_key,
        projection_experience_view_instance_id=(
            activation.projection_experience_view_instance_id
        ),
        projection_experience_graph_identity_id=(
            activation.projection_experience_graph_identity_id
        ),
        object_projection_graph_identity_id=(
            activation.object_projection_graph_identity_id
        ),
        focus_scope_id=(
            active_focus.focus_scope_id if active_focus is not None else None
        ),
        focus_id=active_focus.focus_id if active_focus is not None else None,
        action_count=len(actions),
        actions=actions,
        updated_at=updated_at,
        evidence={
            "source": "interface_experience_lens",
            **_jsonish_mapping(evidence or {}),
        },
    )


def _jsonish_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _jsonish_value(item) for key, item in value.items()}


def _jsonish_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonish_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonish_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
