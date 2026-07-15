from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest
from aware_types import JsonObject

from aware_hub_sdk import (
    AwareHubSdk,
    HubGeneratedApiClient,
    HubPublicMapClient,
    HubPublicMapDiscoveryReceipt,
    HubPublicMapEntry,
    HubSdkError,
)
from aware_hub_service_dto.hub.public_map_discovery import (
    DiscoverPublicMapRequest,
)
from aware_hub_service_dto.hub.public_map_discovery import (
    DiscoverPublicMapResponse,
)
from aware_hub_service_dto.hub.public_map_discovery import (
    HubPublicMapEntry as ApiHubPublicMapEntry,
)


class _RecordingPublicMapApiClient:
    def __init__(self) -> None:
        self.discover_requests: list[DiscoverPublicMapRequest] = []
        self.fail_next_discover: bool = False

    async def discover(
        self,
        request: DiscoverPublicMapRequest,
    ) -> DiscoverPublicMapResponse:
        self.discover_requests.append(request)
        if self.fail_next_discover:
            return DiscoverPublicMapResponse(
                request_id=request.request_id,
                success=False,
                error="hub map offline",
            )
        return DiscoverPublicMapResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/code-package/index.json",
            entries=[
                ApiHubPublicMapEntry(
                    artifact_family="experience-package",
                    artifact_key="workspace.collaboration",
                    channel=request.channel or "stable",
                    revision_id="workspace-experience-rev-1",
                    package_name="aware-workspace-experience",
                    language="python",
                    surface="experience",
                    manifest_kind="aware_api_toml",
                    digest="sha256-workspace-experience",
                    artifact_url=(
                        "https://hub.example.test/artifacts/" "workspace-experience.zip"
                    ),
                    artifact_sha256="sha256-workspace-experience",
                    artifact_size_bytes=4096,
                    media_type="application/zip",
                    title="Workspace Collaboration",
                    summary="Collaboration experience for workspace.",
                    experience_name="workspace.collaboration",
                    fqn_prefix="aware_workspace_experience",
                    producer_kind="workspace",
                    producer_revision_id="workspace-package:rev-1",
                    source_revision_id="workspace-revision:rev-1",
                    visibility="public",
                    metadata=JsonObject(
                        {
                            "artifact_family": "experience-package",
                            "artifact_key": "workspace.collaboration",
                        }
                    ),
                )
            ],
        )


class _RecordingHubApiClient:
    def __init__(self) -> None:
        self.public_map: _RecordingPublicMapApiClient = _RecordingPublicMapApiClient()


class _RecordingGeneratedHubApiClient:
    def __init__(self) -> None:
        self.hub: _RecordingHubApiClient = _RecordingHubApiClient()


@pytest.mark.asyncio
async def test_public_map_discover_builds_generated_request() -> None:
    generated = _RecordingGeneratedHubApiClient()
    sdk = AwareHubSdk(
        cast(HubGeneratedApiClient, cast(object, generated)),
        authority_base_url="https://hub.example.test",
    )
    request_id = uuid4()

    receipt = await sdk.public_map.discover(
        query="collaboration",
        artifact_family="experience-package",
        artifact_key="workspace.collaboration",
        experience_name="workspace.collaboration",
        channel="stable",
        limit=7,
        request_id=request_id,
    )

    request = generated.hub.public_map.discover_requests[0]
    assert request.request_id == request_id
    assert request.query == "collaboration"
    assert request.artifact_family == "experience-package"
    assert request.artifact_key == "workspace.collaboration"
    assert request.experience_name == "workspace.collaboration"
    assert request.authority_base_url == "https://hub.example.test"
    assert request.limit == 7
    assert isinstance(receipt, HubPublicMapDiscoveryReceipt)
    assert receipt.entries == (
        HubPublicMapEntry(
            artifact_family="experience-package",
            artifact_key="workspace.collaboration",
            channel="stable",
            revision_id="workspace-experience-rev-1",
            package_name="aware-workspace-experience",
            language="python",
            surface="experience",
            manifest_kind="aware_api_toml",
            digest="sha256-workspace-experience",
            artifact_url=(
                "https://hub.example.test/artifacts/workspace-experience.zip"
            ),
            artifact_sha256="sha256-workspace-experience",
            artifact_size_bytes=4096,
            media_type="application/zip",
            title="Workspace Collaboration",
            summary="Collaboration experience for workspace.",
            experience_name="workspace.collaboration",
            fqn_prefix="aware_workspace_experience",
            producer_kind="workspace",
            producer_revision_id="workspace-package:rev-1",
            source_revision_id="workspace-revision:rev-1",
            visibility="public",
            metadata={
                "artifact_family": "experience-package",
                "artifact_key": "workspace.collaboration",
            },
        ),
    )


@pytest.mark.asyncio
async def test_public_map_client_uses_index_url_override() -> None:
    generated = _RecordingGeneratedHubApiClient()
    client = HubPublicMapClient(
        api_client=generated,
        index_url="https://hub.example.test/code-package/index.json",
    )

    _ = await client.discover(index_url="file:///tmp/hub-index.json")

    request = generated.hub.public_map.discover_requests[0]
    assert request.index_url == "file:///tmp/hub-index.json"
    assert request.authority_base_url is None


@pytest.mark.asyncio
async def test_public_map_failed_response_raises_sdk_error() -> None:
    generated = _RecordingGeneratedHubApiClient()
    generated.hub.public_map.fail_next_discover = True
    client = HubPublicMapClient(api_client=generated)

    with pytest.raises(HubSdkError, match="hub map offline"):
        _ = await client.discover()
