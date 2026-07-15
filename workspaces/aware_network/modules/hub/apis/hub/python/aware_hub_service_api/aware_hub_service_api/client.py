# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    HUB__ARTIFACT__PUBLISH_ENDPOINT_REF,
    HUB__ARTIFACT__RESOLVE_ENDPOINT_REF,
    HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF,
    HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF,
    HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF,
    HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF,
    HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF,
    HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF,
    HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF,
    HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF,
)
from aware_code_service_dto.code.features.package_distribution import (
    DescribeCodePackageRequest,
    DescribeCodePackageResponse,
    DiscoverCodePackageChannelHeadsRequest,
    DiscoverCodePackageChannelHeadsResponse,
    DownloadCodePackageRequest,
    DownloadCodePackageResponse,
    PublishCodePackageRequest,
    PublishCodePackageResponse,
    ResolveCodePackageRequest,
    ResolveCodePackageResponse,
    SearchCodePackageRequest,
    SearchCodePackageResponse,
)
from aware_hub_service_dto.hub.artifact_authority import (
    PublishHubArtifactRequest,
    PublishHubArtifactResponse,
    ResolveHubArtifactRequest,
    ResolveHubArtifactResponse,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    ResolveDeploymentArtifactRequest,
    ResolveDeploymentArtifactResponse,
)
from aware_hub_service_dto.hub.public_map_discovery import DiscoverPublicMapRequest, DiscoverPublicMapResponse


class HubArtifactCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def publish(self, request: PublishHubArtifactRequest) -> PublishHubArtifactResponse:
        """Publish a generic immutable artifact payload lock through Hub authority truth."""
        return cast(
            PublishHubArtifactResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__ARTIFACT__PUBLISH_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve(self, request: ResolveHubArtifactRequest) -> ResolveHubArtifactResponse:
        """Resolve a generic immutable artifact payload lock through Hub authority truth."""
        return cast(
            ResolveHubArtifactResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__ARTIFACT__RESOLVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class HubCodePackageCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe(self, request: DescribeCodePackageRequest) -> DescribeCodePackageResponse:
        """Describe one CodePackage descriptor through Hub package authority truth."""
        return cast(
            DescribeCodePackageResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def discover_channel_heads(
        self, request: DiscoverCodePackageChannelHeadsRequest
    ) -> DiscoverCodePackageChannelHeadsResponse:
        """Discover public Hub CodePackage channel heads for pre-identity map surfaces."""
        return cast(
            DiscoverCodePackageChannelHeadsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def download(self, request: DownloadCodePackageRequest) -> DownloadCodePackageResponse:
        """Return one explicit CodePackage artifact download lock through Hub package authority truth."""
        return cast(
            DownloadCodePackageResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def publish(self, request: PublishCodePackageRequest) -> PublishCodePackageResponse:
        """Register one staged CodePackage artifact lock into Hub package authority truth."""
        return cast(
            PublishCodePackageResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve(self, request: ResolveCodePackageRequest) -> ResolveCodePackageResponse:
        """Resolve one exact CodePackage artifact lock through Hub package authority truth."""
        return cast(
            ResolveCodePackageResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def search(self, request: SearchCodePackageRequest) -> SearchCodePackageResponse:
        """Search CodePackage descriptors through Hub package authority truth."""
        return cast(
            SearchCodePackageResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class HubDeploymentArtifactCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve(self, request: ResolveDeploymentArtifactRequest) -> ResolveDeploymentArtifactResponse:
        """Resolve a deployment artifact payload lock through Hub authority truth."""
        return cast(
            ResolveDeploymentArtifactResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class HubPublicMapCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def discover(self, request: DiscoverPublicMapRequest) -> DiscoverPublicMapResponse:
        """Discover the public Hub package/revision map for pre-identity Control surfaces."""
        return cast(
            DiscoverPublicMapResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class HubApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.artifact = HubArtifactCapabilityClient(client)
        self.code_package = HubCodePackageCapabilityClient(client)
        self.deployment_artifact = HubDeploymentArtifactCapabilityClient(client)
        self.public_map = HubPublicMapCapabilityClient(client)


class AwareHubServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.hub = HubApiClient(client)


__all__ = [
    "AwareHubServiceApiClient",
    "HubApiClient",
    "HubArtifactCapabilityClient",
    "HubCodePackageCapabilityClient",
    "HubDeploymentArtifactCapabilityClient",
    "HubPublicMapCapabilityClient",
]
