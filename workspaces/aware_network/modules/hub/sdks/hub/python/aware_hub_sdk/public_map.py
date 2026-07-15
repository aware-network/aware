from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_hub_service_dto.hub.public_map_discovery import (
    DiscoverPublicMapRequest,
)
from aware_hub_service_dto.hub.public_map_discovery import (
    DiscoverPublicMapResponse,
)

from aware_hub_sdk.code_package import HubSdkError
from aware_hub_sdk.models import (
    HubPublicMapDiscoveryReceipt,
    HubPublicMapEntry,
)


class _HubPublicMapApiClient(Protocol):
    async def discover(
        self,
        request: DiscoverPublicMapRequest,
    ) -> DiscoverPublicMapResponse: ...


class _HubApiNamespaceClient(Protocol):
    @property
    def public_map(self) -> _HubPublicMapApiClient: ...


class HubGeneratedPublicMapApiClient(Protocol):
    @property
    def hub(self) -> _HubApiNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class HubPublicMapClient:
    api_client: HubGeneratedPublicMapApiClient
    authority_base_url: str | None = None
    index_url: str | None = None

    async def discover(
        self,
        *,
        query: str | None = None,
        artifact_family: str | None = None,
        artifact_key: str | None = None,
        package_name: str | None = None,
        experience_name: str | None = None,
        channel: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        limit: int = 50,
        request_id: UUID | None = None,
    ) -> HubPublicMapDiscoveryReceipt:
        response = await self.api_client.hub.public_map.discover(
            DiscoverPublicMapRequest(
                request_id=request_id,
                query=query,
                artifact_family=artifact_family,
                artifact_key=artifact_key,
                package_name=package_name,
                experience_name=experience_name,
                channel=channel,
                authority_base_url=self._authority_base_url(authority_base_url),
                index_url=self._index_url(index_url),
                limit=limit,
            )
        )
        _raise_if_failed(response)
        return HubPublicMapDiscoveryReceipt(
            entries=tuple(_sdk_public_map_entry(entry) for entry in response.entries),
            authority_source_url=response.authority_source_url,
            request_id=response.request_id,
            info=response.info,
        )

    def _authority_base_url(self, override: str | None) -> str | None:
        if override is not None:
            return override
        return self.authority_base_url

    def _index_url(self, override: str | None) -> str | None:
        if override is not None:
            return override
        return self.index_url


def _sdk_public_map_entry(entry: object) -> HubPublicMapEntry:
    return HubPublicMapEntry(
        artifact_family=str(getattr(entry, "artifact_family")),
        artifact_key=str(getattr(entry, "artifact_key")),
        channel=str(getattr(entry, "channel", "stable")),
        revision_id=getattr(entry, "revision_id", None),
        package_name=getattr(entry, "package_name", None),
        language=getattr(entry, "language", None),
        surface=getattr(entry, "surface", None),
        manifest_kind=getattr(entry, "manifest_kind", None),
        digest=getattr(entry, "digest", None),
        artifact_url=getattr(entry, "artifact_url", None),
        artifact_sha256=getattr(entry, "artifact_sha256", None),
        artifact_size_bytes=getattr(entry, "artifact_size_bytes", None),
        media_type=getattr(entry, "media_type", None),
        title=getattr(entry, "title", None),
        summary=getattr(entry, "summary", None),
        experience_name=getattr(entry, "experience_name", None),
        fqn_prefix=getattr(entry, "fqn_prefix", None),
        producer_kind=getattr(entry, "producer_kind", None),
        producer_revision_id=getattr(entry, "producer_revision_id", None),
        source_revision_id=getattr(entry, "source_revision_id", None),
        visibility=str(getattr(entry, "visibility", "public")),
        metadata=dict(getattr(entry, "metadata", {}) or {}),
    )


def _raise_if_failed(response: object) -> None:
    success = getattr(response, "success", True)
    if success:
        return
    error = getattr(response, "error", None)
    info = getattr(response, "info", None)
    detail = error or info or "unknown error"
    raise HubSdkError(f"Hub SDK public_map.discover failed: {detail}")


__all__ = [
    "HubGeneratedPublicMapApiClient",
    "HubPublicMapClient",
]
