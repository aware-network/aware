"""Hub-owned CodePackage authority resolution."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import urlopen
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CodePackageRef(BaseModel):
    package_name: str
    language: str | None = None
    surface: str | None = None
    channel: str = "stable"
    version: str | None = None
    revision_id: str | None = None
    digest: str | None = None

    model_config = ConfigDict(extra="forbid")


class CodePackageArtifactLock(BaseModel):
    artifact_url: str
    sha256: str
    size_bytes: int | None = None
    media_type: str | None = None
    archive_format: str | None = None
    revision_id: str | None = None
    published_at: str | None = None

    model_config = ConfigDict(extra="forbid")


class CodePackageDescriptor(BaseModel):
    package_name: str
    language: str
    surface: str
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    sources_root: str | None = None
    fqn_prefix: str | None = None
    version: str | None = None
    revision_id: str | None = None
    digest: str | None = None
    artifact_media_type: str | None = None
    artifact_size_bytes: int | None = None
    download_handle: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class CodePackageChannelHead(BaseModel):
    package_name: str
    language: str | None = None
    surface: str | None = None
    channel: str = "stable"
    revision_id: str
    updated_at: str | None = None
    publisher_execution_id: str | None = None
    idempotency_key: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class CodePackageDiscoveryEntry(BaseModel):
    channel_head: CodePackageChannelHead
    descriptor: CodePackageDescriptor | None = None
    artifact_lock: CodePackageArtifactLock | None = None

    model_config = ConfigDict(extra="forbid")


class DiscoverCodePackageChannelHeadsRequest(BaseModel):
    operation: str = Field(default="discover_code_package_channel_heads")
    request_id: UUID | None = None
    query: str | None = None
    package_name: str | None = None
    language: str | None = None
    surface: str | None = None
    channel: str | None = None
    authority_base_url: str | None = None
    index_url: str | None = None
    limit: int = 50

    model_config = ConfigDict(extra="forbid")


class DiscoverCodePackageChannelHeadsResponse(BaseModel):
    operation: str = Field(default="discover_code_package_channel_heads")
    request_id: UUID | None = None
    success: bool = True
    info: str | None = None
    error: str | None = None
    authority_source_url: str | None = None
    entries: list[CodePackageDiscoveryEntry] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SearchCodePackageRequest(BaseModel):
    operation: str = Field(default="search_code_package")
    request_id: UUID | None = None
    query: str | None = None
    package_name: str | None = None
    language: str | None = None
    surface: str | None = None
    channel: str = "stable"
    authority_base_url: str | None = None
    index_url: str | None = None
    limit: int = 50

    model_config = ConfigDict(extra="forbid")


class SearchCodePackageResponse(BaseModel):
    operation: str = Field(default="search_code_package")
    request_id: UUID | None = None
    success: bool = True
    info: str | None = None
    error: str | None = None
    authority_source_url: str | None = None
    descriptors: list[CodePackageDescriptor] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class DescribeCodePackageRequest(BaseModel):
    operation: str = Field(default="describe_code_package")
    request_id: UUID | None = None
    selector: CodePackageRef
    authority_base_url: str | None = None
    index_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class DescribeCodePackageResponse(BaseModel):
    operation: str = Field(default="describe_code_package")
    request_id: UUID | None = None
    success: bool = True
    info: str | None = None
    error: str | None = None
    authority_source_url: str | None = None
    descriptor: CodePackageDescriptor | None = None

    model_config = ConfigDict(extra="forbid")


class ResolveCodePackageRequest(BaseModel):
    operation: str = Field(default="resolve_code_package")
    request_id: UUID | None = None
    selector: CodePackageRef
    authority_base_url: str | None = None
    index_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class ResolveCodePackageResponse(BaseModel):
    operation: str = Field(default="resolve_code_package")
    request_id: UUID | None = None
    success: bool = True
    info: str | None = None
    error: str | None = None
    authority_source_url: str | None = None
    selector: CodePackageRef
    descriptor: CodePackageDescriptor
    artifact_lock: CodePackageArtifactLock

    model_config = ConfigDict(extra="forbid")


class DownloadCodePackageRequest(BaseModel):
    operation: str = Field(default="download_code_package")
    request_id: UUID | None = None
    selector: CodePackageRef
    authority_base_url: str | None = None
    index_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class DownloadCodePackageResponse(BaseModel):
    operation: str = Field(default="download_code_package")
    request_id: UUID | None = None
    success: bool = True
    info: str | None = None
    error: str | None = None
    authority_source_url: str | None = None
    selector: CodePackageRef
    artifact_lock: CodePackageArtifactLock

    model_config = ConfigDict(extra="forbid")


class PublishCodePackageRequest(BaseModel):
    operation: str = Field(default="publish_code_package")
    request_id: UUID | None = None
    descriptor: CodePackageDescriptor
    artifact_lock: CodePackageArtifactLock
    channel: str = "stable"
    authority_base_url: str | None = None
    index_url: str | None = None
    publisher_execution_id: str | None = None
    idempotency_key: str | None = None

    model_config = ConfigDict(extra="forbid")


class PublishCodePackageResponse(BaseModel):
    operation: str = Field(default="publish_code_package")
    request_id: UUID | None = None
    success: bool = True
    info: str | None = None
    error: str | None = None
    authority_source_url: str | None = None
    selector: CodePackageRef | None = None
    descriptor: CodePackageDescriptor | None = None
    artifact_lock: CodePackageArtifactLock | None = None
    accepted: bool = False

    model_config = ConfigDict(extra="forbid")


class _ChannelHead(BaseModel):
    package_name: str
    language: str | None = None
    surface: str | None = None
    channel: str = "stable"
    revision_id: str

    model_config = ConfigDict(extra="allow")


class _IndexedCodePackage(BaseModel):
    descriptor: CodePackageDescriptor
    artifact_lock: CodePackageArtifactLock

    model_config = ConfigDict(extra="forbid")


class _CodePackageIndex(BaseModel):
    version: int = 1
    authority_kind: str = "code_package_distribution"
    packages: list[_IndexedCodePackage] = Field(default_factory=list)
    channel_heads: list[_ChannelHead] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


def search_code_package(
    request: SearchCodePackageRequest,
) -> SearchCodePackageResponse:
    index_url = _resolve_index_url(
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    index = _load_index(index_url)
    descriptors = [
        item.descriptor
        for item in index.packages
        if _matches_search(item.descriptor, request)
    ]
    limit = max(request.limit, 0)
    if limit:
        descriptors = descriptors[:limit]
    else:
        descriptors = []
    return SearchCodePackageResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        descriptors=descriptors,
    )


def discover_code_package_channel_heads(
    request: DiscoverCodePackageChannelHeadsRequest,
) -> DiscoverCodePackageChannelHeadsResponse:
    index_url = _resolve_index_url(
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    index = _load_index(index_url)
    entries = [
        entry
        for entry in (
            _discovery_entry(index=index, head=head)
            for head in index.channel_heads
            if _matches_channel_head(head, request)
        )
        if _matches_discovery_entry(entry, request)
    ]
    limit = max(request.limit, 0)
    if limit:
        entries = entries[:limit]
    else:
        entries = []
    return DiscoverCodePackageChannelHeadsResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        entries=entries,
    )


def describe_code_package(
    request: DescribeCodePackageRequest,
) -> DescribeCodePackageResponse:
    index_url = _resolve_index_url(
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    package = _resolve_package(index=_load_index(index_url), selector=request.selector)
    return DescribeCodePackageResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        descriptor=package.descriptor,
    )


def resolve_code_package(
    request: ResolveCodePackageRequest,
) -> ResolveCodePackageResponse:
    index_url = _resolve_index_url(
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    package = _resolve_package(index=_load_index(index_url), selector=request.selector)
    selector = _resolved_selector(request.selector, package)
    return ResolveCodePackageResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        selector=selector,
        descriptor=package.descriptor,
        artifact_lock=package.artifact_lock,
    )


def download_code_package(
    request: DownloadCodePackageRequest,
) -> DownloadCodePackageResponse:
    index_url = _resolve_index_url(
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    package = _resolve_package(index=_load_index(index_url), selector=request.selector)
    selector = _resolved_selector(request.selector, package)
    return DownloadCodePackageResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        selector=selector,
        artifact_lock=package.artifact_lock,
    )


def publish_code_package(
    request: PublishCodePackageRequest,
) -> PublishCodePackageResponse:
    index_url = _resolve_index_url(
        authority_base_url=request.authority_base_url,
        index_url=request.index_url,
    )
    _validate_publish_request(request)
    index = _load_or_empty_index(index_url)
    package = _IndexedCodePackage(
        descriptor=request.descriptor,
        artifact_lock=request.artifact_lock,
    )
    updated_index = _with_published_package(
        index=index,
        package=package,
        channel=_clean(request.channel) or "stable",
        publisher_execution_id=_clean(request.publisher_execution_id) or None,
        idempotency_key=_clean(request.idempotency_key) or None,
    )
    _write_index(index_url, updated_index)
    selector = _resolved_selector(
        CodePackageRef(
            package_name=request.descriptor.package_name,
            language=request.descriptor.language,
            surface=request.descriptor.surface,
            channel=_clean(request.channel) or "stable",
            version=request.descriptor.version,
            revision_id=request.descriptor.revision_id or request.artifact_lock.revision_id,
            digest=request.descriptor.digest or request.artifact_lock.sha256,
        ),
        package,
    )
    return PublishCodePackageResponse(
        request_id=request.request_id,
        authority_source_url=index_url,
        selector=selector,
        descriptor=request.descriptor,
        artifact_lock=request.artifact_lock,
        accepted=True,
    )


def _resolve_index_url(*, authority_base_url: str | None, index_url: str | None) -> str:
    explicit_index_url = _clean(index_url)
    if explicit_index_url:
        return explicit_index_url
    base_url = _clean(authority_base_url)
    if not base_url:
        raise ValueError("Hub CodePackage resolution requires index_url or authority_base_url.")
    return _join_url(base_url, "code-package/index.json")


def _load_or_empty_index(index_url: str) -> _CodePackageIndex:
    try:
        return _load_index(index_url)
    except FileNotFoundError:
        return _CodePackageIndex()


def _load_index(index_url: str) -> _CodePackageIndex:
    payload = _load_json_url(index_url)
    if not isinstance(payload, dict):
        raise ValueError("Hub CodePackage index payload must be a JSON object.")
    packages = [_coerce_indexed_package(item) for item in payload.get("packages", [])]
    channel_heads = payload.get("channel_heads", [])
    return _CodePackageIndex(
        **{
            key: value
            for key, value in payload.items()
            if key not in {"packages", "channel_heads"}
        },
        packages=packages,
        channel_heads=channel_heads,
    )


def _coerce_indexed_package(value: object) -> _IndexedCodePackage:
    if not isinstance(value, dict):
        raise ValueError("Hub CodePackage index packages must be JSON objects.")
    descriptor_payload = value.get("descriptor") or value
    artifact_payload = (
        value.get("artifact_lock")
        or value.get("artifact")
        or {
            key: value.get(key)
            for key in (
                "artifact_url",
                "sha256",
                "size_bytes",
                "media_type",
                "archive_format",
                "revision_id",
                "published_at",
            )
            if key in value
        }
    )
    if not isinstance(descriptor_payload, dict) or not isinstance(artifact_payload, dict):
        raise ValueError("Hub CodePackage descriptor and artifact_lock must be JSON objects.")
    descriptor = CodePackageDescriptor.model_validate(descriptor_payload)
    artifact_lock = CodePackageArtifactLock.model_validate(artifact_payload)
    return _IndexedCodePackage(descriptor=descriptor, artifact_lock=artifact_lock)


def _validate_publish_request(request: PublishCodePackageRequest) -> None:
    descriptor = request.descriptor
    artifact_lock = request.artifact_lock
    descriptor_revision_id = _clean(descriptor.revision_id)
    artifact_revision_id = _clean(artifact_lock.revision_id)
    if descriptor_revision_id and artifact_revision_id:
        if descriptor_revision_id != artifact_revision_id:
            raise ValueError(
                "Hub CodePackage publish descriptor revision_id must match "
                "artifact_lock revision_id."
            )
    if not descriptor_revision_id and not artifact_revision_id:
        raise ValueError("Hub CodePackage publish requires a revision_id.")
    descriptor_digest = _clean(descriptor.digest)
    artifact_digest = _clean(artifact_lock.sha256)
    if descriptor_digest and artifact_digest and descriptor_digest != artifact_digest:
        raise ValueError(
            "Hub CodePackage publish descriptor digest must match artifact_lock sha256."
        )


def _with_published_package(
    *,
    index: _CodePackageIndex,
    package: _IndexedCodePackage,
    channel: str,
    publisher_execution_id: str | None,
    idempotency_key: str | None,
) -> _CodePackageIndex:
    packages = [
        item for item in index.packages if not _same_package_revision(item, package)
    ]
    packages.append(package)
    channel_heads = [
        head
        for head in index.channel_heads
        if not _same_channel_head(head, package.descriptor, channel)
    ]
    revision_id = package.descriptor.revision_id or package.artifact_lock.revision_id
    if revision_id is None:
        raise ValueError("Hub CodePackage publish requires a revision_id.")
    head_payload: dict[str, object] = {
        "package_name": package.descriptor.package_name,
        "language": package.descriptor.language,
        "surface": package.descriptor.surface,
        "channel": channel,
        "revision_id": revision_id,
    }
    if publisher_execution_id:
        head_payload["publisher_execution_id"] = publisher_execution_id
    if idempotency_key:
        head_payload["idempotency_key"] = idempotency_key
    channel_heads.append(_ChannelHead.model_validate(head_payload))
    return _CodePackageIndex(
        **{
            key: value
            for key, value in index.model_dump(mode="json").items()
            if key not in {"packages", "channel_heads"}
        },
        packages=packages,
        channel_heads=channel_heads,
    )


def _same_package_revision(
    current: _IndexedCodePackage,
    published: _IndexedCodePackage,
) -> bool:
    current_revision_id = current.descriptor.revision_id or current.artifact_lock.revision_id
    published_revision_id = (
        published.descriptor.revision_id or published.artifact_lock.revision_id
    )
    return (
        current.descriptor.package_name == published.descriptor.package_name
        and current.descriptor.language == published.descriptor.language
        and current.descriptor.surface == published.descriptor.surface
        and current.descriptor.version == published.descriptor.version
        and current_revision_id == published_revision_id
    )


def _same_channel_head(
    head: _ChannelHead,
    descriptor: CodePackageDescriptor,
    channel: str,
) -> bool:
    return (
        head.package_name == descriptor.package_name
        and head.channel == channel
        and _matches_optional(descriptor.language, head.language)
        and _matches_optional(descriptor.surface, head.surface)
    )


def _write_index(index_url: str, index: _CodePackageIndex) -> None:
    path = _writable_index_path(index_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_index_payload(index), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _writable_index_path(index_url: str) -> Path:
    parsed = urlparse(index_url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if parsed.scheme in {"http", "https"}:
        raise ValueError(
            "Hub CodePackage publish requires a writable file/path index_url "
            "or authority_base_url."
        )
    if parsed.scheme:
        raise ValueError(
            f"Hub CodePackage publish does not support {parsed.scheme!r} authority URLs."
        )
    return Path(index_url)


def _index_payload(index: _CodePackageIndex) -> dict[str, object]:
    payload = {
        key: value
        for key, value in index.model_dump(mode="json", exclude_none=True).items()
        if key not in {"packages", "channel_heads"}
    }
    payload["packages"] = [
        item.model_dump(mode="json", exclude_none=True) for item in index.packages
    ]
    payload["channel_heads"] = [
        head.model_dump(mode="json", exclude_none=True) for head in index.channel_heads
    ]
    return payload


def _resolve_package(
    *,
    index: _CodePackageIndex,
    selector: CodePackageRef,
) -> _IndexedCodePackage:
    revision_id = _clean(selector.revision_id) or _channel_revision(index, selector)
    digest = _clean(selector.digest)
    candidates = [
        item
        for item in index.packages
        if item.descriptor.package_name == selector.package_name
        and _matches_optional(item.descriptor.language, selector.language)
        and _matches_optional(item.descriptor.surface, selector.surface)
        and _matches_optional(item.descriptor.version, selector.version)
    ]
    if revision_id:
        candidates = [
            item
            for item in candidates
            if item.descriptor.revision_id == revision_id
            or item.artifact_lock.revision_id == revision_id
        ]
    if digest:
        candidates = [
            item
            for item in candidates
            if item.descriptor.digest == digest or item.artifact_lock.sha256 == digest
        ]
    if not candidates:
        raise ValueError(
            "Hub CodePackage authority could not resolve package "
            f"{selector.package_name!r}."
        )
    return candidates[0]


def _channel_revision(index: _CodePackageIndex, selector: CodePackageRef) -> str | None:
    channel = _clean(selector.channel) or "stable"
    for head in index.channel_heads:
        if (
            head.package_name == selector.package_name
            and head.channel == channel
            and _matches_optional(selector.language, head.language)
            and _matches_optional(selector.surface, head.surface)
        ):
            return head.revision_id
    return None


def _resolved_selector(
    selector: CodePackageRef,
    package: _IndexedCodePackage,
) -> CodePackageRef:
    return CodePackageRef(
        package_name=package.descriptor.package_name,
        language=package.descriptor.language,
        surface=package.descriptor.surface,
        channel=selector.channel,
        version=package.descriptor.version or selector.version,
        revision_id=package.descriptor.revision_id or package.artifact_lock.revision_id,
        digest=package.descriptor.digest or package.artifact_lock.sha256,
    )


def _discovery_entry(
    *,
    index: _CodePackageIndex,
    head: _ChannelHead,
) -> CodePackageDiscoveryEntry:
    package = _package_for_channel_head(index=index, head=head)
    return CodePackageDiscoveryEntry(
        channel_head=_public_channel_head(head),
        descriptor=package.descriptor if package is not None else None,
        artifact_lock=package.artifact_lock if package is not None else None,
    )


def _package_for_channel_head(
    *,
    index: _CodePackageIndex,
    head: _ChannelHead,
) -> _IndexedCodePackage | None:
    for package in index.packages:
        revision_id = package.descriptor.revision_id or package.artifact_lock.revision_id
        if (
            package.descriptor.package_name == head.package_name
            and _matches_optional(package.descriptor.language, head.language)
            and _matches_optional(package.descriptor.surface, head.surface)
            and revision_id == head.revision_id
        ):
            return package
    return None


def _public_channel_head(head: _ChannelHead) -> CodePackageChannelHead:
    extras = {
        key: value
        for key, value in (head.model_extra or {}).items()
        if key not in {"updated_at", "publisher_execution_id", "idempotency_key"}
    }
    return CodePackageChannelHead(
        package_name=head.package_name,
        language=head.language,
        surface=head.surface,
        channel=head.channel,
        revision_id=head.revision_id,
        updated_at=_extra_str(head, "updated_at"),
        publisher_execution_id=_extra_str(head, "publisher_execution_id"),
        idempotency_key=_extra_str(head, "idempotency_key"),
        metadata=extras,
    )


def _matches_channel_head(
    head: _ChannelHead,
    request: DiscoverCodePackageChannelHeadsRequest,
) -> bool:
    if _clean(request.package_name) and head.package_name != request.package_name:
        return False
    if not _matches_optional(head.language, request.language):
        return False
    if not _matches_optional(head.surface, request.surface):
        return False
    if not _matches_optional(head.channel, request.channel):
        return False
    return True


def _matches_discovery_entry(
    entry: CodePackageDiscoveryEntry,
    request: DiscoverCodePackageChannelHeadsRequest,
) -> bool:
    query = _clean(request.query).lower()
    if not query:
        return True
    haystack = json.dumps(
        {
            "channel_head": entry.channel_head.model_dump(mode="json"),
            "descriptor": (
                entry.descriptor.model_dump(mode="json")
                if entry.descriptor is not None
                else None
            ),
        },
        sort_keys=True,
    ).lower()
    return query in haystack


def _matches_search(
    descriptor: CodePackageDescriptor,
    request: SearchCodePackageRequest,
) -> bool:
    if _clean(request.package_name) and descriptor.package_name != request.package_name:
        return False
    if not _matches_optional(descriptor.language, request.language):
        return False
    if not _matches_optional(descriptor.surface, request.surface):
        return False
    query = _clean(request.query).lower()
    if query:
        haystack = json.dumps(
            {
                "package_name": descriptor.package_name,
                "fqn_prefix": descriptor.fqn_prefix,
                "metadata": descriptor.metadata,
            },
            sort_keys=True,
        ).lower()
        if query not in haystack:
            return False
    return True


def _matches_optional(value: str | None, expected: str | None) -> bool:
    expected_value = _clean(expected)
    return not expected_value or value == expected_value


def _load_json_url(url: str) -> object:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        from pathlib import Path

        return json.loads(Path(unquote(parsed.path)).read_text(encoding="utf-8"))
    if parsed.scheme in {"http", "https"}:
        with urlopen(url, timeout=30) as response:  # noqa: S310 - Hub authority URL.
            return json.loads(response.read().decode("utf-8"))
    from pathlib import Path

    return json.loads(Path(url).read_text(encoding="utf-8"))


def _join_url(base_url: str, suffix: str) -> str:
    return f"{base_url.rstrip('/')}/{suffix.lstrip('/')}"


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _extra_str(head: _ChannelHead, key: str) -> str | None:
    value = (head.model_extra or {}).get(key)
    if isinstance(value, str):
        return _clean(value) or None
    return None


__all__ = [
    "CodePackageArtifactLock",
    "CodePackageChannelHead",
    "CodePackageDescriptor",
    "CodePackageDiscoveryEntry",
    "CodePackageRef",
    "DescribeCodePackageRequest",
    "DescribeCodePackageResponse",
    "DiscoverCodePackageChannelHeadsRequest",
    "DiscoverCodePackageChannelHeadsResponse",
    "DownloadCodePackageRequest",
    "DownloadCodePackageResponse",
    "PublishCodePackageRequest",
    "PublishCodePackageResponse",
    "ResolveCodePackageRequest",
    "ResolveCodePackageResponse",
    "SearchCodePackageRequest",
    "SearchCodePackageResponse",
    "describe_code_package",
    "discover_code_package_channel_heads",
    "download_code_package",
    "publish_code_package",
    "resolve_code_package",
    "search_code_package",
]
