# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import AsyncIterator, cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF,
    ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
    ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF,
    ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF,
    ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF,
    ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF,
    ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF,
    ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF,
    ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF,
    ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF,
    ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF,
    ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF,
    ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF,
    ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF,
)
from aware_attention_service_dto.attention.section.models import AttentionRuntimeMountSnapshotEvent
from aware_attention_service_dto.attention.section.service_operation import (
    ActivateAttentionSectionObservableRequest,
    ActivateAttentionSectionObservableResponse,
    GetAttentionFocusScopeCommitsRequest,
    GetAttentionFocusScopeCommitsResponse,
    GetAttentionRuntimeMountRequest,
    GetAttentionRuntimeMountResponse,
    GetAttentionSectionStateRequest,
    GetAttentionSectionStateResponse,
    WatchAttentionRuntimeMountRequest,
    WatchAttentionRuntimeMountResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTopologyTransitionRequest,
    ApplyAttentionSessionLayoutTopologyTransitionResponse,
    ApplyAttentionSessionLayoutTransitionRequest,
    ApplyAttentionSessionLayoutTransitionResponse,
    DescribeAttentionSessionRequest,
    DescribeAttentionSessionResponse,
    DescribeAttentionTransitionRequest,
    DescribeAttentionTransitionResponse,
    ListAttentionTransitionsRequest,
    ListAttentionTransitionsResponse,
    MountAttentionSessionLayoutRequest,
    MountAttentionSessionLayoutResponse,
    MountAttentionSessionSectionRequest,
    MountAttentionSessionSectionResponse,
    StartAttentionSessionRequest,
    StartAttentionSessionResponse,
    ValidateAttentionTransitionRequest,
    ValidateAttentionTransitionResponse,
)

AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent = AttentionRuntimeMountSnapshotEvent


class AttentionActivateSectionObservableCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def activate_section_observable(
        self, request: ActivateAttentionSectionObservableRequest
    ) -> ActivateAttentionSectionObservableResponse:
        """Activate one ontology-backed observable for one section-scoped Attention focus scope."""
        return cast(
            ActivateAttentionSectionObservableResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionApplySessionLayoutTopologyTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply_session_layout_topology_transition(
        self, request: ApplyAttentionSessionLayoutTopologyTransitionRequest
    ) -> ApplyAttentionSessionLayoutTopologyTransitionResponse:
        """Atomically commit one complete active-membership/order vector on an AttentionSession lane."""
        return cast(
            ApplyAttentionSessionLayoutTopologyTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionApplySessionLayoutTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply_session_layout_transition(
        self, request: ApplyAttentionSessionLayoutTransitionRequest
    ) -> ApplyAttentionSessionLayoutTransitionResponse:
        """Atomically commit one complete typed shared-layout vector on an AttentionSession lane."""
        return cast(
            ApplyAttentionSessionLayoutTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionDescribeAttentionSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_attention_session(
        self, request: DescribeAttentionSessionRequest
    ) -> DescribeAttentionSessionResponse:
        """Read one AttentionSession and its active layout/section/transition pins."""
        return cast(
            DescribeAttentionSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionDescribeAttentionTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_attention_transition(
        self, request: DescribeAttentionTransitionRequest
    ) -> DescribeAttentionTransitionResponse:
        """Read one AttentionFocusTransition pin plus its parent session chain."""
        return cast(
            DescribeAttentionTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionGetFocusScopeCommitsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_focus_scope_commits(
        self, request: GetAttentionFocusScopeCommitsRequest
    ) -> GetAttentionFocusScopeCommitsResponse:
        """List committed OIG commit pointers observed by one Attention focus scope."""
        return cast(
            GetAttentionFocusScopeCommitsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionGetRuntimeMountCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_runtime_mount(self, request: GetAttentionRuntimeMountRequest) -> GetAttentionRuntimeMountResponse:
        """Read one typed batch snapshot of Attention-owned section state for the currently mounted
        bundle-backed runtime layout, optionally seeding section defaults supplied by Interface."""
        return cast(
            GetAttentionRuntimeMountResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionGetSectionStateCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_section_state(self, request: GetAttentionSectionStateRequest) -> GetAttentionSectionStateResponse:
        """Read the current section-scoped focus-scope and observable state for one Attention section,
        optionally seeding a missing observable from an Interface-supplied default candidate."""
        return cast(
            GetAttentionSectionStateResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionListAttentionTransitionsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list_attention_transitions(
        self, request: ListAttentionTransitionsRequest
    ) -> ListAttentionTransitionsResponse:
        """List AttentionFocusTransition pins by session, section, focus-scope, or kind."""
        return cast(
            ListAttentionTransitionsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionMountAttentionSessionLayoutCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def mount_attention_session_layout(
        self, request: MountAttentionSessionLayoutRequest
    ) -> MountAttentionSessionLayoutResponse:
        """Mount one Attention Layout on an existing committed AttentionSession lane."""
        return cast(
            MountAttentionSessionLayoutResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionMountAttentionSessionSectionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def mount_attention_session_section(
        self, request: MountAttentionSessionSectionRequest
    ) -> MountAttentionSessionSectionResponse:
        """Mount one Attention Section anchor on an existing committed session layout."""
        return cast(
            MountAttentionSessionSectionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionStartAttentionSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def start_attention_session(self, request: StartAttentionSessionRequest) -> StartAttentionSessionResponse:
        """Construct one commit-backed AttentionSession over a verified Identity Session."""
        return cast(
            StartAttentionSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionValidateAttentionTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def validate_attention_transition(
        self, request: ValidateAttentionTransitionRequest
    ) -> ValidateAttentionTransitionResponse:
        """Validate that one AttentionFocusTransition matches expected Attention session coordinates."""
        return cast(
            ValidateAttentionTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class AttentionWatchRuntimeMountCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def watch_runtime_mount(
        self, request: WatchAttentionRuntimeMountRequest
    ) -> WatchAttentionRuntimeMountResponse:
        """Subscribe to streamed Attention runtime-mount snapshots for the currently mounted
        bundle-backed layout candidates."""
        return cast(
            WatchAttentionRuntimeMountResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_watch_runtime_mount(
        self, request: WatchAttentionRuntimeMountRequest
    ) -> AsyncIterator[AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent]:
        """Subscribe to streamed Attention runtime-mount snapshots for the currently mounted
        bundle-backed layout candidates."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent, event)


class AttentionApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.activate_section_observable = AttentionActivateSectionObservableCapabilityClient(client)
        self.apply_session_layout_topology_transition = AttentionApplySessionLayoutTopologyTransitionCapabilityClient(
            client
        )
        self.apply_session_layout_transition = AttentionApplySessionLayoutTransitionCapabilityClient(client)
        self.describe_attention_session = AttentionDescribeAttentionSessionCapabilityClient(client)
        self.describe_attention_transition = AttentionDescribeAttentionTransitionCapabilityClient(client)
        self.get_focus_scope_commits = AttentionGetFocusScopeCommitsCapabilityClient(client)
        self.get_runtime_mount = AttentionGetRuntimeMountCapabilityClient(client)
        self.get_section_state = AttentionGetSectionStateCapabilityClient(client)
        self.list_attention_transitions = AttentionListAttentionTransitionsCapabilityClient(client)
        self.mount_attention_session_layout = AttentionMountAttentionSessionLayoutCapabilityClient(client)
        self.mount_attention_session_section = AttentionMountAttentionSessionSectionCapabilityClient(client)
        self.start_attention_session = AttentionStartAttentionSessionCapabilityClient(client)
        self.validate_attention_transition = AttentionValidateAttentionTransitionCapabilityClient(client)
        self.watch_runtime_mount = AttentionWatchRuntimeMountCapabilityClient(client)


class AwareAttentionServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.attention = AttentionApiClient(client)


__all__ = [
    "AwareAttentionServiceApiClient",
    "AttentionApiClient",
    "AttentionActivateSectionObservableCapabilityClient",
    "AttentionApplySessionLayoutTopologyTransitionCapabilityClient",
    "AttentionApplySessionLayoutTransitionCapabilityClient",
    "AttentionDescribeAttentionSessionCapabilityClient",
    "AttentionDescribeAttentionTransitionCapabilityClient",
    "AttentionGetFocusScopeCommitsCapabilityClient",
    "AttentionGetRuntimeMountCapabilityClient",
    "AttentionGetSectionStateCapabilityClient",
    "AttentionListAttentionTransitionsCapabilityClient",
    "AttentionMountAttentionSessionLayoutCapabilityClient",
    "AttentionMountAttentionSessionSectionCapabilityClient",
    "AttentionStartAttentionSessionCapabilityClient",
    "AttentionValidateAttentionTransitionCapabilityClient",
    "AttentionWatchRuntimeMountCapabilityClient",
    "AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent",
]
