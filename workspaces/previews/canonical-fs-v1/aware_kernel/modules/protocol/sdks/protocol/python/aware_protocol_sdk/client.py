"""Canonical Protocol SDK client with explicit provider injection."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    ProtocolTargetAdmissionProvider,
    ProtocolTargetAdmissionRequest,
    ProtocolTargetAdmissionResult,
)


@dataclass(frozen=True, slots=True)
class ProtocolSdkClient:
    provider: ProtocolTargetAdmissionProvider

    def admit_target(
        self,
        request: ProtocolTargetAdmissionRequest,
    ) -> ProtocolTargetAdmissionResult:
        return self.provider.admit_target(request)


__all__ = ["ProtocolSdkClient"]
