"""Canonical Protocol SDK client with explicit provider injection."""

from __future__ import annotations

from dataclasses import dataclass, replace

from aware_protocol_runtime import ProtocolContractError

from .admission_error import ProtocolTargetAdmissionError
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
        try:
            if type(request) is not ProtocolTargetAdmissionRequest:
                raise ProtocolContractError("Expected exact admission request")
            original = replace(request)
        except (ProtocolContractError, TypeError, ValueError, AttributeError) as error:
            raise ProtocolTargetAdmissionError(
                "admission_request_invalid",
                "Invalid Protocol admission request",
                diagnostics=("request_validation:" + type(error).__name__,),
            ) from error
        result = self.provider.admit_target(replace(original))
        try:
            if type(result) is not ProtocolTargetAdmissionResult:
                raise ProtocolContractError("Expected exact admission result")
            validated = replace(result)
            if validated.request != original:
                raise ProtocolContractError(
                    "Admission result answers a different request"
                )
            manifest = validated.admission.manifest
            if manifest is not None and (
                manifest.target.kind is not original.target_kind
                or manifest.target.authority_mode is not original.authority_mode
            ):
                raise ProtocolContractError(
                    "Admission manifest answers a different authority"
                )
        except (ProtocolContractError, TypeError, ValueError, AttributeError) as error:
            raise ProtocolTargetAdmissionError(
                "admission_provider_result_invalid",
                "Invalid or uncorrelated Protocol admission result",
                diagnostics=("result_validation:" + type(error).__name__,),
                provider_invoked=True,
                reported_result=result,
            ) from error
        return validated


__all__ = ["ProtocolSdkClient"]
