from pathlib import Path

from aware_storage.blob_store import (
    BlobStore,
    LazyBlobContent,
    LocalBlobStore,
    compute_blob_hash,
)

from aware_storage_ontology.bucket.storage_bucket import StorageBucket
from aware_storage_ontology.blob.storage_blob import StorageBlob

from aware_orm.filters import EqFilter, FilterType

from aware_utils.logging import logger


def create_blob_from_content(
    content: bytes | str,
    bucket: StorageBucket,
    blob_store: BlobStore,
    mime_type: str = "text/plain",
) -> StorageBlob:
    """
    Create a StorageBlob by storing content in the specified blob store.

    Args:
        content: Content to store (bytes or string)
        bucket: Storage bucket to use
        blob_store: Blob store to use
        mime_type: MIME type of the content

    Returns:
        StorageBlob record
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    # Compute SHA hash
    sha = compute_blob_hash(content)

    # Store in the storage backend if it doesn't exist
    if not blob_store.exists(sha):
        blob_store.put(sha, content)
        logger.debug(f"🔧 Created new blob file {sha[:8]}... in storage")
    else:
        logger.debug(f"✅ Blob file {sha[:8]}... already exists in storage")

    # Create database record
    blob = StorageBlob(
        sha=sha,
        bucket_id=bucket.id,
        bucket=bucket,
        mime_type=mime_type,
        size_bytes=len(content),
        object_key=f"{sha[:2]}/{sha[2:]}",  # Git-like path structure
        path_local=(str(blob_store._blob_path(sha)) if isinstance(blob_store, LocalBlobStore) else None),
    )
    logger.debug(f"🔧 Created new blob record {sha[:8]}... in bucket {bucket.name} ({len(content)} bytes)")
    return blob


def lazy_text(blob: StorageBlob, blob_store: BlobStore) -> LazyBlobContent:
    """
    Get lazy-loading text content that only fetches from storage when accessed.

    Returns:
        LazyBlobContent instance that behaves like a string
    """
    if not blob.bucket:
        if blob.bucket_id:
            blob.bucket = StorageBucket.get_by_id_sync(blob.bucket_id)
            if not blob.bucket:
                raise ValueError(f"Bucket {blob.bucket_id} not found")
        else:
            raise ValueError(f"Blob {blob.sha[:8]}... has no bucket reference")

    return LazyBlobContent(blob.sha, blob_store)


def get_content(blob: StorageBlob, blob_store: BlobStore) -> bytes:
    """
    Retrieve content for this blob from storage.

    Returns:
        Content bytes

    Raises:
        ValueError: If blob has no bucket reference
        KeyError: If blob not found in storage backend
    """
    if not blob.bucket:
        if blob.bucket_id:
            blob.bucket = StorageBucket.get_by_id_sync(blob.bucket_id)
            if not blob.bucket:
                raise ValueError(f"Bucket {blob.bucket_id} not found")
        else:
            raise ValueError(f"Blob {blob.sha[:8]}... has no bucket reference")

    content = blob_store.get(blob.sha)
    logger.debug(f"Retrieved blob {blob.sha[:8]}... ({len(content)} bytes)")
    return content


def get_content_as_text(blob: StorageBlob, blob_store: BlobStore, encoding: str = "utf-8") -> str:
    """
    Retrieve content as decoded text (immediate fetch).

    Args:
        encoding: Text encoding to use

    Returns:
        Content as string
    """
    content_bytes = get_content(blob, blob_store)
    return content_bytes.decode(encoding)


def as_text(blob: StorageBlob, blob_store: BlobStore) -> LazyBlobContent:
    """
    Alias for lazy_text() - returns lazy-loading text content.

    Returns:
        LazyBlobContent instance that behaves like a string
    """
    return lazy_text(blob, blob_store)


def exists_in_storage(blob: StorageBlob, blob_store: BlobStore) -> bool:
    """
    Check if this blob exists in the storage backend.

    Returns:
        True if blob exists in storage
    """
    if not blob.bucket:
        return False

    return blob_store.exists(blob.sha)


def delete_from_storage(blob: StorageBlob, blob_store: BlobStore) -> bool:
    """
    Delete this blob from both storage backend and database.

    Returns:
        True if deleted, False if not found
    """
    if not blob.bucket:
        logger.warning(f"Blob {blob.sha[:8]}... has no bucket reference")
        return False

    # Delete from storage backend
    backend_deleted = blob_store.delete(blob.sha)

    # TODO: Delete from database when ORM session is available
    # session.delete(self)
    # session.commit()

    if backend_deleted:
        logger.info(f"Deleted blob {blob.sha[:8]}... from bucket {blob.bucket.name}")

    return backend_deleted


def get_path_info(blob: StorageBlob) -> dict:
    """
    Get path information for this blob.

    Returns:
        Dictionary with path information
    """
    return {
        "sha": blob.sha,
        "object_key": blob.object_key,
        "path_local": blob.path_local,
        "bucket_name": blob.bucket.name if blob.bucket else None,
        "backend": blob.bucket.backend.value if blob.bucket else None,
    }


async def check_blob_deduplication(sha: str, bucket: StorageBucket) -> StorageBlob | None:
    """
    Check if a blob already exists in the database by SHA and bucket.

    Returns:
        StorageBlob if found, None otherwise
    """
    try:
        filters: list[FilterType] = [
            EqFilter(column="sha", value=sha),
            EqFilter(column="bucket_id", value=str(bucket.id)),
        ]
        existing_blob = await StorageBlob.get(filters=filters)
        if existing_blob:
            logger.debug(f"✅ Reusing existing blob {sha[:8]}... in bucket {bucket.name}")
            return existing_blob

    except Exception as e:
        # Fallback to creating new blob if lookup fails
        logger.debug(f"Blob lookup failed, creating new: {e}")

    return None


def get_by_sha(sha: str, bucket: StorageBucket | None = None) -> StorageBlob | None:
    """
    Get a StorageBlob by SHA hash.

    Args:
        sha: SHA-256 hash
        bucket: Optional bucket to search in (if None, searches all buckets)

    Returns:
        StorageBlob if found, None otherwise
    """
    # TODO: Replace with proper ORM query when available
    # filters = [EqFilter(column="sha", value=sha)]
    # if bucket:
    #     filters.append(EqFilter(column="bucket_id", value=bucket.id))
    # return cls.meta_get(filters=filters)

    logger.debug(f"Looking for blob {sha[:8]}... (ORM query not implemented yet)")
    return None


def find_by_content(content: bytes | str, bucket: StorageBucket | None = None) -> StorageBlob | None:
    """
    Find a StorageBlob by its content (computes SHA and searches).

    Args:
        content: Content to find
        bucket: Optional bucket to search in

    Returns:
        StorageBlob if found, None otherwise
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    sha = compute_blob_hash(content)
    return get_by_sha(sha, bucket)


def get_mime_type_for_path(path: Path) -> str:
    """
    Get MIME type for a file path (static method for convenience).

    Args:
        path: File path

    Returns:
        MIME type string
    """
    suffix = path.suffix.lower()
    mime_map = {
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".json": "application/json",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".html": "text/html",
        ".css": "text/css",
        ".sql": "text/x-sql",
    }
    return mime_map.get(suffix, "text/plain")
