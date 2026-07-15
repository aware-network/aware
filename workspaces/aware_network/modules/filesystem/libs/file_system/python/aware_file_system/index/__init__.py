"""
File System Index - High-performance caching and incremental updates.

This module provides persistent file system indexing with hash-based change detection
for optimal performance in large repositories and DART materialization support.
"""

try:
    from .file_metadata_cached import FileMetadataCached
except ImportError:
    FileMetadataCached = None

try:
    from .index_storage import IndexStorage
except ImportError:
    IndexStorage = None

try:
    from .incremental_scanner import IncrementalScanner
except ImportError:
    IncrementalScanner = None

try:
    from .file_system_index import FileSystemIndex
except ImportError:
    FileSystemIndex = None

__all__ = []

if FileMetadataCached:
    __all__.append("FileMetadataCached")
if IndexStorage:
    __all__.append("IndexStorage")
if IncrementalScanner:
    __all__.append("IncrementalScanner")
if FileSystemIndex:
    __all__.append("FileSystemIndex")
