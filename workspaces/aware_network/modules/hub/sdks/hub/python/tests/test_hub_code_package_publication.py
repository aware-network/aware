from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import cast

from aware_hub_sdk import (
    HubArtifactClient,
    HubCodePackageArtifactLock,
    HubCodePackageDescriptor,
    HubCodePackagePublicationEntry,
    HubGeneratedArtifactApiClient,
    build_code_package_authority_index_payload,
    oig_commit_refs_from_code_package_descriptor,
    publish_oig_commit_payload_refs_to_hub_artifact_authority,
    publish_oig_commit_payload_refs_to_authority,
    resolve_oig_commit_payload_ref_from_hub_artifact_authority,
    resolve_oig_commit_payload_ref_from_authority,
)
from aware_hub_service import publish_hub_artifact, resolve_hub_artifact
from aware_hub_service_dto.hub.artifact_authority import (
    PublishHubArtifactRequest,
)
from aware_hub_service_dto.hub.artifact_authority import (
    PublishHubArtifactResponse,
)
from aware_hub_service_dto.hub.artifact_authority import (
    ResolveHubArtifactRequest,
)
from aware_hub_service_dto.hub.artifact_authority import (
    ResolveHubArtifactResponse,
)


def test_build_code_package_authority_index_payload() -> None:
    payload = build_code_package_authority_index_payload(
        (
            HubCodePackagePublicationEntry(
                descriptor=HubCodePackageDescriptor(
                    package_name="aware-workspace-interface",
                    language="python",
                    surface="sdk",
                    manifest_kind="pyproject_toml",
                    manifest_relative_path="pyproject.toml",
                    package_root="workspaces/aware_workspace/sdks/workspace/python/public",
                    fqn_prefix="aware_workspace_sdk",
                    version="0.1.0",
                    revision_id="workspace-revision:rev-1:code-package:pkg-1",
                    digest="abc123",
                    artifact_media_type="application/zip",
                    artifact_size_bytes=42,
                    download_handle="workspace-revision:rev-1:code-package:pkg-1",
                    metadata={"producer": "workspace"},
                ),
                artifact_lock=HubCodePackageArtifactLock(
                    artifact_url="file:///tmp/aware-workspace-interface.zip",
                    sha256="abc123",
                    size_bytes=42,
                    media_type="application/zip",
                    archive_format="zip",
                    revision_id="workspace-revision:rev-1:code-package:pkg-1",
                    published_at="2026-05-08T00:00:00Z",
                ),
                channel="stable",
                updated_at="2026-05-08T00:00:00Z",
            ),
        ),
        generated_at="2026-05-08T00:00:00Z",
    )

    assert payload == {
        "version": 1,
        "authority_kind": "code_package_distribution",
        "generated_at": "2026-05-08T00:00:00Z",
        "packages": [
            {
                "descriptor": {
                    "package_name": "aware-workspace-interface",
                    "language": "python",
                    "surface": "sdk",
                    "manifest_kind": "pyproject_toml",
                    "manifest_relative_path": "pyproject.toml",
                    "package_root": "workspaces/aware_workspace/sdks/workspace/python/public",
                    "fqn_prefix": "aware_workspace_sdk",
                    "version": "0.1.0",
                    "revision_id": "workspace-revision:rev-1:code-package:pkg-1",
                    "digest": "abc123",
                    "artifact_media_type": "application/zip",
                    "artifact_size_bytes": 42,
                    "download_handle": "workspace-revision:rev-1:code-package:pkg-1",
                    "metadata": {"producer": "workspace"},
                },
                "artifact_lock": {
                    "artifact_url": "file:///tmp/aware-workspace-interface.zip",
                    "sha256": "abc123",
                    "size_bytes": 42,
                    "media_type": "application/zip",
                    "archive_format": "zip",
                    "revision_id": "workspace-revision:rev-1:code-package:pkg-1",
                    "published_at": "2026-05-08T00:00:00Z",
                },
            },
        ],
        "channel_heads": [
            {
                "package_name": "aware-workspace-interface",
                "language": "python",
                "surface": "sdk",
                "channel": "stable",
                "revision_id": "workspace-revision:rev-1:code-package:pkg-1",
                "updated_at": "2026-05-08T00:00:00Z",
            },
        ],
    }


def test_oig_commit_refs_from_code_package_descriptor() -> None:
    descriptor = HubCodePackageDescriptor(
        package_name="aware-workspace-interface",
        language="python",
        surface="sdk",
        manifest_kind="pyproject_toml",
        manifest_relative_path="pyproject.toml",
        package_root="workspaces/aware_workspace/sdks/workspace/python/public",
        fqn_prefix="aware_workspace_sdk",
        version="0.1.0",
        revision_id="workspace-revision:rev-1:code-package:pkg-1",
        digest="abc123",
        artifact_media_type="application/zip",
        artifact_size_bytes=42,
        download_handle="workspace-revision:rev-1:code-package:pkg-1",
        metadata={
            "producer": "workspace",
            "oig_commit_refs": [
                {
                    "ref_schema": "aware.oig_commit_payload_ref.v1",
                    "payload_contract": "aware.oig_commit_payload.v1",
                    "branch_id": "87550a7c-00cc-4c29-a04d-c476c6ead4d0",
                    "projection_hash": "CodePackage",
                    "commit_id": "d01930c7-9f3f-4481-84ac-f0e48b5ca333",
                    "domain_commit_id": "d01930c7-9f3f-4481-84ac-f0e48b5ca333",
                    "object_instance_graph_commit_id": (
                        "b7a99fc0-737e-4d65-ad6c-63a35d4048de"
                    ),
                    "object_instance_graph_identity_id": (
                        "59d8db89-910c-46aa-9d55-334f266b762b"
                    ),
                    "object_instance_graph_id": (
                        "fbc6be64-2085-49ea-84ee-cf1905b4160f"
                    ),
                    "graph_hash_post": "sha256:graph-post",
                    "payload_url": (
                        "file:///tmp/"
                        "aware-workspace-interface.oig-commit.json"
                    ),
                    "payload_sha256": "a" * 64,
                    "payload_size_bytes": 2048,
                    "payload_media_type": "application/json",
                }
            ],
        },
    )

    refs = oig_commit_refs_from_code_package_descriptor(descriptor)

    assert len(refs) == 1
    assert refs[0].branch_id == "87550a7c-00cc-4c29-a04d-c476c6ead4d0"
    assert refs[0].projection_hash == "CodePackage"
    assert refs[0].commit_id == "d01930c7-9f3f-4481-84ac-f0e48b5ca333"
    assert refs[0].payload_sha256 == "a" * 64
    assert refs[0].metadata["payload_contract"] == "aware.oig_commit_payload.v1"


def test_publish_oig_commit_payload_refs_to_authority_writes_index(
    tmp_path: Path,
) -> None:
    payload_path = tmp_path / "source-oig-commit.json"
    payload_path.write_bytes(b'{"commit":"demo"}')
    ref = _oig_ref_payload(payload_path)
    authority_root = tmp_path / "hub-authority"

    receipt = publish_oig_commit_payload_refs_to_authority(
        refs=(ref,),
        authority_base_url=authority_root.as_uri(),
        channel="candidate",
        publisher_execution_id="codex-test",
        published_at="2026-05-17T00:00:00Z",
    )

    index_path = authority_root / "oig-commit" / "index.json"
    assert receipt.authority_source_url == index_path.as_uri()
    assert len(receipt.refs) == 1
    updated_ref = receipt.refs[0]
    assert updated_ref["payload_url"] == (
        authority_root
        / "oig-commit"
        / "payloads"
        / "sha256"
        / f"{ref['payload_sha256']}.json"
    ).as_uri()
    assert Path(str(updated_ref["payload_url"]).removeprefix("file://")).read_bytes() == (
        payload_path.read_bytes()
    )

    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["authority_kind"] == "oig_commit_payload_distribution"
    assert index["artifacts"][0]["artifact_family"] == "oig-commit"
    assert index["artifacts"][0]["artifact_key"] == ref["artifact_key"]
    assert index["channel_heads"][0]["channel"] == "candidate"

    resolved = resolve_oig_commit_payload_ref_from_authority(
        authority_base_url=authority_root.as_uri(),
        artifact_key=str(ref["artifact_key"]),
        channel="candidate",
    )
    assert resolved["payload_url"] == updated_ref["payload_url"]
    assert resolved["payload_sha256"] == ref["payload_sha256"]


def test_publish_oig_commit_payload_refs_to_hub_artifact_authority(
    tmp_path: Path,
) -> None:
    payload_path = tmp_path / "source-oig-commit.json"
    payload_path.write_bytes(b'{"commit":"demo"}')
    ref = _oig_ref_payload(payload_path)
    authority_root = tmp_path / "hub-authority"
    generated = _LocalGeneratedHubApiClient()

    receipt = asyncio.run(
        publish_oig_commit_payload_refs_to_hub_artifact_authority(
            artifact_client=HubArtifactClient(
                api_client=cast(
                    HubGeneratedArtifactApiClient,
                    cast(object, generated),
                ),
            ),
            refs=(ref,),
            authority_base_url=authority_root.as_uri(),
            channel="candidate",
            publisher_execution_id="codex-test",
            published_at="2026-05-17T00:00:00Z",
        )
    )

    assert len(generated.hub.artifact.publish_requests) == 1
    publish_request = generated.hub.artifact.publish_requests[0]
    assert publish_request.artifact_family == "oig-commit"
    assert publish_request.payload_source_url == payload_path.as_uri()
    assert publish_request.payload_sha256 == ref["payload_sha256"]
    assert receipt.authority_source_url == (
        authority_root / "oig-commit" / "index.json"
    ).as_uri()
    assert receipt.refs[0]["payload_url"] == (
        authority_root
        / "oig-commit"
        / "payloads"
        / "sha256"
        / f"{ref['payload_sha256']}.json"
    ).as_uri()
    resolved = asyncio.run(
        resolve_oig_commit_payload_ref_from_hub_artifact_authority(
            artifact_client=HubArtifactClient(
                api_client=cast(
                    HubGeneratedArtifactApiClient,
                    cast(object, generated),
                ),
            ),
            artifact_key=str(ref["artifact_key"]),
            authority_base_url=authority_root.as_uri(),
            channel="candidate",
        )
    )
    assert resolved["artifact_key"] == ref["artifact_key"]
    assert resolved["payload_sha256"] == ref["payload_sha256"]
    assert resolved["payload_url"] == receipt.refs[0]["payload_url"]


class _LocalGeneratedHubApiClient:
    def __init__(self) -> None:
        self.hub = _LocalHubNamespace()


class _LocalHubNamespace:
    def __init__(self) -> None:
        self.artifact = _LocalHubArtifactClient()


class _LocalHubArtifactClient:
    def __init__(self) -> None:
        self.publish_requests: list[PublishHubArtifactRequest] = []

    async def publish(
        self,
        request: PublishHubArtifactRequest,
    ) -> PublishHubArtifactResponse:
        self.publish_requests.append(request)
        return publish_hub_artifact(request)

    async def resolve(
        self,
        request: ResolveHubArtifactRequest,
    ) -> ResolveHubArtifactResponse:
        return resolve_hub_artifact(request)


def _oig_ref_payload(payload_path: Path) -> dict[str, object]:
    payload_bytes = payload_path.read_bytes()
    branch_id = "87550a7c-00cc-4c29-a04d-c476c6ead4d0"
    commit_id = "d01930c7-9f3f-4481-84ac-f0e48b5ca333"
    projection_hash = "CodePackage"
    return {
        "ref_schema": "aware.oig_commit_payload_ref.v1",
        "payload_contract": "aware.oig_commit_payload.v1",
        "branch_id": branch_id,
        "projection_hash": projection_hash,
        "commit_id": commit_id,
        "domain_commit_id": commit_id,
        "object_instance_graph_commit_id": (
            "b7a99fc0-737e-4d65-ad6c-63a35d4048de"
        ),
        "object_instance_graph_identity_id": (
            "59d8db89-910c-46aa-9d55-334f266b762b"
        ),
        "object_instance_graph_id": "fbc6be64-2085-49ea-84ee-cf1905b4160f",
        "graph_hash_post": "sha256:graph-post",
        "payload_url": payload_path.as_uri(),
        "payload_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "payload_size_bytes": len(payload_bytes),
        "payload_media_type": "application/json",
        "artifact_family": "oig-commit",
        "artifact_key": f"{branch_id}:{projection_hash}:{commit_id}",
        "artifact_revision_id": commit_id,
    }
