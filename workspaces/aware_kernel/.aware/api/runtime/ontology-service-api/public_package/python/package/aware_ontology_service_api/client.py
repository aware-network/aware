# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import AsyncIterator, cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF,
    ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
    ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
    ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
    ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
    ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
    ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF,
    ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF,
)
from aware_ontology_service_dto.graph.config.package_compile import (
    OntologyObjectConfigGraphPackageEnsureRequest,
    OntologyObjectConfigGraphPackageEnsureResponse,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitEventEnvelope,
    OntologyCommitSubscriptionRequest,
    OntologyCommitSubscriptionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetLaneHeadRequest,
    OntologyGraphGetLaneHeadResponse,
    OntologyGraphGetObjectInstanceGraphCommitRequest,
    OntologyGraphGetObjectInstanceGraphCommitResponse,
    OntologyGraphInvokeFunctionRequest,
    OntologyGraphInvokeFunctionResponse,
    OntologyGraphResolveProjectionRequest,
    OntologyGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.persistence.readiness import (
    OntologyPersistenceEnsureReadyRequest,
    OntologyPersistenceEnsureReadyResponse,
)
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyRuntimeArtifactSetResolveRequest,
    OntologyRuntimeArtifactSetResolveResponse,
)

OntologyCommitSubscribeStreamEvent = OntologyCommitEventEnvelope


class OntologyCommitCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def subscribe(self, request: OntologyCommitSubscriptionRequest) -> OntologyCommitSubscriptionResponse:
        """Subscribe to remote-safe Ontology commit fan-out events."""
        return cast(
            OntologyCommitSubscriptionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_subscribe(
        self, request: OntologyCommitSubscriptionRequest
    ) -> AsyncIterator[OntologyCommitSubscribeStreamEvent]:
        """Subscribe to remote-safe Ontology commit fan-out events."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(OntologyCommitSubscribeStreamEvent, event)


class OntologyGraphCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_lane_head(self, request: OntologyGraphGetLaneHeadRequest) -> OntologyGraphGetLaneHeadResponse:
        """Read the current committed ontology graph lane head through Ontology service authority."""
        return cast(
            OntologyGraphGetLaneHeadResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def get_object_instance_graph_commit(
        self, request: OntologyGraphGetObjectInstanceGraphCommitRequest
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse:
        """Read one committed ObjectInstanceGraphCommit through Ontology service authority."""
        return cast(
            OntologyGraphGetObjectInstanceGraphCommitResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def invoke_function(self, request: OntologyGraphInvokeFunctionRequest) -> OntologyGraphInvokeFunctionResponse:
        """Invoke one ontology graph function through Ontology-owned GraphOS authority."""
        return cast(
            OntologyGraphInvokeFunctionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_projection(
        self, request: OntologyGraphResolveProjectionRequest
    ) -> OntologyGraphResolveProjectionResponse:
        """Resolve ontology runtime projection coordinates without mutating graph state."""
        return cast(
            OntologyGraphResolveProjectionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class OntologyPackageCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_object_config_graph_package(
        self, request: OntologyObjectConfigGraphPackageEnsureRequest
    ) -> OntologyObjectConfigGraphPackageEnsureResponse:
        """Ensure one Ontology-owned ObjectConfigGraphPackage through the Ontology service boundary."""
        return cast(
            OntologyObjectConfigGraphPackageEnsureResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class OntologyPersistenceCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_ready(
        self, request: OntologyPersistenceEnsureReadyRequest
    ) -> OntologyPersistenceEnsureReadyResponse:
        """Ensure Ontology GraphOS persistence is ready without making Environment own ontology DB setup."""
        return cast(
            OntologyPersistenceEnsureReadyResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class OntologyRuntimeCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_runtime_artifact_set(
        self, request: OntologyRuntimeArtifactSetResolveRequest
    ) -> OntologyRuntimeArtifactSetResolveResponse:
        """Resolve an Ontology-owned runtime artifact-set descriptor for explicit materialization or revision coordinates."""
        return cast(
            OntologyRuntimeArtifactSetResolveResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class OntologyApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.commit = OntologyCommitCapabilityClient(client)
        self.graph = OntologyGraphCapabilityClient(client)
        self.package = OntologyPackageCapabilityClient(client)
        self.persistence = OntologyPersistenceCapabilityClient(client)
        self.runtime = OntologyRuntimeCapabilityClient(client)


class AwareOntologyServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.ontology = OntologyApiClient(client)


__all__ = [
    "AwareOntologyServiceApiClient",
    "OntologyApiClient",
    "OntologyCommitCapabilityClient",
    "OntologyGraphCapabilityClient",
    "OntologyPackageCapabilityClient",
    "OntologyPersistenceCapabilityClient",
    "OntologyRuntimeCapabilityClient",
    "OntologyCommitSubscribeStreamEvent",
]
