"""
Index Storage - Persistent storage for file system index.

This module provides JSON-based storage for file system indices,
optimized for both Python and DART compatibility.
"""

import json
import os
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, TextIO
from pydantic import BaseModel

from .file_metadata_cached import FileMetadataCached


_INDEX_JSON_READ_SIZE = 64 * 1024


class _IndexJsonReader:
    """Decode one index value at a time, discarding consumed input chunks.

    Nested values still use the standard JSON decoder. Only the root and
    entries object framing is streamed, so memory does not include a complete
    raw metadata tree alongside the validated metadata tree.
    """

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._decoder = json.JSONDecoder()
        self._buffer = ""
        self._position = 0
        self._eof = False

    def _fill(self) -> None:
        chunk = self._stream.read(_INDEX_JSON_READ_SIZE)
        self._buffer = self._buffer[self._position:] + chunk
        self._position = 0
        self._eof = not chunk

    def _peek(self) -> str | None:
        while True:
            while self._position < len(self._buffer):
                character = self._buffer[self._position]
                if character not in " \t\r\n":
                    return character
                self._position += 1
            if self._eof:
                return None
            self._fill()

    def _expect(self, character: str) -> None:
        if self._peek() != character:
            raise ValueError(f"Expected JSON object delimiter {character!r}")
        self._position += 1

    def value(self) -> Any:
        if self._peek() is None:
            raise ValueError("Missing JSON value")
        while True:
            try:
                value, end = self._decoder.raw_decode(
                    self._buffer, self._position
                )
            except json.JSONDecodeError:
                if self._eof:
                    raise
                self._fill()
                continue
            # A number can be partially decoded at a chunk boundary: 1e+2
            # must not become 1 just because the remaining bytes are unread.
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if not self._eof and (
                    end == len(self._buffer)
                    or self._buffer[end] not in " \t\r\n,]}"
                ):
                    self._fill()
                    continue
            self._position = end
            return value

    def object_keys(self) -> Iterator[str]:
        """The caller consumes each yielded key's value before advancing."""
        self._expect("{")
        if self._peek() == "}":
            self._position += 1
            return
        while True:
            key = self.value()
            if not isinstance(key, str):
                raise ValueError("JSON object key is not a string")
            self._expect(":")
            yield key
            if self._peek() == "}":
                self._position += 1
                return
            self._expect(",")

    def finish(self) -> None:
        if self._peek() is not None:
            raise ValueError("Trailing data after JSON index")

    def next_is_object(self) -> bool:
        return self._peek() == "{"


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
                reader = _IndexJsonReader(f)
                data = {}
                result: Dict[str, Optional[FileMetadataCached]] = {}
                entries_are_object = True
                for key in reader.object_keys():
                    if key != "entries":
                        data[key] = reader.value()
                        continue
                    # JSON objects use the last duplicate key. A later entries
                    # body replaces the earlier body, not a union of both.
                    result = {}
                    entries_are_object = reader.next_is_object()
                    if not entries_are_object:
                        reader.value()
                        continue
                    for rel_path in reader.object_keys():
                        entry_data = reader.value()
                        # Keep first-key order like json.load, but overwrite an
                        # earlier value even when the final duplicate is invalid.
                        result[rel_path] = None
                        try:
                            result[rel_path] = IndexEntry(**entry_data).metadata
                        except Exception as e:
                            print(f"Error parsing entry {rel_path}: {e}")
                reader.finish()

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

            if not entries_are_object:
                raise ValueError("JSON index entries are not an object")

            return {
                path: metadata
                for path, metadata in result.items()
                if metadata is not None
            }

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
