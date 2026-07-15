"""
Directory Cache - High-performance directory change detection.

This module provides directory-level caching to dramatically reduce file system
scanning overhead by skipping unchanged directories entirely.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, cast
import msgpack
from pydantic import BaseModel, Field, ConfigDict
from .cache_models import DirectoryChangeReason


logger = logging.getLogger(__name__)


class DirectoryEntry(BaseModel):
    """Cached information about a directory."""

    path: str  # Relative path from root
    mtime_ns: int  # Modification time (nanosecond precision)
    size: int  # Total size of direct children
    child_count: int  # Number of direct children
    file_names: Set[str]  # Set of file names (not full paths)
    subdir_names: Set[str]  # Set of subdirectory names
    has_gitignore: bool  # Whether .gitignore exists
    gitignore_mtime_ns: Optional[int] = None  # .gitignore modification time

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    def has_changed(self, current_stat: os.stat_result, current_child_count: int) -> bool:
        """Check if directory has been modified.

        NOTE: We only check mtime, not child count, because child count
        can change due to temporary files (e.g., __pycache__, .pyc) that
        are excluded from tracking but still affect raw directory counts.
        """
        return current_stat.st_mtime_ns != self.mtime_ns


class CacheData(BaseModel):
    """Structured cache data for persistence."""

    version: int = Field(default=1)
    timestamp: datetime
    entries: Dict[str, DirectoryEntry]


class DirectoryStats(BaseModel):
    """Directory cache statistics."""

    total_directories: int
    total_files_tracked: int
    changed_directories: int
    cache_file: str
    cache_size_bytes: int
    change_reasons: List[DirectoryChangeReason] = Field(default_factory=list)


class DirectoryCache:
    """
    Directory-level cache for fast change detection.

    Key optimizations:
    1. Check directory mtime before scanning contents
    2. Skip entire subtrees if parent unchanged
    3. Cache gitignore patterns per directory
    4. Persist cache between runs
    """

    VERSION = 1
    CACHE_FILENAME = "directory_cache.msgpack"

    def __init__(self, root_path: Path, cache_dir: Optional[Path] = None):
        """
        Initialize directory cache.

        Args:
            root_path: Root directory to cache
            cache_dir: Directory for cache storage (defaults to .aware/index)
        """
        self.root_path = root_path.resolve()

        # Set up cache storage
        if cache_dir is None:
            cache_dir = self.root_path / ".aware" / "index"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / self.CACHE_FILENAME

        # In-memory cache
        self.entries: Dict[str, DirectoryEntry] = {}
        self.changed_dirs: Set[str] = set()
        self.change_reasons: List[DirectoryChangeReason] = []  # Track why dirs changed

        # Load existing cache
        self._load_cache()

        logger.debug(f"Initialized directory cache for {root_path}")

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, "rb") as f:
                raw_unpacked = msgpack.unpack(f, raw=False)
            if not isinstance(raw_unpacked, dict):
                logger.warning(
                    f"Failed to load directory cache: unexpected payload type {type(raw_unpacked)!r}"
                )
                return
            raw_data = cast(dict[str, Any], raw_unpacked)

            # Parse with Pydantic model
            cache_data = CacheData(
                version=raw_data.get("version", 0),
                timestamp=datetime.fromisoformat(raw_data.get("timestamp", datetime.now().isoformat())),
                entries={},
            )

            # Version check
            if cache_data.version != self.VERSION:
                logger.info("Directory cache version mismatch, rebuilding")
                return

            # Load entries with proper type conversion
            for path, entry_data in raw_data.get("entries", {}).items():
                # Convert lists back to sets
                if "file_names" in entry_data:
                    entry_data["file_names"] = set(entry_data["file_names"])
                if "subdir_names" in entry_data:
                    entry_data["subdir_names"] = set(entry_data["subdir_names"])

                cache_data.entries[path] = DirectoryEntry(**entry_data)

            self.entries = cache_data.entries
            logger.debug(f"Loaded directory cache with {len(self.entries)} entries")

        except Exception as e:
            logger.warning(f"Failed to load directory cache: {e}")

    def save_cache(self) -> None:
        """Save cache to disk."""
        try:
            # Create structured data
            cache_data = CacheData(version=self.VERSION, timestamp=datetime.now(), entries=self.entries)

            # Convert to msgpack-compatible format
            # Need to convert sets to lists for msgpack serialization
            entries_dict = {}
            for path, entry in cache_data.entries.items():
                entry_dict = entry.model_dump()
                # Convert sets to lists for serialization
                entry_dict["file_names"] = list(entry_dict.get("file_names", set()))
                entry_dict["subdir_names"] = list(entry_dict.get("subdir_names", set()))
                entries_dict[path] = entry_dict

            data = {
                "version": cache_data.version,
                "timestamp": cache_data.timestamp.isoformat(),
                "entries": entries_dict,
            }

            # Write with atomic rename
            temp_file = self.cache_file.with_suffix(".tmp")
            with open(temp_file, "wb") as f:
                msgpack.pack(data, f)

            temp_file.replace(self.cache_file)
            logger.debug(f"Saved directory cache with {len(self.entries)} entries")

        except Exception as e:
            logger.error(f"Failed to save directory cache: {e}")

    def find_changed_directories(self, should_exclude_dir) -> Set[str]:
        """
        Find all directories that have changed since last scan.

        This is the key optimization - we only scan directories whose
        mtime has changed, skipping entire subtrees when possible.

        Args:
            should_exclude_dir: Function to check if directory should be excluded

        Returns:
            Set of relative paths to directories that need scanning
        """
        self.changed_dirs.clear()
        self.change_reasons.clear()  # Reset change tracking
        self._check_directory_recursive(self.root_path, "", should_exclude_dir)

        logger.debug(f"Directory scan: {len(self.changed_dirs)} of {len(self.entries)} changed")
        return self.changed_dirs.copy()

    def _check_directory_recursive(self, dir_path: Path, rel_path: str, should_exclude_dir) -> bool:
        """
        Recursively check if directory or any child has changed.

        Returns True if changed, False if unchanged.
        """
        try:
            # Get current directory stats
            stat = dir_path.stat()

            # Check if we have cached info
            if rel_path in self.entries:
                entry = self.entries[rel_path]

                # Fast check: has directory been modified?
                if not entry.has_changed(stat, entry.child_count):
                    # Directory unchanged, skip entire subtree!
                    return False

            # Only enumerate directory contents once we know the directory is
            # new or its own mtime changed. This preserves the cache fast path.
            try:
                children = list(dir_path.iterdir())
                child_count = len(children)
            except (PermissionError, OSError):
                # Can't read directory, assume changed
                self.changed_dirs.add(rel_path)
                return True

            if rel_path in self.entries:
                entry = self.entries[rel_path]
                # Track why it changed
                reason = DirectoryChangeReason(
                    path=rel_path or "[root]",
                    reason="mtime_changed",  # We only check mtime now
                    old_mtime_ns=entry.mtime_ns,
                    new_mtime_ns=stat.st_mtime_ns,
                    old_child_count=entry.child_count,
                    new_child_count=child_count,
                )
                self.change_reasons.append(reason)
            else:
                # New directory
                reason = DirectoryChangeReason(
                    path=rel_path or "[root]",
                    reason="new",
                    new_mtime_ns=stat.st_mtime_ns,
                    new_child_count=child_count,
                )
                self.change_reasons.append(reason)

            # Directory is new or changed, need to scan
            self.changed_dirs.add(rel_path)

            for child in children:
                if child.is_dir() and not should_exclude_dir(child):
                    child_rel = os.path.join(rel_path, child.name) if rel_path else child.name
                    self._check_directory_recursive(child, child_rel, should_exclude_dir)

            return True

        except (PermissionError, OSError) as e:
            logger.debug(f"Error checking directory {dir_path}: {e}")
            # Track error
            reason = DirectoryChangeReason(path=rel_path or "[root]", reason="error", error_message=str(e))
            self.change_reasons.append(reason)
            # Assume changed on error
            self.changed_dirs.add(rel_path)
            return True

    def update_directory(
        self,
        dir_path: Path,
        rel_path: str,
        file_names: Set[str],
        subdir_names: Set[str],
    ) -> None:
        """
        Update cache entry for a directory after scanning.

        Args:
            dir_path: Absolute path to directory
            rel_path: Relative path from root
            file_names: Set of file names in directory
            subdir_names: Set of subdirectory names
        """
        try:
            stat = dir_path.stat()

            # Check for .gitignore
            gitignore_path = dir_path / ".gitignore"
            has_gitignore = gitignore_path.exists()
            gitignore_mtime_ns = None

            if has_gitignore:
                try:
                    gitignore_mtime_ns = gitignore_path.stat().st_mtime_ns
                except (PermissionError, OSError):
                    pass

            # Calculate total size of direct children
            total_size = 0
            for name in file_names:
                try:
                    child_stat = (dir_path / name).stat()
                    total_size += child_stat.st_size
                except (PermissionError, OSError):
                    pass

            # Create or update entry
            self.entries[rel_path] = DirectoryEntry(
                path=rel_path,
                mtime_ns=stat.st_mtime_ns,
                size=total_size,
                child_count=len(file_names) + len(subdir_names),
                file_names=file_names.copy(),
                subdir_names=subdir_names.copy(),
                has_gitignore=has_gitignore,
                gitignore_mtime_ns=gitignore_mtime_ns,
            )

        except (PermissionError, OSError) as e:
            logger.debug(f"Error updating directory cache for {dir_path}: {e}")
            # Remove from cache if can't access
            self.entries.pop(rel_path, None)

    def get_unchanged_files(self, changed_dirs: Set[str]) -> Dict[str, Set[str]]:
        """
        Get all files from unchanged directories.

        This allows us to skip scanning these directories entirely.

        Args:
            changed_dirs: Set of directories that have changed

        Returns:
            Dictionary mapping directory path to set of file names
        """
        unchanged_files = {}

        for rel_path, entry in self.entries.items():
            if rel_path not in changed_dirs:
                # Directory unchanged, use cached file list
                if entry.file_names:
                    unchanged_files[rel_path] = entry.file_names.copy()

        return unchanged_files

    def clear(self) -> None:
        """Clear all cached entries and remove cache file."""
        self.entries.clear()
        self.changed_dirs.clear()
        self.change_reasons.clear()

        # Also remove the cache file to prevent loading stale data
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                logger.debug(f"Removed cache file: {self.cache_file}")
            except Exception as e:
                logger.warning(f"Failed to remove cache file: {e}")

    def invalidate_paths(self, paths: Set[str]) -> None:
        """
        Invalidate cache entries for specific paths.

        This method selectively removes cache entries for the given paths
        and their parent directories, forcing a fresh scan on next access.

        Args:
            paths: Set of relative paths to invalidate
        """
        if not paths:
            return

        invalidated_count = 0

        for path in paths:
            # Remove direct entry if it exists
            if path in self.entries:
                del self.entries[path]
                invalidated_count += 1

            # Also invalidate parent directories since file changes affect them
            path_obj = Path(path)
            parent_path = str(path_obj.parent)

            while parent_path and parent_path != "." and parent_path != path:
                if parent_path in self.entries:
                    del self.entries[parent_path]
                    invalidated_count += 1

                # Move up one level
                parent_obj = Path(parent_path).parent
                parent_path = str(parent_obj) if str(parent_obj) != "." else None

        if invalidated_count > 0:
            logger.debug(f"DirectoryCache: Invalidated {invalidated_count} entries for {len(paths)} paths")

    def get_stats(self) -> DirectoryStats:
        """Get cache statistics."""
        total_dirs = len(self.entries)
        total_files = sum(len(e.file_names) for e in self.entries.values())

        return DirectoryStats(
            total_directories=total_dirs,
            total_files_tracked=total_files,
            changed_directories=len(self.changed_dirs),
            cache_file=str(self.cache_file),
            cache_size_bytes=(self.cache_file.stat().st_size if self.cache_file.exists() else 0),
            change_reasons=self.change_reasons[:20],  # First 20 for debugging
        )
