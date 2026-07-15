"""Hub-owned generic artifact authority publish/resolve."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import urlopen

from aware_types import JsonObject
from aware_hub_service_dto.hub.artifact_authority import (
    HubArtifactPayloadLock,
)
from aware_hub_service_dto.hub.artifact_authority import (
    HubArtifactProducerProvenance,
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

HUB_ARTIFACT_AUTHORITY_KIND = "hub_artifact_distribution"
OIG_COMMIT_ARTIFACT_FAMILY = "oig-commit"
OIG_COMMIT_AUTHORITY_KIND = "oig_commit_payload_distribution"
DEFAULT_CHANNEL = "stable"

PublishHubArtifactRequest.model_rebuild(
    _types_namespace={"HubArtifactProducerProvenance": HubArtifactProducerProvenance}
)
PublishHubArtifactResponse.model_rebuild(
    _types_namespace={
        "HubArtifactPayloadLock": HubArtifactPayloadLock,
        "HubArtifactProducerProvenance": HubArtifactProducerProvenance,
    }
)
ResolveHubArtifactResponse.model_rebuild(
    _types_namespace={
        "HubArtifactPayloadLock": HubArtifactPayloadLock,
        "HubArtifactProducerProvenance": HubArtifactProducerProvenance,
    }
)


def publish_hub_artifact(
    request: PublishHubArtifactRequest,
) -> PublishHubArtifactResponse:
    family = _clean_required(request.artifact_family, "artifact_family")
    artifact_key = _clean_required(request.artifact_key, "artifact_key")
    revision_id = _clean_required(request.revision_id, "revision_id")
    channel = _clean(request.channel) or DEFAULT_CHANNEL
    index_url = _resolve_index_url(
        artifact_family=family,
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    index = _load_or_empty_index(index_url=index_url, artifact_family=family)

    payload_bytes = _request_payload_bytes(request)
    payload_media_type = _clean(request.payload_media_type)
    if payload_bytes is not None and not payload_media_type:
        payload_media_type = "application/json" if request.payload_json is not None else "application/octet-stream"
    payload_sha256 = _resolve_payload_sha256(
        expected_sha256=request.payload_sha256,
        payload_bytes=payload_bytes,
    )
    payload_size_bytes = _resolve_payload_size_bytes(
        expected_size=request.payload_size_bytes,
        payload_bytes=payload_bytes,
    )
    payload_url = _resolve_payload_url(
        artifact_family=family,
        authority_base_url=request.authority_base_url,
        index_url=index_url,
        payload_bytes=payload_bytes,
        payload_media_type=payload_media_type,
        payload_sha256=payload_sha256,
        requested_payload_url=request.payload_url,
    )

    producer = _producer_or_default(request.producer)
    artifact_lock = HubArtifactPayloadLock(
        artifact_family=family,
        artifact_key=artifact_key,
        channel=channel,
        revision_id=revision_id,
        payload_url=payload_url,
        payload_sha256=payload_sha256,
        payload_size_bytes=payload_size_bytes,
        payload_media_type=payload_media_type or None,
        payload_contract=_clean(request.payload_contract) or None,
        authority_source_url=index_url,
        selector_key=_clean(request.selector_key) or None,
        target_ref=_clean(request.target_ref) or None,
        metadata=JsonObject(request.metadata or {}),
    )
    updated_index = _with_published_artifact(
        index=index,
        artifact_lock=artifact_lock,
        producer=producer,
        publisher_execution_id=_clean(request.publisher_execution_id) or None,
        idempotency_key=_clean(request.idempotency_key) or None,
        published_at_utc=_clean(request.published_at_utc) or None,
    )
    _write_index(index_url=index_url, payload=updated_index)
    return PublishHubArtifactResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        artifact_lock=artifact_lock,
        producer=producer,
        accepted=True,
    )


def resolve_hub_artifact(
    request: ResolveHubArtifactRequest,
) -> ResolveHubArtifactResponse:
    family = _clean_required(request.artifact_family, "artifact_family")
    artifact_key = _clean_required(request.artifact_key, "artifact_key")
    channel = _clean(request.channel) or DEFAULT_CHANNEL
    index_url = _resolve_index_url(
        artifact_family=family,
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    index = _load_index(index_url=index_url, artifact_family=family)
    artifact = _resolve_artifact_entry(
        index=index,
        artifact_family=family,
        artifact_key=artifact_key,
        channel=channel,
        revision_id=_clean(request.revision_id) or None,
    )
    return ResolveHubArtifactResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        artifact_lock=artifact.lock,
        producer=artifact.producer,
    )


class _ResolvedArtifact:
    def __init__(
        self,
        *,
        lock: HubArtifactPayloadLock,
        producer: HubArtifactProducerProvenance | None,
    ) -> None:
        self.lock = lock
        self.producer = producer


def _request_payload_bytes(request: PublishHubArtifactRequest) -> bytes | None:
    payload_sources = [
        request.payload_json is not None,
        bool(_clean(request.payload_bytes_base64)),
        bool(_clean(request.payload_source_url)),
    ]
    if sum(1 for item in payload_sources if item) > 1:
        raise ValueError(
            "Hub artifact publish accepts only one payload source: "
            "payload_json, payload_bytes_base64, or payload_source_url."
        )
    if request.payload_json is not None:
        return json.dumps(
            request.payload_json,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    payload_base64 = _clean(request.payload_bytes_base64)
    if payload_base64:
        return base64.b64decode(payload_base64, validate=True)
    payload_source_url = _clean(request.payload_source_url)
    if payload_source_url:
        return _read_url_bytes(payload_source_url)
    return None


def _resolve_payload_sha256(
    *,
    expected_sha256: str | None,
    payload_bytes: bytes | None,
) -> str:
    expected = _clean(expected_sha256)
    if payload_bytes is None:
        return _clean_required(expected, "payload_sha256")
    actual = hashlib.sha256(payload_bytes).hexdigest()
    if expected and expected != actual:
        raise ValueError(
            "Hub artifact publish payload_sha256 mismatch: "
            f"expected {expected!r} actual {actual!r}."
        )
    return actual


def _resolve_payload_size_bytes(
    *,
    expected_size: int | None,
    payload_bytes: bytes | None,
) -> int | None:
    if payload_bytes is None:
        return expected_size
    actual = len(payload_bytes)
    if expected_size is not None and expected_size != actual:
        raise ValueError(
            "Hub artifact publish payload_size_bytes mismatch: "
            f"expected {expected_size!r} actual {actual!r}."
        )
    return actual


def _resolve_payload_url(
    *,
    artifact_family: str,
    authority_base_url: str | None,
    index_url: str,
    payload_bytes: bytes | None,
    payload_media_type: str | None,
    payload_sha256: str,
    requested_payload_url: str | None,
) -> str:
    requested = _clean(requested_payload_url)
    if payload_bytes is None:
        return _clean_required(requested, "payload_url")
    payload_url = requested or _payload_url(
        artifact_family=artifact_family,
        authority_base_url=authority_base_url,
        index_url=index_url,
        payload_media_type=payload_media_type,
        payload_sha256=payload_sha256,
    )
    _write_payload_bytes(url=payload_url, payload=payload_bytes)
    return payload_url


def _with_published_artifact(
    *,
    index: dict[str, object],
    artifact_lock: HubArtifactPayloadLock,
    producer: HubArtifactProducerProvenance,
    publisher_execution_id: str | None,
    idempotency_key: str | None,
    published_at_utc: str | None,
) -> dict[str, object]:
    lock_payload = artifact_lock.model_dump(mode="json", exclude_none=True)
    producer_payload = producer.model_dump(mode="json", exclude_none=True)
    entry: dict[str, object] = {
        **lock_payload,
        "producer": producer_payload,
    }
    if publisher_execution_id:
        entry["publisher_execution_id"] = publisher_execution_id
    if idempotency_key:
        entry["idempotency_key"] = idempotency_key
    if published_at_utc:
        entry["published_at_utc"] = published_at_utc

    artifacts = [
        item
        for item in _json_object_sequence(index.get("artifacts"))
        if not _same_artifact_revision(item, lock_payload)
    ]
    artifacts.append(entry)
    heads = [
        item
        for item in _json_object_sequence(index.get("channel_heads"))
        if not _same_channel_head(item, lock_payload)
    ]
    head: dict[str, object] = {
        "artifact_family": artifact_lock.artifact_family,
        "artifact_key": artifact_lock.artifact_key,
        "channel": artifact_lock.channel,
        "revision_id": artifact_lock.revision_id,
    }
    if artifact_lock.selector_key:
        head["selector_key"] = artifact_lock.selector_key
    if published_at_utc:
        head["updated_at_utc"] = published_at_utc
    heads.append(head)

    payload = {
        key: value
        for key, value in index.items()
        if key not in {"artifacts", "channel_heads"}
    }
    payload["artifacts"] = artifacts
    payload["channel_heads"] = heads
    return payload


def _resolve_artifact_entry(
    *,
    index: dict[str, object],
    artifact_family: str,
    artifact_key: str,
    channel: str,
    revision_id: str | None,
) -> _ResolvedArtifact:
    resolved_revision_id = revision_id or _channel_revision(
        index=index,
        artifact_family=artifact_family,
        artifact_key=artifact_key,
        channel=channel,
    )
    for entry in _json_object_sequence(index.get("artifacts")):
        if (
            entry.get("artifact_family") == artifact_family
            and entry.get("artifact_key") == artifact_key
            and entry.get("revision_id") == resolved_revision_id
        ):
            return _artifact_from_entry(entry, channel=channel)
    raise ValueError(
        "Hub artifact authority could not resolve artifact "
        f"family={artifact_family!r} key={artifact_key!r}."
    )


def _artifact_from_entry(
    entry: dict[str, object],
    *,
    channel: str,
) -> _ResolvedArtifact:
    lock_payload = {
        key: value
        for key, value in entry.items()
        if key
        in {
            "artifact_family",
            "artifact_key",
            "revision_id",
            "payload_url",
            "payload_sha256",
            "payload_size_bytes",
            "payload_media_type",
            "payload_contract",
            "authority_source_url",
            "selector_key",
            "target_ref",
            "metadata",
        }
    }
    lock_payload["channel"] = str(entry.get("channel") or channel)
    lock = HubArtifactPayloadLock.model_validate(lock_payload)
    raw_producer = entry.get("producer")
    producer = (
        HubArtifactProducerProvenance.model_validate(raw_producer)
        if isinstance(raw_producer, dict)
        else None
    )
    return _ResolvedArtifact(lock=lock, producer=producer)


def _channel_revision(
    *,
    index: dict[str, object],
    artifact_family: str,
    artifact_key: str,
    channel: str,
) -> str:
    for head in _json_object_sequence(index.get("channel_heads")):
        if (
            head.get("artifact_family") == artifact_family
            and head.get("artifact_key") == artifact_key
            and head.get("channel") == channel
        ):
            return _clean_required(head.get("revision_id"), "revision_id")
    raise ValueError(
        "Hub artifact authority channel head not found: "
        f"family={artifact_family!r} key={artifact_key!r} channel={channel!r}."
    )


def _resolve_index_url(
    *,
    artifact_family: str,
    authority_base_url: str | None,
    index_url: str | None,
) -> str:
    explicit = _clean(index_url)
    if explicit:
        return explicit
    base_url = _clean(authority_base_url)
    if not base_url:
        raise ValueError(
            "Hub artifact authority requires index_url or authority_base_url."
        )
    return _join_url(base_url, f"{_path_segment(artifact_family)}/index.json")


def _payload_url(
    *,
    artifact_family: str,
    authority_base_url: str | None,
    index_url: str,
    payload_media_type: str | None,
    payload_sha256: str,
) -> str:
    suffix = (
        f"{_path_segment(artifact_family)}/payloads/sha256/"
        f"{payload_sha256}{_payload_extension(payload_media_type)}"
    )
    base_url = _clean(authority_base_url)
    if base_url:
        return _join_url(base_url, suffix)
    index_path = _writable_url_path(index_url, operation="publish_hub_artifact_index")
    return (index_path.parent.parent / suffix).resolve().as_uri()


def _payload_extension(media_type: str | None) -> str:
    return ".json" if _clean(media_type) == "application/json" else ".bin"


def _load_or_empty_index(
    *,
    index_url: str,
    artifact_family: str,
) -> dict[str, object]:
    try:
        return _load_index(index_url=index_url, artifact_family=artifact_family)
    except FileNotFoundError:
        return {
            "version": 1,
            "authority_kind": _authority_kind(artifact_family),
            "artifact_family": artifact_family,
        }


def _load_index(
    *,
    index_url: str,
    artifact_family: str,
) -> dict[str, object]:
    payload = _read_json_url(index_url)
    if not isinstance(payload, dict):
        raise ValueError("Hub artifact authority index must be a JSON object.")
    expected_kind = _authority_kind(artifact_family)
    actual_kind = payload.get("authority_kind")
    if actual_kind is not None and actual_kind != expected_kind:
        raise ValueError(
            "Hub artifact authority kind mismatch: "
            f"expected {expected_kind!r} actual {actual_kind!r}."
        )
    return dict(payload)


def _write_index(*, index_url: str, payload: dict[str, object]) -> None:
    path = _writable_url_path(index_url, operation="publish_hub_artifact_index")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json_url(url: str) -> object:
    return json.loads(_read_url_bytes(url).decode("utf-8"))


def _read_url_bytes(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).read_bytes()
    if parsed.scheme in {"http", "https"}:
        with urlopen(url, timeout=30) as response:  # noqa: S310
            return response.read()
    if parsed.scheme:
        raise ValueError(f"Hub artifact authority unsupported URL scheme: {parsed.scheme}")
    return Path(url).expanduser().read_bytes()


def _write_payload_bytes(*, url: str, payload: bytes) -> None:
    path = _writable_url_path(url, operation="publish_hub_artifact_payload")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _writable_url_path(url: str, *, operation: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).resolve()
    if parsed.scheme in {"http", "https"}:
        raise ValueError(f"{operation} requires writable file/path authority.")
    if parsed.scheme:
        raise ValueError(f"{operation} unsupported URL scheme: {parsed.scheme!r}.")
    return Path(url).expanduser().resolve()


def _producer_or_default(
    producer: HubArtifactProducerProvenance | None,
) -> HubArtifactProducerProvenance:
    if producer is not None:
        return producer
    return HubArtifactProducerProvenance()


def _authority_kind(artifact_family: str) -> str:
    if artifact_family == OIG_COMMIT_ARTIFACT_FAMILY:
        return OIG_COMMIT_AUTHORITY_KIND
    return HUB_ARTIFACT_AUTHORITY_KIND


def _json_object_sequence(value: object) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Hub artifact authority index sequence must be a list.")
    items: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("Hub artifact authority index entries must be objects.")
        items.append(dict(item))
    return items


def _same_artifact_revision(
    left: dict[str, object],
    right: dict[str, object],
) -> bool:
    return (
        left.get("artifact_family") == right.get("artifact_family")
        and left.get("artifact_key") == right.get("artifact_key")
        and left.get("revision_id") == right.get("revision_id")
    )


def _same_channel_head(
    left: dict[str, object],
    right: dict[str, object],
) -> bool:
    return (
        left.get("artifact_family") == right.get("artifact_family")
        and left.get("artifact_key") == right.get("artifact_key")
        and left.get("channel") == right.get("channel")
    )


def _path_segment(value: str) -> str:
    segment = _clean_required(value, "path_segment")
    if "/" in segment or "\\" in segment or segment in {".", ".."}:
        raise ValueError(f"Hub artifact authority unsafe path segment: {value!r}.")
    return segment


def _join_url(base_url: str, suffix: str) -> str:
    return f"{base_url.rstrip('/')}/{suffix.lstrip('/')}"


def _clean(value: object) -> str:
    return str(value or "").strip()


def _clean_required(value: object, field_name: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        raise ValueError(f"Hub artifact authority requires {field_name}.")
    return cleaned


__all__ = [
    "DEFAULT_CHANNEL",
    "HUB_ARTIFACT_AUTHORITY_KIND",
    "OIG_COMMIT_ARTIFACT_FAMILY",
    "OIG_COMMIT_AUTHORITY_KIND",
    "HubArtifactPayloadLock",
    "HubArtifactProducerProvenance",
    "PublishHubArtifactRequest",
    "PublishHubArtifactResponse",
    "ResolveHubArtifactRequest",
    "ResolveHubArtifactResponse",
    "publish_hub_artifact",
    "resolve_hub_artifact",
]
