"""
Path utilities for aware core.

This module provides common path manipulation utilities used across the aware codebase,
particularly for handling CI environment path normalization.
"""

from pathlib import Path


def normalize_ci_path(path: str) -> str:
    """
    Normalize path to use /aware/ prefix in CI environment.

    This handles the case where files are at /home/runner/work/aware/aware/
    but we want to work with them as if they're at /aware/

    Args:
        path: Path string to normalize

    Returns:
        Normalized path string
    """
    # Path is already in the /aware format
    if path.startswith("/aware/"):
        return path

    # Handle CI environment where files are in /home/runner/work/aware/aware
    if path.startswith("/home/runner/work/aware/aware/"):
        # Replace the prefix with /aware/, but only if the rewritten path exists
        candidate = path.replace("/home/runner/work/aware/aware/", "/aware/")
        if Path(candidate).exists():
            return candidate
        # Fallback to original path when the rewritten location is absent (e.g., local samples)
        return path

    return path


def normalize_ci_path_obj(path: Path) -> Path:
    """
    Normalize Path object to use /aware/ prefix in CI environment.

    Args:
        path: Path object to normalize

    Returns:
        Normalized Path object
    """
    return Path(normalize_ci_path(str(path)))
