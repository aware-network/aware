"""Adapter exports for workspace bridge ports."""

from .compiler_service_remote import (
    CompilerServiceRemoteAdapter,
    CompilerServiceRequestFn,
)
from .defaults import InMemoryEvidenceAdapter, PassthroughWorkspaceDeltaAdapter
from .upgrade_service_remote import CompilerUpgradeRemoteAdapter

__all__ = [
    "CompilerServiceRemoteAdapter",
    "CompilerServiceRequestFn",
    "CompilerUpgradeRemoteAdapter",
    "InMemoryEvidenceAdapter",
    "PassthroughWorkspaceDeltaAdapter",
]
