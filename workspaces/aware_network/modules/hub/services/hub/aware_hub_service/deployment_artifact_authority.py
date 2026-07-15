"""Hub-owned deployment artifact authority resolution.

Hub resolves immutable deployment artifact revisions through release
distribution index truth. Producer-specific revision data is returned only as
generic provenance so Workspace can publish without becoming part of Hub's API
closure.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aware_release.install_distribution import (
    WorkspaceDeploymentRevision,
    build_workspace_deployment_authority_index_url,
    load_workspace_deployment_index_from_url,
    resolve_workspace_deployment_revision,
)

SUPPORTED_ARTIFACT_FAMILY = "workspace-deployment"


class DeploymentArtifactProducerProvenance(BaseModel):
    producer_kind: str = "workspace"
    producer_revision_id: str | None = None
    source_revision_id: str | None = None
    source_revision_kind: str | None = None
    materialization_ref: str | None = None
    build_ref: str | None = None

    model_config = ConfigDict(extra="forbid")


class DeploymentArtifactLock(BaseModel):
    artifact_family: str = SUPPORTED_ARTIFACT_FAMILY
    artifact_key: str
    channel: str = "stable"
    revision_id: str
    payload_url: str
    payload_sha256: str
    payload_contract_version: str = "aware.workspace_deployment.payload.v1"

    model_config = ConfigDict(extra="forbid")


class DeploymentArtifactTarget(BaseModel):
    selector_key: str
    target_ref: str
    node_package_name: str

    model_config = ConfigDict(extra="forbid")


class ResolveDeploymentArtifactRequest(BaseModel):
    """Hub-owned request for one deployment artifact authority resolution."""

    operation: str = Field(default="resolve_deployment_artifact")
    request_id: UUID | None = None
    artifact_family: str = SUPPORTED_ARTIFACT_FAMILY
    artifact_key: str | None = None
    channel: str = "stable"
    revision_id: str | None = None
    authority_base_url: str | None = None
    index_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class ResolveDeploymentArtifactResponse(BaseModel):
    """Resolved immutable deployment artifact revision metadata."""

    operation: str = Field(default="resolve_deployment_artifact")
    request_id: UUID | None = None
    success: bool = True
    info: str | None = None
    error: str | None = None
    authority_source_url: str
    artifact_family: str
    artifact_key: str
    channel: str
    revision_id: str
    payload_url: str
    payload_sha256: str
    selector_key: str
    target_ref: str
    producer: DeploymentArtifactProducerProvenance
    node_package_name: str
    artifact_lock: DeploymentArtifactLock
    target: DeploymentArtifactTarget

    model_config = ConfigDict(extra="forbid")

    @property
    def deployment_url(self) -> str:
        return self.payload_url

    @property
    def deployment_sha256(self) -> str:
        return self.payload_sha256

    @property
    def workspace_revision_id(self) -> str:
        return self.producer.producer_revision_id or ""

    @property
    def workspace_source_revision_id(self) -> str:
        return self.producer.source_revision_id or ""

    @property
    def workspace_source_revision_kind(self) -> str:
        return self.producer.source_revision_kind or ""

    @property
    def workspace_materialization_ref(self) -> str:
        return self.producer.materialization_ref or ""

    @property
    def workspace_build_ref(self) -> str:
        return self.producer.build_ref or ""


def resolve_deployment_artifact(
    request: ResolveDeploymentArtifactRequest,
) -> ResolveDeploymentArtifactResponse:
    """Resolve a deployment artifact revision from Hub authority truth."""

    artifact_family = _clean(request.artifact_family) or SUPPORTED_ARTIFACT_FAMILY
    if artifact_family != SUPPORTED_ARTIFACT_FAMILY:
        raise ValueError(
            "Hub deployment artifact authority only supports "
            f"{SUPPORTED_ARTIFACT_FAMILY!r}; got {artifact_family!r}."
        )

    channel = _clean(request.channel) or "stable"
    index_url = _resolve_index_url(request=request)
    index = load_workspace_deployment_index_from_url(index_url)
    artifact_key = _clean(request.artifact_key) or index.artifact_key
    if artifact_key != index.artifact_key:
        raise ValueError(
            "Hub deployment artifact authority artifact_key mismatch: "
            f"requested {artifact_key!r} got index {index.artifact_key!r}"
        )
    revision = resolve_workspace_deployment_revision(
        index,
        channel=channel,
        revision_id=_clean(request.revision_id) or None,
    )
    return _response_from_revision(
        authority_source_url=index_url,
        channel=channel,
        request_id=request.request_id,
        revision=revision,
    )


def resolve_workspace_deployment(
    request: ResolveDeploymentArtifactRequest,
) -> ResolveDeploymentArtifactResponse:
    """Compatibility wrapper for older in-process callers."""

    typed_request = ResolveDeploymentArtifactRequest.model_validate(
        request.model_dump(mode="json") if isinstance(request, BaseModel) else request
    )
    return resolve_deployment_artifact(typed_request)


def _resolve_index_url(*, request: ResolveDeploymentArtifactRequest) -> str:
    configured_index_url = _clean(request.index_url)
    if configured_index_url:
        return configured_index_url

    authority_base_url = _clean(request.authority_base_url)
    artifact_key = _clean(request.artifact_key)
    if not authority_base_url or not artifact_key:
        raise ValueError(
            "Hub deployment artifact resolution requires index_url or both "
            "authority_base_url and artifact_key."
        )
    return build_workspace_deployment_authority_index_url(
        base_url=authority_base_url,
        artifact_key=artifact_key,
    )


def _response_from_revision(
    *,
    authority_source_url: str,
    channel: str,
    request_id: UUID | None,
    revision: WorkspaceDeploymentRevision,
) -> ResolveDeploymentArtifactResponse:
    artifact_lock = DeploymentArtifactLock(
        artifact_family=revision.artifact_family,
        artifact_key=revision.artifact_key,
        channel=channel,
        revision_id=revision.revision_id,
        payload_url=revision.deployment_url,
        payload_sha256=revision.deployment_sha256,
    )
    target = DeploymentArtifactTarget(
        selector_key=revision.selector_key,
        target_ref=revision.target_ref,
        node_package_name=revision.node_package_name,
    )
    return ResolveDeploymentArtifactResponse(
        request_id=request_id,
        authority_source_url=authority_source_url,
        artifact_family=revision.artifact_family,
        artifact_key=revision.artifact_key,
        channel=channel,
        revision_id=revision.revision_id,
        payload_url=revision.deployment_url,
        payload_sha256=revision.deployment_sha256,
        selector_key=revision.selector_key,
        target_ref=revision.target_ref,
        producer=DeploymentArtifactProducerProvenance(
            producer_kind="workspace",
            producer_revision_id=revision.workspace_revision_id,
            source_revision_id=revision.workspace_source_revision_id,
            source_revision_kind=revision.workspace_source_revision_kind,
            materialization_ref=revision.workspace_materialization_ref,
            build_ref=revision.workspace_build_ref,
        ),
        node_package_name=revision.node_package_name,
        artifact_lock=artifact_lock,
        target=target,
    )


def _clean(value: str | None) -> str:
    return (value or "").strip()


ResolveWorkspaceDeploymentRequest = ResolveDeploymentArtifactRequest
ResolveWorkspaceDeploymentResponse = ResolveDeploymentArtifactResponse

__all__ = [
    "DeploymentArtifactLock",
    "DeploymentArtifactProducerProvenance",
    "DeploymentArtifactTarget",
    "ResolveDeploymentArtifactRequest",
    "ResolveDeploymentArtifactResponse",
    "ResolveWorkspaceDeploymentRequest",
    "ResolveWorkspaceDeploymentResponse",
    "resolve_deployment_artifact",
    "resolve_workspace_deployment",
]
