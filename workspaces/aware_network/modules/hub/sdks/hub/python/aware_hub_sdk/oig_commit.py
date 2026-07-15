from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import unquote, urlparse
from urllib.request import urlopen

from aware_hub_sdk.models import (
    HubArtifactProducerProvenance,
    HubCodePackageDescriptor,
)

if TYPE_CHECKING:
    from aware_hub_sdk.artifact import HubArtifactClient


OIG_COMMIT_ARTIFACT_FAMILY = "oig-commit"
OIG_COMMIT_AUTHORITY_KIND = "oig_commit_payload_distribution"
OIG_COMMIT_PAYLOAD_CONTRACT = "aware.oig_commit_payload.v1"
OIG_COMMIT_PAYLOAD_MEDIA_TYPE = "application/json"
OIG_COMMIT_PAYLOAD_REF_SCHEMA = "aware.oig_commit_payload_ref.v1"


@dataclass(frozen=True, slots=True)
class HubOigCommitPayloadRef:
    ref_schema: str
    payload_contract: str
    artifact_family: str
    artifact_key: str
    artifact_revision_id: str
    branch_id: str
    projection_hash: str
    commit_id: str
    object_instance_graph_commit_id: str
    payload_url: str
    payload_sha256: str
    payload_size_bytes: int
    payload_media_type: str
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class HubOigCommitPayloadArtifactReceipt:
    authority_source_url: str
    refs: tuple[dict[str, object], ...]


def oig_commit_refs_from_code_package_descriptor(
    descriptor: HubCodePackageDescriptor,
) -> tuple[HubOigCommitPayloadRef, ...]:
    raw_refs = descriptor.metadata.get("oig_commit_refs")
    if not isinstance(raw_refs, list | tuple):
        return ()
    refs: list[HubOigCommitPayloadRef] = []
    for raw_ref in raw_refs:
        if isinstance(raw_ref, Mapping):
            refs.append(_ref_from_mapping(raw_ref))
    return tuple(refs)


async def import_oig_commit_refs_from_code_package_descriptor(
    descriptor: HubCodePackageDescriptor,
    *,
    root_dir: Path | None = None,
) -> tuple[object, ...]:
    """Verify descriptor OIG refs and install them into local `.aware/oig`.

    The import operation is intentionally optional for the Hub SDK package:
    consumers that need local OIG hydration must have `aware-meta` available.
    """

    try:
        from aware_meta.graph.instance.commit.payload_refs import (  # noqa: WPS433
            import_oig_commit_payload_ref,
        )
    except ImportError as exc:  # pragma: no cover - package-boundary guard
        raise RuntimeError(
            "hub_oig_payload_import_requires_aware_meta"
        ) from exc

    receipts: list[object] = []
    for ref in oig_commit_refs_from_code_package_descriptor(descriptor):
        receipts.append(
            await import_oig_commit_payload_ref(
                ref=ref.metadata,
                root_dir=root_dir,
            )
        )
    return tuple(receipts)


def publish_oig_commit_payload_refs_to_authority(
    *,
    refs: Sequence[Mapping[str, object]],
    authority_base_url: str | None = None,
    index_url: str | None = None,
    channel: str = "stable",
    publisher_execution_id: str | None = None,
    published_at: str | None = None,
) -> HubOigCommitPayloadArtifactReceipt:
    """Publish OIG commit payload bytes into a writable Hub file authority.

    This is the SDK-local authority rail that matches the current Hub
    CodePackage file-index publish behavior. It verifies each payload against
    the ref hash/size, copies it under the authority, records an OIG payload
    index, and returns refs rewritten to authority-owned payload URLs.
    """

    if not refs:
        return HubOigCommitPayloadArtifactReceipt(
            authority_source_url=_oig_index_url(
                authority_base_url=authority_base_url,
                index_url=index_url,
            ),
            refs=(),
        )

    authority_index_url = _oig_index_url(
        authority_base_url=authority_base_url,
        index_url=index_url,
    )
    index = _load_or_empty_oig_index(authority_index_url)
    updated_refs: list[dict[str, object]] = []
    artifacts = list(_index_sequence(index.get("artifacts")))
    channel_heads = list(_index_sequence(index.get("channel_heads")))
    for ref in refs:
        normalized = _normalized_ref(ref)
        payload_bytes = _read_url_bytes(str(normalized["payload_url"]))
        payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
        if payload_sha256 != normalized["payload_sha256"]:
            raise ValueError(
                "hub_oig_payload_sha256_mismatch:"
                + f"artifact_key={normalized['artifact_key']}"
            )
        if len(payload_bytes) != normalized["payload_size_bytes"]:
            raise ValueError(
                "hub_oig_payload_size_mismatch:"
                + f"artifact_key={normalized['artifact_key']}"
            )

        payload_url = _write_authority_payload(
            authority_base_url=authority_base_url,
            index_url=authority_index_url,
            payload_sha256=payload_sha256,
            payload_bytes=payload_bytes,
        )
        updated_ref = {
            **normalized,
            "payload_url": payload_url,
            "artifact_channel": channel,
            "artifact_authority_source_url": authority_index_url,
        }
        entry = _artifact_entry(
            ref=updated_ref,
            channel=channel,
            publisher_execution_id=publisher_execution_id,
            published_at=published_at,
        )
        artifacts = [
            item for item in artifacts if not _same_oig_artifact_entry(item, entry)
        ]
        artifacts.append(entry)
        head = _channel_head_entry(ref=updated_ref, channel=channel)
        channel_heads = [
            item for item in channel_heads if not _same_oig_channel_head(item, head)
        ]
        channel_heads.append(head)
        updated_refs.append(updated_ref)

    index_payload = {
        **{
            key: value
            for key, value in index.items()
            if key not in {"version", "authority_kind", "artifacts", "channel_heads"}
        },
        "version": 1,
        "authority_kind": OIG_COMMIT_AUTHORITY_KIND,
        "artifacts": artifacts,
        "channel_heads": channel_heads,
    }
    _write_json_url(authority_index_url, index_payload)
    return HubOigCommitPayloadArtifactReceipt(
        authority_source_url=authority_index_url,
        refs=tuple(updated_refs),
    )


async def publish_oig_commit_payload_refs_to_hub_artifact_authority(
    *,
    artifact_client: "HubArtifactClient",
    refs: Sequence[Mapping[str, object]],
    authority_base_url: str | None = None,
    index_url: str | None = None,
    channel: str = "stable",
    publisher_execution_id: str | None = None,
    published_at: str | None = None,
) -> HubOigCommitPayloadArtifactReceipt:
    """Publish OIG commit payload refs through the Hub artifact API backend."""

    if not refs:
        return HubOigCommitPayloadArtifactReceipt(
            authority_source_url=_oig_index_url(
                authority_base_url=authority_base_url,
                index_url=index_url,
            ),
            refs=(),
        )

    updated_refs: list[dict[str, object]] = []
    authority_source_url: str | None = None
    for ref in refs:
        normalized = _normalized_ref(ref)
        receipt = await artifact_client.publish(
            artifact_family=str(normalized["artifact_family"]),
            artifact_key=str(normalized["artifact_key"]),
            revision_id=str(normalized["artifact_revision_id"]),
            channel=channel,
            authority_base_url=authority_base_url,
            index_url=index_url,
            payload_sha256=str(normalized["payload_sha256"]),
            payload_size_bytes=cast(int, normalized["payload_size_bytes"]),
            payload_media_type=str(normalized["payload_media_type"]),
            payload_contract=str(normalized["payload_contract"]),
            payload_source_url=str(normalized["payload_url"]),
            producer=_oig_producer(normalized),
            publisher_execution_id=publisher_execution_id,
            idempotency_key=_oig_idempotency_key(normalized),
            published_at_utc=published_at,
            metadata={
                "ref_schema": normalized["ref_schema"],
                "payload_contract": normalized["payload_contract"],
                "branch_id": normalized["branch_id"],
                "projection_hash": normalized["projection_hash"],
                "commit_id": normalized["commit_id"],
                "domain_commit_id": normalized["domain_commit_id"],
                "artifact_revision_id": normalized["artifact_revision_id"],
                "object_instance_graph_commit_id": normalized[
                    "object_instance_graph_commit_id"
                ],
                "object_instance_graph_identity_id": normalized[
                    "object_instance_graph_identity_id"
                ],
                "object_instance_graph_id": normalized["object_instance_graph_id"],
                "graph_hash_post": normalized["graph_hash_post"],
                "source_payload_url": normalized["payload_url"],
            },
        )
        lock = receipt.artifact_lock
        authority_source_url = (
            receipt.authority_source_url
            or lock.authority_source_url
            or authority_source_url
        )
        updated_refs.append(
            {
                **normalized,
                "payload_url": lock.payload_url,
                "payload_sha256": lock.payload_sha256,
                "payload_size_bytes": (
                    lock.payload_size_bytes
                    if lock.payload_size_bytes is not None
                    else normalized["payload_size_bytes"]
                ),
                "payload_media_type": (
                    lock.payload_media_type or normalized["payload_media_type"]
                ),
                "payload_contract": lock.payload_contract
                or normalized["payload_contract"],
                "artifact_channel": lock.channel,
                "artifact_authority_source_url": (
                    receipt.authority_source_url or lock.authority_source_url
                ),
            }
        )
    if authority_source_url is None:
        authority_source_url = _oig_index_url(
            authority_base_url=authority_base_url,
            index_url=index_url,
        )
    return HubOigCommitPayloadArtifactReceipt(
        authority_source_url=authority_source_url,
        refs=tuple(updated_refs),
    )


async def resolve_oig_commit_payload_ref_from_hub_artifact_authority(
    *,
    artifact_client: "HubArtifactClient",
    artifact_key: str,
    authority_base_url: str | None = None,
    index_url: str | None = None,
    channel: str = "stable",
    revision_id: str | None = None,
) -> dict[str, object]:
    """Resolve one OIG commit payload ref through the Hub artifact API backend."""

    receipt = await artifact_client.resolve(
        artifact_family=OIG_COMMIT_ARTIFACT_FAMILY,
        artifact_key=artifact_key,
        channel=channel,
        revision_id=revision_id,
        authority_base_url=authority_base_url,
        index_url=index_url,
    )
    lock = receipt.artifact_lock
    metadata = dict(lock.metadata)
    return _normalized_ref(
        {
            **metadata,
            "payload_contract": lock.payload_contract
            or metadata.get("payload_contract")
            or OIG_COMMIT_PAYLOAD_CONTRACT,
            "artifact_family": lock.artifact_family,
            "artifact_key": lock.artifact_key,
            "artifact_revision_id": metadata.get("artifact_revision_id")
            or lock.revision_id,
            "payload_url": lock.payload_url,
            "payload_sha256": lock.payload_sha256,
            "payload_size_bytes": lock.payload_size_bytes,
            "payload_media_type": lock.payload_media_type
            or OIG_COMMIT_PAYLOAD_MEDIA_TYPE,
            "artifact_channel": lock.channel,
            "artifact_authority_source_url": (
                receipt.authority_source_url or lock.authority_source_url
            ),
        }
    )


def resolve_oig_commit_payload_ref_from_authority(
    *,
    artifact_key: str,
    authority_base_url: str | None = None,
    index_url: str | None = None,
    channel: str = "stable",
    revision_id: str | None = None,
) -> dict[str, object]:
    authority_index_url = _oig_index_url(
        authority_base_url=authority_base_url,
        index_url=index_url,
    )
    index = _load_oig_index(authority_index_url)
    clean_artifact_key = _clean_required(artifact_key, "artifact_key")
    clean_revision_id = _clean_optional(revision_id)
    if clean_revision_id is None:
        clean_revision_id = _revision_for_channel(
            index=index,
            artifact_key=clean_artifact_key,
            channel=channel,
        )
    for entry in _index_sequence(index.get("artifacts")):
        if (
            str(entry.get("artifact_family") or "") == OIG_COMMIT_ARTIFACT_FAMILY
            and str(entry.get("artifact_key") or "") == clean_artifact_key
            and str(entry.get("revision_id") or "") == clean_revision_id
        ):
            ref = entry.get("ref")
            if not isinstance(ref, Mapping):
                raise ValueError("hub_oig_payload_authority_ref_missing")
            return _normalized_ref(ref)
    raise ValueError(
        "hub_oig_payload_authority_ref_not_found:"
        + f"artifact_key={clean_artifact_key}"
    )


def code_package_descriptor_with_oig_commit_refs(
    descriptor: HubCodePackageDescriptor,
    refs: Sequence[Mapping[str, object]],
) -> HubCodePackageDescriptor:
    metadata = dict(descriptor.metadata)
    metadata["oig_commit_refs"] = [dict(ref) for ref in refs]
    return HubCodePackageDescriptor(
        package_name=descriptor.package_name,
        language=descriptor.language,
        surface=descriptor.surface,
        manifest_kind=descriptor.manifest_kind,
        manifest_relative_path=descriptor.manifest_relative_path,
        package_root=descriptor.package_root,
        sources_root=descriptor.sources_root,
        fqn_prefix=descriptor.fqn_prefix,
        version=descriptor.version,
        revision_id=descriptor.revision_id,
        digest=descriptor.digest,
        artifact_media_type=descriptor.artifact_media_type,
        artifact_size_bytes=descriptor.artifact_size_bytes,
        download_handle=descriptor.download_handle,
        metadata=metadata,
    )


def _ref_from_mapping(ref: Mapping[str, object]) -> HubOigCommitPayloadRef:
    normalized = _normalized_ref(ref)
    schema = str(normalized["ref_schema"])
    if schema != OIG_COMMIT_PAYLOAD_REF_SCHEMA:
        raise ValueError(f"unsupported_oig_commit_payload_ref_schema:{schema}")
    payload_size_bytes = normalized["payload_size_bytes"]
    if not isinstance(payload_size_bytes, int) or isinstance(
        payload_size_bytes,
        bool,
    ):
        raise ValueError("oig_commit_payload_ref_invalid_int:payload_size_bytes")
    return HubOigCommitPayloadRef(
        ref_schema=schema,
        payload_contract=str(normalized["payload_contract"]),
        artifact_family=str(normalized["artifact_family"]),
        artifact_key=str(normalized["artifact_key"]),
        artifact_revision_id=str(normalized["artifact_revision_id"]),
        branch_id=str(normalized["branch_id"]),
        projection_hash=str(normalized["projection_hash"]),
        commit_id=str(normalized["commit_id"]),
        object_instance_graph_commit_id=str(
            normalized["object_instance_graph_commit_id"]
        ),
        payload_url=str(normalized["payload_url"]),
        payload_sha256=str(normalized["payload_sha256"]),
        payload_size_bytes=payload_size_bytes,
        payload_media_type=str(normalized["payload_media_type"]),
        metadata=normalized,
    )


def _normalized_ref(ref: Mapping[str, object]) -> dict[str, object]:
    payload = dict(ref)
    schema = str(payload.get("ref_schema") or OIG_COMMIT_PAYLOAD_REF_SCHEMA).strip()
    if schema != OIG_COMMIT_PAYLOAD_REF_SCHEMA:
        raise ValueError(f"unsupported_oig_commit_payload_ref_schema:{schema}")
    payload["ref_schema"] = schema
    payload["payload_contract"] = _required_text(payload, "payload_contract")
    if payload["payload_contract"] != OIG_COMMIT_PAYLOAD_CONTRACT:
        raise ValueError(
            "unsupported_oig_commit_payload_contract:"
            + str(payload["payload_contract"])
        )
    payload["branch_id"] = _required_text(payload, "branch_id")
    payload["projection_hash"] = _required_text(payload, "projection_hash")
    payload["commit_id"] = _required_text(payload, "commit_id")
    payload["domain_commit_id"] = str(
        payload.get("domain_commit_id") or payload["commit_id"]
    )
    payload["object_instance_graph_commit_id"] = _required_text(
        payload,
        "object_instance_graph_commit_id",
    )
    payload["object_instance_graph_identity_id"] = _required_text(
        payload,
        "object_instance_graph_identity_id",
    )
    payload["object_instance_graph_id"] = _required_text(
        payload,
        "object_instance_graph_id",
    )
    payload["graph_hash_post"] = _required_text(payload, "graph_hash_post")
    payload["payload_url"] = _required_text(payload, "payload_url")
    payload["payload_sha256"] = _required_sha256(payload, "payload_sha256")
    payload["payload_size_bytes"] = _required_positive_int(
        payload,
        "payload_size_bytes",
    )
    payload["payload_media_type"] = str(
        payload.get("payload_media_type") or OIG_COMMIT_PAYLOAD_MEDIA_TYPE
    ).strip()
    if payload["payload_media_type"] != OIG_COMMIT_PAYLOAD_MEDIA_TYPE:
        raise ValueError(
            "unsupported_oig_commit_payload_media_type:"
            + str(payload["payload_media_type"])
        )
    payload["artifact_family"] = str(
        payload.get("artifact_family") or OIG_COMMIT_ARTIFACT_FAMILY
    ).strip()
    if payload["artifact_family"] != OIG_COMMIT_ARTIFACT_FAMILY:
        raise ValueError(
            "unsupported_oig_commit_artifact_family:"
            + str(payload["artifact_family"])
        )
    payload["artifact_key"] = str(
        payload.get("artifact_key")
        or f"{payload['branch_id']}:{payload['projection_hash']}:{payload['commit_id']}"
    ).strip()
    payload["artifact_revision_id"] = str(
        payload.get("artifact_revision_id") or payload["commit_id"]
    ).strip()
    return payload


def _required_text(ref: Mapping[str, object], key: str) -> str:
    value = ref.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"oig_commit_payload_ref_missing:{key}")


def _required_int(ref: Mapping[str, object], key: str) -> int:
    value = ref.get(key)
    if isinstance(value, bool):
        raise ValueError(f"oig_commit_payload_ref_invalid_int:{key}")
    if isinstance(value, int):
        return value
    raise ValueError(f"oig_commit_payload_ref_missing:{key}")


def _required_positive_int(ref: Mapping[str, object], key: str) -> int:
    value = _required_int(ref, key)
    if value > 0:
        return value
    raise ValueError(f"oig_commit_payload_ref_invalid_int:{key}")


def _required_sha256(ref: Mapping[str, object], key: str) -> str:
    value = _required_text(ref, key)
    if len(value) == 64 and all(char in "0123456789abcdef" for char in value):
        return value
    raise ValueError(f"oig_commit_payload_ref_invalid_sha256:{key}")


def _oig_index_url(*, authority_base_url: str | None, index_url: str | None) -> str:
    clean_index_url = _clean_optional(index_url)
    if clean_index_url is not None:
        return clean_index_url
    base_url = _clean_optional(authority_base_url)
    if base_url is None:
        raise ValueError("hub_oig_payload_authority_url_required")
    return _join_url(base_url, "oig-commit/index.json")


def _payload_url(*, authority_base_url: str | None, index_url: str, sha256: str) -> str:
    base_url = _clean_optional(authority_base_url)
    if base_url is not None:
        return _join_url(base_url, f"oig-commit/payloads/sha256/{sha256}.json")
    parsed = urlparse(index_url)
    if parsed.scheme == "file":
        index_path = Path(unquote(parsed.path))
        return (index_path.parent / "payloads" / "sha256" / f"{sha256}.json").as_uri()
    if parsed.scheme:
        raise ValueError("hub_oig_payload_authority_base_url_required")
    return (
        Path(index_url).parent / "payloads" / "sha256" / f"{sha256}.json"
    ).resolve().as_uri()


def _write_authority_payload(
    *,
    authority_base_url: str | None,
    index_url: str,
    payload_sha256: str,
    payload_bytes: bytes,
) -> str:
    url = _payload_url(
        authority_base_url=authority_base_url,
        index_url=index_url,
        sha256=payload_sha256,
    )
    path = _writable_url_path(url, operation="publish_oig_commit_payload")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == payload_bytes:
        return url
    path.write_bytes(payload_bytes)
    return url


def _load_or_empty_oig_index(index_url: str) -> dict[str, object]:
    try:
        return _load_oig_index(index_url)
    except FileNotFoundError:
        return {"version": 1, "authority_kind": OIG_COMMIT_AUTHORITY_KIND}


def _load_oig_index(index_url: str) -> dict[str, object]:
    payload = json.loads(_read_url_bytes(index_url).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("hub_oig_payload_authority_index_not_object")
    return cast(dict[str, object], payload)


def _write_json_url(url: str, payload: Mapping[str, object]) -> None:
    path = _writable_url_path(url, operation="publish_oig_commit_payload_index")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_url_bytes(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).read_bytes()
    if parsed.scheme in {"http", "https"}:
        with urlopen(url, timeout=30) as response:  # nosec B310
            return cast(bytes, response.read())
    if parsed.scheme:
        raise ValueError(f"hub_oig_payload_url_unsupported:{parsed.scheme}")
    return Path(url).expanduser().resolve().read_bytes()


def _writable_url_path(url: str, *, operation: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if parsed.scheme in {"http", "https"}:
        raise ValueError(f"{operation}_requires_writable_file_authority")
    if parsed.scheme:
        raise ValueError(f"{operation}_unsupported_authority_scheme:{parsed.scheme}")
    return Path(url).expanduser().resolve()


def _artifact_entry(
    *,
    ref: Mapping[str, object],
    channel: str,
    publisher_execution_id: str | None,
    published_at: str | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "artifact_family": ref["artifact_family"],
        "artifact_key": ref["artifact_key"],
        "revision_id": ref["artifact_revision_id"],
        "channel": channel,
        "payload_url": ref["payload_url"],
        "payload_sha256": ref["payload_sha256"],
        "payload_size_bytes": ref["payload_size_bytes"],
        "payload_media_type": ref["payload_media_type"],
        "payload_contract": ref["payload_contract"],
        "ref": dict(ref),
    }
    if publisher_execution_id:
        payload["publisher_execution_id"] = publisher_execution_id
    if published_at:
        payload["published_at"] = published_at
    return payload


def _channel_head_entry(
    *,
    ref: Mapping[str, object],
    channel: str,
) -> dict[str, object]:
    return {
        "artifact_family": ref["artifact_family"],
        "artifact_key": ref["artifact_key"],
        "channel": channel,
        "revision_id": ref["artifact_revision_id"],
    }


def _same_oig_artifact_entry(
    left: Mapping[str, object],
    right: Mapping[str, object],
) -> bool:
    return (
        left.get("artifact_family") == right.get("artifact_family")
        and left.get("artifact_key") == right.get("artifact_key")
        and left.get("revision_id") == right.get("revision_id")
    )


def _same_oig_channel_head(
    left: Mapping[str, object],
    right: Mapping[str, object],
) -> bool:
    return (
        left.get("artifact_family") == right.get("artifact_family")
        and left.get("artifact_key") == right.get("artifact_key")
        and left.get("channel") == right.get("channel")
    )


def _oig_producer(ref: Mapping[str, object]) -> HubArtifactProducerProvenance:
    workspace_revision_id = _clean_optional(
        str(ref.get("workspace_revision_id") or "")
    )
    revision_code_package_id = _clean_optional(
        str(ref.get("revision_code_package_id") or "")
    )
    return HubArtifactProducerProvenance(
        producer_kind="workspace",
        producer_key="oig_commit_payload",
        producer_revision_id=workspace_revision_id
        or str(ref["object_instance_graph_commit_id"]),
        source_revision_id=revision_code_package_id or str(ref["commit_id"]),
        source_revision_kind="workspace_revision_code_package",
        metadata={
            "branch_id": ref["branch_id"],
            "projection_hash": ref["projection_hash"],
            "commit_id": ref["commit_id"],
            "domain_commit_id": ref["domain_commit_id"],
            "object_instance_graph_commit_id": ref[
                "object_instance_graph_commit_id"
            ],
        },
    )


def _oig_idempotency_key(ref: Mapping[str, object]) -> str:
    return "oig_commit_payload:" + ":".join(
        (
            str(ref["artifact_family"]),
            str(ref["artifact_key"]),
            str(ref["artifact_revision_id"]),
        )
    )


def _revision_for_channel(
    *,
    index: Mapping[str, object],
    artifact_key: str,
    channel: str,
) -> str:
    for head in _index_sequence(index.get("channel_heads")):
        if (
            str(head.get("artifact_family") or "") == OIG_COMMIT_ARTIFACT_FAMILY
            and str(head.get("artifact_key") or "") == artifact_key
            and str(head.get("channel") or "") == channel
        ):
            return str(head.get("revision_id") or "")
    raise ValueError(
        "hub_oig_payload_authority_channel_head_not_found:"
        + f"artifact_key={artifact_key}"
    )


def _index_sequence(value: object) -> Iterable[dict[str, object]]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _join_url(base_url: str, relative_path: str) -> str:
    base = base_url.rstrip("/")
    relative = relative_path.lstrip("/")
    return f"{base}/{relative}"


def _clean_optional(value: str | None) -> str | None:
    clean = (value or "").strip()
    return clean or None


def _clean_required(value: str, field_name: str) -> str:
    clean = value.strip()
    if clean:
        return clean
    raise ValueError(f"hub_oig_payload_authority_missing:{field_name}")


__all__ = [
    "HubOigCommitPayloadArtifactReceipt",
    "HubOigCommitPayloadRef",
    "OIG_COMMIT_ARTIFACT_FAMILY",
    "OIG_COMMIT_AUTHORITY_KIND",
    "OIG_COMMIT_PAYLOAD_CONTRACT",
    "OIG_COMMIT_PAYLOAD_MEDIA_TYPE",
    "OIG_COMMIT_PAYLOAD_REF_SCHEMA",
    "code_package_descriptor_with_oig_commit_refs",
    "import_oig_commit_refs_from_code_package_descriptor",
    "oig_commit_refs_from_code_package_descriptor",
    "publish_oig_commit_payload_refs_to_hub_artifact_authority",
    "publish_oig_commit_payload_refs_to_authority",
    "resolve_oig_commit_payload_ref_from_hub_artifact_authority",
    "resolve_oig_commit_payload_ref_from_authority",
]
