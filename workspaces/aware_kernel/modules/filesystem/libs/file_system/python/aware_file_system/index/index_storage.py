"""
Index Storage - Persistent storage for file system index.

This module provides JSON-based storage for file system indices,
optimized for both Python and DART compatibility.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from pydantic import BaseModel

from .file_metadata_cached import FileMetadataCached


class IndexEntry(BaseModel):
    """Single entry in the file system index."""

    metadata: FileMetadataCached
    last_checked: datetime
    is_valid: bool = True


class IndexData(BaseModel):
    """Complete index data structure."""

    version: str
    timestamp: datetime
    entries: Dict[str, IndexEntry]


class IndexStats(BaseModel):
    """Index storage statistics."""

    exists: bool
    file_size: Optional[int] = None
    last_modified: Optional[datetime] = None
    entry_count: Optional[int] = None
    version: Optional[str] = None
    error: Optional[str] = None


class IndexStorage(BaseModel):
    """
    Persistent storage manager for file system index.

    Features:
    1. JSON-based storage for DART compatibility
    2. Incremental updates
    3. Corruption recovery
    4. Version management
    """

    storage_path: Path
    version: str = "1.0"

    def __init__(self, storage_path: str, **data):
        super().__init__(storage_path=Path(storage_path), **data)
        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save_index(self, index_data: Dict[str, FileMetadataCached]) -> bool:
        """
        Save complete index to storage.

        Args:
            index_data: Dictionary of relative_path -> FileMetadataCached

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Create structured data
            entries = {}
            for rel_path, metadata in index_data.items():
                entries[rel_path] = IndexEntry(metadata=metadata, last_checked=datetime.now(), is_valid=True)

            index_obj = IndexData(version=self.version, timestamp=datetime.now(), entries=entries)

            # Write to temporary file first, then atomic rename
            temp_path = self.storage_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(index_obj.model_dump(), f, indent=2, default=str)

            # Atomic rename for crash safety
            temp_path.replace(self.storage_path)
            return True

        except Exception as e:
            print(f"Error saving index: {e}")
            return False

    def load_index(self) -> Optional[Dict[str, FileMetadataCached]]:
        """
        Load index from storage.

        Returns:
            Dictionary of relative_path -> FileMetadataCached, or None if load failed
        """
        if not self.storage_path.exists():
            return None

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse with Pydantic model
            index_obj = IndexData(
                version=data.get("version", ""),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                entries={},
            )

            # Version check
            if index_obj.version != self.version:
                print(f"Index version mismatch: expected {self.version}, got {index_obj.version}")
                return None

            # Convert entries
            result = {}
            for rel_path, entry_data in data.get("entries", {}).items():
                try:
                    # Parse entry
                    entry = IndexEntry(**entry_data)
                    # Extract metadata
                    result[rel_path] = entry.metadata

                except Exception as e:
                    print(f"Error parsing entry {rel_path}: {e}")
                    continue

            return result

        except Exception as e:
            print(f"Error loading index: {e}")
            return None

    def update_entry(self, rel_path: str, metadata: FileMetadataCached) -> bool:
        """
        Update a single entry in the index.

        For large indices, this is more efficient than full saves.

        Args:
            rel_path: Relative path of the file
            metadata: Updated metadata

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Load existing index
            index_data = self.load_index() or {}

            # Update the entry
            index_data[rel_path] = metadata

            # Save back
            return self.save_index(index_data)

        except Exception as e:
            print(f"Error updating entry {rel_path}: {e}")
            return False

    def remove_entry(self, rel_path: str) -> bool:
        """
        Remove an entry from the index.

        Args:
            rel_path: Relative path of the file to remove

        Returns:
            True if removal successful, False otherwise
        """
        try:
            # Load existing index
            index_data = self.load_index()
            if not index_data:
                return False

            # Remove the entry if it exists
            if rel_path in index_data:
                del index_data[rel_path]
                return self.save_index(index_data)

            return True  # Entry didn't exist, consider it successful

        except Exception as e:
            print(f"Error removing entry {rel_path}: {e}")
            return False

    def get_stats(self) -> IndexStats:
        """
        Get statistics about the stored index.

        Returns:
            IndexStats with index statistics
        """
        if not self.storage_path.exists():
            return IndexStats(exists=False)

        try:
            stat = self.storage_path.stat()
            index_data = self.load_index()

            return IndexStats(
                exists=True,
                file_size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                entry_count=len(index_data) if index_data else 0,
                version=self.version,
            )

        except Exception as e:
            return IndexStats(exists=True, error=str(e))

    def cleanup_invalid_entries(self) -> int:
        """
        Remove entries marked as invalid from the index.

        Returns:
            Number of entries removed
        """
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entries = data.get("entries", {})
            original_count = len(entries)

            # Filter out invalid entries
            valid_entries = {
                rel_path: entry_data for rel_path, entry_data in entries.items() if entry_data.get("is_valid", True)
            }

            # Update and save if changes made
            removed_count = original_count - len(valid_entries)
            if removed_count > 0:
                data["entries"] = valid_entries
                data["timestamp"] = datetime.now().isoformat()

                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)

            return removed_count

        except Exception as e:
            print(f"Error cleaning up invalid entries: {e}")
            return 0
