# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import AsyncIterator, cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    META__COMMIT__SUBSCRIBE_ENDPOINT_REF,
    META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF,
    META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
    META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
    META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
    META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF,
    META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF,
    META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
    META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
    META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF,
    META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF,
)
from aware_meta_service_dto.diagnostics.completeness import (
    MetaCompletenessAnalyzeRequest,
    MetaCompletenessAnalyzeResponse,
)
from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageEnsureRequest,
    MetaObjectConfigGraphPackageEnsureResponse,
)
from aware_meta_service_dto.graph.instance.commit_event import (
    MetaCommitEventEnvelope,
    MetaCommitSubscriptionRequest,
    MetaCommitSubscriptionResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadRequest,
    MetaGraphGetLaneHeadResponse,
    MetaGraphGetObjectInstanceGraphCommitRequest,
    MetaGraphGetObjectInstanceGraphCommitResponse,
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
    MetaGraphInvokeTemporalFunctionRequest,
    MetaGraphInvokeTemporalFunctionResponse,
    MetaGraphResolveProjectionRequest,
    MetaGraphResolveProjectionResponse,
)
from aware_meta_service_dto.graph.view.graph_view import (
    MetaGraphResolveGraphViewRequest,
    MetaGraphResolveGraphViewResponse,
)
from aware_meta_service_dto.persistence.database_readiness import (
    MetaPersistenceEnsureDatabaseReadyRequest,
    MetaPersistenceEnsureDatabaseReadyResponse,
)
from aware_meta_service_dto.runtime.read_model import MetaRuntimeReadModelRequest, MetaRuntimeReadModelResponse

MetaCommitSubscribeStreamEvent = MetaCommitEventEnvelope


class MetaCommitCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def subscribe(self, request: MetaCommitSubscriptionRequest) -> MetaCommitSubscriptionResponse:
        """Subscribe to remote-safe Meta commit fan-out events."""
        return cast(
            MetaCommitSubscriptionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__COMMIT__SUBSCRIBE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_subscribe(
        self, request: MetaCommitSubscriptionRequest
    ) -> AsyncIterator[MetaCommitSubscribeStreamEvent]:
        """Subscribe to remote-safe Meta commit fan-out events."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=META__COMMIT__SUBSCRIBE_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(MetaCommitSubscribeStreamEvent, event)


class MetaDiagnosticsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def analyze_object_config_graph_completeness(
        self, request: MetaCompletenessAnalyzeRequest
    ) -> MetaCompletenessAnalyzeResponse:
        """Analyze one Meta ObjectConfigGraph package for constructor/projection completeness without mutating graph state."""
        return cast(
            MetaCompletenessAnalyzeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MetaGraphCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_lane_head(self, request: MetaGraphGetLaneHeadRequest) -> MetaGraphGetLaneHeadResponse:
        """Read the current committed graph lane head through Meta service authority."""
        return cast(
            MetaGraphGetLaneHeadResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def get_object_instance_graph_commit(
        self, request: MetaGraphGetObjectInstanceGraphCommitRequest
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse:
        """Read one committed ObjectInstanceGraphCommit through Meta service authority."""
        return cast(
            MetaGraphGetObjectInstanceGraphCommitResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def invoke_function(self, request: MetaGraphInvokeFunctionRequest) -> MetaGraphInvokeFunctionResponse:
        """Invoke one graph function through the canonical Meta commit authority boundary."""
        return cast(
            MetaGraphInvokeFunctionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def invoke_temporal_function(
        self, request: MetaGraphInvokeTemporalFunctionRequest
    ) -> MetaGraphInvokeTemporalFunctionResponse:
        """Invoke one graph function against an explicit temporal overlay without committing durable graph state."""
        return cast(
            MetaGraphInvokeTemporalFunctionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_graph_view(self, request: MetaGraphResolveGraphViewRequest) -> MetaGraphResolveGraphViewResponse:
        """Resolve a renderer-safe Meta graph view from lane and commit coordinates without mutating graph state."""
        return cast(
            MetaGraphResolveGraphViewResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_projection(
        self, request: MetaGraphResolveProjectionRequest
    ) -> MetaGraphResolveProjectionResponse:
        """Resolve runtime projection coordinates through Meta service authority without mutating graph state."""
        return cast(
            MetaGraphResolveProjectionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MetaPackageCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_object_config_graph_package(
        self, request: MetaObjectConfigGraphPackageEnsureRequest
    ) -> MetaObjectConfigGraphPackageEnsureResponse:
        """Ensure one canonical ObjectConfigGraphPackage through Meta Service authority."""
        return cast(
            MetaObjectConfigGraphPackageEnsureResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MetaPersistenceCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_database_ready(
        self, request: MetaPersistenceEnsureDatabaseReadyRequest
    ) -> MetaPersistenceEnsureDatabaseReadyResponse:
        """Ensure the OCG-backed database is ready from a Structure-resolved environment DB artifact receipt."""
        return cast(
            MetaPersistenceEnsureDatabaseReadyResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MetaRuntimeReadModelCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_workspace(self, request: MetaRuntimeReadModelRequest) -> MetaRuntimeReadModelResponse:
        """Describe Meta-owned runtime read-model truth for Workspace-required projections without exposing raw runtime/index objects."""
        return cast(
            MetaRuntimeReadModelResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MetaApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.commit = MetaCommitCapabilityClient(client)
        self.diagnostics = MetaDiagnosticsCapabilityClient(client)
        self.graph = MetaGraphCapabilityClient(client)
        self.package = MetaPackageCapabilityClient(client)
        self.persistence = MetaPersistenceCapabilityClient(client)
        self.runtime_read_model = MetaRuntimeReadModelCapabilityClient(client)


class AwareMetaServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.meta = MetaApiClient(client)


__all__ = [
    "AwareMetaServiceApiClient",
    "MetaApiClient",
    "MetaCommitCapabilityClient",
    "MetaDiagnosticsCapabilityClient",
    "MetaGraphCapabilityClient",
    "MetaPackageCapabilityClient",
    "MetaPersistenceCapabilityClient",
    "MetaRuntimeReadModelCapabilityClient",
    "MetaCommitSubscribeStreamEvent",
]
