"""
Cache Coordination Module for FileSystem Index Management.

This module provides event-driven cache synchronization between FileSystemIndex
and RepositoryIndex to eliminate manual cache invalidation requirements.
"""

from .events import FileSystemChangeEvent, EventEmitter
from .coordinator import CacheCoordinator, CacheableIndex

__all__ = [
    "FileSystemChangeEvent",
    "EventEmitter",
    "CacheCoordinator",
    "CacheableIndex",
]
