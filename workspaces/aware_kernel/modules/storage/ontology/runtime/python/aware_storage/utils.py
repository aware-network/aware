"""High-level storage helpers for working with `StorageBlob` references.

This module is intentionally **provider-native** and does not depend on Supabase.

Current canonical behavior:
- `StorageBlob` records are treated as metadata that point to content-addressable blobs (SHA-256).
- The concrete storage backend is resolved from the associated `StorageBucket` (LOCAL/MEMORY today; S3/GCS/AZURE via injection later).

Notes:
- Access control is a separate concern. This module provides an optional hook for an access checker.
- For async callers, sync backend reads are executed in `asyncio.to_thread()` to avoid blocking the loop.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Awaitable, Callable
from uuid import UUID

from aware_storage_ontology.blob.storage_blob import StorageBlob
from aware_storage_ontology.bucket.storage_bucket import StorageBucket
from aware_storage_ontology.bucket.storage_bucket_enums import StorageBackend

from aware_storage.bucket_handlers import create_blob_store
from aware_storage.blob_store import BlobStore, LocalBlobStore

from aware_utils.logging import logger

BlobAccessChecker = Callable[[UUID, StorageBlob], Awaitable[None]]

_access_checker: BlobAccessChecker | None = None
_blob_store_cache: dict[UUID, BlobStore] = {}
_EXECUTOR: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(
            max_workers=int(os.getenv("AWARE_STORAGE_IO_WORKERS", "4")),
            thread_name_prefix="aware-storage-io",
        )
    return _EXECUTOR


def set_blob_access_checker(checker: BlobAccessChecker | None) -> None:
    """Install an optional access-check hook.

    If set, the checker is called for `download_*` operations before reading content.
    """

    global _access_checker
    _access_checker = checker


def clear_blob_store_cache() -> None:
    """Clear per-bucket blob store cache (tests/tools)."""

    _blob_store_cache.clear()


async def _get_storage_blob(object_id: UUID) -> StorageBlob:
    blob = await StorageBlob.get_by_id(object_id)
    if blob is None:
        raise FileNotFoundError(f"StorageBlob not found: {object_id}")
    return blob


async def _hydrate_bucket(blob: StorageBlob) -> StorageBucket | None:
    if blob.bucket is not None:
        return blob.bucket
    if blob.bucket_id is None:
        return None

    bucket = StorageBucket.get_by_id_sync(blob.bucket_id)
    if bucket is None:
        bucket = await StorageBucket.get_by_id(blob.bucket_id)
    blob.bucket = bucket
    return bucket


def _derive_local_root_from_path_local(path_local: str) -> Path:
    path = Path(path_local)
    # LocalBlobStore stores blobs at: <root>/<sha[:2]>/<sha[2:]>
    # so root is two levels up from the file.
    return path.parent.parent


def _resolve_blob_store(*, blob: StorageBlob, bucket: StorageBucket | None) -> BlobStore:
    # Prefer explicit bucket resolution.
    if bucket is not None and bucket.id is not None:
        cached = _blob_store_cache.get(bucket.id)
        if cached is not None:
            return cached

        try:
            store = create_blob_store(bucket)
        except Exception:
            if bucket.backend == StorageBackend.local and blob.path_local:
                store = LocalBlobStore(_derive_local_root_from_path_local(blob.path_local))
            else:
                raise

        _blob_store_cache[bucket.id] = store
        return store

    # Fallback: infer local store root from `path_local` when present.
    if blob.path_local:
        return LocalBlobStore(_derive_local_root_from_path_local(blob.path_local))

    raise ValueError("Unable to resolve blob store: StorageBlob has no bucket and no path_local")


async def download_blob_bytes(
    *,
    finance_entity_id: UUID,
    object_id: UUID,
    require_ownership: bool = False,
) -> bytes:
    """Resolve a `StorageBlob` to raw bytes.

    Args:
        finance_entity_id: Caller identity (reserved for access control hooks).
        object_id: `StorageBlob.id`
        require_ownership: Reserved for future policy (currently enforced by access checker if installed).
    """

    if require_ownership:
        logger.debug(
            "download_blob_bytes(require_ownership=True): ownership enforcement is delegated to access checker"
        )

    blob = await _get_storage_blob(object_id)

    if _access_checker is not None:
        await _access_checker(finance_entity_id, blob)

    bucket = await _hydrate_bucket(blob)
    store = _resolve_blob_store(blob=blob, bucket=bucket)

    try:
        loop = asyncio.get_running_loop()
        logger.debug(
            "download_blob_bytes: reading sha=%s backend=%s",
            blob.sha,
            getattr(bucket, "backend", None),
        )
        data = await loop.run_in_executor(_get_executor(), store.get, blob.sha)
        logger.debug("download_blob_bytes: read complete sha=%s bytes=%d", blob.sha, len(data))
        return data
    except KeyError as exc:
        raise FileNotFoundError(f"Blob content missing for sha={blob.sha}") from exc


async def download_file(
    finance_entity_id: UUID,
    object_id: UUID,
    save_path: str | None = None,
    require_ownership: bool = False,
) -> str:
    """Download a blob and materialize it on disk.

    Returns:
        Local filesystem path containing the blob bytes.
    """

    data = await download_blob_bytes(
        finance_entity_id=finance_entity_id,
        object_id=object_id,
        require_ownership=require_ownership,
    )

    if save_path is None:
        with tempfile.NamedTemporaryFile(mode="wb", prefix="download_", delete=False) as temp_file:
            save_path = temp_file.name

    path = Path(save_path)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_get_executor(), path.write_bytes, data)
    return str(path)


def get_mime_type(file_path: str) -> str:
    """Get the MIME type of a file."""

    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


__all__ = [
    "BlobAccessChecker",
    "clear_blob_store_cache",
    "download_blob_bytes",
    "download_file",
    "get_mime_type",
    "set_blob_access_checker",
]
