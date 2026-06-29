from pathlib import Path

from aware_storage_ontology.bucket.storage_bucket_enums import StorageBackend
from aware_storage_ontology.blob.storage_blob import StorageBlob
from aware_storage_ontology.bucket.storage_bucket import StorageBucket

from aware_storage.blob_handlers import create_blob_from_content
from aware_storage.blob_store import BlobStore, LocalBlobStore, InMemoryBlobStore

from aware_utils.logging import logger


def create_blob_store(bucket: StorageBucket) -> BlobStore:
    """
    Create a BlobStore instance for this bucket.

    Returns:
        BlobStore implementation instance
    """
    if bucket.backend == StorageBackend.local:
        if bucket.config:
            path_local = bucket.config.get("path_local", f"/var/aware/blobs/{bucket.name}")
            root = Path(path_local)
            blob_store = LocalBlobStore(root)
            logger.debug(f"Created LocalBlobStore for bucket {bucket.name} at {root}")
        else:
            raise ValueError(f"Bucket {bucket.name} has no config")

    elif bucket.backend == StorageBackend.memory:
        blob_store = InMemoryBlobStore()
        logger.debug(f"Created InMemoryBlobStore for bucket {bucket.name}")

    elif bucket.backend == StorageBackend.s3:
        raise NotImplementedError("S3 backend not yet implemented")

    elif bucket.backend == StorageBackend.gcs:
        raise NotImplementedError("GCS backend not yet implemented")

    elif bucket.backend == StorageBackend.azure:
        raise NotImplementedError("Azure backend not yet implemented")

    else:
        raise ValueError(f"Unsupported storage backend: {bucket.backend}")

    return blob_store


def put_blob(
    bucket: StorageBucket,
    content: bytes | str,
    blob_store: BlobStore,
    mime_type: str = "text/plain",
) -> StorageBlob:
    """
    Store content in this bucket and create a StorageBlob record.

    Args:
        bucket: Storage bucket to use
        blob_store: Blob store to use
        content: Content to store (bytes or string)
        mime_type: MIME type of the content

    Returns:
        StorageBlob record
    """
    return create_blob_from_content(content=content, bucket=bucket, blob_store=blob_store, mime_type=mime_type)


def delete_blob_by_sha(bucket: StorageBucket, blob_store: BlobStore, sha: str) -> bool:
    """
    Delete a blob by SHA hash from both storage backend and database.

    Args:
        bucket: Storage bucket to use
        blob_store: Blob store to use
        sha: SHA-256 hash of the blob

    Returns:
        True if deleted, False if not found
    """
    # Delete from storage backend
    backend_deleted = blob_store.delete(sha)

    if backend_deleted:
        # TODO: Delete from database when ORM session is available
        # StorageBlob.meta_delete_many(
        #     filters=[
        #         EqFilter(column="sha", value=sha),
        #         EqFilter(column="bucket_id", value=self.id)
        #     ]
        # )
        logger.info(f"Deleted blob {sha[:8]}... from bucket {bucket.name}")

    return backend_deleted


def get_stats(bucket: StorageBucket, blob_store: BlobStore) -> dict:
    """Get storage statistics for this bucket."""
    base_stats = getattr(blob_store, "get_stats", lambda: {})()

    return {
        "bucket_name": bucket.name,
        "backend": bucket.backend.value,
        "config": bucket.config,
        **base_stats,
    }
