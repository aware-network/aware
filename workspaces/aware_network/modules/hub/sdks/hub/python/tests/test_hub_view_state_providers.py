from __future__ import annotations

from uuid import UUID

import pytest

from aware_hub_service_dto.hub.view.channel_heads import HubPublicDiscoveryViewStateV1
from aware_hub_sdk import (
    HubCodePackageArtifactLock,
    HubCodePackageChannelHead,
    HubCodePackageDescriptor,
    HubCodePackageDiscoveryEntry,
    HubCodePackageDiscoveryReceipt,
    HubPublicDiscoveryV1ProviderInput,
    ViewProviderProvenanceV1,
    hub_public_discovery_v1_provider_input,
    hub_public_discovery_v1_provider_input_from_client,
    hub_public_discovery_view_state,
)


def test_hub_public_discovery_view_state_from_receipt() -> None:
    receipt = _receipt()

    state = hub_public_discovery_view_state(
        provider_input=HubPublicDiscoveryV1ProviderInput(
            receipt=receipt,
            query="kernel",
            channel="stable",
            provenance=ViewProviderProvenanceV1(branch_id="branch-1"),
        )
    )

    assert isinstance(state, HubPublicDiscoveryViewStateV1)
    assert state.provenance["view_ref"] == "hub.channel_heads"
    assert state.provenance["projection_view_key"] == "home.channel_heads.v1"
    assert state.status == "ready"
    assert state.summary == "1 public channel head"
    assert state.authority_source_url == "https://hub.example.test/index.json"
    assert state.provenance["entry_count"] == 1
    assert state.provenance["branch_id"] == "branch-1"
    assert state.entries[0].package_name == "aware-workspace"
    assert state.entries[0].descriptor is not None
    assert state.entries[0].descriptor.manifest_relative_path == "aware.workspace.toml"
    assert state.entries[0].artifact_lock is not None
    assert state.entries[0].artifact_lock.sha256 == "abc123"


@pytest.mark.asyncio
async def test_hub_public_discovery_provider_input_from_client() -> None:
    client = _RecordingHubCodePackageClient()

    provider_input = await hub_public_discovery_v1_provider_input_from_client(
        client=client,
        query="kernel",
        package_name="aware-workspace",
        language="python",
        surface="experience",
        channel="stable",
        authority_base_url="https://hub.example.test",
        index_url="https://hub.example.test/index.json",
        limit=5,
        request_id=UUID("11111111-1111-1111-1111-111111111111"),
    )

    assert provider_input.receipt is client.receipt
    assert client.calls == [
        {
            "query": "kernel",
            "package_name": "aware-workspace",
            "language": "python",
            "surface": "experience",
            "channel": "stable",
            "authority_base_url": "https://hub.example.test",
            "index_url": "https://hub.example.test/index.json",
            "limit": 5,
            "request_id": UUID("11111111-1111-1111-1111-111111111111"),
        }
    ]

    state = hub_public_discovery_view_state(provider_input=provider_input)
    assert state.status == "ready"
    assert state.entries[0].revision_id == "rev-123"


def test_hub_public_discovery_provider_input_resolver_waiting() -> None:
    provider_input = hub_public_discovery_v1_provider_input(
        {
            "query": "empty",
            "limit": "9",
            "provenance": {"branch_id": "branch-2"},
        }
    )

    state = hub_public_discovery_view_state(provider_input=provider_input)

    assert state.status == "waiting"
    assert state.entries == []
    assert state.query == "empty"
    assert state.limit == 9
    assert state.provenance["branch_id"] == "branch-2"
    assert (
        getattr(hub_public_discovery_view_state, "provider_input_resolver")
        is hub_public_discovery_v1_provider_input
    )


class _RecordingHubCodePackageClient:
    def __init__(self) -> None:
        self.receipt = _receipt()
        self.calls: list[dict[str, object]] = []

    async def discover_channel_heads(
        self,
        *,
        query: str | None = None,
        package_name: str | None = None,
        language: object | None = None,
        surface: object | None = None,
        channel: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        limit: int = 50,
        request_id: UUID | None = None,
    ) -> HubCodePackageDiscoveryReceipt:
        self.calls.append(
            {
                "query": query,
                "package_name": package_name,
                "language": language,
                "surface": surface,
                "channel": channel,
                "authority_base_url": authority_base_url,
                "index_url": index_url,
                "limit": limit,
                "request_id": request_id,
            }
        )
        return self.receipt


def _receipt() -> HubCodePackageDiscoveryReceipt:
    return HubCodePackageDiscoveryReceipt(
        authority_source_url="https://hub.example.test/index.json",
        request_id=UUID("11111111-1111-1111-1111-111111111111"),
        entries=(
            HubCodePackageDiscoveryEntry(
                channel_head=HubCodePackageChannelHead(
                    package_name="aware-workspace",
                    language="python",
                    surface="experience",
                    channel="stable",
                    revision_id="rev-123",
                    updated_at="2026-05-08T00:00:00Z",
                    publisher_execution_id="codex-test",
                    metadata={"kind": "kernel-map"},
                ),
                descriptor=HubCodePackageDescriptor(
                    package_name="aware-workspace",
                    language="python",
                    surface="experience",
                    manifest_kind="aware_experience_toml",
                    manifest_relative_path="aware.workspace.toml",
                    package_root="workspaces/aware_workspace/experiences/aware-workspace",
                    sources_root="workspaces/aware_workspace/experiences/aware-workspace",
                    fqn_prefix="aware_workspace",
                    version="0.1.0",
                    revision_id="rev-123",
                    digest="sha256:def456",
                    metadata={"role": "workspace"},
                ),
                artifact_lock=HubCodePackageArtifactLock(
                    artifact_url="https://hub.example.test/artifacts/rev-123.tar.gz",
                    sha256="abc123",
                    size_bytes=42,
                    media_type="application/gzip",
                    archive_format="tar.gz",
                    revision_id="rev-123",
                    published_at="2026-05-08T00:00:00Z",
                ),
            ),
        ),
    )
