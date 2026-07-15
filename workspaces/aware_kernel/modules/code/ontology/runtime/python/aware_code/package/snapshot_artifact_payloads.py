from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from aware_code.package.snapshot_json import atomic_write_json, read_json_object_or_none
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_artifact import CodePackageArtifactRef
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore


CODE_PACKAGE_ARTIFACT_PAYLOAD_BUNDLE_SCHEMA = (
    "aware.code.package.artifact_payload_bundle.v1"
)


def code_package_artifact_refs_require_payload_bundle(
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> bool:
    return any(
        "workspace_revision" in artifact_ref.required_for
        and _is_embedded_package_artifact(artifact_ref=artifact_ref)
        for artifact_ref in code_package_artifact_refs
    )


def write_code_package_artifact_payload_bundle(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package: CodePackage,
    commit_id: UUID,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> None:
    bundle_root = _artifact_payload_bundle_root(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package.id,
        commit_id=commit_id,
    )
    artifacts: list[dict[str, object]] = []
    for artifact_ref in sorted(
        code_package_artifact_refs,
        key=lambda item: (item.output_key, item.artifact_key),
    ):
        if "workspace_revision" not in artifact_ref.required_for:
            continue
        if not _is_embedded_package_artifact(artifact_ref=artifact_ref):
            continue
        if artifact_ref.relative_path is None:
            continue
        source_path = _artifact_payload_source_path(
            store=store,
            code_package=code_package,
            artifact_ref=artifact_ref,
        )
        content = source_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        expected_digest = (artifact_ref.digest or "").strip().lower()
        if not expected_digest:
            raise RuntimeError(
                "CodePackage artifact payload requires a producer digest: "
                f"code_package_id={code_package.id} "
                f"artifact_key={artifact_ref.artifact_key!r}"
            )
        if digest != expected_digest:
            raise RuntimeError(
                "CodePackage artifact payload digest mismatch: "
                f"code_package_id={code_package.id} "
                f"artifact_key={artifact_ref.artifact_key!r} "
                f"expected={expected_digest} actual={digest}"
            )
        package_relative_path = _artifact_package_relative_path(
            store=store,
            code_package=code_package,
            source_path=source_path,
        )
        blob_path = bundle_root / "blobs" / f"{digest}.bin"
        _atomic_write_bytes(path=blob_path, content=content)
        artifacts.append(
            {
                "artifact_key": artifact_ref.artifact_key,
                "output_key": artifact_ref.output_key,
                "relative_path": package_relative_path,
                "sha256": digest,
                "byte_length": len(content),
                "blob_relative_path": f"blobs/{digest}.bin",
            }
        )
    atomic_write_json(
        bundle_root / "manifest.json",
        {
            "schema": CODE_PACKAGE_ARTIFACT_PAYLOAD_BUNDLE_SCHEMA,
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "code_package_id": str(code_package.id),
            "commit_id": str(commit_id),
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )


def load_code_package_artifact_payloads_at_commit(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    commit_id: UUID,
) -> dict[str, bytes]:
    bundle_root = _artifact_payload_bundle_root(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        commit_id=commit_id,
    )
    payload = read_json_object_or_none(bundle_root / "manifest.json")
    if payload is None:
        return {}
    _validate_payload_manifest(
        payload=payload,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        commit_id=commit_id,
    )
    raw_artifacts = payload.get("artifacts")
    if not isinstance(raw_artifacts, list):
        raise RuntimeError(
            "CodePackage artifact payload manifest artifacts must be a list"
        )
    result: dict[str, bytes] = {}
    for raw_artifact in raw_artifacts:
        if not isinstance(raw_artifact, Mapping):
            raise RuntimeError(
                "CodePackage artifact payload manifest row must be an object"
            )
        relative_path = _required_manifest_text(raw_artifact, "relative_path")
        digest = _required_manifest_text(raw_artifact, "sha256").lower()
        blob_relative_path = _required_manifest_text(
            raw_artifact,
            "blob_relative_path",
        )
        blob_path = (bundle_root / blob_relative_path).resolve()
        if not _is_relative_to(path=blob_path, parent=bundle_root.resolve()):
            raise RuntimeError(
                "CodePackage artifact payload manifest references an unsafe blob path: "
                f"blob_relative_path={blob_relative_path!r}"
            )
        if not blob_path.is_file():
            raise RuntimeError(
                "CodePackage artifact payload blob is missing: "
                f"code_package_id={code_package_id} commit_id={commit_id} "
                f"relative_path={relative_path!r}"
            )
        content = blob_path.read_bytes()
        actual_digest = hashlib.sha256(content).hexdigest()
        if actual_digest != digest:
            raise RuntimeError(
                "CodePackage artifact payload blob digest mismatch: "
                f"relative_path={relative_path!r} expected={digest} "
                f"actual={actual_digest}"
            )
        raw_byte_length = raw_artifact.get("byte_length")
        if not isinstance(raw_byte_length, int) or raw_byte_length != len(content):
            raise RuntimeError(
                "CodePackage artifact payload blob length mismatch: "
                f"relative_path={relative_path!r}"
            )
        if relative_path in result:
            raise RuntimeError(
                "CodePackage artifact payload manifest contains duplicate paths: "
                f"relative_path={relative_path!r}"
            )
        result[relative_path] = content
    if payload.get("artifact_count") != len(result):
        raise RuntimeError("CodePackage artifact payload manifest count mismatch")
    return result


def code_package_artifact_payload_bundle_satisfies_refs_at_commit(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    commit_id: UUID,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> bool:
    expected_digests_by_path: dict[str, str] = {}
    for artifact_ref in code_package_artifact_refs:
        if "workspace_revision" not in artifact_ref.required_for:
            continue
        if not _is_embedded_package_artifact(artifact_ref=artifact_ref):
            continue
        relative_path = (artifact_ref.relative_path or "").strip().strip("/")
        digest = (artifact_ref.digest or "").strip().lower()
        if not relative_path or not digest:
            return False
        existing_digest = expected_digests_by_path.get(relative_path)
        if existing_digest is not None and existing_digest != digest:
            return False
        expected_digests_by_path[relative_path] = digest
    if not expected_digests_by_path:
        return True
    try:
        payloads = load_code_package_artifact_payloads_at_commit(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            commit_id=commit_id,
        )
    except RuntimeError:
        return False
    if set(payloads) != set(expected_digests_by_path):
        return False
    return all(
        hashlib.sha256(payloads[path]).hexdigest() == digest
        for path, digest in expected_digests_by_path.items()
    )


def _artifact_payload_bundle_root(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    commit_id: UUID,
) -> Path:
    return (
        store.aware_root
        / ".aware"
        / "oig"
        / str(branch_id)
        / projection_hash
        / "indexes"
        / "code_package_artifact_payloads"
        / str(code_package_id)
        / str(commit_id)
    )


def _is_embedded_package_artifact(*, artifact_ref: CodePackageArtifactRef) -> bool:
    receipt_payload = artifact_ref.receipt_payload
    return (
        isinstance(receipt_payload, Mapping)
        and receipt_payload.get("output_kind") == "embedded_artifact"
    )


def _artifact_payload_source_path(
    *,
    store: FSCommitStore,
    code_package: CodePackage,
    artifact_ref: CodePackageArtifactRef,
) -> Path:
    receipt_payload = artifact_ref.receipt_payload
    if isinstance(receipt_payload, Mapping):
        raw_path = receipt_payload.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            source_path = Path(raw_path).expanduser().resolve()
            if not _is_relative_to(
                path=source_path,
                parent=store.aware_root.resolve(),
            ):
                raise RuntimeError(
                    "CodePackage artifact producer path is outside authority root: "
                    f"path={source_path.as_posix()}"
                )
            if not source_path.is_file():
                raise RuntimeError(
                    "CodePackage artifact producer path is not a file: "
                    f"path={source_path.as_posix()}"
                )
            return source_path
    relative_path = Path(artifact_ref.relative_path or "")
    source_path = (
        store.aware_root / code_package.package_root / relative_path
    ).resolve()
    package_root = (store.aware_root / code_package.package_root).resolve()
    if not _is_relative_to(path=source_path, parent=package_root):
        raise RuntimeError(
            "CodePackage artifact relative path escapes its package root: "
            f"relative_path={artifact_ref.relative_path!r}"
        )
    if not source_path.is_file():
        raise RuntimeError(
            "CodePackage artifact payload source is missing: "
            f"path={source_path.as_posix()}"
        )
    return source_path


def _artifact_package_relative_path(
    *,
    store: FSCommitStore,
    code_package: CodePackage,
    source_path: Path,
) -> str:
    package_root = (store.aware_root / code_package.package_root).resolve()
    try:
        relative_path = source_path.relative_to(package_root)
    except ValueError as exc:
        raise RuntimeError(
            "CodePackage artifact producer path is outside its declared package root: "
            f"package_root={package_root.as_posix()} "
            f"path={source_path.as_posix()}"
        ) from exc
    if not relative_path.parts:
        raise RuntimeError(
            "CodePackage artifact payload path cannot be the package root"
        )
    return relative_path.as_posix()


def _validate_payload_manifest(
    *,
    payload: Mapping[str, object],
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    commit_id: UUID,
) -> None:
    expected = {
        "schema": CODE_PACKAGE_ARTIFACT_PAYLOAD_BUNDLE_SCHEMA,
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "code_package_id": str(code_package_id),
        "commit_id": str(commit_id),
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            raise RuntimeError(
                "CodePackage artifact payload manifest identity mismatch: "
                f"field={key} expected={expected_value!r} actual={payload.get(key)!r}"
            )


def _required_manifest_text(payload: Mapping[object, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            "CodePackage artifact payload manifest requires text field: " f"field={key}"
        )
    return value.strip()


def _atomic_write_bytes(*, path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def _is_relative_to(*, path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


__all__ = [
    "CODE_PACKAGE_ARTIFACT_PAYLOAD_BUNDLE_SCHEMA",
    "code_package_artifact_refs_require_payload_bundle",
    "code_package_artifact_payload_bundle_satisfies_refs_at_commit",
    "load_code_package_artifact_payloads_at_commit",
    "write_code_package_artifact_payload_bundle",
]
