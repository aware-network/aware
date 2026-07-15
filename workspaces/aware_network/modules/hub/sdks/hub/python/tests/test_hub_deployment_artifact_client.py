from __future__ import annotations

from uuid import uuid4

import pytest

from aware_hub_sdk import (
    AwareHubSdk,
    HubDeploymentArtifactClient,
    HubDeploymentArtifactResolveReceipt,
    HubSdkError,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    DeploymentArtifactLock,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    DeploymentArtifactProducerProvenance,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    DeploymentArtifactTarget,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    ResolveDeploymentArtifactRequest,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    ResolveDeploymentArtifactResponse,
)


class _RecordingDeploymentArtifactApiClient:
    def __init__(self) -> None:
        self.resolve_requests: list[ResolveDeploymentArtifactRequest] = []
        self.fail_next_resolve = False

    async def resolve(
        self,
        request: ResolveDeploymentArtifactRequest,
    ) -> ResolveDeploymentArtifactResponse:
        self.resolve_requests.append(request)
        if self.fail_next_resolve:
            return ResolveDeploymentArtifactResponse(
                request_id=request.request_id,
                success=False,
                error="deployment authority offline",
                authority_source_url="https://hub.example.test/index.json",
                artifact_family=request.artifact_family,
                artifact_key=request.artifact_key or "kernel-node",
                channel=request.channel,
                revision_id="rev-123",
                payload_url="https://hub.example.test/deployment.json",
                payload_sha256="0" * 64,
                selector_key="node:kernel-node",
                target_ref="node:kernel-node",
                producer=_api_producer(),
                node_package_name="kernel-node",
                artifact_lock=_api_lock(),
                target=_api_target(),
            )
        return ResolveDeploymentArtifactResponse(
            request_id=request.request_id,
            authority_source_url="https://hub.example.test/index.json",
            artifact_family=request.artifact_family,
            artifact_key=request.artifact_key or "kernel-node",
            channel=request.channel,
            revision_id="rev-123",
            payload_url="https://hub.example.test/deployment.json",
            payload_sha256="a" * 64,
            selector_key="node:kernel-node",
            target_ref="node:kernel-node",
            producer=_api_producer(),
            node_package_name="kernel-node",
            artifact_lock=_api_lock(),
            target=_api_target(),
        )


class _RecordingHubApiClient:
    def __init__(self) -> None:
        self.deployment_artifact = _RecordingDeploymentArtifactApiClient()


class _RecordingGeneratedHubApiClient:
    def __init__(self) -> None:
        self.hub = _RecordingHubApiClient()


@pytest.mark.asyncio
async def test_deployment_artifact_resolve_returns_public_lock_receipt() -> None:
    generated = _RecordingGeneratedHubApiClient()
    client = HubDeploymentArtifactClient(
        api_client=generated,
        authority_base_url="https://hub.example.test",
    )
    request_id = uuid4()

    receipt = await client.resolve(
        artifact_key="kernel-node",
        channel="stable",
        request_id=request_id,
    )

    request = generated.hub.deployment_artifact.resolve_requests[0]
    assert request.request_id == request_id
    assert request.artifact_key == "kernel-node"
    assert request.authority_base_url == "https://hub.example.test"
    assert isinstance(receipt, HubDeploymentArtifactResolveReceipt)
    assert receipt.artifact_lock.artifact_key == "kernel-node"
    assert receipt.artifact_lock.payload_url.endswith("/deployment.json")
    assert receipt.target.node_package_name == "kernel-node"
    assert receipt.producer.producer_kind == "workspace"
    assert receipt.producer.producer_revision_id == "workspace-revision-123"


@pytest.mark.asyncio
async def test_aware_hub_sdk_exposes_deployment_artifact_client() -> None:
    generated = _RecordingGeneratedHubApiClient()

    sdk = AwareHubSdk(generated)

    receipt = await sdk.deployment_artifact.resolve(artifact_key="kernel-node")
    assert receipt.artifact_lock.revision_id == "rev-123"


@pytest.mark.asyncio
async def test_deployment_artifact_resolve_raises_on_failure() -> None:
    generated = _RecordingGeneratedHubApiClient()
    generated.hub.deployment_artifact.fail_next_resolve = True
    client = HubDeploymentArtifactClient(api_client=generated)

    with pytest.raises(HubSdkError, match="deployment authority offline"):
        await client.resolve(artifact_key="kernel-node")


def _api_lock() -> DeploymentArtifactLock:
    return DeploymentArtifactLock(
        artifact_family="workspace-deployment",
        artifact_key="kernel-node",
        channel="stable",
        revision_id="rev-123",
        payload_url="https://hub.example.test/deployment.json",
        payload_sha256="a" * 64,
        payload_contract_version="aware.workspace_deployment.payload.v1",
    )


def _api_target() -> DeploymentArtifactTarget:
    return DeploymentArtifactTarget(
        selector_key="node:kernel-node",
        target_ref="node:kernel-node",
        node_package_name="kernel-node",
    )


def _api_producer() -> DeploymentArtifactProducerProvenance:
    return DeploymentArtifactProducerProvenance(
        producer_kind="workspace",
        producer_revision_id="workspace-revision-123",
        source_revision_id="git-commit-123",
        source_revision_kind="git",
        materialization_ref="workspace-materialization-123",
        build_ref="workspace-build-123",
    )
