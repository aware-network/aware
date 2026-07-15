from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast
from uuid import UUID

from aware_content_service_dto.content.content_service_operation import (
    CommitContentTextRequest,
    CommitContentTextResponse,
    ContentTextCommitPartV1,
    ContentPackageExportDocumentV1,
    MaterializeContentPackageRequest,
    MaterializeContentPackageResponse,
    ResolveContentTextRequest,
    ResolveContentTextResponse,
)


class ContentSdkError(RuntimeError):
    pass


class ContentTextCapabilityClient(Protocol):
    async def commit_content_text(
        self,
        request: CommitContentTextRequest,
    ) -> CommitContentTextResponse: ...

    async def resolve_content_text(
        self,
        request: ResolveContentTextRequest,
    ) -> ResolveContentTextResponse: ...


class ContentPackageCapabilityClient(Protocol):
    async def materialize_content_package(
        self,
        request: MaterializeContentPackageRequest,
    ) -> MaterializeContentPackageResponse: ...


class ContentApiNamespaceClient(Protocol):
    @property
    def package(self) -> ContentPackageCapabilityClient: ...

    @property
    def text(self) -> ContentTextCapabilityClient: ...


class ContentGeneratedApiClient(Protocol):
    @property
    def content(self) -> ContentApiNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class AwareContentSdk:
    api_client: ContentGeneratedApiClient

    async def resolve_content_text(
        self,
        *,
        content_id: UUID | None = None,
        content_class_instance_identity_id: UUID | None = None,
        content_class_config_id: UUID | None = None,
        actor_id: UUID | None = None,
        branch_id: UUID | None = None,
        media_type: str = "text/plain",
        include_parts: bool = True,
        max_chars: int | None = None,
    ) -> ResolveContentTextResponse:
        response = await self.api_client.content.text.resolve_content_text(
            ResolveContentTextRequest(
                actor_id=actor_id,
                branch_id=branch_id,
                content_id=content_id,
                content_class_instance_identity_id=content_class_instance_identity_id,
                content_class_config_id=content_class_config_id,
                media_type=media_type,
                include_parts=include_parts,
                max_chars=max_chars,
            )
        )
        _raise_if_failed(response, operation="resolve_content_text")
        if response.resolution is None:
            raise ContentSdkError(
                "Content resolve_content_text response is missing resolution."
            )
        return response

    async def commit_content_text(
        self,
        *,
        content_key: str,
        source_kind: str,
        source_ref: str,
        actor_id: UUID | None = None,
        branch_id: UUID | None = None,
        title: str | None = None,
        media_type: str = "text/plain",
        text: str | None = None,
        parts: list[ContentTextCommitPartV1] | None = None,
        digest_algorithm: str = "sha256",
        digest: str | None = None,
        size_bytes: int | None = None,
        provenance: Mapping[str, object] | None = None,
    ) -> CommitContentTextResponse:
        response = await self.api_client.content.text.commit_content_text(
            CommitContentTextRequest(
                actor_id=actor_id,
                branch_id=branch_id,
                content_key=content_key,
                title=title,
                source_kind=source_kind,
                source_ref=source_ref,
                media_type=media_type,
                text=text,
                parts=list(parts or ()),
                digest_algorithm=digest_algorithm,
                digest=digest,
                size_bytes=size_bytes,
                provenance=cast(Any, dict(provenance or {})),
            )
        )
        _raise_if_failed(response, operation="commit_content_text")
        if response.commit_result is None:
            raise ContentSdkError(
                "Content commit_content_text response is missing commit_result."
            )
        return _commit_text_response_with_transport_receipt_evidence(
            response=response,
            api_client=self.api_client,
        )

    async def materialize_content_package(
        self,
        *,
        package_export: ContentPackageExportDocumentV1,
        actor_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> MaterializeContentPackageResponse:
        response = await self.api_client.content.package.materialize_content_package(
            MaterializeContentPackageRequest(
                actor_id=actor_id,
                branch_id=branch_id,
                package_export=package_export,
            )
        )
        _raise_if_failed(response, operation="materialize_content_package")
        if response.materialization is None:
            raise ContentSdkError(
                "Content materialize_content_package response is missing materialization."
            )
        return _materialize_response_with_transport_receipt_evidence(
            response=response,
            api_client=self.api_client,
        )


def build_content_sdk(*, api_client: ContentGeneratedApiClient) -> AwareContentSdk:
    return AwareContentSdk(api_client=api_client)


def _raise_if_failed(response: object, *, operation: str) -> None:
    success = bool(getattr(response, "success", False))
    if success:
        return
    error = getattr(response, "error", None) or f"Content SDK {operation} failed."
    raise ContentSdkError(str(error))


def _materialize_response_with_transport_receipt_evidence(
    *,
    response: MaterializeContentPackageResponse,
    api_client: object,
) -> MaterializeContentPackageResponse:
    receipt_payload = _service_host_transport_receipt_payload(api_client)
    if not receipt_payload or response.materialization is None:
        return response
    domain_commit_id = _first_uuid(
        receipt_payload,
        (
            "domain_commit_id",
            "service_operation_commit_id",
            "api_call_outcome_commit_id",
        ),
    )
    service_host_receipt_ref = _first_text(
        receipt_payload,
        (
            "service_host_receipt_ref",
            "receipt_ref",
            "api_dispatch_receipt_ref",
        ),
    ) or _service_host_receipt_ref(receipt_payload)
    if domain_commit_id is None and service_host_receipt_ref is None:
        return response

    materialization = response.materialization
    materialization_update: dict[str, Any] = {
        "domain_commit_id": materialization.domain_commit_id or domain_commit_id,
        "service_host_receipt_ref": (
            materialization.service_host_receipt_ref or service_host_receipt_ref
        ),
        "provenance": _merge_mapping(
            materialization.provenance,
            {
                "service_host_transport_receipt": dict(receipt_payload),
            },
        ),
    }
    updated_artifact_refs = [
        artifact_ref.model_copy(
            update={
                "domain_commit_id": artifact_ref.domain_commit_id
                or materialization_update["domain_commit_id"],
                "service_host_receipt_ref": artifact_ref.service_host_receipt_ref
                or materialization_update["service_host_receipt_ref"],
            }
        )
        for artifact_ref in materialization.artifact_refs
    ]
    materialization_update["artifact_refs"] = updated_artifact_refs
    updated_materialization = materialization.model_copy(update=materialization_update)

    receipt = response.receipt
    receipt_update = {}
    if receipt is not None:
        receipt_update = {
            "domain_commit_id": receipt.domain_commit_id
            or materialization_update["domain_commit_id"],
            "service_host_receipt_ref": receipt.service_host_receipt_ref
            or materialization_update["service_host_receipt_ref"],
            "metadata": _merge_mapping(
                receipt.metadata,
                {
                    "service_host_transport_receipt": dict(receipt_payload),
                },
            ),
        }
    return response.model_copy(
        update={
            "materialization": updated_materialization,
            "receipt": receipt.model_copy(update=receipt_update)
            if receipt is not None
            else None,
        }
    )


def _commit_text_response_with_transport_receipt_evidence(
    *,
    response: CommitContentTextResponse,
    api_client: object,
) -> CommitContentTextResponse:
    receipt_payload = _service_host_transport_receipt_payload(api_client)
    commit_result = response.commit_result
    if not receipt_payload or commit_result is None:
        return response
    domain_commit_id = _first_uuid(
        receipt_payload,
        (
            "domain_commit_id",
            "service_operation_commit_id",
            "api_call_outcome_commit_id",
        ),
    )
    service_host_receipt_ref = _first_text(
        receipt_payload,
        (
            "service_host_receipt_ref",
            "receipt_ref",
            "api_dispatch_receipt_ref",
        ),
    ) or _service_host_receipt_ref(receipt_payload)
    updated_result = commit_result.model_copy(
        update={
            "domain_commit_id": commit_result.domain_commit_id or domain_commit_id,
            "service_host_receipt_ref": (
                commit_result.service_host_receipt_ref or service_host_receipt_ref
            ),
            "provenance": _merge_mapping(
                commit_result.provenance,
                {"service_host_transport_receipt": dict(receipt_payload)},
            ),
        }
    )
    receipt = response.receipt
    updated_receipt = (
        receipt.model_copy(
            update={
                "domain_commit_id": receipt.domain_commit_id
                or updated_result.domain_commit_id,
                "service_host_receipt_ref": receipt.service_host_receipt_ref
                or updated_result.service_host_receipt_ref,
                "metadata": _merge_mapping(
                    receipt.metadata,
                    {"service_host_transport_receipt": dict(receipt_payload)},
                ),
            }
        )
        if receipt is not None
        else None
    )
    return response.model_copy(
        update={"commit_result": updated_result, "receipt": updated_receipt}
    )


def _service_host_transport_receipt_payload(api_client: object) -> dict[str, object]:
    invoker = getattr(api_client, "_client", None) or getattr(api_client, "client", None)
    diagnostics = getattr(invoker, "last_invocation_diagnostics", None)
    transport_receipt = getattr(diagnostics, "transport_receipt", None)
    if isinstance(transport_receipt, Mapping):
        return dict(transport_receipt)
    return {}


def _first_uuid(payload: Mapping[str, object], keys: tuple[str, ...]) -> UUID | None:
    for key in keys:
        resolved = _uuid_or_none(payload.get(key))
        if resolved is not None:
            return resolved
    return None


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None or value == "":
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _first_text(payload: Mapping[str, object], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = _optional_text(payload.get(key))
        if value is not None:
            return value
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _service_host_receipt_ref(payload: Mapping[str, object]) -> str | None:
    for prefix, key in (
        ("service-host", "network_request_id"),
        ("service-api-call", "api_call_id"),
        ("service-operation-commit", "service_operation_commit_id"),
        ("api-call-outcome-commit", "api_call_outcome_commit_id"),
    ):
        value = _optional_text(payload.get(key))
        if value is not None:
            return f"{prefix}:{value}"
    return None


def _merge_mapping(
    base: Mapping[str, object],
    overlay: Mapping[str, object],
) -> dict[str, object]:
    merged = dict(base)
    merged.update(overlay)
    return merged


__all__ = [
    "AwareContentSdk",
    "ContentApiNamespaceClient",
    "ContentGeneratedApiClient",
    "ContentPackageCapabilityClient",
    "ContentSdkError",
    "ContentTextCapabilityClient",
    "build_content_sdk",
]
