from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from aware_hub_service_dto.hub.view.channel_heads import (
    HubPublicDiscoveryArtifactLockV1,
    HubPublicDiscoveryDescriptorV1,
    HubPublicDiscoveryEntryV1,
    HubPublicDiscoveryViewStateV1,
)
from pydantic import BaseModel, ConfigDict, Field

from aware_hub_sdk.code_package import HubCodeLanguage, HubCodePackageSurface

HUB_CHANNEL_HEADS_API_VIEW_REF = "hub.channel_heads"
HUB_CHANNEL_HEADS_PROJECTION_VIEW_KEY = "home.channel_heads.v1"


class ViewProviderProvenanceV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    source_kind: str | None = Field(default="hub_service_api")
    authority_source_url: str | None = Field(default=None)
    request_id: str | None = Field(default=None)
    branch_id: str | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    state_provider_ref: str | None = Field(default=None)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class HubPublicDiscoveryV1ProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    receipt: Any | None = Field(default=None)
    query: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    language: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    channel: str | None = Field(default=None)
    limit: int = Field(default=50)
    error: str | None = Field(default=None)
    provenance: ViewProviderProvenanceV1 = Field(
        default_factory=ViewProviderProvenanceV1
    )

    def to_json(self) -> dict[str, Any]:
        payload = self.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"receipt"},
        )
        if self.receipt is not None:
            payload["has_receipt"] = True
        return payload


class HubPublicDiscoveryCodePackageClient(Protocol):
    async def discover_channel_heads(
        self,
        *,
        query: str | None = None,
        package_name: str | None = None,
        language: HubCodeLanguage | None = None,
        surface: HubCodePackageSurface | None = None,
        channel: str | None = None,
        authority_base_url: str | None = None,
        index_url: str | None = None,
        limit: int = 50,
        request_id: UUID | None = None,
    ) -> object: ...


async def hub_public_discovery_v1_provider_input_from_client(
    *,
    client: HubPublicDiscoveryCodePackageClient,
    query: str | None = None,
    package_name: str | None = None,
    language: HubCodeLanguage | None = None,
    surface: HubCodePackageSurface | None = None,
    channel: str | None = None,
    authority_base_url: str | None = None,
    index_url: str | None = None,
    limit: int = 50,
    request_id: UUID | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
    raise_errors: bool = False,
) -> HubPublicDiscoveryV1ProviderInput:
    base_provenance = _provider_provenance(provenance)
    try:
        receipt = await client.discover_channel_heads(
            query=query,
            package_name=package_name,
            language=language,
            surface=surface,
            channel=channel,
            authority_base_url=authority_base_url,
            index_url=index_url,
            limit=limit,
            request_id=request_id,
        )
    except Exception as exc:
        if raise_errors:
            raise
        return HubPublicDiscoveryV1ProviderInput(
            query=query,
            package_name=package_name,
            language=_enum_value(language),
            surface=_enum_value(surface),
            channel=channel,
            limit=limit,
            error=str(exc),
            provenance=base_provenance,
        )

    return HubPublicDiscoveryV1ProviderInput(
        receipt=receipt,
        query=query,
        package_name=package_name,
        language=_enum_value(language),
        surface=_enum_value(surface),
        channel=channel,
        limit=limit,
        provenance=_provider_provenance(
            {
                **base_provenance.to_json(),
                "authority_source_url": _optional_text(
                    _field(receipt, "authority_source_url")
                )
                or base_provenance.authority_source_url,
                "request_id": _optional_text(_field(receipt, "request_id"))
                or base_provenance.request_id,
            }
        ),
    )


def hub_public_discovery_v1_provider_input(
    provider_context: object,
) -> HubPublicDiscoveryV1ProviderInput:
    receipt = _context_value(
        provider_context,
        "hub_public_discovery_receipt",
        "hub_code_package_discovery_receipt",
        "discovery_receipt",
        "receipt",
    )
    error = _optional_text(
        _context_value(provider_context, "hub_public_discovery_error", "error")
    )
    return HubPublicDiscoveryV1ProviderInput(
        receipt=receipt,
        query=_optional_text(_context_value(provider_context, "query")),
        package_name=_optional_text(_context_value(provider_context, "package_name")),
        language=_optional_text(_context_value(provider_context, "language")),
        surface=_optional_text(_context_value(provider_context, "surface")),
        channel=_optional_text(_context_value(provider_context, "channel")),
        limit=_optional_int(_context_value(provider_context, "limit")) or 50,
        error=error,
        provenance=_provider_provenance(
            _mapping_payload(_context_value(provider_context, "provenance"))
        ),
    )


def hub_public_discovery_view_state_from_input(
    provider_input: HubPublicDiscoveryV1ProviderInput | Mapping[str, Any],
) -> HubPublicDiscoveryViewStateV1:
    typed_input = HubPublicDiscoveryV1ProviderInput.model_validate(provider_input)
    entries = [
        _discovery_entry(entry) for entry in _receipt_entries(typed_input.receipt)
    ]
    status = _view_status(typed_input, entries)
    return HubPublicDiscoveryViewStateV1(
        status=status,
        authority_source_url=_authority_source_url(typed_input),
        query=typed_input.query,
        package_name=typed_input.package_name,
        language=typed_input.language,
        surface=typed_input.surface,
        channel=typed_input.channel,
        limit=typed_input.limit,
        entries=entries,
        summary=_summary(entries, status=status),
        error=typed_input.error,
        provenance=_provenance_payload(typed_input, entries=entries),
    )


def hub_public_discovery_view_state(
    *,
    provider_input: HubPublicDiscoveryV1ProviderInput | Mapping[str, Any],
) -> HubPublicDiscoveryViewStateV1:
    return hub_public_discovery_view_state_from_input(provider_input)


setattr(
    hub_public_discovery_view_state,
    "provider_input_resolver",
    hub_public_discovery_v1_provider_input,
)


def _discovery_entry(entry: object) -> HubPublicDiscoveryEntryV1:
    channel_head = _field(entry, "channel_head") or entry
    descriptor = _field(entry, "descriptor")
    artifact_lock = _field(entry, "artifact_lock")
    package_name = _optional_text(_field(channel_head, "package_name"))
    language = _enum_value(_field(channel_head, "language"))
    surface = _enum_value(_field(channel_head, "surface"))
    channel = _optional_text(_field(channel_head, "channel")) or "stable"
    revision_id = _optional_text(_field(channel_head, "revision_id"))
    return HubPublicDiscoveryEntryV1(
        package_name=package_name,
        language=language,
        surface=surface,
        channel=channel,
        revision_id=revision_id,
        updated_at=_optional_text(_field(channel_head, "updated_at")),
        publisher_execution_id=_optional_text(
            _field(channel_head, "publisher_execution_id")
        ),
        idempotency_key=_optional_text(_field(channel_head, "idempotency_key")),
        metadata=_metadata(_field(channel_head, "metadata")),
        descriptor=_descriptor(descriptor),
        artifact_lock=_artifact_lock(artifact_lock),
        refs={
            key: value
            for key, value in {
                "package_name": package_name,
                "language": language,
                "surface": surface,
                "channel": channel,
                "revision_id": revision_id,
            }.items()
            if value is not None
        },
    )


def _descriptor(descriptor: object | None) -> HubPublicDiscoveryDescriptorV1 | None:
    if descriptor is None:
        return None
    return HubPublicDiscoveryDescriptorV1(
        package_name=_optional_text(_field(descriptor, "package_name")),
        language=_enum_value(_field(descriptor, "language")),
        surface=_enum_value(_field(descriptor, "surface")),
        manifest_kind=_enum_value(_field(descriptor, "manifest_kind")),
        version=_optional_text(_field(descriptor, "version")),
        revision_id=_optional_text(_field(descriptor, "revision_id")),
        digest=_optional_text(_field(descriptor, "digest")),
        package_root=_optional_text(_field(descriptor, "package_root")),
        sources_root=_optional_text(_field(descriptor, "sources_root")),
        fqn_prefix=_optional_text(_field(descriptor, "fqn_prefix")),
        manifest_relative_path=_optional_text(
            _field(descriptor, "manifest_relative_path")
        ),
        artifact_media_type=_optional_text(_field(descriptor, "artifact_media_type")),
        artifact_size_bytes=_optional_int(_field(descriptor, "artifact_size_bytes")),
        download_handle=_optional_text(_field(descriptor, "download_handle")),
        metadata=_metadata(_field(descriptor, "metadata")),
    )


def _artifact_lock(lock: object | None) -> HubPublicDiscoveryArtifactLockV1 | None:
    if lock is None:
        return None
    return HubPublicDiscoveryArtifactLockV1(
        artifact_url=_optional_text(_field(lock, "artifact_url")),
        sha256=_optional_text(_field(lock, "sha256")),
        size_bytes=_optional_int(_field(lock, "size_bytes")),
        media_type=_optional_text(_field(lock, "media_type")),
        archive_format=_optional_text(_field(lock, "archive_format")),
        revision_id=_optional_text(_field(lock, "revision_id")),
        published_at=_optional_text(_field(lock, "published_at")),
    )


def _receipt_entries(receipt: object | None) -> list[object]:
    value = _field(receipt, "entries") if receipt is not None else None
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _view_status(
    typed_input: HubPublicDiscoveryV1ProviderInput,
    entries: list[HubPublicDiscoveryEntryV1],
) -> str:
    if typed_input.error:
        return "error"
    if entries:
        return "ready"
    if typed_input.receipt is not None:
        return "empty"
    return "waiting"


def _authority_source_url(typed_input: HubPublicDiscoveryV1ProviderInput) -> str | None:
    return (
        _optional_text(_field(typed_input.receipt, "authority_source_url"))
        or typed_input.provenance.authority_source_url
    )


def _summary(entries: list[HubPublicDiscoveryEntryV1], *, status: str) -> str:
    if status == "waiting":
        return "Waiting for Hub discovery"
    if status == "error":
        return "Hub discovery unavailable"
    count = len(entries)
    if count == 1:
        return "1 public channel head"
    return f"{count} public channel heads"


def _provenance_payload(
    typed_input: HubPublicDiscoveryV1ProviderInput,
    *,
    entries: list[HubPublicDiscoveryEntryV1],
) -> dict[str, Any]:
    payload = typed_input.provenance.to_json()
    payload["view_ref"] = HUB_CHANNEL_HEADS_API_VIEW_REF
    payload["projection_view_key"] = HUB_CHANNEL_HEADS_PROJECTION_VIEW_KEY
    payload["state_provider_ref"] = (
        "aware_hub_sdk.view_state_providers.hub_public_discovery_view_state"
    )
    payload["entry_count"] = len(entries)
    authority_source_url = _authority_source_url(typed_input)
    if authority_source_url is not None:
        payload["authority_source_url"] = authority_source_url
    request_id = _optional_text(_field(typed_input.receipt, "request_id"))
    if request_id is not None:
        payload["request_id"] = request_id
    return payload


def _provider_provenance(
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None,
) -> ViewProviderProvenanceV1:
    if isinstance(provenance, ViewProviderProvenanceV1):
        return provenance
    return ViewProviderProvenanceV1.model_validate(dict(provenance or {}))


def _context_value(provider_context: object, *names: str) -> object | None:
    if isinstance(provider_context, Mapping):
        for name in names:
            if name in provider_context:
                return provider_context[name]
        return None
    for name in names:
        if hasattr(provider_context, name):
            return getattr(provider_context, name)
    return None


def _field(value: object | None, name: str) -> object | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _mapping_payload(value: object | None) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _enum_value(value: object | None) -> str | None:
    if isinstance(value, Enum):
        return str(value.value)
    return _optional_text(value)


def _metadata(value: object | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object | None) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


__all__ = [
    "HubPublicDiscoveryCodePackageClient",
    "HubPublicDiscoveryV1ProviderInput",
    "ViewProviderProvenanceV1",
    "hub_public_discovery_v1_provider_input",
    "hub_public_discovery_v1_provider_input_from_client",
    "hub_public_discovery_view_state",
    "hub_public_discovery_view_state_from_input",
]
