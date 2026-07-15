from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from aware_comms.http.file.model import DownloadFileRequest, UploadFileResponse
from aware_storage.blob_store import LocalBlobStore
from aware_storage.stable_ids import stable_storage_blob_id
from aware_utils.aware_root import ensure_aware_state_dir, require_aware_root
from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class BlobMetadata:
    id: UUID
    sha: str
    mime_type: str
    size_bytes: int
    filename: str | None
    uploaded_by: UUID
    created_at: str

    def to_json(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "sha": self.sha,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "filename": self.filename,
            "uploaded_by": str(self.uploaded_by),
            "created_at": self.created_at,
        }

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> "BlobMetadata":
        try:
            return cls(
                id=UUID(str(payload["id"])),
                sha=str(payload["sha"]),
                mime_type=str(payload.get("mime_type") or "application/octet-stream"),
                size_bytes=int(payload.get("size_bytes") or 0),
                filename=str(payload["filename"]) if payload.get("filename") else None,
                uploaded_by=UUID(str(payload["uploaded_by"])),
                created_at=str(payload.get("created_at") or ""),
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid blob metadata payload") from exc


_BLOB_STORE: LocalBlobStore | None = None
_BLOB_META_DIR: Path | None = None


def resolve_storage_root() -> Path:
    aware_root = require_aware_root(purpose="Storage blob data-plane")
    aware_dir = ensure_aware_state_dir(aware_root=aware_root, require_writable=True)
    return aware_dir / "blob_store"


def ensure_store() -> tuple[LocalBlobStore, Path]:
    global _BLOB_STORE, _BLOB_META_DIR

    root = resolve_storage_root()
    objects_root = root / "objects"
    meta_root = root / "meta"
    objects_root.mkdir(parents=True, exist_ok=True)
    meta_root.mkdir(parents=True, exist_ok=True)

    if _BLOB_STORE is None or _BLOB_STORE.root != objects_root:  # type: ignore[attr-defined]
        # Store raw bytes so HTTP FileResponse can support media Range behavior.
        _BLOB_STORE = LocalBlobStore(objects_root, compress=False)

    _BLOB_META_DIR = meta_root
    return _BLOB_STORE, meta_root


def read_local_blob_metadata(object_id: UUID) -> BlobMetadata | None:
    _store, meta_root = ensure_store()
    return read_metadata(meta_root, object_id)


def resolve_local_blob_path(sha: str) -> Path:
    store, _meta_root = ensure_store()
    return store._blob_path(sha)


def _upload_chunk_size_bytes() -> int:
    raw = str(os.environ.get("AWARE_BLOB_UPLOAD_CHUNK_BYTES") or "").strip()
    if not raw:
        return 1024 * 1024
    try:
        value = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid AWARE_BLOB_UPLOAD_CHUNK_BYTES={raw!r}") from exc
    return max(16 * 1024, value)


def _upload_max_bytes() -> int | None:
    raw = str(os.environ.get("AWARE_BLOB_UPLOAD_MAX_BYTES") or "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid AWARE_BLOB_UPLOAD_MAX_BYTES={raw!r}") from exc
    if value <= 0:
        return None
    return value


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(payload, indent=None, separators=(",", ":"), sort_keys=True)
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)


def meta_path(meta_root: Path, object_id: UUID) -> Path:
    return meta_root / f"{object_id}.json"


def read_metadata(meta_root: Path, object_id: UUID) -> BlobMetadata | None:
    path = meta_path(meta_root, object_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid blob metadata format")
    return BlobMetadata.from_json(payload)


async def upload_file_handler(file: UploadFile, user_id: UUID) -> UploadFileResponse:
    store, meta_root = ensure_store()

    chunk_size = _upload_chunk_size_bytes()
    max_bytes = _upload_max_bytes()

    mime_type = (file.content_type or "").strip() or "application/octet-stream"
    uploaded_size = 0
    hasher = hashlib.sha256()

    tmp_root = meta_root.parent / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, dir=tmp_root, prefix="upload_", suffix=".tmp"
        ) as fh:
            tmp_path = Path(fh.name)
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                uploaded_size += len(chunk)
                if max_bytes is not None and uploaded_size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Upload too large (max={max_bytes} bytes)",
                    )
                hasher.update(chunk)
                fh.write(chunk)

        if uploaded_size == 0:
            raise HTTPException(status_code=400, detail="Empty upload")

        sha = hasher.hexdigest()
        object_id = stable_storage_blob_id(sha=sha)

        blob_path = store._blob_path(sha)
        if not blob_path.exists():
            blob_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.replace(blob_path)
            tmp_path = None
        else:
            logger.debug("Upload deduplicated: sha=%s already exists", sha)

        meta = BlobMetadata(
            id=object_id,
            sha=sha,
            mime_type=mime_type,
            size_bytes=uploaded_size,
            filename=(file.filename or None),
            uploaded_by=user_id,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        )
        _atomic_write_json(meta_path(meta_root, object_id), meta.to_json())

        logger.info(
            "Stored blob upload object_id=%s sha=%s bytes=%d mime=%s uploaded_by=%s",
            object_id,
            sha,
            uploaded_size,
            mime_type,
            user_id,
        )

        return UploadFileResponse(
            object_id=object_id,
            sha=sha,
            mime_type=mime_type,
            size_bytes=uploaded_size,
        )
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:  # pragma: no cover - best effort cleanup
                pass


async def download_file_handler(
    request: DownloadFileRequest, user_id: UUID
) -> FileResponse:
    store, meta_root = ensure_store()

    meta = read_metadata(meta_root, request.object_id)
    if meta is None:
        raise HTTPException(
            status_code=404, detail=f"Blob metadata not found: {request.object_id}"
        )

    blob_path = store._blob_path(meta.sha)
    if not blob_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Blob content missing for sha={meta.sha}"
        )

    headers: dict[str, str] = {"ETag": meta.sha}
    if os.environ.get("ENVIRONMENT") != "dev":
        headers["Cache-Control"] = "public, max-age=31536000, immutable"

    logger.info(
        "Serving blob download object_id=%s sha=%s path=%s requested_by=%s",
        request.object_id,
        meta.sha,
        blob_path,
        user_id,
    )

    return FileResponse(
        path=str(blob_path),
        media_type=meta.mime_type or "application/octet-stream",
        filename=meta.filename,
        headers=headers,
    )


__all__ = [
    "BlobMetadata",
    "download_file_handler",
    "ensure_store",
    "read_local_blob_metadata",
    "read_metadata",
    "resolve_local_blob_path",
    "resolve_storage_root",
    "upload_file_handler",
]
