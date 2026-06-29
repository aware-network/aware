"""
Blob Store - Content-addressable storage for repository content.

Provides Git-like content storage with:
- Content-addressable blobs (SHA-256 keyed)
- Pluggable storage backends (local filesystem, S3, etc.)
- Deduplication and compression
- Lazy loading support
"""

from __future__ import annotations
import gzip
import hashlib
from pathlib import Path
from typing import Protocol

# Logging
from aware_utils.logging import logger


class BlobStore(Protocol):
    """Protocol for content-addressable blob storage."""

    def put(self, sha: str, content: bytes) -> None:
        """Store content under the given SHA-256 hash."""
        ...

    def get(self, sha: str) -> bytes:
        """Retrieve content by SHA-256 hash."""
        ...

    def exists(self, sha: str) -> bool:
        """Check if a blob exists."""
        ...

    def delete(self, sha: str) -> bool:
        """Delete a blob. Returns True if deleted, False if not found."""
        ...

    def list_blobs(self) -> list[str]:
        """List all blob hashes in the store."""
        ...


class LocalBlobStore:
    """
    Local filesystem implementation of blob storage.

    Stores blobs in a Git-like directory structure:
    - objects/12/34567890abcdef... (first 2 chars as subdirectory)
    - Content is optionally gzip compressed (default: enabled)
    - Atomic writes with temporary files
    """

    def __init__(self, root: Path, *, compress: bool = True):
        """
        Initialize local blob store.

        Args:
            root: Root directory for blob storage
            compress: When True, store blobs gzip-compressed on disk.
                When False, store raw bytes (recommended for multimedia).
        """
        self.root = Path(root)
        self.compress = compress
        self.root.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized LocalBlobStore at {self.root}")

    def _blob_path(self, sha: str) -> Path:
        """Get the file path for a blob hash."""
        if len(sha) < 2:
            raise ValueError(f"Invalid SHA hash: {sha}")
        return self.root / sha[:2] / sha[2:]

    def put(self, sha: str, content: bytes) -> None:
        """Store content under the given SHA-256 hash."""
        blob_path = self._blob_path(sha)

        # Skip if already exists (deduplication)
        if blob_path.exists():
            logger.debug(f"Blob {sha[:8]}... already exists, skipping")
            return

        # Create parent directory
        blob_path.parent.mkdir(parents=True, exist_ok=True)

        # Compress content (optional)
        stored = gzip.compress(content) if self.compress else content

        # Atomic write using temporary file
        temp_path = blob_path.with_suffix(".tmp")
        try:
            temp_path.write_bytes(stored)
            temp_path.rename(blob_path)
            if self.compress:
                logger.debug(f"Stored blob {sha[:8]}... ({len(content)} -> {len(stored)} bytes)")
            else:
                logger.debug(f"Stored blob {sha[:8]}... ({len(stored)} bytes)")
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to store blob {sha[:8]}...") from e

    def get(self, sha: str) -> bytes:
        """Retrieve content by SHA-256 hash."""
        blob_path = self._blob_path(sha)

        if not blob_path.exists():
            raise KeyError(f"Blob not found: {sha[:8]}...")

        try:
            stored = blob_path.read_bytes()
            if self.compress:
                content = gzip.decompress(stored)
                logger.debug(f"Retrieved blob {sha[:8]}... ({len(stored)} -> {len(content)} bytes)")
                return content
            logger.debug(f"Retrieved blob {sha[:8]}... ({len(stored)} bytes)")
            return stored
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve blob {sha[:8]}...") from e

    def exists(self, sha: str) -> bool:
        """Check if a blob exists."""
        return self._blob_path(sha).exists()

    def delete(self, sha: str) -> bool:
        """Delete a blob. Returns True if deleted, False if not found."""
        blob_path = self._blob_path(sha)

        if not blob_path.exists():
            return False

        try:
            blob_path.unlink()
            logger.debug(f"Deleted blob {sha[:8]}...")

            # Try to remove empty parent directory
            try:
                blob_path.parent.rmdir()
            except OSError:
                pass  # Directory not empty, that's fine

            return True
        except Exception as e:
            logger.warning(f"Failed to delete blob {sha[:8]}...: {e}")
            return False

    def list_blobs(self) -> list[str]:
        """List all blob hashes in the store."""
        blobs = []

        if not self.root.exists():
            return blobs

        for prefix_dir in self.root.iterdir():
            if not prefix_dir.is_dir() or len(prefix_dir.name) != 2:
                continue

            for blob_file in prefix_dir.iterdir():
                if blob_file.is_file():
                    # Reconstruct full hash
                    full_hash = prefix_dir.name + blob_file.name
                    blobs.append(full_hash)

        return sorted(blobs)

    def get_stats(self) -> dict:
        """Get storage statistics."""
        blobs = self.list_blobs()
        total_size = 0

        for sha in blobs:
            blob_path = self._blob_path(sha)
            if blob_path.exists():
                total_size += blob_path.stat().st_size

        return {
            "blob_count": len(blobs),
            "total_size_bytes": total_size,
            "root_path": str(self.root),
        }


class InMemoryBlobStore:
    """
    In-memory blob store for testing.

    Stores all blobs in memory without compression.
    Useful for unit tests and temporary storage.
    """

    def __init__(self):
        """Initialize in-memory blob store."""
        self._blobs: dict[str, bytes] = {}
        logger.debug("Initialized InMemoryBlobStore")

    def put(self, sha: str, content: bytes) -> None:
        """Store content under the given SHA-256 hash."""
        self._blobs[sha] = content
        logger.debug(f"Stored blob {sha[:8]}... ({len(content)} bytes)")

    def get(self, sha: str) -> bytes:
        """Retrieve content by SHA-256 hash."""
        if sha not in self._blobs:
            raise KeyError(f"Blob not found: {sha[:8]}...")

        content = self._blobs[sha]
        logger.debug(f"Retrieved blob {sha[:8]}... ({len(content)} bytes)")
        return content

    def exists(self, sha: str) -> bool:
        """Check if a blob exists."""
        return sha in self._blobs

    def delete(self, sha: str) -> bool:
        """Delete a blob. Returns True if deleted, False if not found."""
        if sha in self._blobs:
            del self._blobs[sha]
            logger.debug(f"Deleted blob {sha[:8]}...")
            return True
        return False

    def list_blobs(self) -> list[str]:
        """List all blob hashes in the store."""
        return sorted(self._blobs.keys())

    def clear(self) -> None:
        """Clear all blobs (for testing)."""
        self._blobs.clear()
        logger.debug("Cleared all blobs")

    def get_stats(self) -> dict:
        """Get storage statistics."""
        total_size = sum(len(content) for content in self._blobs.values())

        return {
            "blob_count": len(self._blobs),
            "total_size_bytes": total_size,
            "storage_type": "memory",
        }


class LazyBlobContent(str):
    """
    Lazy-loading string that fetches content from blob store on first access.

    This behaves like a normal string but only loads the actual content
    when the string methods are called.
    """

    # Declare attributes for type checking
    _blob_hash: str
    _blob_store: BlobStore
    _content: str | None
    _loaded: bool

    def __new__(cls, blob_hash: str, blob_store: BlobStore):
        # Create empty string initially - will be populated on first access
        obj = str.__new__(cls, "")
        obj._blob_hash = blob_hash
        obj._blob_store = blob_store
        obj._content = None
        obj._loaded = False
        return obj

    def _ensure_loaded(self):
        """Load content from blob store if not already loaded."""
        if not self._loaded:
            try:
                content_bytes = self._blob_store.get(self._blob_hash)
                self._content = content_bytes.decode("utf-8")
                self._loaded = True
                logger.debug(f"Lazy-loaded blob {self._blob_hash[:8]}...")
            except Exception as e:
                logger.error(f"Failed to load blob {self._blob_hash[:8]}...: {e}")
                self._content = ""
                self._loaded = True

    def __str__(self) -> str:
        self._ensure_loaded()
        return self._content or ""

    def __repr__(self) -> str:
        if self._loaded:
            return repr(self._content or "")
        return f"LazyBlobContent({self._blob_hash[:8]}...)"

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._content or "")

    def __getitem__(self, key):
        self._ensure_loaded()
        return (self._content or "")[key]

    def __contains__(self, item):
        self._ensure_loaded()
        return item in (self._content or "")

    def __eq__(self, other):
        self._ensure_loaded()
        return (self._content or "") == other

    def __add__(self, other):
        self._ensure_loaded()
        return (self._content or "") + other

    def __radd__(self, other):
        self._ensure_loaded()
        return other + (self._content or "")

    def __iter__(self):
        self._ensure_loaded()
        return iter(self._content or "")

    def __bool__(self):
        self._ensure_loaded()
        return bool(self._content)

    # Forward all common string methods to ensure lazy loading
    def split(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").split(*args, **kwargs)

    def strip(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").strip(*args, **kwargs)

    def replace(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").replace(*args, **kwargs)

    def startswith(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").startswith(*args, **kwargs)

    def endswith(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").endswith(*args, **kwargs)

    def find(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").find(*args, **kwargs)

    def join(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").join(*args, **kwargs)

    def encode(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").encode(*args, **kwargs)

    def lower(self):
        self._ensure_loaded()
        return (self._content or "").lower()

    def upper(self):
        self._ensure_loaded()
        return (self._content or "").upper()

    def capitalize(self):
        self._ensure_loaded()
        return (self._content or "").capitalize()

    def title(self):
        self._ensure_loaded()
        return (self._content or "").title()

    def splitlines(self, *args, **kwargs):
        self._ensure_loaded()
        return (self._content or "").splitlines(*args, **kwargs)


def compute_blob_hash(content: str | bytes) -> str:
    """
    Compute SHA-256 hash for content.

    Args:
        content: String or bytes content

    Returns:
        SHA-256 hash as hex string
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    return hashlib.sha256(content).hexdigest()
