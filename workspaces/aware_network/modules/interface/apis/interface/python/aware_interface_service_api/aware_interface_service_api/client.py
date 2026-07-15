# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import AsyncIterator, cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF,
    INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF,
    INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF,
    INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
    INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF,
    INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF,
    INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF,
    INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF,
    INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF,
    INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF,
    INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF,
    INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF,
    INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF,
    INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF,
    INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF,
    INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF,
    INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF,
    INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF,
    INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF,
    INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF,
    INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF,
    INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF,
    INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF,
    INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF,
    INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF,
    INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF,
    INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionRequest,
    InterfaceActionResponse,
    InterfaceActivateRuntimeFocusRequest,
    InterfaceActivateRuntimeFocusResponse,
    InterfaceAdmitEnvironmentActorRequest,
    InterfaceAdmitEnvironmentActorResponse,
    InterfaceApiEventNotification,
    InterfaceApiStreamClosedNotification,
    InterfaceApplyAttentionLayoutTopologyTransitionRequest,
    InterfaceApplyAttentionLayoutTopologyTransitionResponse,
    InterfaceApplyAttentionLayoutTransitionRequest,
    InterfaceApplyAttentionLayoutTransitionResponse,
    InterfaceEnterAppScreenRequest,
    InterfaceEnterAppScreenResponse,
    InterfaceEnterEnvironmentRequest,
    InterfaceEnterEnvironmentResponse,
    InterfaceExperienceSessionMountRequest,
    InterfaceExperienceSessionMountResponse,
    InterfaceFollowRequest,
    InterfaceFollowResponse,
    InterfaceInvokeApiRequest,
    InterfaceInvokeApiResponse,
    InterfaceJoinEnvironmentSessionRequest,
    InterfaceJoinEnvironmentSessionResponse,
    InterfaceReportRendererCapabilitiesRequest,
    InterfaceReportRendererCapabilitiesResponse,
    InterfaceRequestWindowLayoutRequest,
    InterfaceRequestWindowLayoutResponse,
    InterfaceResolveExperienceLensRequest,
    InterfaceResolveExperienceLensResponse,
    InterfaceSelectEnvironmentNavigationTargetRequest,
    InterfaceSelectEnvironmentNavigationTargetResponse,
    InterfaceSelectProfileRequest,
    InterfaceSelectProfileResponse,
    InterfaceSelectRuntimeLayoutRequest,
    InterfaceSelectRuntimeLayoutResponse,
    InterfaceSelectStepRequest,
    InterfaceSelectStepResponse,
    InterfaceSessionDescribeRequest,
    InterfaceSessionDescribeResponse,
    InterfaceSessionStartRequest,
    InterfaceSessionStartResponse,
    InterfaceStateNotification,
    InterfaceStatusRequest,
    InterfaceStatusResponse,
    InterfaceStopRequest,
    InterfaceStopResponse,
    InterfaceStreamApiRequest,
    InterfaceStreamApiResponse,
    InterfaceSyncViewStateCursorRequest,
    InterfaceSyncViewStateCursorResponse,
    NamespaceEnsureRequest,
    NamespaceEnsureResponse,
    NamespaceListRequest,
    NamespaceListResponse,
    PingRequest,
    PingResponse,
)

InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent = (
    InterfaceApiStreamClosedNotification | InterfaceApiEventNotification
)
InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent = InterfaceStateNotification


class InterfaceActivateInterfaceRuntimeFocusCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def activate_interface_runtime_focus(
        self, request: InterfaceActivateRuntimeFocusRequest
    ) -> InterfaceActivateRuntimeFocusResponse:
        """Activate an Interface runtime section representation or focus target."""
        return cast(
            InterfaceActivateRuntimeFocusResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceAdmitEnvironmentActorCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def admit_environment_actor(
        self, request: InterfaceAdmitEnvironmentActorRequest
    ) -> InterfaceAdmitEnvironmentActorResponse:
        """Admit the current Interface actor to an Environment/Profile before Experience lens resolution."""
        return cast(
            InterfaceAdmitEnvironmentActorResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceAdmitInterfaceCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def admit_interface(self, request: NamespaceEnsureRequest) -> NamespaceEnsureResponse:
        """Admit or resume one renderer/agent namespace into the Interface service runtime."""
        return cast(
            NamespaceEnsureResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceApplyAttentionLayoutTopologyTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply_attention_layout_topology_transition(
        self, request: InterfaceApplyAttentionLayoutTopologyTransitionRequest
    ) -> InterfaceApplyAttentionLayoutTopologyTransitionResponse:
        """Commit one complete active-membership/order vector through Interface Host and Attention authority."""
        return cast(
            InterfaceApplyAttentionLayoutTopologyTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceApplyAttentionLayoutTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply_attention_layout_transition(
        self, request: InterfaceApplyAttentionLayoutTransitionRequest
    ) -> InterfaceApplyAttentionLayoutTransitionResponse:
        """Commit one complete shared-layout vector through Interface Host and Attention authority."""
        return cast(
            InterfaceApplyAttentionLayoutTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceDescribeInterfaceSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_interface_session(
        self, request: InterfaceSessionDescribeRequest
    ) -> InterfaceSessionDescribeResponse:
        """Read one committed InterfaceSession and its Interface-owned ExperienceSession portal rows."""
        return cast(
            InterfaceSessionDescribeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceEnterAppScreenCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def enter_app_screen(self, request: InterfaceEnterAppScreenRequest) -> InterfaceEnterAppScreenResponse:
        """Enter one committed AppPackage screen through Interface Host and Experience layout activation."""
        return cast(
            InterfaceEnterAppScreenResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceEnterEnvironmentCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def enter_environment(self, request: InterfaceEnterEnvironmentRequest) -> InterfaceEnterEnvironmentResponse:
        """Enter or resume an Environment shell context without Interface-owned Process/Thread defaults."""
        return cast(
            InterfaceEnterEnvironmentResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceGetInterfaceStateCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_interface_state(self, request: InterfaceStatusRequest) -> InterfaceStatusResponse:
        """Read the current Interface host state for an admitted namespace."""
        return cast(
            InterfaceStatusResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceInvokeInterfaceApiCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def invoke_interface_api(self, request: InterfaceInvokeApiRequest) -> InterfaceInvokeApiResponse:
        """Invoke a mounted API endpoint from Interface action context."""
        return cast(
            InterfaceInvokeApiResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceJoinEnvironmentSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def join_environment_session(
        self, request: InterfaceJoinEnvironmentSessionRequest
    ) -> InterfaceJoinEnvironmentSessionResponse:
        """Join an Environment session and consume the Environment-owned default navigation context."""
        return cast(
            InterfaceJoinEnvironmentSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceListInterfaceNamespacesCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list_interface_namespaces(self, request: NamespaceListRequest) -> NamespaceListResponse:
        """List locally admitted Interface namespaces for operator/debug surfaces."""
        return cast(
            NamespaceListResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceMountInterfaceExperienceSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def mount_interface_experience_session(
        self, request: InterfaceExperienceSessionMountRequest
    ) -> InterfaceExperienceSessionMountResponse:
        """Commit one InterfaceSession-owned portal to an existing ExperienceSession authority."""
        return cast(
            InterfaceExperienceSessionMountResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfacePerformInterfaceActionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def perform_interface_action(self, request: InterfaceActionRequest) -> InterfaceActionResponse:
        """Dispatch a mounted Interface action through the canonical service boundary."""
        return cast(
            InterfaceActionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfacePingInterfaceHostCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ping_interface_host(self, request: PingRequest) -> PingResponse:
        """Read local Interface host readiness for service transport adapters."""
        return cast(
            PingResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceReportRendererCapabilitiesCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def report_renderer_capabilities(
        self, request: InterfaceReportRendererCapabilitiesRequest
    ) -> InterfaceReportRendererCapabilitiesResponse:
        """Report renderer capabilities for the admitted Interface namespace."""
        return cast(
            InterfaceReportRendererCapabilitiesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceRequestInterfaceWindowLayoutCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def request_interface_window_layout(
        self, request: InterfaceRequestWindowLayoutRequest
    ) -> InterfaceRequestWindowLayoutResponse:
        """Request a canonical Interface window/layout/section binding for a consumer action."""
        return cast(
            InterfaceRequestWindowLayoutResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceResolveExperienceLensCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_experience_lens(
        self, request: InterfaceResolveExperienceLensRequest
    ) -> InterfaceResolveExperienceLensResponse:
        """Resolve the current Interface focus into an actor-specific Experience lens over an admitted Environment session."""
        return cast(
            InterfaceResolveExperienceLensResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceSelectEnvironmentNavigationTargetCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def select_environment_navigation_target(
        self, request: InterfaceSelectEnvironmentNavigationTargetRequest
    ) -> InterfaceSelectEnvironmentNavigationTargetResponse:
        """Select the active Environment Process/Thread target through Interface-owned shell navigation."""
        return cast(
            InterfaceSelectEnvironmentNavigationTargetResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceSelectInterfaceProfileCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def select_interface_profile(self, request: InterfaceSelectProfileRequest) -> InterfaceSelectProfileResponse:
        """Select the active Interface control profile for an admitted namespace."""
        return cast(
            InterfaceSelectProfileResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceSelectInterfaceRuntimeLayoutCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def select_interface_runtime_layout(
        self, request: InterfaceSelectRuntimeLayoutRequest
    ) -> InterfaceSelectRuntimeLayoutResponse:
        """Select the active Interface runtime layout configuration."""
        return cast(
            InterfaceSelectRuntimeLayoutResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceSelectInterfaceStepCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def select_interface_step(self, request: InterfaceSelectStepRequest) -> InterfaceSelectStepResponse:
        """Select the active Interface orchestration step for an admitted namespace."""
        return cast(
            InterfaceSelectStepResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceStartInterfaceSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def start_interface_session(self, request: InterfaceSessionStartRequest) -> InterfaceSessionStartResponse:
        """Commit one Interface-owned shared door rooted on a canonical Identity Session."""
        return cast(
            InterfaceSessionStartResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceStopInterfaceNamespaceCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def stop_interface_namespace(self, request: InterfaceStopRequest) -> InterfaceStopResponse:
        """Stop one local Interface namespace."""
        return cast(
            InterfaceStopResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceStreamInterfaceApiCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def stream_interface_api(self, request: InterfaceStreamApiRequest) -> InterfaceStreamApiResponse:
        """Invoke a mounted streaming API endpoint from Interface action context."""
        return cast(
            InterfaceStreamApiResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_stream_interface_api(
        self, request: InterfaceStreamApiRequest
    ) -> AsyncIterator[InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent]:
        """Invoke a mounted streaming API endpoint from Interface action context."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent, event)


class InterfaceSyncViewStateCursorCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def sync_view_state_cursor(
        self, request: InterfaceSyncViewStateCursorRequest
    ) -> InterfaceSyncViewStateCursorResponse:
        """Acknowledge consumed view-state cursors for Interface renderer backpressure."""
        return cast(
            InterfaceSyncViewStateCursorResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class InterfaceWatchInterfaceStateCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def watch_interface_state(self, request: InterfaceFollowRequest) -> InterfaceFollowResponse:
        """Read and stream Interface host state snapshots for an admitted namespace."""
        return cast(
            InterfaceFollowResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_watch_interface_state(
        self, request: InterfaceFollowRequest
    ) -> AsyncIterator[InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent]:
        """Read and stream Interface host state snapshots for an admitted namespace."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent, event)


class InterfaceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.activate_interface_runtime_focus = InterfaceActivateInterfaceRuntimeFocusCapabilityClient(client)
        self.admit_environment_actor = InterfaceAdmitEnvironmentActorCapabilityClient(client)
        self.admit_interface = InterfaceAdmitInterfaceCapabilityClient(client)
        self.apply_attention_layout_topology_transition = (
            InterfaceApplyAttentionLayoutTopologyTransitionCapabilityClient(client)
        )
        self.apply_attention_layout_transition = InterfaceApplyAttentionLayoutTransitionCapabilityClient(client)
        self.describe_interface_session = InterfaceDescribeInterfaceSessionCapabilityClient(client)
        self.enter_app_screen = InterfaceEnterAppScreenCapabilityClient(client)
        self.enter_environment = InterfaceEnterEnvironmentCapabilityClient(client)
        self.get_interface_state = InterfaceGetInterfaceStateCapabilityClient(client)
        self.invoke_interface_api = InterfaceInvokeInterfaceApiCapabilityClient(client)
        self.join_environment_session = InterfaceJoinEnvironmentSessionCapabilityClient(client)
        self.list_interface_namespaces = InterfaceListInterfaceNamespacesCapabilityClient(client)
        self.mount_interface_experience_session = InterfaceMountInterfaceExperienceSessionCapabilityClient(client)
        self.perform_interface_action = InterfacePerformInterfaceActionCapabilityClient(client)
        self.ping_interface_host = InterfacePingInterfaceHostCapabilityClient(client)
        self.report_renderer_capabilities = InterfaceReportRendererCapabilitiesCapabilityClient(client)
        self.request_interface_window_layout = InterfaceRequestInterfaceWindowLayoutCapabilityClient(client)
        self.resolve_experience_lens = InterfaceResolveExperienceLensCapabilityClient(client)
        self.select_environment_navigation_target = InterfaceSelectEnvironmentNavigationTargetCapabilityClient(client)
        self.select_interface_profile = InterfaceSelectInterfaceProfileCapabilityClient(client)
        self.select_interface_runtime_layout = InterfaceSelectInterfaceRuntimeLayoutCapabilityClient(client)
        self.select_interface_step = InterfaceSelectInterfaceStepCapabilityClient(client)
        self.start_interface_session = InterfaceStartInterfaceSessionCapabilityClient(client)
        self.stop_interface_namespace = InterfaceStopInterfaceNamespaceCapabilityClient(client)
        self.stream_interface_api = InterfaceStreamInterfaceApiCapabilityClient(client)
        self.sync_view_state_cursor = InterfaceSyncViewStateCursorCapabilityClient(client)
        self.watch_interface_state = InterfaceWatchInterfaceStateCapabilityClient(client)


class AwareInterfaceServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.interface = InterfaceApiClient(client)


__all__ = [
    "AwareInterfaceServiceApiClient",
    "InterfaceApiClient",
    "InterfaceActivateInterfaceRuntimeFocusCapabilityClient",
    "InterfaceAdmitEnvironmentActorCapabilityClient",
    "InterfaceAdmitInterfaceCapabilityClient",
    "InterfaceApplyAttentionLayoutTopologyTransitionCapabilityClient",
    "InterfaceApplyAttentionLayoutTransitionCapabilityClient",
    "InterfaceDescribeInterfaceSessionCapabilityClient",
    "InterfaceEnterAppScreenCapabilityClient",
    "InterfaceEnterEnvironmentCapabilityClient",
    "InterfaceGetInterfaceStateCapabilityClient",
    "InterfaceInvokeInterfaceApiCapabilityClient",
    "InterfaceJoinEnvironmentSessionCapabilityClient",
    "InterfaceListInterfaceNamespacesCapabilityClient",
    "InterfaceMountInterfaceExperienceSessionCapabilityClient",
    "InterfacePerformInterfaceActionCapabilityClient",
    "InterfacePingInterfaceHostCapabilityClient",
    "InterfaceReportRendererCapabilitiesCapabilityClient",
    "InterfaceRequestInterfaceWindowLayoutCapabilityClient",
    "InterfaceResolveExperienceLensCapabilityClient",
    "InterfaceSelectEnvironmentNavigationTargetCapabilityClient",
    "InterfaceSelectInterfaceProfileCapabilityClient",
    "InterfaceSelectInterfaceRuntimeLayoutCapabilityClient",
    "InterfaceSelectInterfaceStepCapabilityClient",
    "InterfaceStartInterfaceSessionCapabilityClient",
    "InterfaceStopInterfaceNamespaceCapabilityClient",
    "InterfaceStreamInterfaceApiCapabilityClient",
    "InterfaceSyncViewStateCursorCapabilityClient",
    "InterfaceWatchInterfaceStateCapabilityClient",
    "InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent",
    "InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent",
]
