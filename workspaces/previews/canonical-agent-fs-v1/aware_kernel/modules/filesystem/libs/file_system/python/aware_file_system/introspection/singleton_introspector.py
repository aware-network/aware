"""
Singleton FileSystemIntrospector - Ensures proper caching and reuse.

This module provides a singleton pattern for FileSystemIntrospector to ensure
that the same instance is reused across the application, maximizing cache benefits.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from aware_file_system.config import Config
from aware_file_system.models import ProjectStructure

from aware_file_system.introspection.introspector import FileSystemIntrospector

logger = logging.getLogger(__name__)


class SingletonFileSystemIntrospector:
    """
    Singleton wrapper for FileSystemIntrospector.

    Ensures that the same instance is reused for the same root path,
    maximizing cache benefits and avoiding redundant introspection.
    """

    _instances: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls, config: Config) -> Any:
        """
        Get or create a singleton instance for the given config.

        Uses root_path as the key to ensure one instance per repository.

        Args:
            config: Configuration for the introspector

        Returns:
            FileSystemIntrospector instance (original or optimized)
        """
        # Use normalized root path as key
        root_path = str(Path(config.file_system.root_path).resolve())

        if root_path not in cls._instances:
            logger.info(f"Creating new FileSystemIntrospector instance for: {root_path}")
            # Create new instance using the best available implementation
            instance = FileSystemIntrospector(config)
            cls._instances[root_path] = instance
        else:
            logger.debug(f"Reusing existing FileSystemIntrospector instance for: {root_path}")

        return cls._instances[root_path]

    @classmethod
    def introspect(cls, config: Config) -> ProjectStructure:
        """
        Convenience method for introspection using singleton pattern.

        Args:
            config: Configuration for introspection

        Returns:
            ProjectStructure with file metadata
        """
        instance = cls.get_instance(config)
        return instance.introspect()

    @classmethod
    def clear_cache(cls, root_path: Optional[str] = None) -> None:
        """
        Clear cached instances.

        Args:
            root_path: Specific path to clear, or None to clear all
        """
        if root_path:
            normalized_path = str(Path(root_path).resolve())
            if normalized_path in cls._instances:
                logger.info(f"Clearing FileSystemIntrospector cache for: {normalized_path}")

                # If optimized, clear its cache too
                instance = cls._instances[normalized_path]
                if hasattr(instance, "invalidate_cache"):
                    instance.invalidate_cache()

                del cls._instances[normalized_path]
        else:
            logger.info("Clearing all FileSystemIntrospector caches")

            # Clear internal caches if optimized
            for instance in cls._instances.values():
                if hasattr(instance, "invalidate_cache"):
                    instance.invalidate_cache()

            cls._instances.clear()

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get cache statistics across all instances.

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "instances_count": len(cls._instances),
            "root_paths": list(cls._instances.keys()),
        }

        # Get performance stats from instances
        instance_stats = {}
        for root_path, instance in cls._instances.items():
            if hasattr(instance, "get_performance_stats"):
                try:
                    instance_stats[root_path] = instance.get_performance_stats()
                except Exception as e:
                    logger.warning(f"Error getting stats for {root_path}: {e}")

        if instance_stats:
            stats["performance_stats"] = instance_stats

        return stats


# Convenience functions for direct usage
def introspect(config: Config) -> ProjectStructure:
    """
    Perform file system introspection using singleton pattern.

    Args:
        config: Configuration for introspection

    Returns:
        ProjectStructure with file metadata
    """
    return SingletonFileSystemIntrospector.introspect(config)


def get_introspector_instance(config: Config):
    """
    Get FileSystemIntrospector instance using singleton pattern.

    Args:
        config: Configuration for the introspector

    Returns:
        FileSystemIntrospector instance
    """
    return SingletonFileSystemIntrospector.get_instance(config)


def clear_introspector_cache(root_path: Optional[str] = None) -> None:
    """
    Clear FileSystemIntrospector cache.

    Args:
        root_path: Specific path to clear, or None to clear all
    """
    SingletonFileSystemIntrospector.clear_cache(root_path)


def get_introspector_stats() -> Dict[str, Any]:
    """
    Get FileSystemIntrospector cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    return SingletonFileSystemIntrospector.get_cache_stats()
