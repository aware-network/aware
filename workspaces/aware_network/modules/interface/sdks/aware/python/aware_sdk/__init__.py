"""Aware SDK convenience bundle."""

from __future__ import annotations

from .app import (
    AwareAppLaunchDescriptor,
    AwareAppLaunchDescriptorError,
    AwareAppSession,
    AwareAppSessionError,
)

__all__ = [
    "AwareAppLaunchDescriptor",
    "AwareAppLaunchDescriptorError",
    "AwareAppSession",
    "AwareAppSessionError",
    "__version__",
]

__version__ = "0.8.0"
