from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from aware_types import JsonObject

from aware_hub_sdk import (
    AwareHubSdk,
    HubCodePackageArtifactLock,
    HubCodePackageClient,
    HubCodePackageChannelHead,
    HubCodePackageDescriptor,
    HubCodePackageDiscoveryEntry,
    HubCodePackageDiscoveryReceipt,
    HubCodePackageDownloadReceipt,
    HubCodePackagePublicationEntry,
    HubCodePackagePublishReceipt,
    HubCodePackageResolveReceipt,
    HubCodePackageSelector,
    HubSdkError,
)
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
from aware_code_service_dto.code.features.package_distribution import CodePackageChannelHead
from aware_code_service_dto.code.features.package_distribution import (
    CodePackageDiscoveryEntry,
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


class _RecordingCodePackageApiClient:
    def __init__(self) -> None:
        self.discover_channel_heads_requests: list[
            DiscoverCodePackageChannelHeadsRequest
        ] = []
        self.search_requests: list[SearchCodePackageRequest] = []
        self.describe_requests: list[DescribeCodePackageRequest] = []
        self.resolve_requests: list[ResolveCodePackageRequest] = []
        self.download_requests: list[DownloadCodePackageRequest] = []
        self.publish_requests: list[PublishCodePackageRequest] = []
        self.fail_next_search = False

    async def discover_channel_heads(
        self,
        request: DiscoverCodePackageChannelHeadsRequest,
    ) -> DiscoverCodePackageChannelHeadsResponse:
        self.discover_channel_heads_requests.append(request)
        return DiscoverCodePackageChannelHeadsResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/index.json",
            entries=[
                CodePackageDiscoveryEntry(
                    channel_head=CodePackageChannelHead(
                        package_name="aware-workspace-api",
                        language=CodeLanguage.python,
                        surface="api",
                        channel=request.channel or "stable",
                        revision_id="rev-123",
                        updated_at="2026-05-08T00:00:00Z",
                        publisher_execution_id="codex-test",
                        metadata=JsonObject({"kind": "kernel-map"}),
                    ),
                    descriptor=_api_descriptor(),
                    artifact_lock=_api_artifact_lock(),
                )
            ],
        )

    async def search(
        self,
        request: SearchCodePackageRequest,
    ) -> SearchCodePackageResponse:
        self.search_requests.append(request)
        if self.fail_next_search:
            return SearchCodePackageResponse(
                request_id=request.request_id,
                success=False,
                error="authority offline",
            )
        return SearchCodePackageResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/index.json",
            descriptors=[_api_descriptor()],
        )

    async def describe(
        self,
        request: DescribeCodePackageRequest,
    ) -> DescribeCodePackageResponse:
        self.describe_requests.append(request)
        return DescribeCodePackageResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/index.json",
            descriptor=_api_descriptor(),
        )

    async def resolve(
        self,
        request: ResolveCodePackageRequest,
    ) -> ResolveCodePackageResponse:
        self.resolve_requests.append(request)
        return ResolveCodePackageResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/index.json",
            selector=request.selector,
            descriptor=_api_descriptor(),
            artifact_lock=_api_artifact_lock(),
        )

    async def download(
        self,
        request: DownloadCodePackageRequest,
    ) -> DownloadCodePackageResponse:
        self.download_requests.append(request)
        return DownloadCodePackageResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/index.json",
            selector=request.selector,
            artifact_lock=_api_artifact_lock(),
        )

    async def publish(
        self,
        request: PublishCodePackageRequest,
    ) -> PublishCodePackageResponse:
        self.publish_requests.append(request)
        return PublishCodePackageResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/index.json",
            selector=CodePackageRef(
                package_name=request.descriptor.package_name,
                language=request.descriptor.language,
                surface=request.descriptor.surface,
                channel=request.channel,
                version=request.descriptor.version,
                revision_id=request.descriptor.revision_id,
                digest=request.descriptor.digest,
            ),
            descriptor=request.descriptor,
            artifact_lock=request.artifact_lock,
            accepted=True,
        )


class _RecordingHubApiClient:
    def __init__(self) -> None:
        self.code_package = _RecordingCodePackageApiClient()


class _RecordingGeneratedHubApiClient:
    def __init__(self) -> None:
        self.hub = _RecordingHubApiClient()


@pytest.mark.asyncio
async def test_discover_channel_heads_builds_public_map_request() -> None:
    generated = _RecordingGeneratedHubApiClient()
    client = HubCodePackageClient(
        api_client=generated,
        authority_base_url="https://hub.example.test",
    )
    request_id = uuid4()

    receipt = await client.discover_channel_heads(
        query="kernel",
        channel="stable",
        surface="api",
        limit=12,
        request_id=request_id,
    )

    request = generated.hub.code_package.discover_channel_heads_requests[0]
    assert request.request_id == request_id
    assert request.query == "kernel"
    assert request.channel == "stable"
    assert request.surface == "api"
    assert request.authority_base_url == "https://hub.example.test"
    assert request.limit == 12
    assert isinstance(receipt, HubCodePackageDiscoveryReceipt)
    assert receipt.entries == (
        HubCodePackageDiscoveryEntry(
            channel_head=HubCodePackageChannelHead(
                package_name="aware-workspace-api",
                language="python",
                surface="api",
                channel="stable",
                revision_id="rev-123",
                updated_at="2026-05-08T00:00:00Z",
                publisher_execution_id="codex-test",
                metadata={"kind": "kernel-map"},
            ),
            descriptor=_sdk_descriptor(),
            artifact_lock=_sdk_artifact_lock(),
        ),
    )


@pytest.mark.asyncio
async def test_search_builds_generated_api_request_and_normalizes_descriptors() -> None:
    generated = _RecordingGeneratedHubApiClient()
    client = HubCodePackageClient(
        api_client=generated,
        authority_base_url="https://hub.example.test",
    )
    request_id = uuid4()

    receipt = await client.search(
        query="workspace",
        package_name="aware-workspace-api",
        language="python",
        surface="api",
        request_id=request_id,
        limit=10,
    )

    request = generated.hub.code_package.search_requests[0]
    assert request.request_id == request_id
    assert request.query == "workspace"
    assert request.package_name == "aware-workspace-api"
    assert request.language is CodeLanguage.python
    assert request.surface == "api"
    assert request.authority_base_url == "https://hub.example.test"
    assert request.limit == 10
    assert receipt.request_id == request_id
    assert receipt.authority_source_url == "https://hub.example.test/index.json"
    assert receipt.descriptors == (
        HubCodePackageDescriptor(
            package_name="aware-workspace-api",
            language="python",
            surface="api",
            manifest_kind="aware_api_toml",
            manifest_relative_path="aware.api.toml",
            package_root="workspaces/aware_workspace/apis/workspace",
            sources_root="python",
            fqn_prefix="aware_workspace_service_api",
            version="0.1.0",
            revision_id="rev-123",
            digest="sha256:descriptor",
            artifact_media_type="application/vnd.aware.code-package+zip",
            artifact_size_bytes=512,
            download_handle="workspace-api-python",
            metadata={"owner": "sdk-test"},
        ),
    )


@pytest.mark.asyncio
async def test_describe_resolve_and_download_use_generated_api_client() -> None:
    generated = _RecordingGeneratedHubApiClient()
    sdk = AwareHubSdk(
        generated,
        index_url="https://hub.example.test/index.json",
    )
    selector = HubCodePackageSelector(
        package_name="aware-workspace-api",
        language="python",
        surface="api",
        channel="stable",
    )

    describe = await sdk.code_package.describe(selector)
    resolve = await sdk.code_package.resolve(selector, revision_id="rev-123")
    download = await sdk.code_package.download("aware-workspace-api", surface="api")

    assert describe.descriptor.package_name == "aware-workspace-api"
    assert isinstance(resolve, HubCodePackageResolveReceipt)
    assert resolve.selector.revision_id == "rev-123"
    assert resolve.artifact_lock.sha256 == "abc123"
    assert isinstance(download, HubCodePackageDownloadReceipt)
    assert download.artifact_lock.artifact_url == (
        "https://hub.example.test/artifacts/workspace-api-python.zip"
    )
    assert not hasattr(download, "local_path")
    assert generated.hub.code_package.describe_requests[0].index_url == (
        "https://hub.example.test/index.json"
    )
    assert generated.hub.code_package.resolve_requests[0].selector.revision_id == (
        "rev-123"
    )
    assert generated.hub.code_package.download_requests[0].selector.package_name == (
        "aware-workspace-api"
    )


@pytest.mark.asyncio
async def test_publish_uses_generated_api_client_and_returns_receipt() -> None:
    generated = _RecordingGeneratedHubApiClient()
    client = HubCodePackageClient(
        api_client=generated,
        index_url="https://hub.example.test/index.json",
    )
    request_id = uuid4()

    receipt = await client.publish(
        HubCodePackagePublicationEntry(
            descriptor=HubCodePackageDescriptor(
                package_name="aware-workspace-sdk",
                language="python",
                surface="sdk",
                manifest_kind="pyproject_toml",
                manifest_relative_path="pyproject.toml",
                package_root="workspaces/aware_workspace/sdks/workspace/python/public",
                fqn_prefix="aware_workspace_sdk",
                revision_id="workspace-revision:rev-1:code-package:sdk-python",
                digest="abc123",
                metadata={"producer": "workspace"},
            ),
            artifact_lock=HubCodePackageArtifactLock(
                artifact_url="https://hub.example.test/artifacts/workspace-sdk.zip",
                sha256="abc123",
                revision_id="workspace-revision:rev-1:code-package:sdk-python",
                media_type="application/zip",
                archive_format="zip",
            ),
            channel="preview",
        ),
        channel="stable",
        publisher_execution_id="codex-test",
        idempotency_key="workspace-sdk-rev-1",
        request_id=request_id,
    )

    request = generated.hub.code_package.publish_requests[0]
    assert request.request_id == request_id
    assert request.index_url == "https://hub.example.test/index.json"
    assert request.channel == "stable"
    assert request.publisher_execution_id == "codex-test"
    assert request.idempotency_key == "workspace-sdk-rev-1"
    assert request.descriptor.language is CodeLanguage.python
    assert request.descriptor.surface == "sdk"
    assert request.descriptor.manifest_kind == "pyproject_toml"
    assert request.artifact_lock.sha256 == "abc123"
    assert isinstance(receipt, HubCodePackagePublishReceipt)
    assert receipt.accepted is True
    assert receipt.selector.package_name == "aware-workspace-sdk"
    assert receipt.selector.channel == "stable"
    assert receipt.descriptor.manifest_kind == "pyproject_toml"


@pytest.mark.asyncio
async def test_failed_generated_api_response_raises_sdk_error() -> None:
    generated = _RecordingGeneratedHubApiClient()
    generated.hub.code_package.fail_next_search = True
    client = HubCodePackageClient(api_client=generated)

    with pytest.raises(HubSdkError, match="authority offline"):
        await client.search(package_name="aware-workspace-api")


def test_sdk_source_does_not_import_hub_service_internals() -> None:
    package_root = Path(__file__).parents[1] / "aware_hub_sdk"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(package_root.glob("*.py"))
    )

    assert "services.hub" not in source
    assert "from aware_hub_service " not in source
    assert "import aware_hub_service " not in source
    assert "aware_hub_service.code_package_authority" not in source


def _api_descriptor() -> CodePackageDescriptor:
    return CodePackageDescriptor.model_validate(
        {
            "package_name": "aware-workspace-api",
            "language": CodeLanguage.python,
            "surface": "api",
            "manifest_kind": "aware_api_toml",
            "manifest_relative_path": "aware.api.toml",
            "package_root": "workspaces/aware_workspace/apis/workspace",
            "sources_root": "python",
            "fqn_prefix": "aware_workspace_service_api",
            "version": "0.1.0",
            "revision_id": "rev-123",
            "digest": "sha256:descriptor",
            "artifact_media_type": "application/vnd.aware.code-package+zip",
            "artifact_size_bytes": 512,
            "download_handle": "workspace-api-python",
            "metadata": {"owner": "sdk-test"},
        }
    )


def _sdk_descriptor() -> HubCodePackageDescriptor:
    return HubCodePackageDescriptor(
        package_name="aware-workspace-api",
        language="python",
        surface="api",
        manifest_kind="aware_api_toml",
        manifest_relative_path="aware.api.toml",
        package_root="workspaces/aware_workspace/apis/workspace",
        sources_root="python",
        fqn_prefix="aware_workspace_service_api",
        version="0.1.0",
        revision_id="rev-123",
        digest="sha256:descriptor",
        artifact_media_type="application/vnd.aware.code-package+zip",
        artifact_size_bytes=512,
        download_handle="workspace-api-python",
        metadata={"owner": "sdk-test"},
    )


def _api_artifact_lock() -> CodePackageArtifactLock:
    return CodePackageArtifactLock(
        artifact_url="https://hub.example.test/artifacts/workspace-api-python.zip",
        sha256="abc123",
        size_bytes=2048,
        media_type="application/zip",
        archive_format="zip",
        revision_id="rev-123",
        published_at="2026-04-29T09:00:00Z",
    )


def _sdk_artifact_lock() -> HubCodePackageArtifactLock:
    return HubCodePackageArtifactLock(
        artifact_url="https://hub.example.test/artifacts/workspace-api-python.zip",
        sha256="abc123",
        size_bytes=2048,
        media_type="application/zip",
        archive_format="zip",
        revision_id="rev-123",
        published_at="2026-04-29T09:00:00Z",
    )
