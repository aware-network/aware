from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)

from aware_experience_service_dto.experience.environment_profile.models import (
    ExperienceEnvironmentProfileSpec,
    ExperienceEnvironmentProfileTopologySeedSpec,
)
from aware_experience_service_dto.experience.environment_profile.service_operation import (
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ProvisionExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileRequest,
)
from aware_experience_service_dto.experience.package_materialization.service_operation import (
    ResolveExperiencePackageProjectionOwnershipRequest,
)
from aware_experience_service_dto.experience.actor_admission.service_operation import (
    AdmitExperienceActorConfigRequest,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_experience_service_dto.experience.layout_transition.models import (
    ExperienceLayoutActorRoleGate,
)
from aware_experience_service_dto.experience.layout_transition.service_operation import (
    RequestExperienceLayoutTransitionRequest,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceLayoutGraphBindingRequest,
    ActivateExperienceSectionGraphBindingRequest,
    ApplyExperienceViewEventTransitionRequest,
    ExperienceSectionGraphBindingActivationScope,
    GetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingStateRequest,
    GetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingStateRequest,
    InvokeExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionRequest,
    WatchExperienceSectionGraphBindingsRequest,
)
from aware_experience_service_dto.experience.session_handoff.models import (
    ExperienceSessionHandoffActorContext,
    ExperienceSessionHandoffFeatureSpec,
    ExperienceSessionHandoffScope,
)
from aware_experience_service_dto.experience.session_handoff.service_operation import (
    EnsureExperienceSessionHandoffRequest,
    GetExperienceSessionHandoffStatusRequest,
)
from aware_experience_service_dto.experience.session_context.models import (
    ExperienceSessionAttentionResolutionRequest,
)
from aware_experience_service_dto.experience.session_context.service_operation import (
    ResolveExperienceSessionContextRequest,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
)
from aware_experience_service_dto.experience.session_commit.service_operation import (
    DescribeExperienceSessionRequest,
    MountExperienceSessionProfileRequest,
    StartExperienceSessionRequest,
)
from aware_experience_service_dto.experience.thread_layout_resolution.service_operation import (
    ResolveExperienceThreadLayoutIntentRequest,
)
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
)

_T = TypeVar("_T", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class ExperienceSdkClient:
    api_client: Any

    async def describe_experience_session(
        self,
        request: object | None = None,
        *,
        experience_session_id: UUID | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            DescribeExperienceSessionRequest,
            experience_session_id=experience_session_id,
        )
        return await self._invoke(
            "describe_experience_session",
            "describe_experience_session",
            request,
        )

    async def start_experience_session(
        self,
        request: object | None = None,
        *,
        environment_experience_id: UUID | None = None,
        environment_id: UUID | None = None,
        identity_session_id: UUID | None = None,
        environment_session_id: UUID | None = None,
        state: str = "active",
    ) -> object:
        request = _request_or_model(
            request,
            StartExperienceSessionRequest,
            environment_experience_id=environment_experience_id,
            environment_id=environment_id,
            identity_session_id=identity_session_id,
            environment_session_id=environment_session_id,
            state=state,
        )
        return await self._invoke(
            "start_experience_session",
            "start_experience_session",
            request,
        )

    async def mount_experience_session_profile(
        self,
        request: object | None = None,
        *,
        experience_session_id: UUID | None = None,
        profile_id: UUID | None = None,
        status: str = "active",
        metadata_json: dict[str, object] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            MountExperienceSessionProfileRequest,
            experience_session_id=experience_session_id,
            profile_id=profile_id,
            status=status,
            metadata_json=metadata_json or {},
        )
        return await self._invoke(
            "mount_experience_session_profile",
            "mount_experience_session_profile",
            request,
        )

    async def resolve_thread_layout_intent(
        self,
        request: object | None = None,
        *,
        intent_key: str | None = None,
        experience_name: str | None = None,
        profile_key: str | None = None,
        environment_id: UUID | None = None,
        environment_handle: str | None = None,
        environment_selector: str | None = None,
        request_context: dict[str, object] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            ResolveExperienceThreadLayoutIntentRequest,
            intent_key=intent_key,
            experience_name=experience_name,
            profile_key=profile_key,
            environment_id=environment_id,
            environment_handle=environment_handle,
            environment_selector=environment_selector,
            request_context=request_context or {},
        )
        return await self._invoke(
            "resolve_experience_thread_layout_intent",
            "resolve_experience_thread_layout_intent",
            request,
        )

    async def request_layout_transition(
        self,
        request: object | None = None,
        *,
        namespace: str | None = None,
        actor_id: UUID | None = None,
        identity_id: UUID | None = None,
        intent_key: str | None = None,
        role_gate: ExperienceLayoutActorRoleGate | dict[str, object] | None = None,
        reason: str | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            RequestExperienceLayoutTransitionRequest,
            namespace=namespace,
            actor_id=actor_id,
            identity_id=identity_id,
            intent_key=intent_key,
            role_gate=role_gate,
            reason=reason,
        )
        return await self._invoke(
            "request_experience_layout_transition",
            "request_experience_layout_transition",
            request,
        )

    async def admit_actor_config(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        actor_id: UUID | None = None,
        actor_config_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: list[UUID] | None = None,
        requested_role_config_names: list[str] | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            AdmitExperienceActorConfigRequest,
            experience_name=experience_name,
            actor_id=actor_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=requested_role_config_ids or [],
            requested_role_config_names=requested_role_config_names or [],
            reason=reason,
            evidence=evidence or {},
        )
        return await self._invoke(
            "actor_admission",
            "admit_experience_actor_config",
            request,
        )

    async def upsert_environment_profile(
        self,
        request: object | None = None,
        *,
        environment_id: UUID | None = None,
        profile: ExperienceEnvironmentProfileSpec | dict[str, object] | None = None,
        topology_seeds: (
            list[ExperienceEnvironmentProfileTopologySeedSpec | dict[str, object]]
            | None
        ) = None,
        actor_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
        experience_name: str | None = None,
        request_context: dict[str, object] | None = None,
        validate_only: bool = False,
    ) -> object:
        request = _request_or_model(
            request,
            UpsertExperienceEnvironmentProfileRequest,
            environment_id=environment_id,
            profile=profile,
            topology_seeds=topology_seeds or [],
            actor_id=actor_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            experience_name=experience_name,
            request_context=request_context or {},
            validate_only=validate_only,
        )
        return await self._invoke(
            "environment_profile",
            "upsert_experience_environment_profile",
            request,
        )

    async def provision_environment_profile(
        self,
        request: object | None = None,
        *,
        environment_id: UUID | None = None,
        topology_seed_key: str | None = None,
        environment_experience_profile_id: UUID | None = None,
        profile_key: str | None = None,
        actor_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
        experience_name: str | None = None,
        request_context: dict[str, object] | None = None,
        validate_only: bool = False,
    ) -> object:
        request = _request_or_model(
            request,
            ProvisionExperienceEnvironmentProfileRequest,
            environment_id=environment_id,
            topology_seed_key=topology_seed_key,
            environment_experience_profile_id=environment_experience_profile_id,
            profile_key=profile_key,
            actor_id=actor_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            experience_name=experience_name,
            request_context=request_context or {},
            validate_only=validate_only,
        )
        return await self._invoke(
            "environment_profile",
            "provision_experience_environment_profile",
            request,
        )

    async def apply_environment_profile_programs(
        self,
        request: object | None = None,
        *,
        environment_id: UUID | None = None,
        environment_experience_profile_id: UUID | None = None,
        profile_key: str | None = None,
        phase: str = "bootstrap",
        target_actor_id: UUID | None = None,
        actor_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
        experience_name: str | None = None,
        request_context: dict[str, object] | None = None,
        validate_only: bool = False,
    ) -> object:
        request = _request_or_model(
            request,
            ApplyExperienceEnvironmentProfileProgramsRequest,
            environment_id=environment_id,
            environment_experience_profile_id=environment_experience_profile_id,
            profile_key=profile_key,
            phase=phase,
            target_actor_id=target_actor_id,
            actor_id=actor_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            experience_name=experience_name,
            request_context=request_context or {},
            validate_only=validate_only,
        )
        return await self._invoke(
            "environment_profile",
            "apply_experience_environment_profile_programs",
            request,
        )

    async def resolve_package_projection_ownership(
        self,
        request: object | None = None,
        *,
        workspace_root: str | None = None,
        experience_toml_path: str | None = None,
        package_name: str | None = None,
        experience_name: str | None = None,
        request_context: dict[str, object] | None = None,
        validate_only: bool = True,
    ) -> object:
        request = _request_or_model(
            request,
            ResolveExperiencePackageProjectionOwnershipRequest,
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
            package_name=package_name,
            experience_name=experience_name,
            request_context=request_context or {},
            validate_only=validate_only,
        )
        return await self._invoke(
            "package_materialization",
            "resolve_experience_package_projection_ownership",
            request,
        )

    async def get_section_graph_binding_catalog(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        section_keys: list[str] | None = None,
        binding_keys: list[str] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            GetExperienceSectionGraphBindingCatalogRequest,
            experience_name=experience_name,
            section_keys=section_keys or [],
            binding_keys=binding_keys or [],
        )
        return await self._invoke(
            "get_experience_section_graph_binding_catalog",
            "get_experience_section_graph_binding_catalog",
            request,
        )

    async def get_layout_graph_binding_catalog(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        layout_binding_keys: list[str] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            GetExperienceLayoutGraphBindingCatalogRequest,
            experience_name=experience_name,
            layout_binding_keys=layout_binding_keys or [],
        )
        return await self._invoke(
            "get_experience_layout_graph_binding_catalog",
            "get_experience_layout_graph_binding_catalog",
            request,
        )

    async def get_section_graph_binding_state(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        binding_key: str | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            GetExperienceSectionGraphBindingStateRequest,
            experience_name=experience_name,
            binding_key=binding_key,
        )
        return await self._invoke(
            "get_experience_section_graph_binding_state",
            "get_experience_section_graph_binding_state",
            request,
        )

    async def get_layout_graph_binding_state(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        layout_binding_key: str | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            GetExperienceLayoutGraphBindingStateRequest,
            experience_name=experience_name,
            layout_binding_key=layout_binding_key,
        )
        return await self._invoke(
            "get_experience_layout_graph_binding_state",
            "get_experience_layout_graph_binding_state",
            request,
        )

    async def activate_section_graph_binding(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        binding_key: str | None = None,
        activation_scope: (
            ExperienceSectionGraphBindingActivationScope | dict[str, object] | None
        ) = None,
        rationale: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
        focus_scope_title: str | None = None,
        focus_scope_description: str | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            ActivateExperienceSectionGraphBindingRequest,
            experience_name=experience_name,
            binding_key=binding_key,
            activation_scope=activation_scope,
            rationale=rationale,
            section_title=section_title,
            section_description=section_description,
            focus_scope_title=focus_scope_title,
            focus_scope_description=focus_scope_description,
        )
        return await self._invoke(
            "activate_experience_section_graph_binding",
            "activate_experience_section_graph_binding",
            request,
        )

    async def activate_layout_graph_binding(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        layout_binding_key: str | None = None,
        activation_scope: (
            ExperienceSectionGraphBindingActivationScope | dict[str, object] | None
        ) = None,
        rationale: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
        focus_scope_title: str | None = None,
        focus_scope_description: str | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            ActivateExperienceLayoutGraphBindingRequest,
            experience_name=experience_name,
            layout_binding_key=layout_binding_key,
            activation_scope=activation_scope,
            rationale=rationale,
            section_title=section_title,
            section_description=section_description,
            focus_scope_title=focus_scope_title,
            focus_scope_description=focus_scope_description,
        )
        return await self._invoke(
            "activate_experience_layout_graph_binding",
            "activate_experience_layout_graph_binding",
            request,
        )

    async def apply_view_event_transition(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        profile_key: str | None = None,
        transition_key: str | None = None,
        event_type: str | None = None,
        target_view_ref: str | None = None,
        target_binding_key: str | None = None,
        source_view_ref: str | None = None,
        event_id: UUID | None = None,
        action_intent_id: UUID | None = None,
        action_type: str | None = None,
        target_section_key: str | None = None,
        target_graph_identity_ref: str | None = None,
        activation_scope: (
            ExperienceSectionGraphBindingActivationScope | dict[str, object] | None
        ) = None,
        rationale: str | None = None,
        section_title: str | None = None,
        section_description: str | None = None,
        focus_scope_title: str | None = None,
        focus_scope_description: str | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            ApplyExperienceViewEventTransitionRequest,
            experience_name=experience_name,
            profile_key=profile_key,
            transition_key=transition_key,
            source_view_ref=source_view_ref,
            event_id=event_id,
            event_type=event_type,
            action_intent_id=action_intent_id,
            action_type=action_type,
            target_view_ref=target_view_ref,
            target_binding_key=target_binding_key,
            target_section_key=target_section_key,
            target_graph_identity_ref=target_graph_identity_ref,
            activation_scope=activation_scope,
            rationale=rationale,
            section_title=section_title,
            section_description=section_description,
            focus_scope_title=focus_scope_title,
            focus_scope_description=focus_scope_description,
        )
        return await self._invoke(
            "apply_experience_view_event_transition",
            "apply_experience_view_event_transition",
            request,
        )

    async def watch_section_graph_bindings(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        section_keys: list[str] | None = None,
        binding_keys: list[str] | None = None,
        poll_interval_ms: int = 1000,
    ) -> object:
        request = _request_or_model(
            request,
            WatchExperienceSectionGraphBindingsRequest,
            experience_name=experience_name,
            section_keys=section_keys or [],
            binding_keys=binding_keys or [],
            poll_interval_ms=poll_interval_ms,
        )
        return await self._invoke(
            "watch_experience_section_graph_bindings",
            "watch_experience_section_graph_bindings",
            request,
        )

    async def record_view_invocation_action(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        projection_experience_view_instance_id: UUID | None = None,
        view_invocation_action_config_id: UUID | None = None,
        invocation_key: UUID | None = None,
        actor_id: UUID | None = None,
        api_call_id: UUID | None = None,
        sdk_operation_call_id: UUID | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
        status: str = "pending",
    ) -> object:
        request = _request_or_model(
            request,
            RecordExperienceViewInvocationActionRequest,
            experience_name=experience_name,
            projection_experience_view_instance_id=projection_experience_view_instance_id,
            view_invocation_action_config_id=view_invocation_action_config_id,
            invocation_key=invocation_key,
            actor_id=actor_id,
            api_call_id=api_call_id,
            sdk_operation_call_id=sdk_operation_call_id,
            request_ref=request_ref,
            receipt_ref=receipt_ref,
            status=status,
        )
        return await self._invoke(
            "record_experience_view_invocation_action",
            "record_experience_view_invocation_action",
            request,
        )

    async def invoke_view_invocation_action(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        projection_experience_view_instance_id: UUID | None = None,
        view_invocation_action_config_id: UUID | None = None,
        invocation_key: UUID | None = None,
        actor_id: UUID | None = None,
        request_payload: dict[str, object] | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            InvokeExperienceViewInvocationActionRequest,
            experience_name=experience_name,
            projection_experience_view_instance_id=projection_experience_view_instance_id,
            view_invocation_action_config_id=view_invocation_action_config_id,
            invocation_key=invocation_key,
            actor_id=actor_id,
            request_payload=request_payload or {},
            request_ref=request_ref,
            receipt_ref=receipt_ref,
        )
        return await self._invoke(
            "invoke_experience_view_invocation_action",
            "invoke_experience_view_invocation_action",
            request,
        )

    async def ensure_session_handoff(
        self,
        request: object | None = None,
        *,
        session_scope: ExperienceSessionHandoffScope | dict[str, object] | None = None,
        actor_context: (
            ExperienceSessionHandoffActorContext | dict[str, object] | None
        ) = None,
        environment_admission: (
            EnvironmentActorAdmissionReceipt | dict[str, object] | object | None
        ) = None,
        environment_session_join: (
            EnvironmentSessionJoinReceipt | dict[str, object] | object | None
        ) = None,
        experience_actor_admission: (
            ExperienceActorConfigAdmissionReceipt | dict[str, object] | object | None
        ) = None,
        experience_identity_session_config_id: UUID | None = None,
        feature: ExperienceSessionHandoffFeatureSpec | dict[str, object] | None = None,
        idempotency_key: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            EnsureExperienceSessionHandoffRequest,
            session_scope=session_scope,
            actor_context=actor_context,
            environment_admission=_environment_admission_receipt(environment_admission),
            environment_session_join=_environment_session_join_receipt(
                environment_session_join,
            ),
            experience_actor_admission=_experience_actor_admission_receipt(
                experience_actor_admission,
            ),
            experience_identity_session_config_id=experience_identity_session_config_id,
            feature=feature,
            idempotency_key=idempotency_key,
            evidence=evidence or {},
        )
        return await self._invoke(
            "session_handoff",
            "ensure_experience_session_handoff",
            request,
        )

    async def get_session_handoff_status(
        self,
        request: object | None = None,
        *,
        session_scope: ExperienceSessionHandoffScope | dict[str, object] | None = None,
        feature_key: str | None = None,
        lease_key: str | None = None,
        include_health: bool = True,
        evidence: dict[str, object] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            GetExperienceSessionHandoffStatusRequest,
            session_scope=session_scope,
            feature_key=feature_key,
            lease_key=lease_key,
            include_health=include_health,
            evidence=evidence or {},
        )
        return await self._invoke(
            "session_handoff",
            "get_experience_session_handoff_status",
            request,
        )

    async def resolve_session_context(
        self,
        request: object | None = None,
        *,
        session_scope: ExperienceSessionHandoffScope | dict[str, object] | None = None,
        actor_context: (
            ExperienceSessionHandoffActorContext | dict[str, object] | None
        ) = None,
        environment_admission: (
            EnvironmentActorAdmissionReceipt | dict[str, object] | object | None
        ) = None,
        environment_session_join: (
            EnvironmentSessionJoinReceipt | dict[str, object] | object | None
        ) = None,
        experience_actor_admission: (
            ExperienceActorConfigAdmissionReceipt | dict[str, object] | object | None
        ) = None,
        experience_identity_session_config_id: UUID | None = None,
        environment_attention: (
            ExperienceSessionAttentionResolutionRequest | dict[str, object] | None
        ) = None,
        idempotency_key: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            ResolveExperienceSessionContextRequest,
            session_scope=session_scope,
            actor_context=actor_context,
            environment_admission=_environment_admission_receipt(environment_admission),
            environment_session_join=_environment_session_join_receipt(
                environment_session_join,
            ),
            experience_actor_admission=_experience_actor_admission_receipt(
                experience_actor_admission,
            ),
            experience_identity_session_config_id=experience_identity_session_config_id,
            environment_attention=environment_attention,
            idempotency_key=idempotency_key,
            evidence=evidence or {},
        )
        return await self._invoke(
            "session_context",
            "resolve_experience_session_context",
            request,
        )

    async def resolve_session_view_frame(
        self,
        request: object | None = None,
        *,
        session_scope: ExperienceSessionHandoffScope | dict[str, object] | None = None,
        actor_context: (
            ExperienceSessionHandoffActorContext | dict[str, object] | None
        ) = None,
        environment_admission: (
            EnvironmentActorAdmissionReceipt | dict[str, object] | object | None
        ) = None,
        environment_session_join: (
            EnvironmentSessionJoinReceipt | dict[str, object] | object | None
        ) = None,
        experience_actor_admission: (
            ExperienceActorConfigAdmissionReceipt | dict[str, object] | object | None
        ) = None,
        experience_identity_session_config_id: UUID | None = None,
        environment_attention: (
            ExperienceSessionAttentionResolutionRequest | dict[str, object] | None
        ) = None,
        idempotency_key: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> object:
        request = _request_or_model(
            request,
            ResolveExperienceSessionViewFrameRequest,
            session_scope=session_scope,
            actor_context=actor_context,
            environment_admission=_environment_admission_receipt(environment_admission),
            environment_session_join=_environment_session_join_receipt(
                environment_session_join,
            ),
            experience_actor_admission=_experience_actor_admission_receipt(
                experience_actor_admission,
            ),
            experience_identity_session_config_id=experience_identity_session_config_id,
            environment_attention=environment_attention,
            idempotency_key=idempotency_key,
            evidence=evidence or {},
        )
        return await self._invoke(
            "session_view_frame",
            "resolve_experience_session_view_frame",
            request,
        )

    async def watch_experience_view_state(
        self,
        request: object | None = None,
        *,
        experience_name: str | None = None,
        session_view_frame_request: (
            ResolveExperienceSessionViewFrameRequest | dict[str, object] | None
        ) = None,
        projection_experience_view_instance_id: UUID | None = None,
        provider_context: dict[str, object] | None = None,
        known_cursor: str | None = None,
        known_digest: str | None = None,
        poll_interval_ms: int | None = None,
    ) -> object:
        if request is None and session_view_frame_request is None:
            raise ValueError(
                "ExperienceSdkClient.watch_experience_view_state requires "
                "session_view_frame_request."
            )
        request = _request_or_model(
            request,
            WatchExperienceViewStateRequest,
            experience_name=experience_name,
            session_view_frame_request=session_view_frame_request,
            projection_experience_view_instance_id=(
                projection_experience_view_instance_id
            ),
            provider_context=provider_context or {},
            known_cursor=known_cursor,
            known_digest=known_digest,
            poll_interval_ms=poll_interval_ms,
        )
        return await self._invoke(
            "watch_experience_view_state",
            "watch_experience_view_state",
            request,
        )

    async def _invoke(
        self,
        capability_name: str,
        endpoint_name: str,
        request: object,
    ) -> object:
        capability = getattr(self.api_client.experience, capability_name)
        endpoint = getattr(capability, endpoint_name)
        return await endpoint(request)


def build_experience_sdk_client(api_client: Any) -> ExperienceSdkClient:
    return ExperienceSdkClient(api_client=api_client)


def _request_or_model(
    request: object | None,
    model_cls: type[_T],
    **values: object,
) -> object:
    if request is not None:
        return request
    payload = {key: value for key, value in values.items() if value is not None}
    return model_cls.model_validate(payload)


def _environment_admission_receipt(
    value: object | None,
) -> EnvironmentActorAdmissionReceipt | None:
    if value is None:
        return None
    if isinstance(value, EnvironmentActorAdmissionReceipt):
        return value

    dto_receipt = getattr(value, "dto_receipt", None)
    if dto_receipt is not None:
        return _environment_admission_receipt(dto_receipt)

    payload: object
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        payload = value
    return EnvironmentActorAdmissionReceipt.model_validate(payload)


def _environment_session_join_receipt(
    value: object | None,
) -> EnvironmentSessionJoinReceipt | None:
    if value is None:
        return None
    if isinstance(value, EnvironmentSessionJoinReceipt):
        return value

    dto_receipt = getattr(value, "dto_receipt", None)
    if dto_receipt is not None:
        return _environment_session_join_receipt(dto_receipt)

    receipt = getattr(value, "receipt", None)
    if receipt is not None:
        return _environment_session_join_receipt(receipt)

    payload: object
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        payload = value
    return EnvironmentSessionJoinReceipt.model_validate(payload)


def _experience_actor_admission_receipt(
    value: object | None,
) -> ExperienceActorConfigAdmissionReceipt | None:
    if value is None:
        return None
    if isinstance(value, ExperienceActorConfigAdmissionReceipt):
        return value

    dto_receipt = getattr(value, "dto_receipt", None)
    if dto_receipt is not None:
        return _experience_actor_admission_receipt(dto_receipt)

    receipt = getattr(value, "receipt", None)
    if receipt is not None:
        return _experience_actor_admission_receipt(receipt)

    payload: object
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        payload = value
    return ExperienceActorConfigAdmissionReceipt.model_validate(payload)
