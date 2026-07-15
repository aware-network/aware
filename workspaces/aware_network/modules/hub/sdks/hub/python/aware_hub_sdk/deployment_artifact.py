from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_hub_service_dto.hub.deployment_artifact_authority import (
    ResolveDeploymentArtifactRequest,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    ResolveDeploymentArtifactResponse,
)

from aware_hub_sdk.code_package import HubSdkError
from aware_hub_sdk.models import (
    HubDeploymentArtifactLock,
    HubDeploymentArtifactProducerProvenance,
    HubDeploymentArtifactResolveReceipt,
    HubDeploymentArtifactTarget,
)


class _HubDeploymentArtifactApiClient(Protocol):
    async def resolve(
        self,
        request: ResolveDeploymentArtifactRequest,
    ) -> ResolveDeploymentArtifactResponse: ...


class _HubDeploymentArtifactNamespaceClient(Protocol):
    @property
    def deployment_artifact(self) -> _HubDeploymentArtifactApiClient: ...


class HubGeneratedDeploymentArtifactApiClient(Protocol):
    @property
    def hub(self) -> _HubDeploymentArtifactNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class HubDeploymentArtifactClient:
    api_client: HubGeneratedDeploymentArtifactApiClient
    authority_base_url: str | None = None
    index_url: str | None = None

    async def resolve(
        self,
        *,
        artifact_key: str | None = None,
        artifact_family: str = "workspace-deployment",
        channel: str = "stable",
        revision_id: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        request_id: UUID | None = None,
    ) -> HubDeploymentArtifactResolveReceipt:
        response = await self.api_client.hub.deployment_artifact.resolve(
            ResolveDeploymentArtifactRequest(
                request_id=request_id,
                artifact_family=artifact_family,
                artifact_key=artifact_key,
                channel=channel,
                revision_id=revision_id,
                authority_base_url=self._authority_base_url(authority_base_url),
                index_url=self._index_url(index_url),
            )
        )
        _raise_if_failed(response, operation="resolve_deployment_artifact")
        return _sdk_receipt(response)

    def _authority_base_url(self, override: str | None) -> str | None:
        return override if override is not None else self.authority_base_url

    def _index_url(self, override: str | None) -> str | None:
        return override if override is not None else self.index_url


def _sdk_receipt(
    response: ResolveDeploymentArtifactResponse,
) -> HubDeploymentArtifactResolveReceipt:
    return HubDeploymentArtifactResolveReceipt(
        artifact_lock=HubDeploymentArtifactLock(
            artifact_family=response.artifact_lock.artifact_family,
            artifact_key=response.artifact_lock.artifact_key,
            channel=response.artifact_lock.channel,
            revision_id=response.artifact_lock.revision_id,
            payload_url=response.artifact_lock.payload_url,
            payload_sha256=response.artifact_lock.payload_sha256,
            payload_contract_version=(
                response.artifact_lock.payload_contract_version
            ),
        ),
        target=HubDeploymentArtifactTarget(
            selector_key=response.target.selector_key,
            target_ref=response.target.target_ref,
            node_package_name=response.target.node_package_name,
        ),
        producer=HubDeploymentArtifactProducerProvenance(
            producer_kind=response.producer.producer_kind,
            producer_revision_id=response.producer.producer_revision_id,
            source_revision_id=response.producer.source_revision_id,
            source_revision_kind=response.producer.source_revision_kind,
            materialization_ref=response.producer.materialization_ref,
            build_ref=response.producer.build_ref,
        ),
        authority_source_url=response.authority_source_url,
        request_id=response.request_id,
        info=response.info,
    )


def _raise_if_failed(response: object, *, operation: str) -> None:
    success = getattr(response, "success", True)
    if success:
        return
    error = getattr(response, "error", None)
    info = getattr(response, "info", None)
    detail = error or info or "unknown error"
    raise HubSdkError(f"Hub SDK {operation} failed: {detail}")


__all__ = [
    "HubDeploymentArtifactClient",
    "HubGeneratedDeploymentArtifactApiClient",
]
