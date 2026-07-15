# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF,
    CONTENT__TEXT__COMMIT_CONTENT_TEXT_ENDPOINT_REF,
    CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF,
)
from aware_content_service_dto.content.content_service_operation import (
    CommitContentTextRequest,
    CommitContentTextResponse,
    MaterializeContentPackageRequest,
    MaterializeContentPackageResponse,
    ResolveContentTextRequest,
    ResolveContentTextResponse,
)


class ContentPackageCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def materialize_content_package(
        self, request: MaterializeContentPackageRequest
    ) -> MaterializeContentPackageResponse:
        """Materialize a provider export document into Content-owned ContentPackage truth."""
        return cast(
            MaterializeContentPackageResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ContentTextCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def commit_content_text(self, request: CommitContentTextRequest) -> CommitContentTextResponse:
        """Commit provider-neutral text as Content truth and return exact commit evidence."""
        return cast(
            CommitContentTextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CONTENT__TEXT__COMMIT_CONTENT_TEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_content_text(self, request: ResolveContentTextRequest) -> ResolveContentTextResponse:
        """Resolve one Content object into deterministic text parts and a flattened text payload."""
        return cast(
            ResolveContentTextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ContentApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.package = ContentPackageCapabilityClient(client)
        self.text = ContentTextCapabilityClient(client)


class AwareContentServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.content = ContentApiClient(client)


__all__ = [
    "AwareContentServiceApiClient",
    "ContentApiClient",
    "ContentPackageCapabilityClient",
    "ContentTextCapabilityClient",
]
