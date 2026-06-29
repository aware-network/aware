"""
File System Index - High-performance caching integration for FileSystemIntrospector.

This module provides a drop-in replacement for the existing FileSystemIntrospector
with dramatic performance improvements through caching and incremental updates.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Set, Any
import logging

from aware_file_system.config import Config
from aware_file_system.models import ProjectStructure, FileMetadata, ChangeType
from aware_file_system.index.incremental_scanner import IncrementalScanner, ScanResult
from aware_file_system.index.file_metadata_cached import FileMetadataCached
from aware_file_system.coordination import (
    CacheCoordinator,
    EventEmitter,
)

logger = logging.getLogger(__name__)


class FileSystemIndex:
    """
    High-performance file system index with caching and incremental updates.

    This is a drop-in replacement for FileSystemIntrospector that provides:
    1. Dramatic performance improvements (4.5s -> <1s)
    2. Session-level caching for repeated operations
    3. Persistent caching across application restarts
    4. Incremental updates for large repositories
    5. Full compatibility with existing ProjectStructure interface
    """

    def __init__(
        self,
        config: Config,
        cache_coordinator: Optional[CacheCoordinator] = None,
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize the file system index.

        Args:
            config: Configuration for file system scanning
            cache_coordinator: Optional cache coordinator for coordinated invalidation
            cache_dir: Optional custom cache directory
        """
        self.config = config
        self.root_path = Path(config.file_system.root_path).resolve()
        self.scanner = IncrementalScanner(config, cache_dir)
        self.cache_coordinator = cache_coordinator

        # Performance tracking
        self._last_scan_result: Optional[ScanResult] = None

        # Event emitter for cache coordination
        self.event_emitter = EventEmitter("FileSystemIndex")

        # Register with cache coordinator if provided
        if cache_coordinator:
            cache_coordinator.register_index(self, "FileSystemIndex")
            self.event_emitter.add_handler(cache_coordinator)

        logger.debug(
            f"Initialized FileSystemIndex for {self.root_path} with coordination: {cache_coordinator is not None}"
        )

    def introspect(self, force_refresh: bool = False) -> ProjectStructure:
        """
        Perform high-performance introspection with caching.

        This method provides the same interface as FileSystemIntrospector.introspect()
        but with dramatic performance improvements through caching.

        Args:
            force_refresh: If True, bypass session cache AND directory cache for immediate change detection

        Returns:
            ProjectStructure containing all file metadata
        """
        start_time = datetime.now()

        # Timing checkpoint 1: Cache operations
        cache_start = datetime.now()
        # For validation/debugging scenarios, also invalidate caches and reset persistent index
        if force_refresh:
            logger.debug("FileSystemIndex force refresh: invalidating directory cache and resetting persistent index")
            # Ensure directory-level cache is cleared so discovery sees all current files
            self.invalidate_directory_cache()
            # Reset both session cache and on-disk index so the next scan fully rebuilds
            try:
                self.scanner.invalidate_session_cache()
                self.scanner.reset_persistent_index()
            except Exception as exc:
                logger.warning(f"Failed to fully reset file system index caches: {exc}")
        cache_time = (datetime.now() - cache_start).total_seconds()

        # Timing checkpoint 2: Incremental scan
        scan_start = datetime.now()
        # Perform incremental scan (bypass session cache if force_refresh=True)
        scan_result = self.scanner.scan_incremental(use_session_cache=not force_refresh)
        self._last_scan_result = scan_result
        scan_time = (datetime.now() - scan_start).total_seconds()

        # Timing checkpoint 3: Metadata conversion
        metadata_start = datetime.now()
        # Convert cached metadata to standard FileMetadata format
        files_metadata = self._build_files_metadata_dict(scan_result)
        metadata_time = (datetime.now() - metadata_start).total_seconds()

        # Timing checkpoint 4: ProjectStructure assembly
        structure_start = datetime.now()
        # Build ProjectStructure
        project_structure = ProjectStructure(
            root_path=str(self.root_path),
            tree="",  # Generate tree if needed
            files_metadata=files_metadata,
            total_size=sum(metadata.size for metadata in files_metadata.values()),
            file_count=len(files_metadata),
            max_depth=max((metadata.depth for metadata in files_metadata.values()), default=0),
            last_updated=datetime.now(),
        )

        # Generate tree representation if enabled
        if self.config.file_system.generate_tree:
            project_structure.tree = self._generate_tree(project_structure)
        structure_time = (datetime.now() - structure_start).total_seconds()

        # Timing checkpoint 5: Event coordination
        events_start = datetime.now()
        # Emit change events for cache coordination
        self._detect_changes_and_emit_events(scan_result)
        events_time = (datetime.now() - events_start).total_seconds()

        # Log performance metrics with granular timing breakdown
        total_time = (datetime.now() - start_time).total_seconds()
        logger.debug(
            f"FileSystemIndex introspection complete: "
            f"{project_structure.file_count} files, "
            f"{scan_result.files_content_read}/{scan_result.files_processed} files read, "
            f"cache hit ratio: {scan_result.cache_hit_ratio:.1%}, "
            f"total time: {total_time:.2f}s"
        )
        logger.debug(
            f"🔍 FileSystemIndex timing breakdown: "
            f"cache: {cache_time:.2f}s, "
            f"scan: {scan_time:.2f}s, "
            f"metadata: {metadata_time:.2f}s, "
            f"structure: {structure_time:.2f}s, "
            f"events: {events_time:.2f}s"
        )

        return project_structure

    def list_relative_paths(self, force_refresh: bool = False) -> Set[str]:
        """
        Return current repository-relative file paths without materializing file content.

        This is the lightweight counterpart to ``introspect()`` for callers that only
        need file membership and not a full ``ProjectStructure`` with ``FileMetadata``
        content payloads.
        """
        if force_refresh:
            logger.debug("FileSystemIndex force refresh for path listing: invalidating directory cache")
            self.invalidate_directory_cache()
            try:
                self.scanner.invalidate_session_cache()
                self.scanner.reset_persistent_index()
            except Exception as exc:
                logger.warning(f"Failed to fully reset file system index caches: {exc}")

        scan_result = self.scanner.scan_incremental(use_session_cache=not force_refresh)
        self._last_scan_result = scan_result
        if not self.scanner._session_cache:
            return set()
        return set(self.scanner._session_cache.keys())

    def scan_relative_metadata(
        self,
        force_refresh: bool = False,
    ) -> tuple[ScanResult, Dict[str, FileMetadataCached]]:
        """
        Return the latest incremental scan result plus cached relative file metadata.

        This is the lightweight status/observation path counterpart to ``introspect()``,
        exposing change detection + stat metadata without materializing file contents.
        """
        if force_refresh:
            logger.debug("FileSystemIndex force refresh for metadata scan: invalidating directory cache")
            self.invalidate_directory_cache()
            try:
                self.scanner.invalidate_session_cache()
                self.scanner.reset_persistent_index()
            except Exception as exc:
                logger.warning(f"Failed to fully reset file system index caches: {exc}")

        scan_result = self.scanner.scan_incremental(use_session_cache=not force_refresh)
        self._last_scan_result = scan_result
        if not self.scanner._session_cache:
            return scan_result, {}
        return scan_result, dict(self.scanner._session_cache)

    def _build_files_metadata_dict(self, scan_result: ScanResult) -> Dict[str, FileMetadata]:
        """
        Build files metadata dictionary from scan result.

        This method handles the conversion from cached metadata to standard FileMetadata,
        with intelligent hash computation only when needed.

        Args:
            scan_result: Result from incremental scan

        Returns:
            Dictionary of relative_path -> FileMetadata
        """
        files_metadata = {}

        # Get all current files from scanner's session cache
        if self.scanner._session_cache:
            for rel_path, cached_metadata in self.scanner._session_cache.items():
                try:
                    abs_path = str(self.root_path / rel_path)

                    # Convert to standard FileMetadata format
                    # Only reads content if hash computation is needed
                    file_metadata = cached_metadata.to_file_metadata(abs_path)
                    files_metadata[rel_path] = file_metadata

                except Exception as e:
                    logger.warning(f"Error converting metadata for {rel_path}: {e}")
                    continue

        return files_metadata

    def _generate_tree(self, structure: ProjectStructure) -> str:
        """
        Generate a tree representation of the project structure.

        This is identical to the original FileSystemIntrospector implementation
        for compatibility.

        Args:
            structure: Project structure to represent

        Returns:
            String representation of the project tree
        """
        import os

        def add_files_from_dir(path_parts: list[str], prefix: str, is_last: bool) -> list[str]:
            # Base path represented by path_parts
            current_path = os.path.join(*path_parts) if path_parts else ""

            # Find files and directories at this path
            files = []
            dirs = []

            for file_path in structure.files_metadata:
                file_parts = file_path.split(os.sep)

                # Handle file at current directory level
                if len(file_parts) == len(path_parts) + 1:
                    # For files directly in this directory, check if parent dir matches
                    if len(path_parts) == 0:  # Root directory
                        # For root dir, we can't do a join, so check if file has no directory parts
                        if len(file_parts) == 1:
                            files.append(file_parts[0])
                    else:
                        # For non-root dirs, check if parent directory matches
                        parent_dir = os.path.join(*file_parts[:-1])
                        if parent_dir == current_path:
                            files.append(file_parts[-1])

                # Handle subdirectories
                elif len(file_parts) > len(path_parts) + 1:
                    # Get the immediate subdirectory at this level
                    if len(path_parts) == 0:  # Root directory
                        subdir = file_parts[0]
                    else:
                        # For non-root dirs, check if this file is in our tree
                        parent_dir = os.path.join(*file_parts[: len(path_parts)])
                        if parent_dir == current_path:
                            subdir = file_parts[len(path_parts)]
                        else:
                            continue

                    if subdir not in dirs:
                        dirs.append(subdir)

            # Sort files and directories
            files.sort()
            dirs.sort()

            lines = []
            # Add directories first
            for i, dir_name in enumerate(dirs):
                is_last_item = (i == len(dirs) - 1) and (len(files) == 0)
                dir_prefix = "└── " if is_last_item else "├── "
                lines.append(f"{prefix}{dir_prefix}{dir_name}/")

                # Recursively add subdirectory contents
                next_prefix = prefix + ("    " if is_last_item else "│   ")
                new_path_parts = path_parts + [dir_name]
                lines.extend(add_files_from_dir(new_path_parts, next_prefix, is_last_item))

            # Add files
            for i, file_name in enumerate(files):
                is_last_item = i == len(files) - 1
                file_prefix = "└── " if is_last_item else "├── "
                lines.append(f"{prefix}{file_prefix}{file_name}")

            return lines

        lines = [str(self.root_path)]
        lines.extend(add_files_from_dir([], "", True))
        return "\n".join(lines)

    def invalidate_cache(self) -> None:
        """
        Invalidate all caches to force a complete rescan.

        Useful when you know files have changed outside of normal detection.
        """
        self.scanner.invalidate_session_cache()
        logger.debug("FileSystemIndex cache invalidated")

    def invalidate_directory_cache(self) -> None:
        """
        Invalidate the directory cache, forcing a full directory rescan.
        """
        self.scanner.invalidate_directory_cache()
        logger.debug("FileSystemIndex directory cache invalidated")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get detailed performance statistics.

        Returns:
            Dictionary with performance and cache statistics
        """
        cache_stats = self.scanner.get_cache_stats()

        performance_stats = {"cache": cache_stats, "last_scan": None}

        if self._last_scan_result:
            performance_stats["last_scan"] = {
                "total_changes": self._last_scan_result.total_changes,
                "files_processed": self._last_scan_result.files_processed,
                "files_content_read": self._last_scan_result.files_content_read,
                "cache_hit_ratio": self._last_scan_result.cache_hit_ratio,
                "scan_time": self._last_scan_result.scan_time,
            }

        return performance_stats

    def cleanup_cache(self) -> int:
        """
        Clean up invalid cache entries.

        Returns:
            Number of entries removed
        """
        return self.scanner.cleanup_cache()

    # CacheableIndex protocol implementation
    def invalidate_paths(self, paths: Set[str]) -> None:
        """
        Invalidate cache entries for specific paths (CacheableIndex interface).

        This provides selective cache invalidation coordinated by the CacheCoordinator.

        Args:
            paths: Set of relative paths that need cache invalidation
        """
        if not paths:
            return

        # Selective session cache invalidation
        if self.scanner._session_cache:
            for path in paths:
                self.scanner._session_cache.pop(path, None)

        # Selective directory cache invalidation
        self.scanner._dir_cache.invalidate_paths(paths)

        logger.debug(f"FileSystemIndex: Invalidated {len(paths)} cache paths")

    def invalidate_all(self) -> None:
        """
        Invalidate entire cache (CacheableIndex interface).

        This is a fallback method used when selective invalidation fails.
        """
        self.scanner.invalidate_session_cache()
        self.scanner.invalidate_directory_cache()
        logger.debug("FileSystemIndex: Performed full cache invalidation")

    def _detect_changes_and_emit_events(self, scan_result: ScanResult) -> None:
        """
        Detect changes and emit events for cache coordination.

        This method analyzes the scan result and emits appropriate change events
        for other components to coordinate their cache invalidation.

        Args:
            scan_result: Result from incremental scan containing change information
        """
        if not self.cache_coordinator:
            return  # No coordination needed

        # Collect all changed paths
        all_changed_paths = set()
        all_changed_paths.update(scan_result.added.keys())
        all_changed_paths.update(scan_result.modified.keys())
        all_changed_paths.update(scan_result.deleted)

        if not all_changed_paths:
            return  # No changes detected

        # Emit change event for coordination
        self.event_emitter.emit_change_event(
            change_type=ChangeType.update,  # Mixed changes - coordinator will handle details
            affected_paths=all_changed_paths,
            additional_context={
                "scan_stats": {
                    "files_added": len(scan_result.added),
                    "files_modified": len(scan_result.modified),
                    "files_deleted": len(scan_result.deleted),
                    "scan_time": scan_result.scan_time,
                    "cache_hit_ratio": scan_result.cache_hit_ratio,
                }
            },
        )

        logger.debug(f"Emitted change event for {len(all_changed_paths)} affected paths")

    @classmethod
    def create_optimized_introspector(cls, config: Config, cache_dir: Optional[str] = None) -> "FileSystemIndex":
        """
        Factory method to create an optimized introspector.

        This provides a clear migration path from FileSystemIntrospector to FileSystemIndex.

        Args:
            config: File system configuration
            cache_dir: Optional custom cache directory

        Returns:
            FileSystemIndex instance ready for use
        """
        return cls(config, cache_dir=cache_dir)
