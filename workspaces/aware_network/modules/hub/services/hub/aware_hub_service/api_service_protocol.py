from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from .code_package_authority import (
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
    describe_code_package,
    discover_code_package_channel_heads,
    download_code_package,
    publish_code_package,
    resolve_code_package,
    search_code_package,
)
from .deployment_artifact_authority import (
    ResolveDeploymentArtifactRequest,
    ResolveDeploymentArtifactResponse,
    resolve_deployment_artifact,
)
from .artifact_authority import (
    PublishHubArtifactRequest,
    PublishHubArtifactResponse,
    ResolveHubArtifactRequest,
    ResolveHubArtifactResponse,
    publish_hub_artifact,
    resolve_hub_artifact,
)
from .public_map_authority import (
    DiscoverPublicMapRequest,
    DiscoverPublicMapResponse,
    discover_public_map,
)

_RequestT = TypeVar("_RequestT", bound=BaseModel)


def build_aware_hub_service_protocol_handler() -> object:
    return _AwareHubServiceProtocolHandler()


class _HubCodePackageCapabilityHandler:
    async def discover_channel_heads(
        self,
        request: object,
    ) -> DiscoverCodePackageChannelHeadsResponse:
        typed_request = _coerce_request(request, DiscoverCodePackageChannelHeadsRequest)
        return discover_code_package_channel_heads(typed_request)

    async def search(
        self,
        request: object,
    ) -> SearchCodePackageResponse:
        typed_request = _coerce_request(request, SearchCodePackageRequest)
        return search_code_package(typed_request)

    async def describe(
        self,
        request: object,
    ) -> DescribeCodePackageResponse:
        typed_request = _coerce_request(request, DescribeCodePackageRequest)
        return describe_code_package(typed_request)

    async def resolve(
        self,
        request: object,
    ) -> ResolveCodePackageResponse:
        typed_request = _coerce_request(request, ResolveCodePackageRequest)
        return resolve_code_package(typed_request)

    async def download(
        self,
        request: object,
    ) -> DownloadCodePackageResponse:
        typed_request = _coerce_request(request, DownloadCodePackageRequest)
        return download_code_package(typed_request)

    async def publish(
        self,
        request: object,
    ) -> PublishCodePackageResponse:
        typed_request = _coerce_request(request, PublishCodePackageRequest)
        return publish_code_package(typed_request)


class _HubDeploymentArtifactCapabilityHandler:
    async def resolve(
        self,
        request: object,
    ) -> ResolveDeploymentArtifactResponse:
        typed_request = _coerce_request(request, ResolveDeploymentArtifactRequest)
        return resolve_deployment_artifact(typed_request)


class _HubArtifactCapabilityHandler:
    async def publish(
        self,
        request: object,
    ) -> PublishHubArtifactResponse:
        typed_request = _coerce_request(request, PublishHubArtifactRequest)
        return publish_hub_artifact(typed_request)

    async def resolve(
        self,
        request: object,
    ) -> ResolveHubArtifactResponse:
        typed_request = _coerce_request(request, ResolveHubArtifactRequest)
        return resolve_hub_artifact(typed_request)


class _HubPublicMapCapabilityHandler:
    async def discover(
        self,
        request: object,
    ) -> DiscoverPublicMapResponse:
        typed_request = _coerce_request(request, DiscoverPublicMapRequest)
        return discover_public_map(typed_request)


class _HubApiServiceProtocolHandler:
    def __init__(self) -> None:
        self.artifact = _HubArtifactCapabilityHandler()
        self.code_package = _HubCodePackageCapabilityHandler()
        self.deployment_artifact = _HubDeploymentArtifactCapabilityHandler()
        self.public_map = _HubPublicMapCapabilityHandler()


class _AwareHubServiceProtocolHandler:
    def __init__(self) -> None:
        self.hub = _HubApiServiceProtocolHandler()


def _coerce_request(request: object, model_cls: type[_RequestT]) -> _RequestT:
    if isinstance(request, model_cls):
        return request
    if isinstance(request, BaseModel):
        payload = request.model_dump(mode="json")
    else:
        payload = request
    return model_cls.model_validate(payload)


__all__ = [
    "build_aware_hub_service_protocol_handler",
]
