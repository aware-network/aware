"""
Cache Models - Fully typed Pydantic models for file system caching.

This module provides comprehensive type-safe models for all cache-related
data structures, ensuring type safety and consistency across the system.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, List
from pydantic import BaseModel, Field


class DirectoryChangeReason(BaseModel):
    """Detailed information about why a directory was marked as changed."""

    path: str
    reason: str  # "new", "mtime_changed", "child_count_changed", "error"
    old_mtime_ns: Optional[int] = None
    new_mtime_ns: Optional[int] = None
    old_child_count: Optional[int] = None
    new_child_count: Optional[int] = None
    error_message: Optional[str] = None


class DirectoryScanResult(BaseModel):
    """Result of directory scanning operation."""

    total_directories: int
    changed_directories: int
    unchanged_directories: int
    new_directories: int
    deleted_directories: int
    error_directories: int
    scan_time_ms: float
    change_reasons: List[DirectoryChangeReason] = Field(default_factory=list)


class CachePerformanceMetrics(BaseModel):
    """Performance metrics for cache operations."""

    cache_hit_ratio: float
    directories_skipped: int
    directories_scanned: int
    files_from_cache: int
    files_scanned: int
    total_time_ms: float
    cache_lookup_time_ms: float
    directory_scan_time_ms: float
    file_scan_time_ms: float


class SessionCacheInfo(BaseModel):
    """Information about session-level cache."""

    active: bool
    entries: int
    last_scan: Optional[datetime] = None
    age_seconds: Optional[float] = None
    memory_usage_bytes: Optional[int] = None


class CacheDebugInfo(BaseModel):
    """Comprehensive debug information for cache diagnostics."""

    directory_cache: DirectoryScanResult
    session_cache: SessionCacheInfo
    performance: CachePerformanceMetrics
    volatile_directories: List[str] = Field(default_factory=list, description="Directories that frequently change")
    recommendations: List[str] = Field(default_factory=list, description="Optimization recommendations")
