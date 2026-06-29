"""
Incremental Scanner - High-performance file system scanning with change detection.

This module provides incremental scanning that only processes files that have
actually changed, dramatically improving performance for large repositories.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Set, Optional
import logging

from aware_file_system.config import Config
from aware_file_system.filters.composite import Composite

from aware_file_system.index.file_metadata_cached import FileMetadataCached
from aware_file_system.index.index_storage import IndexStorage
from aware_file_system.index.directory_cache import DirectoryCache

logger = logging.getLogger(__name__)


DEFAULT_SCANNER_IGNORED_DIRS = frozenset(
    {
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".git",
        ".svn",
        ".hg",
        ".venv",
        "venv",
        "node_modules",
        "build",
        "dist",
        ".dart_tool",
        ".aware",
        "_aware",
        ".pytest_cache",
        ".hypothesis",
        ".tox",
        ".fvm",
        ".nox",
        "htmlcov",
        ".nyc_output",
        "target",
        ".sass-cache",
        ".parcel-cache",
        ".next",
        ".cache",
    }
)

DEFAULT_SCANNER_IGNORED_PATH_FRAGMENTS = frozenset(
    {
        "node_modules",
        ".mypy_cache",
        ".ruff_cache",
        ".dart_tool",
        ".venv",
        "site-packages",
        "/.pytest_cache/",
        "/.cache/",
        "/target/",
        "/.git/logs",
        "/.git/refs",
        "/.git/objects",
        "/build/",
        "/dist/",
        "/__pycache__/",
    }
)


class ScanResult:
    """Result of an incremental scan operation."""

    def __init__(self):
        self.added: Dict[str, FileMetadataCached] = {}
        self.modified: Dict[str, FileMetadataCached] = {}
        self.deleted: Set[str] = set()
        self.unchanged: Set[str] = set()
        self.scan_time: float = 0.0
        self.files_processed: int = 0
        self.files_content_read: int = 0  # Files that required content reading

    @property
    def total_changes(self) -> int:
        """Total number of changes detected."""
        return len(self.added) + len(self.modified) + len(self.deleted)

    @property
    def cache_hit_ratio(self) -> float:
        """Ratio of files that didn't require content reading."""
        if self.files_processed == 0:
            return 1.0
        return 1.0 - (self.files_content_read / self.files_processed)


class IncrementalScanner:
    """
    High-performance incremental file system scanner.

    Key features:
    1. Only scans files that changed (mtime/size check)
    2. Lazy hash computation (only when needed)
    3. Persistent caching across scans
    4. Session-level caching for repository operations
    """

    def __init__(self, config: Config, cache_dir: Optional[str] = None):
        """
        Initialize incremental scanner.

        Args:
            config: File system configuration
            cache_dir: Directory for persistent cache (defaults to .aware/index)
        """
        self.config = config
        self.root_path = Path(config.file_system.root_path).resolve()
        self._filter: Composite | None = None

        # Filter result cache to avoid repeated expensive filter calls
        self._filter_cache: Dict[str, bool] = {}
        self._filter_cache_hits = 0
        self._filter_cache_misses = 0

        # Set up persistent storage
        if cache_dir is None:
            cache_dir_path = self.root_path / ".aware" / "index"
        else:
            cache_dir_path = Path(cache_dir)

        cache_dir_path.mkdir(parents=True, exist_ok=True)
        index_file = cache_dir_path / "file_index.json"
        self.storage = IndexStorage(str(index_file))

        # In-memory cache for session-level operations
        self._session_cache: Optional[Dict[str, FileMetadataCached]] = None
        self._last_scan_time: Optional[datetime] = None

        # Directory cache for fast change detection
        self._dir_cache = DirectoryCache(self.root_path, cache_dir_path)

        logger.debug(f"Initialized incremental scanner for {self.root_path}")
        logger.debug(f"Index storage: {index_file}")

    @property
    def filter(self) -> Composite:
        if self._filter is None:
            self._filter = Composite.from_config(self.config.filter, str(self.root_path))
        return self._filter

    def scan_incremental(self, use_session_cache: bool = True) -> ScanResult:
        """
        Perform incremental scan of the file system.

        Args:
            use_session_cache: If True, use session-level cache for repeated scans

        Returns:
            ScanResult with details of changes detected
        """
        start_time = datetime.now()
        result = ScanResult()

        # Fast session cache for very recent scans (2 seconds for interactive use)
        if use_session_cache and self._session_cache is not None and self._last_scan_time is not None:
            time_since_last = (start_time - self._last_scan_time).total_seconds()
            if time_since_last < 2.0:  # 2 second fast cache validity for rapid operations
                logger.debug(f"Fast session cache hit: {time_since_last:.1f}s since last scan")
                # Return optimized result showing no changes but maintain file count
                result.scan_time = (datetime.now() - start_time).total_seconds()
                result.files_processed = len(self._session_cache)
                result.files_content_read = 0  # No content read, 100% cache hit
                return result

        # Timing checkpoint 1: Index loading
        index_start = datetime.now()
        # Load existing index from persistent storage
        existing_index = self.storage.load_index() or {}

        # Clean up stale entries that no longer exist on disk
        stale_entries = []
        for rel_path in list(existing_index.keys()):
            abs_path = self.root_path / rel_path
            if not abs_path.exists():
                stale_entries.append(rel_path)
                del existing_index[rel_path]

        if stale_entries:
            logger.info(f"Cleaned {len(stale_entries)} stale entries from index")
            # Save cleaned index immediately to prevent future warnings
            self.storage.save_index(existing_index)
            # Also invalidate session cache since it may contain stale entries
            self.invalidate_session_cache()

        logger.debug(f"Loaded existing index with {len(existing_index)} entries (cleaned {len(stale_entries)} stale)")
        index_load_time = (datetime.now() - index_start).total_seconds()

        # Timing checkpoint 2: File discovery
        discovery_start = datetime.now()
        # Get current files from file system - only after fast cache miss
        # Use optimized directory-aware discovery
        current_files = self._discover_current_files_optimized()
        logger.debug(f"Discovered {len(current_files)} current files")
        discovery_time = (datetime.now() - discovery_start).total_seconds()

        # Timing checkpoint 3: Session cache validation
        cache_check_start = datetime.now()
        # If using session cache, check if file discovery matches cached state
        if use_session_cache and self._session_cache is not None:
            time_since_last = (
                (start_time - self._last_scan_time).total_seconds() if self._last_scan_time else float("inf")
            )

            # Check if discovered files match session cache (no changes detected)
            cached_files = set(self._session_cache.keys())
            current_file_paths = current_files  # current_files is already a Set[str]

            if time_since_last < 30 and cached_files == current_file_paths:
                logger.debug("Session cache valid: no file system changes detected")
                # Return optimized result showing no changes but maintain file count
                result.scan_time = (datetime.now() - start_time).total_seconds()
                result.files_processed = len(current_files)
                result.files_content_read = 0  # No content read, 100% cache hit
                return result
        cache_check_time = (datetime.now() - cache_check_start).total_seconds()

        # Timing checkpoint 4: Change processing
        changes_start = datetime.now()
        # Process changes when cache miss or file system changes detected
        result = self._process_file_changes(existing_index, current_files)
        changes_time = (datetime.now() - changes_start).total_seconds()

        # Update persistent storage with new/modified files
        updated_index = existing_index.copy()
        updated_index.update(result.added)
        updated_index.update(result.modified)

        # Remove deleted files from index
        for deleted_path in result.deleted:
            updated_index.pop(deleted_path, None)

        # Save updated index
        if result.total_changes > 0:
            self.storage.save_index(updated_index)
            logger.debug(f"Saved updated index with {len(updated_index)} entries")

        # Record timing
        result.scan_time = (datetime.now() - start_time).total_seconds()

        # Always update session cache with latest scan results for future use
        # This ensures FileSystemIndex can access files even after force_refresh
        self._session_cache = updated_index
        self._last_scan_time = datetime.now()  # Set to END time, not start time

        logger.debug(
            f"✅ Incremental scan complete: {result.total_changes} changes, "
            f"{result.files_content_read}/{result.files_processed} files read, "
            f"cache hit ratio: {result.cache_hit_ratio:.1%}, "
            f"time: {result.scan_time:.2f}s"
            f"🔍 Timing breakdown: "
            f"index_load: {index_load_time:.2f}s, "
            f"discovery: {discovery_time:.2f}s, "
            f"cache_check: {cache_check_time:.2f}s, "
            f"changes: {changes_time:.2f}s"
        )

        return result

    def _discover_current_files_optimized(self) -> Set[str]:
        """
        Optimized file discovery using directory cache.
        Only scans directories that have changed.

        Returns:
            Set of relative file paths
        """
        from datetime import datetime

        start_time = datetime.now()
        current_files = set()

        # Step 1: Find changed directories (fast stat-based check)
        changed_dirs = self._dir_cache.find_changed_directories(self._should_exclude_directory_basic)

        # Step 2: Get files from unchanged directories (from cache)
        unchanged_files = self._dir_cache.get_unchanged_files(changed_dirs)
        for dir_path, file_names in unchanged_files.items():
            dir_prefix = dir_path + "/" if dir_path else ""
            for file_name in file_names:
                # Directory cache entries are already built from filtered file
                # names in `_scan_single_directory`, so unchanged-cache reuse
                # must not pay the filter cost again.
                current_files.add(dir_prefix + file_name)

        # Step 3: Scan only changed directories
        for dir_rel_path in sorted(changed_dirs):  # Sort for consistent order
            dir_full_path = self.root_path / dir_rel_path if dir_rel_path else self.root_path
            self._scan_single_directory(dir_full_path, dir_rel_path, current_files)

        # Step 4: Save updated directory cache
        self._dir_cache.save_cache()

        total_time = (datetime.now() - start_time).total_seconds()

        logger.debug(f"Directory cache stats: {self._dir_cache.get_stats().model_dump()}")

        # Performance logging to track improvement
        logger.debug(
            f"File discovery completed in {total_time:.2f}s: "
            f"{len(current_files)} files found, "
            f"{len(changed_dirs)} dirs scanned"
        )

        return current_files

    def _should_include_cached(self, file_path: str) -> bool:
        """
        Cached version of filter.should_include() to avoid repeated expensive filter calls.

        Args:
            file_path: Relative file path

        Returns:
            True if file should be included
        """
        # Check cache first
        if file_path in self._filter_cache:
            self._filter_cache_hits += 1
            return self._filter_cache[file_path]

        # Compute and cache result
        self._filter_cache_misses += 1
        full_path = str(self.root_path / file_path)
        result = self.filter.should_include(full_path)
        self._filter_cache[file_path] = result
        return result

    def _scan_single_directory(self, dir_path: Path, rel_path: str, current_files: Set[str]) -> None:
        """
        Scan a single directory and update caches.

        Args:
            dir_path: Absolute path to directory
            rel_path: Relative path from root
            current_files: Set to add discovered files to
        """
        try:
            file_names = set()
            subdir_names = set()

            # List directory contents once
            for item in dir_path.iterdir():
                if item.is_file() or (item.is_symlink() and self._is_symlink_within_workspace(item)):
                    if item.is_file():  # Follow symlinks if within workspace
                        # Apply filter
                        file_rel_path = os.path.join(rel_path, item.name) if rel_path else item.name
                        if self._should_include_cached(file_rel_path):
                            file_name = item.name
                            file_names.add(file_name)

                            # Add to current files
                            current_files.add(file_rel_path)

                elif item.is_dir():
                    if not self._should_exclude_directory_basic(item):
                        subdir_names.add(item.name)

            # Update directory cache
            self._dir_cache.update_directory(dir_path, rel_path, file_names, subdir_names)

        except (PermissionError, OSError) as e:
            logger.warning(f"Error scanning directory {dir_path}: {e}")

    def _discover_current_files(self) -> Set[str]:
        """
        Discover all current files in the file system.

        Uses the same symlink protection and scanning pattern as the original introspector
        with hybrid directory exclusions for performance.

        Returns:
            Set of relative file paths
        """
        current_files = set()
        visited_dirs = set()  # Track visited directories to prevent loops

        def scan_directory(directory: Path, depth: int = 0) -> None:
            try:
                # Prevent infinite recursion
                if depth > 20:
                    logger.warning(f"Max depth reached at: {directory}")
                    return

                # Prevent directory loops
                real_path = directory.resolve()
                if real_path in visited_dirs:
                    logger.debug(f"Already visited: {directory} -> {real_path}")
                    return
                visited_dirs.add(real_path)

                # Debug output every 100 directories
                if len(visited_dirs) % 100 == 0:
                    logger.debug(f"Scanned {len(visited_dirs)} directories, current: {directory}")

                # Get all items in the directory (same as original introspector)
                items = list(directory.iterdir())

                # Process all files first, then directories (same pattern as original)
                for item in items:
                    # Check if it's a file (but don't follow symlinks outside workspace)
                    if item.is_file() or (item.is_symlink() and self._is_symlink_within_workspace(item)):
                        # Only process if it's a real file or a symlink within workspace
                        if item.is_file():  # This will follow symlinks only if we got here
                            # Use external filter for files
                            rel_path = str(item.relative_to(self.root_path))
                            if self._should_include_cached(rel_path):
                                current_files.add(rel_path)

                # Process subdirectories (same pattern as original)
                for item in items:
                    # Check if it's a directory (but don't follow symlinks outside workspace)
                    if item.is_dir() or (item.is_symlink() and self._is_symlink_within_workspace(item)):
                        # Only recurse if it's a real directory or a symlink within workspace
                        if item.is_dir():  # This will follow symlinks only if we got here
                            # HYBRID: Basic directory exclusions first (performance + reliability)
                            if self._should_exclude_directory_basic(item):
                                logger.debug(f"Excluding directory: {item}")
                                continue
                            # Then scan the directory
                            scan_directory(item, depth + 1)

            except (PermissionError, OSError) as e:
                logger.warning(f"Error scanning {directory}: {e}")

        logger.debug(f"Starting file discovery from: {self.root_path}")
        scan_directory(self.root_path, 0)
        logger.debug(f"Discovery complete: {len(current_files)} files, {len(visited_dirs)} directories")
        return current_files

    def _is_symlink_within_workspace(self, path: Path) -> bool:
        """
        Check if a symlink points to a target within the workspace root.

        CRITICAL FIX: Now validates BOTH symlink location AND target location
        to prevent traversal into external SDKs like Flutter/FVM.

        Args:
            path: Path to check (should be a symlink)

        Returns:
            True if the symlink target is within workspace root, False otherwise
        """
        if not path.is_symlink():
            return False

        try:
            # First check: Is the symlink itself within workspace?
            # (This should always pass since we're scanning from workspace root)
            path.relative_to(self.root_path)

            # Second check: Is the TARGET within workspace?
            # This is the critical check that prevents SDK traversal
            target = path.resolve()
            target.relative_to(self.root_path)

            # Both checks passed - safe to traverse
            return True
        except (ValueError, OSError):
            # ValueError: target is not within workspace root
            # OSError: broken symlink or permission issues
            try:
                target_desc = str(path.resolve()) if path.exists() else "broken"
            except Exception:
                target_desc = "unresolvable"
            logger.debug(f"Skipping symlink outside workspace: {path} -> {target_desc}")
            return False

    def _should_exclude_directory_basic(self, directory: Path) -> bool:
        """
        Basic directory exclusions for performance and reliability only.

        This must not exclude semantic/user names such as demos, examples,
        migrations, docs, assets, or tests. Canonical workspace status and
        delta rails depend on this scanner and must not silently hide source.

        Args:
            directory: Directory path to check

        Returns:
            True if directory should be excluded, False otherwise
        """
        dir_name = directory.name
        # IMPORTANT:
        # Directory exclusion heuristics must be based on paths *relative to the scan root*,
        # otherwise absolute paths like `/tmp/pytest-.../test_*` will accidentally exclude
        # legitimate workspaces that happen to live under `/tmp` or contain "test_" in
        # a parent directory name.
        dir_str = str(directory)
        try:
            rel = directory.resolve().relative_to(self.root_path).as_posix().strip("/")
            dir_str_for_patterns = f"/{rel}/" if rel else "/"
        except Exception:
            dir_str_for_patterns = dir_str

        ignored_dirs = _scanner_ignored_dirs(config=self.config.filter)
        if dir_name in ignored_dirs:
            return True

        # FAST PATH: String containment checks for infrastructure paths only.
        ignored_fragments = _scanner_ignored_path_fragments(config=self.config.filter)
        if any(
            pattern in dir_str_for_patterns
            for pattern in ignored_fragments
        ):
            return True

        # Pattern-based exclusions for file names in directory names
        if dir_name.endswith(".lock") or dir_name.endswith(".tmp"):
            return True

        return False

    def _process_file_changes(
        self, existing_index: Dict[str, FileMetadataCached], current_files: Set[str]
    ) -> ScanResult:
        """
        Process changes between existing index and current files.

        Optimized to only process changed files for maximum performance.

        Args:
            existing_index: Previously cached file metadata
            current_files: Currently discovered files

        Returns:
            ScanResult with detected changes
        """
        result = ScanResult()

        # Detect file changes efficiently
        indexed_files = set(existing_index.keys())
        result.deleted = indexed_files - current_files
        added_files = current_files - indexed_files

        # Only process files that might have changed (added + potentially modified)
        files_to_check = added_files.copy()

        # For existing files, quickly check if they might be modified using mtime/size
        for rel_path in indexed_files & current_files:  # intersection: existing files
            abs_path = str(self.root_path / rel_path)
            cached_metadata = existing_index[rel_path]

            # Quick modification check without creating full metadata
            try:
                stat_info = Path(abs_path).stat()
                # Compare mtime and size (fast check)
                cached_mtime = cached_metadata.last_modified.timestamp()
                if stat_info.st_mtime != cached_mtime or stat_info.st_size != cached_metadata.size:
                    files_to_check.add(rel_path)
                else:
                    # File definitely unchanged
                    result.unchanged.add(rel_path)
            except (OSError, AttributeError):
                # If stat fails, assume it might be changed
                files_to_check.add(rel_path)

        logger.debug(f"Processing {len(files_to_check)} potentially changed files out of {len(current_files)} total")

        # Process only files that might have changed
        for rel_path in files_to_check:
            abs_path = str(self.root_path / rel_path)
            cached_metadata = existing_index.get(rel_path)

            try:
                # Create optimized metadata (with cache reuse)
                current_metadata = FileMetadataCached.from_file_fast(abs_path, str(self.root_path), cached_metadata)

                result.files_processed += 1

                if cached_metadata is None:
                    # New file
                    result.added[rel_path] = current_metadata
                    if current_metadata.needs_hash_computation():
                        result.files_content_read += 1
                elif cached_metadata.mtime_ns == 0:
                    # Backfill nanosecond mtime support into the persisted scanner index.
                    result.modified[rel_path] = current_metadata
                    if current_metadata.needs_hash_computation():
                        result.files_content_read += 1
                elif current_metadata.is_modified_fast(cached_metadata):
                    # File modified (based on mtime/size)
                    result.modified[rel_path] = current_metadata
                    if current_metadata.needs_hash_computation():
                        result.files_content_read += 1
                else:
                    # File unchanged after detailed check
                    result.unchanged.add(rel_path)

            except FileNotFoundError:
                # File was in index but no longer exists - add to deleted set
                logger.debug(f"File no longer exists, marking as deleted: {rel_path}")
                result.deleted.add(rel_path)
                continue
            except Exception as e:
                logger.warning(f"Error processing {rel_path}: {e}")
                continue

        # Add quick stats for performance monitoring
        total_files = len(current_files)
        processed_files = len(files_to_check)
        result.files_processed = total_files  # Total files in scan

        # Avoid division by zero when there are no files
        if total_files == 0:
            percent = 0.0
        else:
            percent = processed_files / total_files

        logger.debug(f"Delta processing: {processed_files}/{total_files} files checked ({percent:.1%})")

        return result

    def _should_exclude_directory(self, directory: Path) -> bool:
        """
        REMOVED: No hardcoded directory exclusions.
        Use external filter.should_include() instead.

        This method is kept for compatibility but always returns False.
        """
        return False

    def _create_empty_result(self) -> ScanResult:
        """Create an empty scan result for cache hits."""
        result = ScanResult()
        result.scan_time = 0.001  # Minimal time for cache hit
        return result

    def invalidate_session_cache(self) -> None:
        """Invalidate the session-level cache to force a fresh scan."""
        self._session_cache = None
        self._last_scan_time = None
        logger.debug("Session cache invalidated")

    def reset_persistent_index(self) -> None:
        """
        Reset the persistent file index so the next scan rebuilds it from scratch.

        This is used for force-refresh scenarios (e.g., canonical environment builds)
        where we want to guarantee that no stale entries survive across runs.
        """
        try:
            # Save an empty index to storage
            self.storage.save_index({})
            # Also clear session cache so subsequent scans don't reuse stale state
            self._session_cache = None
            self._last_scan_time = None
            logger.debug("Persistent file index reset for incremental scanner")
        except Exception as exc:
            logger.warning(f"Failed to reset persistent file index: {exc}")

    def invalidate_directory_cache(self) -> None:
        """Invalidate the directory cache, forcing a full rescan."""
        cache_size = len(self._dir_cache.entries)
        self._dir_cache.clear()
        logger.debug(f"Directory cache invalidated ({cache_size} entries cleared, cache file removed)")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cache performance.

        Returns:
            Dictionary with cache statistics
        """
        storage_stats = self.storage.get_stats()
        dir_stats = self._dir_cache.get_stats()

        return {
            "persistent_cache": storage_stats.model_dump(),
            "session_cache": {
                "active": self._session_cache is not None,
                "entries": len(self._session_cache) if self._session_cache else 0,
                "last_scan": (self._last_scan_time.isoformat() if self._last_scan_time else None),
            },
            "directory_cache": dir_stats.model_dump(),
        }

    def cleanup_cache(self) -> int:
        """
        Clean up invalid entries from persistent cache.

        Returns:
            Number of entries removed
        """
        return self.storage.cleanup_invalid_entries()


def _scanner_ignored_dirs(*, config: object) -> frozenset[str]:
    inherit_defaults = getattr(config, "inherit_ignore_defaults", True)
    configured_dirs = getattr(config, "ignored_dirs", None) or []
    custom_dirs = frozenset(
        str(item).strip()
        for item in configured_dirs
        if str(item).strip()
    )
    if not inherit_defaults:
        return custom_dirs
    return DEFAULT_SCANNER_IGNORED_DIRS | custom_dirs


def _scanner_ignored_path_fragments(*, config: object) -> frozenset[str]:
    inherit_defaults = getattr(config, "inherit_ignore_defaults", True)
    if not inherit_defaults:
        return frozenset()
    return DEFAULT_SCANNER_IGNORED_PATH_FRAGMENTS
