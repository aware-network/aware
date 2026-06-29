"""
AWARE File System - Core file system introspection and analysis.

This package provides file system introspection, filtering, and analysis
capabilities for the AWARE system.
"""

# Core models and configuration
from .models import ProjectStructure, FileMetadata, FileType, Changes
from .config import (
    Config,
    FileSystemConfig,
    FilterConfig,
    CanonicalSourceFilterConfig,
    CodeIntrospectionFilterConfig,
)

# Core introspector (original implementation)
from .introspection.introspector import FileSystemIntrospector
from .index.file_metadata_cached import FileMetadataCached
from .index.incremental_scanner import IncrementalScanner, ScanResult
from .index.index_storage import IndexStorage
from .index.file_system_index import FileSystemIndex
from .native_backend import (
    FileSystemBackendCapabilities,
    active_backend_capabilities,
    detect_native_backend,
)

from .introspection.singleton_introspector import (
    introspect,
    get_introspector_instance,
    clear_introspector_cache,
    get_introspector_stats,
    SingletonFileSystemIntrospector,
)

# Export core components
__all__ = [
    # Models
    "ProjectStructure",
    "FileMetadata",
    "FileType",
    "Changes",
    # Configuration
    "Config",
    "FileSystemConfig",
    "FilterConfig",
    "CanonicalSourceFilterConfig",
    "CodeIntrospectionFilterConfig",
    # Introspector
    "FileSystemIntrospector",
    "FileMetadataCached",
    "IncrementalScanner",
    "ScanResult",
    "IndexStorage",
    "FileSystemIndex",
    "FileSystemBackendCapabilities",
    "active_backend_capabilities",
    "detect_native_backend",
    # singleton
    "introspect",
    "get_introspector_instance",
    "clear_introspector_cache",
    "get_introspector_stats",
    "SingletonFileSystemIntrospector",
    "__version__",
]

__version__ = "0.1.1"
