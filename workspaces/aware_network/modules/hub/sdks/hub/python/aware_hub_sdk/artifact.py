from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Protocol, cast
from urllib.request import urlopen
from uuid import UUID

from aware_hub_service_dto.hub.artifact_authority import (
    HubArtifactPayloadLock as ApiHubArtifactPayloadLock,
)
from aware_hub_service_dto.hub.artifact_authority import (
    HubArtifactProducerProvenance as ApiHubArtifactProducerProvenance,
)
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

from aware_hub_sdk.code_package import HubSdkError
from aware_hub_sdk.models import (
    HubArtifactPayloadLock,
    HubArtifactJsonResolveReceipt,
    HubArtifactProducerProvenance,
    HubArtifactPublishReceipt,
    HubArtifactResolveReceipt,
)


class _HubArtifactApiClient(Protocol):
    async def publish(
        self,
        request: PublishHubArtifactRequest,
    ) -> PublishHubArtifactResponse: ...

    async def resolve(
        self,
        request: ResolveHubArtifactRequest,
    ) -> ResolveHubArtifactResponse: ...


class _HubArtifactNamespaceClient(Protocol):
    @property
    def artifact(self) -> _HubArtifactApiClient: ...


class HubGeneratedArtifactApiClient(Protocol):
    @property
    def hub(self) -> _HubArtifactNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class HubArtifactClient:
    api_client: HubGeneratedArtifactApiClient
    authority_base_url: str | None = None
    index_url: str | None = None

    async def publish(
        self,
        *,
        artifact_family: str,
        artifact_key: str,
        revision_id: str,
        channel: str = "stable",
        authority_base_url: str | None = None,
        index_url: str | None = None,
        payload_url: str | None = None,
        payload_sha256: str | None = None,
        payload_size_bytes: int | None = None,
        payload_media_type: str | None = None,
        payload_contract: str | None = None,
        payload_json: Mapping[str, object] | None = None,
        payload_bytes_base64: str | None = None,
        payload_source_url: str | None = None,
        selector_key: str | None = None,
        target_ref: str | None = None,
        producer: HubArtifactProducerProvenance | Mapping[str, object] | None = None,
        publisher_execution_id: str | None = None,
        idempotency_key: str | None = None,
        published_at_utc: str | None = None,
        metadata: Mapping[str, object] | None = None,
        request_id: UUID | None = None,
    ) -> HubArtifactPublishReceipt:
        response = await self.api_client.hub.artifact.publish(
            PublishHubArtifactRequest(
                request_id=request_id,
                artifact_family=artifact_family,
                artifact_key=artifact_key,
                revision_id=revision_id,
                channel=channel,
                authority_base_url=self._authority_base_url(authority_base_url),
                index_url=self._index_url(index_url),
                payload_url=payload_url,
                payload_sha256=payload_sha256,
                payload_size_bytes=payload_size_bytes,
                payload_media_type=payload_media_type,
                payload_contract=payload_contract,
                payload_json=(
                    cast(Any, dict(payload_json or {}))
                    if payload_json is not None
                    else None
                ),
                payload_bytes_base64=payload_bytes_base64,
                payload_source_url=payload_source_url,
                selector_key=selector_key,
                target_ref=target_ref,
                producer=_api_producer(producer),
                publisher_execution_id=publisher_execution_id,
                idempotency_key=idempotency_key,
                published_at_utc=published_at_utc,
                metadata=cast(Any, dict(metadata or {})),
            )
        )
        _raise_if_failed(response, operation="publish_hub_artifact")
        return HubArtifactPublishReceipt(
            artifact_lock=_sdk_lock(response.artifact_lock),
            producer=_sdk_producer(response.producer),
            authority_source_url=response.authority_source_url,
            accepted=response.accepted,
            request_id=response.request_id,
            info=response.info,
        )

    async def resolve(
        self,
        *,
        artifact_family: str,
        artifact_key: str,
        channel: str = "stable",
        revision_id: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        request_id: UUID | None = None,
    ) -> HubArtifactResolveReceipt:
        response = await self.api_client.hub.artifact.resolve(
            ResolveHubArtifactRequest(
                request_id=request_id,
                artifact_family=artifact_family,
                artifact_key=artifact_key,
                channel=channel,
                revision_id=revision_id,
                authority_base_url=self._authority_base_url(authority_base_url),
                index_url=self._index_url(index_url),
            )
        )
        _raise_if_failed(response, operation="resolve_hub_artifact")
        return HubArtifactResolveReceipt(
            artifact_lock=_sdk_lock(response.artifact_lock),
            producer=_sdk_producer(response.producer),
            authority_source_url=response.authority_source_url,
            request_id=response.request_id,
            info=response.info,
        )

    async def resolve_json_payload(
        self,
        *,
        artifact_family: str,
        artifact_key: str,
        channel: str = "stable",
        revision_id: str | None = None,
        expected_payload_contract: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        request_id: UUID | None = None,
        max_payload_bytes: int = 8 * 1024 * 1024,
        read_timeout_s: float = 30.0,
    ) -> HubArtifactJsonResolveReceipt:
        """Resolve and verify one immutable JSON payload without writing it locally."""

        receipt = await self.resolve(
            artifact_family=artifact_family,
            artifact_key=artifact_key,
            channel=channel,
            revision_id=revision_id,
            authority_base_url=authority_base_url,
            index_url=index_url,
            request_id=request_id,
        )
        lock = receipt.artifact_lock
        if expected_payload_contract is not None and (
            lock.payload_contract != expected_payload_contract
        ):
            raise HubSdkError(
                "Hub artifact payload contract mismatch: "
                f"expected {expected_payload_contract!r} "
                f"actual {lock.payload_contract!r}."
            )
        if max_payload_bytes <= 0:
            raise HubSdkError("Hub artifact max_payload_bytes must be positive.")
        if read_timeout_s <= 0:
            raise HubSdkError("Hub artifact read_timeout_s must be positive.")
        if (
            lock.payload_size_bytes is not None
            and lock.payload_size_bytes > max_payload_bytes
        ):
            raise HubSdkError(
                "Hub artifact payload exceeds the configured size bound: "
                f"size={lock.payload_size_bytes} max={max_payload_bytes}."
            )
        try:
            with urlopen(  # noqa: S310
                lock.payload_url,
                timeout=read_timeout_s,
            ) as response:
                payload_bytes = response.read(max_payload_bytes + 1)
        except Exception as exc:
            raise HubSdkError(
                f"Hub artifact payload read failed for {lock.payload_url!r}: {exc}"
            ) from exc
        if len(payload_bytes) > max_payload_bytes:
            raise HubSdkError(
                "Hub artifact payload exceeds the configured size bound: "
                f"max={max_payload_bytes}."
            )
        if (
            lock.payload_size_bytes is not None
            and len(payload_bytes) != lock.payload_size_bytes
        ):
            raise HubSdkError(
                "Hub artifact payload size mismatch: "
                f"expected {lock.payload_size_bytes} actual {len(payload_bytes)}."
            )
        actual_digest = hashlib.sha256(payload_bytes).hexdigest()
        if actual_digest != lock.payload_sha256:
            raise HubSdkError(
                "Hub artifact payload digest mismatch: "
                f"expected {lock.payload_sha256!r} actual {actual_digest!r}."
            )
        try:
            payload = json.loads(payload_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HubSdkError("Hub artifact payload is not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise HubSdkError("Hub artifact JSON payload must be an object.")
        return HubArtifactJsonResolveReceipt(
            artifact_lock=lock,
            payload=cast(Mapping[str, object], payload),
            authority_source_url=receipt.authority_source_url,
            producer=receipt.producer,
            request_id=receipt.request_id,
            info=receipt.info,
        )

    def _authority_base_url(self, override: str | None) -> str | None:
        return override if override is not None else self.authority_base_url

    def _index_url(self, override: str | None) -> str | None:
        return override if override is not None else self.index_url


def _api_producer(
    producer: HubArtifactProducerProvenance | Mapping[str, object] | None,
) -> ApiHubArtifactProducerProvenance | None:
    if producer is None:
        return None
    if isinstance(producer, HubArtifactProducerProvenance):
        payload = {
            "producer_kind": producer.producer_kind,
            "producer_key": producer.producer_key,
            "provenance_key": producer.provenance_key,
            "producer_revision_id": producer.producer_revision_id,
            "source_revision_id": producer.source_revision_id,
            "source_revision_kind": producer.source_revision_kind,
            "materialization_ref": producer.materialization_ref,
            "build_ref": producer.build_ref,
            "metadata": dict(producer.metadata),
        }
    else:
        payload = dict(producer)
    return ApiHubArtifactProducerProvenance.model_validate(payload)


def _sdk_lock(lock: ApiHubArtifactPayloadLock) -> HubArtifactPayloadLock:
    return HubArtifactPayloadLock(
        artifact_family=lock.artifact_family,
        artifact_key=lock.artifact_key,
        channel=lock.channel,
        revision_id=lock.revision_id,
        payload_url=lock.payload_url,
        payload_sha256=lock.payload_sha256,
        payload_size_bytes=lock.payload_size_bytes,
        payload_media_type=lock.payload_media_type,
        payload_contract=lock.payload_contract,
        authority_source_url=lock.authority_source_url,
        selector_key=lock.selector_key,
        target_ref=lock.target_ref,
        metadata=dict(lock.metadata),
    )


def _sdk_producer(
    producer: ApiHubArtifactProducerProvenance | None,
) -> HubArtifactProducerProvenance | None:
    if producer is None:
        return None
    return HubArtifactProducerProvenance(
        producer_kind=producer.producer_kind,
        producer_key=producer.producer_key,
        provenance_key=producer.provenance_key,
        producer_revision_id=producer.producer_revision_id,
        source_revision_id=producer.source_revision_id,
        source_revision_kind=producer.source_revision_kind,
        materialization_ref=producer.materialization_ref,
        build_ref=producer.build_ref,
        metadata=dict(producer.metadata),
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
    "HubArtifactClient",
    "HubGeneratedArtifactApiClient",
]
