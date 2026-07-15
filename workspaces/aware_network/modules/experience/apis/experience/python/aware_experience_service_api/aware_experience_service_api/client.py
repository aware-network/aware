# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import AsyncIterator, cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF,
    EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF,
    EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF,
    EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF,
    EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF,
    EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF,
    EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF,
    EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
    EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF,
    EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF,
    EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF,
    EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF,
    EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF,
    EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF,
    EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
    EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF,
    EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF,
    EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF,
    EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF,
    EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF,
    EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF,
    EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF,
    EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF,
    EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF,
    EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF,
)
from aware_experience_service_dto.experience.actor_admission.service_operation import (
    AdmitExperienceActorConfigRequest,
    AdmitExperienceActorConfigResponse,
)
from aware_experience_service_dto.experience.environment_profile.service_operation import (
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ApplyExperienceEnvironmentProfileProgramsResponse,
    ProvisionExperienceEnvironmentProfileRequest,
    ProvisionExperienceEnvironmentProfileResponse,
    UpsertExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileResponse,
)
from aware_experience_service_dto.experience.layout_transition.service_operation import (
    RequestExperienceLayoutTransitionRequest,
    RequestExperienceLayoutTransitionResponse,
)
from aware_experience_service_dto.experience.package_materialization.service_operation import (
    ResolveExperiencePackageProjectionOwnershipRequest,
    ResolveExperiencePackageProjectionOwnershipResponse,
)
from aware_experience_service_dto.experience.program.service_operation import (
    ApplyProgramRefRequest,
    ApplyProgramRefResponse,
    GetTurnExecutionRequest,
    GetTurnExecutionResponse,
    RunProgramRequest,
    RunProgramResponse,
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_experience_service_dto.experience.section_graph_binding.models import ExperienceSectionGraphBindingStateEvent
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceLayoutGraphBindingRequest,
    ActivateExperienceLayoutGraphBindingResponse,
    ActivateExperienceSectionGraphBindingRequest,
    ActivateExperienceSectionGraphBindingResponse,
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
    GetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingCatalogResponse,
    GetExperienceLayoutGraphBindingStateRequest,
    GetExperienceLayoutGraphBindingStateResponse,
    GetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingCatalogResponse,
    GetExperienceSectionGraphBindingStateRequest,
    GetExperienceSectionGraphBindingStateResponse,
    InvokeExperienceViewInvocationActionRequest,
    InvokeExperienceViewInvocationActionResponse,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
    ResolveExperienceInvocationActionRolePolicyRequest,
    ResolveExperienceInvocationActionRolePolicyResponse,
    WatchExperienceSectionGraphBindingsRequest,
    WatchExperienceSectionGraphBindingsResponse,
)
from aware_experience_service_dto.experience.session_commit.service_operation import (
    DescribeExperienceSessionRequest,
    DescribeExperienceSessionResponse,
    MountExperienceSessionProfileRequest,
    MountExperienceSessionProfileResponse,
    StartExperienceSessionRequest,
    StartExperienceSessionResponse,
)
from aware_experience_service_dto.experience.session_context.service_operation import (
    ResolveExperienceSessionContextRequest,
    ResolveExperienceSessionContextResponse,
)
from aware_experience_service_dto.experience.session_handoff.service_operation import (
    EnsureExperienceSessionHandoffRequest,
    EnsureExperienceSessionHandoffResponse,
    GetExperienceSessionHandoffStatusRequest,
    GetExperienceSessionHandoffStatusResponse,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
    ResolveExperienceSessionViewFrameResponse,
)
from aware_experience_service_dto.experience.thread_layout_resolution.service_operation import (
    ResolveExperienceThreadLayoutIntentRequest,
    ResolveExperienceThreadLayoutIntentResponse,
)
from aware_experience_service_dto.experience.view_state.models import ExperienceViewStateEvent
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
    WatchExperienceViewStateResponse,
)

ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent = (
    ExperienceSectionGraphBindingStateEvent
)
ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent = ExperienceViewStateEvent


class ExperienceActivateExperienceLayoutGraphBindingCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def activate_experience_layout_graph_binding(
        self, request: ActivateExperienceLayoutGraphBindingRequest
    ) -> ActivateExperienceLayoutGraphBindingResponse:
        """Activate one Experience layout graph binding through its grouped section graph bindings."""
        return cast(
            ActivateExperienceLayoutGraphBindingResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceActivateExperienceSectionGraphBindingCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def activate_experience_section_graph_binding(
        self, request: ActivateExperienceSectionGraphBindingRequest
    ) -> ActivateExperienceSectionGraphBindingResponse:
        """Activate one Experience section graph binding through the canonical Experience coordination seam."""
        return cast(
            ActivateExperienceSectionGraphBindingResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceActorAdmissionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def admit_experience_actor_config(
        self, request: AdmitExperienceActorConfigRequest
    ) -> AdmitExperienceActorConfigResponse:
        """Admit one actor under an Experience ActorConfig and return Identity-backed role assignment evidence."""
        return cast(
            AdmitExperienceActorConfigResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceApplyExperienceViewEventTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply_experience_view_event_transition(
        self, request: ApplyExperienceViewEventTransitionRequest
    ) -> ApplyExperienceViewEventTransitionResponse:
        """Apply an Experience-owned View -> Event -> View transition through a target section-graph binding."""
        return cast(
            ApplyExperienceViewEventTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceDescribeExperienceSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_experience_session(
        self, request: DescribeExperienceSessionRequest
    ) -> DescribeExperienceSessionResponse:
        """Describe one committed ExperienceSession through the Experience-owned projection read model."""
        return cast(
            DescribeExperienceSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceEnvironmentProfileCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply_experience_environment_profile_programs(
        self, request: ApplyExperienceEnvironmentProfileProgramsRequest
    ) -> ApplyExperienceEnvironmentProfileProgramsResponse:
        """Execute Experience-owned EnvironmentExperience profile program apply declarations."""
        return cast(
            ApplyExperienceEnvironmentProfileProgramsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def provision_experience_environment_profile(
        self, request: ProvisionExperienceEnvironmentProfileRequest
    ) -> ProvisionExperienceEnvironmentProfileResponse:
        """Provision one Experience-owned EnvironmentExperience profile topology seed."""
        return cast(
            ProvisionExperienceEnvironmentProfileResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def upsert_experience_environment_profile(
        self, request: UpsertExperienceEnvironmentProfileRequest
    ) -> UpsertExperienceEnvironmentProfileResponse:
        """Resolve and upsert one Experience-owned EnvironmentExperience profile contract."""
        return cast(
            UpsertExperienceEnvironmentProfileResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceGetExperienceLayoutGraphBindingCatalogCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_experience_layout_graph_binding_catalog(
        self, request: GetExperienceLayoutGraphBindingCatalogRequest
    ) -> GetExperienceLayoutGraphBindingCatalogResponse:
        """Read the canonical Experience layout-graph-binding catalog for one Experience."""
        return cast(
            GetExperienceLayoutGraphBindingCatalogResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceGetExperienceLayoutGraphBindingStateCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_experience_layout_graph_binding_state(
        self, request: GetExperienceLayoutGraphBindingStateRequest
    ) -> GetExperienceLayoutGraphBindingStateResponse:
        """Read current Attention-backed state for one Experience layout graph binding."""
        return cast(
            GetExperienceLayoutGraphBindingStateResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceGetExperienceSectionGraphBindingCatalogCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_experience_section_graph_binding_catalog(
        self, request: GetExperienceSectionGraphBindingCatalogRequest
    ) -> GetExperienceSectionGraphBindingCatalogResponse:
        """Read the canonical section-graph-binding catalog for one Experience."""
        return cast(
            GetExperienceSectionGraphBindingCatalogResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceGetExperienceSectionGraphBindingStateCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_experience_section_graph_binding_state(
        self, request: GetExperienceSectionGraphBindingStateRequest
    ) -> GetExperienceSectionGraphBindingStateResponse:
        """Read the current Attention-backed state for one Experience section graph binding."""
        return cast(
            GetExperienceSectionGraphBindingStateResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceInvokeExperienceViewInvocationActionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def invoke_experience_view_invocation_action(
        self, request: InvokeExperienceViewInvocationActionRequest
    ) -> InvokeExperienceViewInvocationActionResponse:
        """Invoke one API-backed view action through Experience and record its Service/API receipt provenance."""
        return cast(
            InvokeExperienceViewInvocationActionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceMountExperienceSessionProfileCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def mount_experience_session_profile(
        self, request: MountExperienceSessionProfileRequest
    ) -> MountExperienceSessionProfileResponse:
        """Commit one session-local Experience profile mount without selecting global active state."""
        return cast(
            MountExperienceSessionProfileResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperiencePackageMaterializationCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_experience_package_projection_ownership(
        self, request: ResolveExperiencePackageProjectionOwnershipRequest
    ) -> ResolveExperiencePackageProjectionOwnershipResponse:
        """Resolve Experience package projection ownership and consumer requirements without exposing runtime internals."""
        return cast(
            ResolveExperiencePackageProjectionOwnershipResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceProgramCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply_program_ref(self, request: ApplyProgramRefRequest) -> ApplyProgramRefResponse:
        """Apply one pre-resolved Experience program reference."""
        return cast(
            ApplyProgramRefResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def get_turn_execution(self, request: GetTurnExecutionRequest) -> GetTurnExecutionResponse:
        """Read one Experience-owned Program turn execution."""
        return cast(
            GetTurnExecutionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def run_program(self, request: RunProgramRequest) -> RunProgramResponse:
        """Run one Experience-owned Program through the Experience API boundary."""
        return cast(
            RunProgramResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def submit_program_turn(self, request: SubmitProgramTurnRequest) -> SubmitProgramTurnResponse:
        """Submit one Experience-owned Program turn."""
        return cast(
            SubmitProgramTurnResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceRecordExperienceViewInvocationActionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def record_experience_view_invocation_action(
        self, request: RecordExperienceViewInvocationActionRequest
    ) -> RecordExperienceViewInvocationActionResponse:
        """Record one concrete invocation action through a resolved Experience view instance."""
        return cast(
            RecordExperienceViewInvocationActionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceRequestExperienceLayoutTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def request_experience_layout_transition(
        self, request: RequestExperienceLayoutTransitionRequest
    ) -> RequestExperienceLayoutTransitionResponse:
        """Request one Experience layout transition through Experience -> Attention."""
        return cast(
            RequestExperienceLayoutTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceResolveExperienceInvocationActionRolePolicyCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_experience_invocation_action_role_policy(
        self, request: ResolveExperienceInvocationActionRolePolicyRequest
    ) -> ResolveExperienceInvocationActionRolePolicyResponse:
        """Resolve declared Experience role policy for one invocation action config without authorizing a concrete actor."""
        return cast(
            ResolveExperienceInvocationActionRolePolicyResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceResolveExperienceThreadLayoutIntentCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_experience_thread_layout_intent(
        self, request: ResolveExperienceThreadLayoutIntentRequest
    ) -> ResolveExperienceThreadLayoutIntentResponse:
        """Resolve a semantic Experience intent into config-level Thread-Layout targets and evidence."""
        return cast(
            ResolveExperienceThreadLayoutIntentResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceSessionContextCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_experience_session_context(
        self, request: ResolveExperienceSessionContextRequest
    ) -> ResolveExperienceSessionContextResponse:
        """Resolve actor-specific Experience session context over Environment session Attention resolution."""
        return cast(
            ResolveExperienceSessionContextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceSessionHandoffCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_experience_session_handoff(
        self, request: EnsureExperienceSessionHandoffRequest
    ) -> EnsureExperienceSessionHandoffResponse:
        """Admit an actor to an Experience session and ensure one Experience session feature."""
        return cast(
            EnsureExperienceSessionHandoffResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def get_experience_session_handoff_status(
        self, request: GetExperienceSessionHandoffStatusRequest
    ) -> GetExperienceSessionHandoffStatusResponse:
        """Read Experience session actor admission and session feature lease health."""
        return cast(
            GetExperienceSessionHandoffStatusResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceSessionViewFrameCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_experience_session_view_frame(
        self, request: ResolveExperienceSessionViewFrameRequest
    ) -> ResolveExperienceSessionViewFrameResponse:
        """Resolve a consumer read frame over actor-specific Experience context and shared Environment Attention."""
        return cast(
            ResolveExperienceSessionViewFrameResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceStartExperienceSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def start_experience_session(self, request: StartExperienceSessionRequest) -> StartExperienceSessionResponse:
        """Commit one ExperienceSession rooted on a child Identity Session with explicit EnvironmentSession provenance."""
        return cast(
            StartExperienceSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExperienceWatchExperienceSectionGraphBindingsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def watch_experience_section_graph_bindings(
        self, request: WatchExperienceSectionGraphBindingsRequest
    ) -> WatchExperienceSectionGraphBindingsResponse:
        """Read and stream Experience section-graph-binding state snapshots."""
        return cast(
            WatchExperienceSectionGraphBindingsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_watch_experience_section_graph_bindings(
        self, request: WatchExperienceSectionGraphBindingsRequest
    ) -> AsyncIterator[ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent]:
        """Read and stream Experience section-graph-binding state snapshots."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(
                ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent, event
            )


class ExperienceWatchExperienceViewStateCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def watch_experience_view_state(
        self, request: WatchExperienceViewStateRequest
    ) -> WatchExperienceViewStateResponse:
        """Read and stream Experience-owned view-state snapshots for one mounted view subscription."""
        return cast(
            WatchExperienceViewStateResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_watch_experience_view_state(
        self, request: WatchExperienceViewStateRequest
    ) -> AsyncIterator[ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent]:
        """Read and stream Experience-owned view-state snapshots for one mounted view subscription."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent, event)


class ExperienceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.activate_experience_layout_graph_binding = ExperienceActivateExperienceLayoutGraphBindingCapabilityClient(
            client
        )
        self.activate_experience_section_graph_binding = (
            ExperienceActivateExperienceSectionGraphBindingCapabilityClient(client)
        )
        self.actor_admission = ExperienceActorAdmissionCapabilityClient(client)
        self.apply_experience_view_event_transition = ExperienceApplyExperienceViewEventTransitionCapabilityClient(
            client
        )
        self.describe_experience_session = ExperienceDescribeExperienceSessionCapabilityClient(client)
        self.environment_profile = ExperienceEnvironmentProfileCapabilityClient(client)
        self.get_experience_layout_graph_binding_catalog = (
            ExperienceGetExperienceLayoutGraphBindingCatalogCapabilityClient(client)
        )
        self.get_experience_layout_graph_binding_state = ExperienceGetExperienceLayoutGraphBindingStateCapabilityClient(
            client
        )
        self.get_experience_section_graph_binding_catalog = (
            ExperienceGetExperienceSectionGraphBindingCatalogCapabilityClient(client)
        )
        self.get_experience_section_graph_binding_state = (
            ExperienceGetExperienceSectionGraphBindingStateCapabilityClient(client)
        )
        self.invoke_experience_view_invocation_action = ExperienceInvokeExperienceViewInvocationActionCapabilityClient(
            client
        )
        self.mount_experience_session_profile = ExperienceMountExperienceSessionProfileCapabilityClient(client)
        self.package_materialization = ExperiencePackageMaterializationCapabilityClient(client)
        self.program = ExperienceProgramCapabilityClient(client)
        self.record_experience_view_invocation_action = ExperienceRecordExperienceViewInvocationActionCapabilityClient(
            client
        )
        self.request_experience_layout_transition = ExperienceRequestExperienceLayoutTransitionCapabilityClient(client)
        self.resolve_experience_invocation_action_role_policy = (
            ExperienceResolveExperienceInvocationActionRolePolicyCapabilityClient(client)
        )
        self.resolve_experience_thread_layout_intent = ExperienceResolveExperienceThreadLayoutIntentCapabilityClient(
            client
        )
        self.session_context = ExperienceSessionContextCapabilityClient(client)
        self.session_handoff = ExperienceSessionHandoffCapabilityClient(client)
        self.session_view_frame = ExperienceSessionViewFrameCapabilityClient(client)
        self.start_experience_session = ExperienceStartExperienceSessionCapabilityClient(client)
        self.watch_experience_section_graph_bindings = ExperienceWatchExperienceSectionGraphBindingsCapabilityClient(
            client
        )
        self.watch_experience_view_state = ExperienceWatchExperienceViewStateCapabilityClient(client)


class AwareExperienceServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.experience = ExperienceApiClient(client)


__all__ = [
    "AwareExperienceServiceApiClient",
    "ExperienceApiClient",
    "ExperienceActivateExperienceLayoutGraphBindingCapabilityClient",
    "ExperienceActivateExperienceSectionGraphBindingCapabilityClient",
    "ExperienceActorAdmissionCapabilityClient",
    "ExperienceApplyExperienceViewEventTransitionCapabilityClient",
    "ExperienceDescribeExperienceSessionCapabilityClient",
    "ExperienceEnvironmentProfileCapabilityClient",
    "ExperienceGetExperienceLayoutGraphBindingCatalogCapabilityClient",
    "ExperienceGetExperienceLayoutGraphBindingStateCapabilityClient",
    "ExperienceGetExperienceSectionGraphBindingCatalogCapabilityClient",
    "ExperienceGetExperienceSectionGraphBindingStateCapabilityClient",
    "ExperienceInvokeExperienceViewInvocationActionCapabilityClient",
    "ExperienceMountExperienceSessionProfileCapabilityClient",
    "ExperiencePackageMaterializationCapabilityClient",
    "ExperienceProgramCapabilityClient",
    "ExperienceRecordExperienceViewInvocationActionCapabilityClient",
    "ExperienceRequestExperienceLayoutTransitionCapabilityClient",
    "ExperienceResolveExperienceInvocationActionRolePolicyCapabilityClient",
    "ExperienceResolveExperienceThreadLayoutIntentCapabilityClient",
    "ExperienceSessionContextCapabilityClient",
    "ExperienceSessionHandoffCapabilityClient",
    "ExperienceSessionViewFrameCapabilityClient",
    "ExperienceStartExperienceSessionCapabilityClient",
    "ExperienceWatchExperienceSectionGraphBindingsCapabilityClient",
    "ExperienceWatchExperienceViewStateCapabilityClient",
    "ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent",
    "ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent",
]
