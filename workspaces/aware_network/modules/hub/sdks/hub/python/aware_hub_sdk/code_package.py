from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Protocol
from uuid import UUID

from aware_code_service_dto.code.features.package_distribution import CodeLanguage
from aware_code_service_dto.code.features.package_distribution import (
    CodePackageArtifactLock,
)
from aware_code_service_dto.code.features.package_distribution import (
    CodePackageDescriptor,
)
from aware_code_service_dto.code.features.package_distribution import CodePackageRef
from aware_code_service_dto.code.features.package_distribution import (
    DescribeCodePackageRequest,
)
from aware_code_service_dto.code.features.package_distribution import (
    DescribeCodePackageResponse,
)
from aware_code_service_dto.code.features.package_distribution import (
    DiscoverCodePackageChannelHeadsRequest,
)
from aware_code_service_dto.code.features.package_distribution import (
    DiscoverCodePackageChannelHeadsResponse,
)
from aware_code_service_dto.code.features.package_distribution import (
    DownloadCodePackageRequest,
)
from aware_code_service_dto.code.features.package_distribution import (
    DownloadCodePackageResponse,
)
from aware_code_service_dto.code.features.package_distribution import (
    PublishCodePackageRequest,
)
from aware_code_service_dto.code.features.package_distribution import (
    PublishCodePackageResponse,
)
from aware_code_service_dto.code.features.package_distribution import (
    ResolveCodePackageRequest,
)
from aware_code_service_dto.code.features.package_distribution import (
    ResolveCodePackageResponse,
)
from aware_code_service_dto.code.features.package_distribution import (
    SearchCodePackageRequest,
)
from aware_code_service_dto.code.features.package_distribution import (
    SearchCodePackageResponse,
)

from aware_hub_sdk.models import (
    HubCodePackageArtifactLock,
    HubCodePackageChannelHead,
    HubCodePackageDescribeReceipt,
    HubCodePackageDescriptor,
    HubCodePackageDiscoveryEntry,
    HubCodePackageDiscoveryReceipt,
    HubCodePackageDownloadReceipt,
    HubCodePackagePublicationEntry,
    HubCodePackagePublishReceipt,
    HubCodePackageResolveReceipt,
    HubCodePackageSearchReceipt,
    HubCodePackageSelector,
)

HubCodeLanguage = CodeLanguage | str
HubCodePackageSurface = str


class _HubCodePackageApiClient(Protocol):
    async def discover_channel_heads(
        self,
        request: DiscoverCodePackageChannelHeadsRequest,
    ) -> DiscoverCodePackageChannelHeadsResponse: ...

    async def describe(
        self,
        request: DescribeCodePackageRequest,
    ) -> DescribeCodePackageResponse: ...

    async def download(
        self,
        request: DownloadCodePackageRequest,
    ) -> DownloadCodePackageResponse: ...

    async def publish(
        self,
        request: PublishCodePackageRequest,
    ) -> PublishCodePackageResponse: ...

    async def resolve(
        self,
        request: ResolveCodePackageRequest,
    ) -> ResolveCodePackageResponse: ...

    async def search(
        self,
        request: SearchCodePackageRequest,
    ) -> SearchCodePackageResponse: ...


class _HubApiNamespaceClient(Protocol):
    @property
    def code_package(self) -> _HubCodePackageApiClient: ...


class HubGeneratedApiClient(Protocol):
    @property
    def hub(self) -> _HubApiNamespaceClient: ...


class HubSdkError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class HubCodePackageClient:
    api_client: HubGeneratedApiClient
    authority_base_url: str | None = None
    index_url: str | None = None

    async def discover_channel_heads(
        self,
        *,
        query: str | None = None,
        package_name: str | None = None,
        language: HubCodeLanguage | None = None,
        surface: HubCodePackageSurface | None = None,
        channel: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        limit: int = 50,
        request_id: UUID | None = None,
    ) -> HubCodePackageDiscoveryReceipt:
        response = await self.api_client.hub.code_package.discover_channel_heads(
            DiscoverCodePackageChannelHeadsRequest(
                request_id=request_id,
                query=query,
                package_name=package_name,
                language=_api_language(language),
                surface=_api_surface(surface),
                channel=channel,
                authority_base_url=self._authority_base_url(authority_base_url),
                index_url=self._index_url(index_url),
                limit=limit,
            )
        )
        _raise_if_failed(response, operation="discover_channel_heads")
        return HubCodePackageDiscoveryReceipt(
            entries=tuple(_sdk_discovery_entry(entry) for entry in response.entries),
            authority_source_url=response.authority_source_url,
            request_id=response.request_id,
            info=response.info,
        )

    async def search(
        self,
        *,
        query: str | None = None,
        package_name: str | None = None,
        language: HubCodeLanguage | None = None,
        surface: HubCodePackageSurface | None = None,
        channel: str = "stable",
        authority_base_url: str | None = None,
        index_url: str | None = None,
        limit: int = 50,
        request_id: UUID | None = None,
    ) -> HubCodePackageSearchReceipt:
        response = await self.api_client.hub.code_package.search(
            SearchCodePackageRequest(
                request_id=request_id,
                query=query,
                package_name=package_name,
                language=_api_language(language),
                surface=_api_surface(surface),
                channel=channel,
                authority_base_url=self._authority_base_url(authority_base_url),
                index_url=self._index_url(index_url),
                limit=limit,
            )
        )
        _raise_if_failed(response, operation="search")
        return HubCodePackageSearchReceipt(
            descriptors=tuple(
                _sdk_descriptor(descriptor) for descriptor in response.descriptors
            ),
            authority_source_url=response.authority_source_url,
            request_id=response.request_id,
            info=response.info,
        )

    async def describe(
        self,
        selector: HubCodePackageSelector | str,
        *,
        language: HubCodeLanguage | None = None,
        surface: HubCodePackageSurface | None = None,
        channel: str | None = None,
        version: str | None = None,
        revision_id: str | None = None,
        digest: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        request_id: UUID | None = None,
    ) -> HubCodePackageDescribeReceipt:
        request = DescribeCodePackageRequest(
            request_id=request_id,
            selector=_api_selector(
                _sdk_selector(
                    selector,
                    language=language,
                    surface=surface,
                    channel=channel,
                    version=version,
                    revision_id=revision_id,
                    digest=digest,
                )
            ),
            authority_base_url=self._authority_base_url(authority_base_url),
            index_url=self._index_url(index_url),
        )
        response = await self.api_client.hub.code_package.describe(request)
        _raise_if_failed(response, operation="describe")
        descriptor = response.descriptor
        if descriptor is None:
            raise HubSdkError("Hub SDK describe returned no descriptor.")
        return HubCodePackageDescribeReceipt(
            descriptor=_sdk_descriptor(descriptor),
            authority_source_url=response.authority_source_url,
            request_id=response.request_id,
            info=response.info,
        )

    async def resolve(
        self,
        selector: HubCodePackageSelector | str,
        *,
        language: HubCodeLanguage | None = None,
        surface: HubCodePackageSurface | None = None,
        channel: str | None = None,
        version: str | None = None,
        revision_id: str | None = None,
        digest: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        request_id: UUID | None = None,
    ) -> HubCodePackageResolveReceipt:
        request = ResolveCodePackageRequest(
            request_id=request_id,
            selector=_api_selector(
                _sdk_selector(
                    selector,
                    language=language,
                    surface=surface,
                    channel=channel,
                    version=version,
                    revision_id=revision_id,
                    digest=digest,
                )
            ),
            authority_base_url=self._authority_base_url(authority_base_url),
            index_url=self._index_url(index_url),
        )
        response = await self.api_client.hub.code_package.resolve(request)
        _raise_if_failed(response, operation="resolve")
        return HubCodePackageResolveReceipt(
            selector=_sdk_selector_from_api(response.selector),
            descriptor=_sdk_descriptor(response.descriptor),
            artifact_lock=_sdk_artifact_lock(response.artifact_lock),
            authority_source_url=response.authority_source_url,
            request_id=response.request_id,
            info=response.info,
        )

    async def download(
        self,
        selector: HubCodePackageSelector | str,
        *,
        language: HubCodeLanguage | None = None,
        surface: HubCodePackageSurface | None = None,
        channel: str | None = None,
        version: str | None = None,
        revision_id: str | None = None,
        digest: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        request_id: UUID | None = None,
    ) -> HubCodePackageDownloadReceipt:
        request = DownloadCodePackageRequest(
            request_id=request_id,
            selector=_api_selector(
                _sdk_selector(
                    selector,
                    language=language,
                    surface=surface,
                    channel=channel,
                    version=version,
                    revision_id=revision_id,
                    digest=digest,
                )
            ),
            authority_base_url=self._authority_base_url(authority_base_url),
            index_url=self._index_url(index_url),
        )
        response = await self.api_client.hub.code_package.download(request)
        _raise_if_failed(response, operation="download")
        return HubCodePackageDownloadReceipt(
            selector=_sdk_selector_from_api(response.selector),
            artifact_lock=_sdk_artifact_lock(response.artifact_lock),
            authority_source_url=response.authority_source_url,
            request_id=response.request_id,
            info=response.info,
        )

    async def publish(
        self,
        entry: HubCodePackagePublicationEntry,
        *,
        channel: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        publisher_execution_id: str | None = None,
        idempotency_key: str | None = None,
        request_id: UUID | None = None,
    ) -> HubCodePackagePublishReceipt:
        response = await self.api_client.hub.code_package.publish(
            PublishCodePackageRequest(
                request_id=request_id,
                descriptor=_api_descriptor_from_sdk(entry.descriptor),
                artifact_lock=_api_artifact_lock_from_sdk(entry.artifact_lock),
                channel=channel or entry.channel,
                authority_base_url=self._authority_base_url(authority_base_url),
                index_url=self._index_url(index_url),
                publisher_execution_id=publisher_execution_id,
                idempotency_key=idempotency_key,
            )
        )
        _raise_if_failed(response, operation="publish")
        if response.selector is None:
            raise HubSdkError("Hub SDK publish returned no selector.")
        if response.descriptor is None:
            raise HubSdkError("Hub SDK publish returned no descriptor.")
        if response.artifact_lock is None:
            raise HubSdkError("Hub SDK publish returned no artifact_lock.")
        return HubCodePackagePublishReceipt(
            selector=_sdk_selector_from_api(response.selector),
            descriptor=_sdk_descriptor(response.descriptor),
            artifact_lock=_sdk_artifact_lock(response.artifact_lock),
            authority_source_url=response.authority_source_url,
            accepted=response.accepted,
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


def _sdk_selector(
    selector: HubCodePackageSelector | str,
    *,
    language: HubCodeLanguage | None = None,
    surface: HubCodePackageSurface | None = None,
    channel: str | None = None,
    version: str | None = None,
    revision_id: str | None = None,
    digest: str | None = None,
) -> HubCodePackageSelector:
    base = (
        HubCodePackageSelector(package_name=selector)
        if isinstance(selector, str)
        else selector
    )
    updates: dict[str, str | None] = {}
    if language is not None:
        updates["language"] = _enum_value(language)
    if surface is not None:
        updates["surface"] = _enum_value(surface)
    if channel is not None:
        updates["channel"] = channel
    if version is not None:
        updates["version"] = version
    if revision_id is not None:
        updates["revision_id"] = revision_id
    if digest is not None:
        updates["digest"] = digest
    if not updates:
        return base
    return replace(base, **updates)


def _api_selector(selector: HubCodePackageSelector) -> CodePackageRef:
    return CodePackageRef(
        package_name=selector.package_name,
        language=_api_language(selector.language),
        surface=_api_surface(selector.surface),
        channel=selector.channel,
        version=selector.version,
        revision_id=selector.revision_id,
        digest=selector.digest,
    )


def _sdk_selector_from_api(selector: CodePackageRef) -> HubCodePackageSelector:
    return HubCodePackageSelector(
        package_name=selector.package_name,
        language=_enum_value(selector.language),
        surface=_enum_value(selector.surface),
        channel=selector.channel,
        version=selector.version,
        revision_id=selector.revision_id,
        digest=selector.digest,
    )


def _sdk_descriptor(descriptor: CodePackageDescriptor) -> HubCodePackageDescriptor:
    return HubCodePackageDescriptor(
        package_name=descriptor.package_name,
        language=_required_enum_value(descriptor.language),
        surface=_required_enum_value(descriptor.surface),
        manifest_kind=_required_enum_value(descriptor.manifest_kind),
        manifest_relative_path=descriptor.manifest_relative_path,
        package_root=descriptor.package_root,
        sources_root=descriptor.sources_root,
        fqn_prefix=descriptor.fqn_prefix,
        version=descriptor.version,
        revision_id=descriptor.revision_id,
        digest=descriptor.digest,
        artifact_media_type=descriptor.artifact_media_type,
        artifact_size_bytes=descriptor.artifact_size_bytes,
        download_handle=descriptor.download_handle,
        metadata=dict(descriptor.metadata),
    )


def _sdk_artifact_lock(lock: CodePackageArtifactLock) -> HubCodePackageArtifactLock:
    return HubCodePackageArtifactLock(
        artifact_url=lock.artifact_url,
        sha256=lock.sha256,
        size_bytes=lock.size_bytes,
        media_type=lock.media_type,
        archive_format=lock.archive_format,
        revision_id=lock.revision_id,
        published_at=lock.published_at,
    )


def _sdk_channel_head(head: object) -> HubCodePackageChannelHead:
    return HubCodePackageChannelHead(
        package_name=str(getattr(head, "package_name")),
        language=_enum_value(getattr(head, "language", None)),
        surface=_enum_value(getattr(head, "surface", None)),
        channel=str(getattr(head, "channel", "stable")),
        revision_id=str(getattr(head, "revision_id")),
        updated_at=getattr(head, "updated_at", None),
        publisher_execution_id=getattr(head, "publisher_execution_id", None),
        idempotency_key=getattr(head, "idempotency_key", None),
        metadata=dict(getattr(head, "metadata", {}) or {}),
    )


def _sdk_discovery_entry(entry: object) -> HubCodePackageDiscoveryEntry:
    descriptor = getattr(entry, "descriptor", None)
    artifact_lock = getattr(entry, "artifact_lock", None)
    return HubCodePackageDiscoveryEntry(
        channel_head=_sdk_channel_head(getattr(entry, "channel_head")),
        descriptor=_sdk_descriptor(descriptor) if descriptor is not None else None,
        artifact_lock=(
            _sdk_artifact_lock(artifact_lock) if artifact_lock is not None else None
        ),
    )


def _api_descriptor_from_sdk(
    descriptor: HubCodePackageDescriptor,
) -> CodePackageDescriptor:
    return CodePackageDescriptor.model_validate(
        {
            "package_name": descriptor.package_name,
            "language": _api_language(descriptor.language),
            "surface": _api_surface(descriptor.surface),
            "manifest_kind": _api_manifest_kind(descriptor.manifest_kind),
            "manifest_relative_path": descriptor.manifest_relative_path,
            "package_root": descriptor.package_root,
            "sources_root": descriptor.sources_root,
            "fqn_prefix": descriptor.fqn_prefix,
            "version": descriptor.version,
            "revision_id": descriptor.revision_id,
            "digest": descriptor.digest,
            "artifact_media_type": descriptor.artifact_media_type,
            "artifact_size_bytes": descriptor.artifact_size_bytes,
            "download_handle": descriptor.download_handle,
            "metadata": dict(descriptor.metadata),
        }
    )


def _api_artifact_lock_from_sdk(
    artifact_lock: HubCodePackageArtifactLock,
) -> CodePackageArtifactLock:
    return CodePackageArtifactLock(
        artifact_url=artifact_lock.artifact_url,
        sha256=artifact_lock.sha256,
        size_bytes=artifact_lock.size_bytes,
        media_type=artifact_lock.media_type,
        archive_format=artifact_lock.archive_format,
        revision_id=artifact_lock.revision_id,
        published_at=artifact_lock.published_at,
    )


def _api_language(value: HubCodeLanguage | None) -> CodeLanguage | None:
    if value is None or isinstance(value, CodeLanguage):
        return value
    return CodeLanguage(value)


def _api_surface(value: HubCodePackageSurface | None) -> str | None:
    return _enum_value(value)


def _api_manifest_kind(value: str) -> str:
    return _enum_value(value) or ""


def _enum_value(value: Enum | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    return value


def _required_enum_value(
    value: CodeLanguage | str,
) -> str:
    return _enum_value(value) or ""


def _raise_if_failed(response: object, *, operation: str) -> None:
    success = getattr(response, "success", True)
    if success:
        return
    error = getattr(response, "error", None)
    info = getattr(response, "info", None)
    detail = error or info or "unknown error"
    raise HubSdkError(f"Hub SDK {operation} failed: {detail}")


__all__ = [
    "HubCodeLanguage",
    "HubCodePackageClient",
    "HubCodePackageSurface",
    "HubGeneratedApiClient",
    "HubSdkError",
]
