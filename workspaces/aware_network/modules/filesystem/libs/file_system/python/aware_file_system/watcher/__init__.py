"""
File System Watcher Module - Real-time file system monitoring.
"""

from .file_system_watcher import (
    FileSystemWatcher,
    RepositoryFileSystemWatcher,
    FileChangeEvent,
)

__all__ = [
    "FileSystemWatcher",
    "RepositoryFileSystemWatcher",
    "FileChangeEvent",
]
