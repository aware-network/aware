from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from aware_hub_sdk.artifact import HubArtifactClient
from aware_hub_sdk.code_package import HubSdkError
from aware_hub_service_dto.hub.artifact_authority import (
    HubArtifactPayloadLock,
    ResolveHubArtifactRequest,
    ResolveHubArtifactResponse,
)


class _ArtifactApiClient:
    def __init__(self, *, payload_path: Path, digest: str) -> None:
        self.payload_path = payload_path
        self.digest = digest

    async def resolve(
        self,
        request: ResolveHubArtifactRequest,
    ) -> ResolveHubArtifactResponse:
        size = self.payload_path.stat().st_size
        return ResolveHubArtifactResponse(
            request_id=request.request_id,
            authority_source_url="file:///tmp/hub-index.json",
            artifact_lock=HubArtifactPayloadLock(
                artifact_family=request.artifact_family,
                artifact_key=request.artifact_key,
                channel=request.channel,
                revision_id=request.revision_id or "workspace-revision:resolved",
                payload_url=self.payload_path.as_uri(),
                payload_sha256=self.digest,
                payload_size_bytes=size,
                payload_media_type="application/json",
                payload_contract="aware.workspace.revision_dependency_manifest.v1",
            ),
        )


class _HubApiNamespace:
    def __init__(self, artifact: _ArtifactApiClient) -> None:
        self.artifact = artifact


class _GeneratedHubApiClient:
    def __init__(self, artifact: _ArtifactApiClient) -> None:
        self.hub = _HubApiNamespace(artifact)


@pytest.mark.asyncio
async def test_resolve_json_payload_verifies_digest_and_contract(
    tmp_path: Path,
) -> None:
    payload = {"schema": "aware.workspace.revision_dependency_manifest.v1"}
    payload_bytes = json.dumps(payload).encode("utf-8")
    payload_path = tmp_path / "manifest.json"
    payload_path.write_bytes(payload_bytes)
    generated = _GeneratedHubApiClient(
        _ArtifactApiClient(
            payload_path=payload_path,
            digest=hashlib.sha256(payload_bytes).hexdigest(),
        )
    )

    receipt = await HubArtifactClient(cast(Any, generated)).resolve_json_payload(
        artifact_family="workspace-revision-dependency-manifest",
        artifact_key="aware_agent",
        revision_id="workspace-revision:resolved",
        expected_payload_contract=("aware.workspace.revision_dependency_manifest.v1"),
    )

    assert receipt.payload == payload
    assert receipt.artifact_lock.artifact_key == "aware_agent"


@pytest.mark.asyncio
async def test_resolve_json_payload_rejects_digest_mismatch(tmp_path: Path) -> None:
    payload_path = tmp_path / "manifest.json"
    payload_path.write_text('{"schema":"v1"}', encoding="utf-8")
    generated = _GeneratedHubApiClient(
        _ArtifactApiClient(payload_path=payload_path, digest="0" * 64)
    )

    with pytest.raises(HubSdkError, match="digest mismatch"):
        await HubArtifactClient(cast(Any, generated)).resolve_json_payload(
            artifact_family="workspace-revision-dependency-manifest",
            artifact_key="aware_agent",
        )
