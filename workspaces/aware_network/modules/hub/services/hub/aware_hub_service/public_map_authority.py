"""Hub-owned public map discovery over package authority truth."""

from __future__ import annotations

import json
from collections.abc import Mapping
from enum import Enum
from typing import cast

from aware_hub_service_dto.hub.public_map_discovery import (
    DiscoverPublicMapRequest,
)
from aware_hub_service_dto.hub.public_map_discovery import (
    DiscoverPublicMapResponse,
)
from aware_hub_service_dto.hub.public_map_discovery import HubPublicMapEntry
from aware_types import JsonObject, JsonValue

from .code_package_authority import (
    CodePackageDiscoveryEntry,
    DiscoverCodePackageChannelHeadsRequest,
    discover_code_package_channel_heads,
)

_SCAN_LIMIT = 1000


def discover_public_map(
    request: DiscoverPublicMapRequest,
) -> DiscoverPublicMapResponse:
    if request.limit <= 0:
        return DiscoverPublicMapResponse(
            request_id=request.request_id,
            entries=[],
        )

    code_package_response = discover_code_package_channel_heads(
        DiscoverCodePackageChannelHeadsRequest(
            request_id=request.request_id,
            package_name=request.package_name,
            channel=request.channel,
            authority_base_url=request.authority_base_url,
            index_url=request.index_url,
            limit=_scan_limit(request.limit),
        )
    )
    entries = [
        public_entry
        for public_entry in (
            _public_map_entry(entry) for entry in code_package_response.entries
        )
        if _matches_public_map_entry(public_entry, request)
    ]
    return DiscoverPublicMapResponse(
        request_id=request.request_id,
        authority_source_url=code_package_response.authority_source_url,
        entries=entries[: request.limit],
    )


def _scan_limit(limit: int) -> int:
    return max(min(_SCAN_LIMIT, limit * 20), limit)


def _public_map_entry(entry: CodePackageDiscoveryEntry) -> HubPublicMapEntry:
    head = entry.channel_head
    descriptor = entry.descriptor
    artifact_lock = entry.artifact_lock
    metadata = _entry_metadata(entry)
    package_name = (
        descriptor.package_name if descriptor is not None else head.package_name
    )
    artifact_family = _artifact_family(metadata)
    return HubPublicMapEntry(
        artifact_family=artifact_family,
        artifact_key=_metadata_str(metadata, "artifact_key") or package_name,
        channel=head.channel,
        revision_id=(
            head.revision_id
            or _optional_attr(descriptor, "revision_id")
            or _optional_attr(artifact_lock, "revision_id")
        ),
        package_name=package_name,
        language=_enum_or_str(_optional_attr(descriptor, "language") or head.language),
        surface=_enum_or_str(_optional_attr(descriptor, "surface") or head.surface),
        manifest_kind=_enum_or_str(_optional_attr(descriptor, "manifest_kind")),
        digest=(
            _optional_attr(descriptor, "digest")
            or _optional_attr(artifact_lock, "sha256")
        ),
        artifact_url=_optional_attr(artifact_lock, "artifact_url"),
        artifact_sha256=_optional_attr(artifact_lock, "sha256"),
        artifact_size_bytes=(
            _optional_int_attr(artifact_lock, "size_bytes")
            or _optional_int_attr(descriptor, "artifact_size_bytes")
        ),
        media_type=(
            _optional_attr(artifact_lock, "media_type")
            or _optional_attr(descriptor, "artifact_media_type")
        ),
        title=_metadata_str(metadata, "title", "display_name", "name"),
        summary=_metadata_str(metadata, "summary", "description"),
        experience_name=_metadata_str(
            metadata,
            "experience_name",
            "experience_package_name",
            "experience",
        ),
        fqn_prefix=_optional_attr(descriptor, "fqn_prefix"),
        producer_kind=_metadata_str(metadata, "producer_kind", "producer"),
        producer_revision_id=_metadata_str(metadata, "producer_revision_id"),
        source_revision_id=_metadata_str(metadata, "source_revision_id"),
        visibility=_metadata_str(metadata, "visibility") or "public",
        metadata=JsonObject(metadata),
    )


def _entry_metadata(entry: CodePackageDiscoveryEntry) -> dict[str, JsonValue]:
    descriptor_metadata = (
        dict(entry.descriptor.metadata) if entry.descriptor is not None else {}
    )
    channel_head_metadata = dict(entry.channel_head.metadata or {})
    metadata: dict[str, object] = dict(descriptor_metadata)
    if channel_head_metadata:
        metadata["channel_head"] = channel_head_metadata
    return dict(JsonObject(cast(dict[str, JsonValue], metadata)))


def _artifact_family(metadata: Mapping[str, object]) -> str:
    explicit_family = _metadata_str(
        metadata,
        "artifact_family",
        "hub_artifact_family",
    )
    if explicit_family:
        return explicit_family
    kind = _metadata_str(metadata, "kind", "package_kind")
    return {
        "experience": "experience-package",
        "semantic": "semantic-package",
        "workspace": "workspace-revision",
        "kernel": "kernel-revision",
        "interface": "interface-package",
        "service": "service-package",
    }.get(kind or "", "code-package")


def _matches_public_map_entry(
    entry: HubPublicMapEntry,
    request: DiscoverPublicMapRequest,
) -> bool:
    if not _matches_optional(entry.artifact_family, request.artifact_family):
        return False
    if not _matches_optional(entry.artifact_key, request.artifact_key):
        return False
    if not _matches_optional(entry.package_name, request.package_name):
        return False
    if not _matches_optional(entry.experience_name, request.experience_name):
        return False
    if not _matches_optional(entry.channel, request.channel):
        return False
    query = _clean(request.query).lower()
    if not query:
        return True
    return query in json.dumps(entry.model_dump(mode="json"), sort_keys=True).lower()


def _matches_optional(value: str | None, expected: str | None) -> bool:
    expected_value = _clean(expected)
    return not expected_value or value == expected_value


def _metadata_str(metadata: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str):
            clean_value = _clean(value)
            if clean_value:
                return clean_value
    return None


def _optional_attr(value: object | None, name: str) -> str | None:
    if value is None:
        return None
    attr = getattr(value, name, None)
    return _enum_or_str(attr)


def _optional_int_attr(value: object | None, name: str) -> int | None:
    if value is None:
        return None
    attr = getattr(value, name, None)
    return attr if isinstance(attr, int) else None


def _enum_or_str(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(cast(object, value.value))
    if isinstance(value, str):
        return value
    return str(value)


def _clean(value: str | None) -> str:
    return (value or "").strip()


__all__ = [
    "DiscoverPublicMapRequest",
    "DiscoverPublicMapResponse",
    "HubPublicMapEntry",
    "discover_public_map",
]
