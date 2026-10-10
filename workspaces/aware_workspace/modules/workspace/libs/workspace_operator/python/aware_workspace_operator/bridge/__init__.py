"""Bridge backbone exports for workspace-environment orchestration."""

from .interfaces import (
    CompilerSessionPort,
    EvidencePort,
    UpgradePort,
    WorkspaceDeltaPort,
)
from .models import (
    BridgeEvidenceEvent,
    CompilerOperationResult,
    UpgradeExecutionResult,
    WorkspaceBridgeCycleRequest,
    WorkspaceBridgeCycleResult,
)
from .orchestrator import WorkspaceBridgeOrchestrator

__all__ = [
    "BridgeEvidenceEvent",
    "CompilerOperationResult",
    "CompilerSessionPort",
    "EvidencePort",
    "UpgradeExecutionResult",
    "UpgradePort",
    "WorkspaceBridgeCycleRequest",
    "WorkspaceBridgeCycleResult",
    "WorkspaceBridgeOrchestrator",
    "WorkspaceDeltaPort",
]
