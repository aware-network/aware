from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import urlopen
from uuid import UUID

from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)


OIG_COMMIT_PAYLOAD_CONTRACT = "aware.oig_commit_payload.v1"
OIG_COMMIT_PAYLOAD_REF_SCHEMA = "aware.oig_commit_payload_ref.v1"
OIG_COMMIT_PAYLOAD_MEDIA_TYPE = "application/json"
OIG_COMMIT_ARTIFACT_FAMILY = "oig-commit"


@dataclass(frozen=True, slots=True)
class OigCommitPayloadRef:
    """Public locator for one immutable OIG commit payload."""

    ref_schema: str
    payload_contract: str
    branch_id: str
    projection_hash: str
    commit_id: str
    domain_commit_id: str
    object_instance_graph_commit_id: str
    object_instance_graph_identity_id: str
    object_instance_graph_id: str
    graph_hash_post: str
    payload_url: str
    payload_sha256: str
    payload_size_bytes: int
    payload_media_type: str
    artifact_family: str
    artifact_key: str
    artifact_revision_id: str
    source: str | None = None
    workspace_revision_id: str | None = None
    revision_code_package_id: str | None = None
    code_package_id: str | None = None

    def to_metadata(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ref_schema": self.ref_schema,
            "payload_contract": self.payload_contract,
            "branch_id": self.branch_id,
            "projection_hash": self.projection_hash,
            "commit_id": self.commit_id,
            "domain_commit_id": self.domain_commit_id,
            "object_instance_graph_commit_id": self.object_instance_graph_commit_id,
            "object_instance_graph_identity_id": (
                self.object_instance_graph_identity_id
            ),
            "object_instance_graph_id": self.object_instance_graph_id,
            "graph_hash_post": self.graph_hash_post,
            "payload_url": self.payload_url,
            "payload_sha256": self.payload_sha256,
            "payload_size_bytes": self.payload_size_bytes,
            "payload_media_type": self.payload_media_type,
            "artifact_family": self.artifact_family,
            "artifact_key": self.artifact_key,
            "artifact_revision_id": self.artifact_revision_id,
        }
        if self.source is not None:
            payload["source"] = self.source
        if self.workspace_revision_id is not None:
            payload["workspace_revision_id"] = self.workspace_revision_id
        if self.revision_code_package_id is not None:
            payload["revision_code_package_id"] = self.revision_code_package_id
        if self.code_package_id is not None:
            payload["code_package_id"] = self.code_package_id
        return payload


@dataclass(frozen=True, slots=True)
class OigCommitPayloadImportReceipt:
    status: str
    branch_id: str
    projection_hash: str
    commit_id: str
    object_instance_graph_commit_id: str
    payload_sha256: str
    wrote_commit: bool


async def export_oig_commit_payload_ref(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    root_dir: Path | None = None,
    payload_url: str | None = None,
    source: str | None = None,
    workspace_revision_id: UUID | None = None,
    revision_code_package_id: UUID | None = None,
    code_package_id: UUID | None = None,
) -> OigCommitPayloadRef:
    """Export a verified public ref for a local `.aware/oig` commit payload."""

    clean_projection_hash = _required_text(
        projection_hash,
        "projection_hash",
    )
    store = FSCommitStore(root_dir=root_dir)
    commit_path = store.commit_file_path(
        branch_id=branch_id,
        projection_hash=clean_projection_hash,
        commit_id=commit_id,
    )
    if not commit_path.is_file():
        raise RuntimeError(
            "oig_commit_payload_missing:"
            + f"branch_id={branch_id} projection_hash={clean_projection_hash} "
            + f"commit_id={commit_id}"
        )
    payload_bytes = commit_path.read_bytes()
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    commit = await store.get_commit(
        branch_id=branch_id,
        projection_hash=clean_projection_hash,
        commit_id=commit_id,
    )
    if commit is None:
        raise RuntimeError(
            "oig_commit_payload_unreadable:"
            + f"branch_id={branch_id} projection_hash={clean_projection_hash} "
            + f"commit_id={commit_id}"
        )

    return OigCommitPayloadRef(
        ref_schema=OIG_COMMIT_PAYLOAD_REF_SCHEMA,
        payload_contract=OIG_COMMIT_PAYLOAD_CONTRACT,
        branch_id=str(branch_id),
        projection_hash=clean_projection_hash,
        commit_id=str(commit_id),
        domain_commit_id=str(commit_id),
        object_instance_graph_commit_id=str(commit.id),
        object_instance_graph_identity_id=str(commit.object_instance_graph_identity_id),
        object_instance_graph_id=str(commit.object_instance_graph_id),
        graph_hash_post=str(commit.graph_hash_post or ""),
        payload_url=payload_url or commit_path.resolve().as_uri(),
        payload_sha256=payload_sha256,
        payload_size_bytes=len(payload_bytes),
        payload_media_type=OIG_COMMIT_PAYLOAD_MEDIA_TYPE,
        artifact_family=OIG_COMMIT_ARTIFACT_FAMILY,
        artifact_key=_artifact_key(
            branch_id=branch_id,
            projection_hash=clean_projection_hash,
            commit_id=commit_id,
        ),
        artifact_revision_id=str(commit_id),
        source=source,
        workspace_revision_id=(
            str(workspace_revision_id) if workspace_revision_id is not None else None
        ),
        revision_code_package_id=(
            str(revision_code_package_id)
            if revision_code_package_id is not None
            else None
        ),
        code_package_id=str(code_package_id) if code_package_id is not None else None,
    )


async def import_oig_commit_payload_ref(
    *,
    ref: Mapping[str, object],
    root_dir: Path | None = None,
) -> OigCommitPayloadImportReceipt:
    """Verify one public OIG payload ref and install it into local `.aware/oig`."""

    normalized = normalize_oig_commit_payload_ref(ref)
    payload_bytes = _read_payload_bytes(str(normalized["payload_url"]))
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    expected_sha256 = str(normalized["payload_sha256"])
    if payload_sha256 != expected_sha256:
        raise RuntimeError(
            "oig_commit_payload_sha256_mismatch:"
            + f"commit_id={normalized['commit_id']} expected={expected_sha256} "
            + f"actual={payload_sha256}"
        )

    commit = ObjectInstanceGraphCommit.model_validate_json(payload_bytes)
    _validate_commit_against_ref(commit=commit, ref=normalized)

    store = FSCommitStore(root_dir=root_dir)
    wrote_commit = await store.put_commit_file(
        branch_id=UUID(str(normalized["branch_id"])),
        projection_hash=str(normalized["projection_hash"]),
        commit=commit,
    )
    return OigCommitPayloadImportReceipt(
        status="imported",
        branch_id=str(normalized["branch_id"]),
        projection_hash=str(normalized["projection_hash"]),
        commit_id=str(normalized["commit_id"]),
        object_instance_graph_commit_id=str(
            normalized["object_instance_graph_commit_id"]
        ),
        payload_sha256=payload_sha256,
        wrote_commit=wrote_commit,
    )


def normalize_oig_commit_payload_ref(
    ref: Mapping[str, object],
) -> dict[str, object]:
    payload = dict(ref)
    schema = str(payload.get("ref_schema") or "").strip()
    if schema and schema != OIG_COMMIT_PAYLOAD_REF_SCHEMA:
        raise ValueError(f"unsupported_oig_commit_payload_ref_schema:{schema}")
    payload["ref_schema"] = OIG_COMMIT_PAYLOAD_REF_SCHEMA
    payload["payload_contract"] = (
        str(payload.get("payload_contract") or OIG_COMMIT_PAYLOAD_CONTRACT).strip()
    )
    if payload["payload_contract"] != OIG_COMMIT_PAYLOAD_CONTRACT:
        raise ValueError(
            "unsupported_oig_commit_payload_contract:"
            + str(payload["payload_contract"])
        )

    for key in (
        "branch_id",
        "commit_id",
        "domain_commit_id",
        "object_instance_graph_commit_id",
        "object_instance_graph_identity_id",
        "object_instance_graph_id",
    ):
        payload[key] = str(_required_uuid(payload.get(key), key))
    payload["projection_hash"] = _required_text(
        payload.get("projection_hash"),
        "projection_hash",
    )
    if payload["commit_id"] != payload["domain_commit_id"]:
        raise ValueError("oig_commit_payload_ref_commit_id_mismatch")

    payload["graph_hash_post"] = _required_text(
        payload.get("graph_hash_post"),
        "graph_hash_post",
    )
    payload["payload_url"] = _required_text(payload.get("payload_url"), "payload_url")
    payload["payload_sha256"] = _required_sha256(
        payload.get("payload_sha256"),
        "payload_sha256",
    )
    payload["payload_size_bytes"] = _required_positive_int(
        payload.get("payload_size_bytes"),
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
    payload["artifact_key"] = str(
        payload.get("artifact_key")
        or _artifact_key(
            branch_id=UUID(str(payload["branch_id"])),
            projection_hash=str(payload["projection_hash"]),
            commit_id=UUID(str(payload["commit_id"])),
        )
    ).strip()
    payload["artifact_revision_id"] = str(
        payload.get("artifact_revision_id") or payload["commit_id"]
    ).strip()
    return payload


def _validate_commit_against_ref(
    *,
    commit: ObjectInstanceGraphCommit,
    ref: Mapping[str, object],
) -> None:
    if str(commit.commit.id) != str(ref["commit_id"]):
        raise RuntimeError("oig_commit_payload_commit_id_mismatch")
    if str(commit.id) != str(ref["object_instance_graph_commit_id"]):
        raise RuntimeError("oig_commit_payload_oig_commit_id_mismatch")
    if str(commit.object_instance_graph_identity_id) != str(
        ref["object_instance_graph_identity_id"]
    ):
        raise RuntimeError("oig_commit_payload_identity_id_mismatch")
    if str(commit.object_instance_graph_id) != str(ref["object_instance_graph_id"]):
        raise RuntimeError("oig_commit_payload_graph_id_mismatch")
    if str(commit.projection_hash or "") != str(ref["projection_hash"]):
        raise RuntimeError("oig_commit_payload_projection_hash_mismatch")
    if str(commit.graph_hash_post or "") != str(ref["graph_hash_post"]):
        raise RuntimeError("oig_commit_payload_graph_hash_post_mismatch")


def _read_payload_bytes(payload_url: str) -> bytes:
    parsed = urlparse(payload_url)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).read_bytes()
    if parsed.scheme in {"http", "https"}:
        with urlopen(payload_url, timeout=30) as response:  # nosec B310
            return response.read()
    raise ValueError(f"unsupported_oig_commit_payload_url:{payload_url}")


def _artifact_key(*, branch_id: UUID, projection_hash: str, commit_id: UUID) -> str:
    return f"{branch_id}:{projection_hash}:{commit_id}"


def _required_text(value: object, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"oig_commit_payload_ref_missing:{field_name}")


def _required_uuid(value: object, field_name: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return UUID(value.strip())
        except ValueError as exc:
            raise ValueError(
                f"oig_commit_payload_ref_invalid_uuid:{field_name}"
            ) from exc
    raise ValueError(f"oig_commit_payload_ref_missing:{field_name}")


def _required_sha256(value: object, field_name: str) -> str:
    text = _required_text(value, field_name)
    if len(text) == 64 and all(char in "0123456789abcdef" for char in text):
        return text
    raise ValueError(f"oig_commit_payload_ref_invalid_sha256:{field_name}")


def _required_positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"oig_commit_payload_ref_invalid_int:{field_name}")
    if isinstance(value, int) and value > 0:
        return value
    raise ValueError(f"oig_commit_payload_ref_invalid_int:{field_name}")


__all__ = [
    "OIG_COMMIT_ARTIFACT_FAMILY",
    "OIG_COMMIT_PAYLOAD_CONTRACT",
    "OIG_COMMIT_PAYLOAD_MEDIA_TYPE",
    "OIG_COMMIT_PAYLOAD_REF_SCHEMA",
    "OigCommitPayloadImportReceipt",
    "OigCommitPayloadRef",
    "export_oig_commit_payload_ref",
    "import_oig_commit_payload_ref",
    "normalize_oig_commit_payload_ref",
]
