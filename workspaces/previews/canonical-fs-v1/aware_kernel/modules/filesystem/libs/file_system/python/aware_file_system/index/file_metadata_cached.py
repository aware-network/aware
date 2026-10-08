"""
Cached File Metadata - Optimized file metadata with incremental hash computation.

This module provides an optimized version of FileMetadata that avoids reading
file content unless absolutely necessary for hash computation.
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from aware_file_system.models import FileType, FileMetadata


class FileMetadataCached(BaseModel):
    """
    Optimized FileMetadata with caching and incremental hash computation.

    Key optimizations:
    1. Only reads file content when mtime/size indicate changes
    2. Caches hash computation results
    3. Supports fast change detection without content reads
    4. Compatible with existing FileMetadata interface
    """

    path: str = Field(..., description="Relative path of the file within the project")
    name: str = Field(..., description="Name of the file")
    size: int = Field(..., description="Size of the file in bytes")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    mtime_ns: int = Field(0, description="Last modification timestamp in nanoseconds")
    file_type: FileType = Field(..., description="Type of the file")
    mime_type: str = Field(..., description="MIME type of the file")
    depth: int = Field(..., description="Depth of the file in the directory structure")
    hash: Optional[str] = Field(None, description="Hash of the file content (computed lazily)")

    # Optimization fields (not in original FileMetadata)
    hash_computed: bool = Field(False, description="Whether hash has been computed")
    content_cache: Optional[bytes] = Field(None, description="Cached file content", exclude=True)

    @classmethod
    def from_file_fast(
        cls,
        file_path: str,
        root_path: str,
        cached_metadata: Optional["FileMetadataCached"] = None,
    ) -> "FileMetadataCached":
        """
        Create FileMetadataCached with fast change detection.

        Only reads file content if mtime/size changed from cached version.

        Args:
            file_path: Absolute path to the file
            root_path: Root path for relative path calculation
            cached_metadata: Previously cached metadata for comparison

        Returns:
            FileMetadataCached instance with optimized hash computation
        """
        stat = os.stat(file_path)
        relative_path = os.path.relpath(file_path, root_path)
        depth = relative_path.count(os.sep)
        mime_type, _ = mimetypes.guess_type(file_path)

        # Fast change detection using mtime and size
        current_mtime = datetime.fromtimestamp(stat.st_mtime)
        current_mtime_ns = stat.st_mtime_ns
        current_size = stat.st_size

        # Check if we can reuse cached hash
        can_reuse_hash = (
            cached_metadata is not None
            and cached_metadata.mtime_ns == current_mtime_ns
            and cached_metadata.size == current_size
            and cached_metadata.hash_computed
            and cached_metadata.hash is not None
        )

        if can_reuse_hash and cached_metadata and cached_metadata.hash:
            # Reuse existing hash without reading file content
            return cls(
                path=relative_path,
                name=os.path.basename(file_path),
                size=current_size,
                last_modified=current_mtime,
                mtime_ns=current_mtime_ns,
                file_type=cls._get_file_type(mime_type),
                mime_type=mime_type or "application/octet-stream",
                depth=depth,
                hash=cached_metadata.hash,
                hash_computed=True,
                content_cache=None,  # Don't cache content by default
            )
        else:
            # File changed or no cache - create without hash (lazy computation)
            return cls(
                path=relative_path,
                name=os.path.basename(file_path),
                size=current_size,
                last_modified=current_mtime,
                mtime_ns=current_mtime_ns,
                file_type=cls._get_file_type(mime_type),
                mime_type=mime_type or "application/octet-stream",
                depth=depth,
                hash=None,
                hash_computed=False,
                content_cache=None,
            )

    def compute_hash_if_needed(self, file_path: str) -> str:
        """
        Compute hash only if not already computed.

        Args:
            file_path: Absolute path to the file

        Returns:
            File content hash (SHA256)
        """
        if self.hash_computed and self.hash:
            return self.hash

        # Read file content and compute hash
        with open(file_path, "rb") as f:
            content = f.read()

        # Use SHA256 for better collision resistance than MD5
        file_hash = hashlib.sha256(content).hexdigest()

        # Cache the result
        self.hash = file_hash
        self.hash_computed = True

        return file_hash

    def get_content(self, file_path: str) -> bytes:
        """
        Get file content with caching support.

        Args:
            file_path: Absolute path to the file

        Returns:
            File content as bytes
        """
        if self.content_cache is not None:
            return self.content_cache

        with open(file_path, "rb") as f:
            content = f.read()

        # Cache content for potential reuse
        self.content_cache = content
        return content

    def needs_hash_computation(self) -> bool:
        """Check if hash computation is needed."""
        return not self.hash_computed or self.hash is None

    def to_file_metadata(self, file_path: str) -> FileMetadata:
        """
        Convert to standard FileMetadata format (with content).

        This is for compatibility with existing code that expects FileMetadata.

        Args:
            file_path: Absolute path to the file

        Returns:
            FileMetadata instance with content included
        """
        # Ensure hash is computed
        if not self.hash_computed:
            self.compute_hash_if_needed(file_path)

        # Get content
        content = self.get_content(file_path)

        # Hash should be computed by now, but add safety check
        computed_hash = self.hash or ""

        return FileMetadata(
            path=self.path,
            name=self.name,
            size=self.size,
            last_modified=self.last_modified,
            file_type=self.file_type,
            mime_type=self.mime_type,
            depth=self.depth,
            hash=computed_hash,
            content=content,
        )

    def is_modified_fast(self, other: "FileMetadataCached") -> bool:
        """
        Fast modification check using mtime/size (no hash computation).

        Args:
            other: FileMetadataCached to compare against

        Returns:
            True if likely modified, False if likely unchanged
        """
        return self.size != other.size or self.last_modified != other.last_modified

    def is_modified_with_hash(self, other: "FileMetadataCached", file_path: str) -> bool:
        """
        Definitive modification check using hash computation if needed.

        Args:
            other: FileMetadataCached to compare against
            file_path: Absolute path to the file

        Returns:
            True if modified, False if unchanged
        """
        # Fast check first
        if self.is_modified_fast(other):
            return True

        # If mtime/size same, compare hashes
        if not self.hash_computed:
            self.compute_hash_if_needed(file_path)
        if not other.hash_computed:
            other.compute_hash_if_needed(file_path)

        return self.hash != other.hash

    @staticmethod
    def _get_file_type(mime_type: Optional[str]) -> FileType:
        """Determine the FileType based on the MIME type."""
        if mime_type:
            if mime_type.startswith("text"):
                return FileType.TEXT
            elif mime_type.startswith("audio"):
                return FileType.AUDIO
            elif mime_type.startswith("image"):
                return FileType.IMAGE
            elif mime_type.startswith("video"):
                return FileType.VIDEO
        return FileType.OTHER
