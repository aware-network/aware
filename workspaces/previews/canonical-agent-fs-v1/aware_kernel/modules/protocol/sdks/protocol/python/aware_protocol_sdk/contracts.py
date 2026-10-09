"""Typed request and result contracts for canonical Protocol SDK operations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from aware_protocol_runtime import (
    ProtocolAdmissionResult,
    ProtocolAuthorityMode,
    ProtocolContractError,
    ProtocolTargetKind,
)

PROTOCOL_ADMIT_TARGET_OPERATION_REF = "protocol_sdk.admit_target"
PROTOCOL_ADMIT_TARGET_PROVIDER_OPERATION_REF = "protocol.target.admit"
PROTOCOL_TARGET_ADMISSION_REQUEST_CONTRACT = (
    "aware.protocol.target-admission-request.v1"
)
PROTOCOL_TARGET_ADMISSION_RESULT_CONTRACT = "aware.protocol.target-admission-result.v2"


def _text(value: object, field_name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ProtocolContractError(f"{field_name} must be non-empty trimmed text")
    return value


@dataclass(frozen=True, slots=True)
class ProtocolTargetAdmissionRequest:
    authority_mode: ProtocolAuthorityMode
    target_ref: str
    source_ref: str
    target_kind: ProtocolTargetKind = ProtocolTargetKind.REPOSITORY

    def __post_init__(self) -> None:
        if type(self) is not ProtocolTargetAdmissionRequest:
            raise ProtocolContractError(
                "request must be ProtocolTargetAdmissionRequest"
            )
        if type(self.authority_mode) is not ProtocolAuthorityMode:
            raise ProtocolContractError("authority_mode must be ProtocolAuthorityMode")
        if type(self.target_kind) is not ProtocolTargetKind:
            raise ProtocolContractError("target_kind must be ProtocolTargetKind")
        object.__setattr__(self, "target_ref", _text(self.target_ref, "target_ref"))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": PROTOCOL_TARGET_ADMISSION_REQUEST_CONTRACT,
            "target_kind": self.target_kind.value,
            "authority_mode": self.authority_mode.value,
            "target_ref": self.target_ref,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True, slots=True)
class ProtocolTargetAdmissionResult:
    provider_ref: str
    provider_distribution: str
    provider_version: str
    admission: ProtocolAdmissionResult
    request: ProtocolTargetAdmissionRequest
    evidence: tuple[str, ...] = ()
    operation_ref: str = PROTOCOL_ADMIT_TARGET_OPERATION_REF

    def __post_init__(self) -> None:
        if type(self) is not ProtocolTargetAdmissionResult:
            raise ProtocolContractError("result must be ProtocolTargetAdmissionResult")
        if (
            type(self.operation_ref) is not str
            or self.operation_ref != PROTOCOL_ADMIT_TARGET_OPERATION_REF
        ):
            raise ProtocolContractError(
                "operation_ref must identify protocol_sdk.admit_target"
            )
        object.__setattr__(
            self, "provider_ref", _text(self.provider_ref, "provider_ref")
        )
        object.__setattr__(
            self,
            "provider_distribution",
            _text(self.provider_distribution, "provider_distribution"),
        )
        object.__setattr__(
            self,
            "provider_version",
            _text(self.provider_version, "provider_version"),
        )
        if type(self.admission) is not ProtocolAdmissionResult:
            raise ProtocolContractError("admission must be ProtocolAdmissionResult")
        if type(self.request) is not ProtocolTargetAdmissionRequest:
            raise ProtocolContractError(
                "request must be ProtocolTargetAdmissionRequest"
            )
        object.__setattr__(self, "request", replace(self.request))
        object.__setattr__(self, "admission", snapshot_admission(self.admission))
        if type(self.evidence) not in (tuple, list):
            raise ProtocolContractError("evidence must be a tuple or list of strings")
        evidence = tuple(self.evidence)
        if any(type(item) is not str or not item for item in evidence):
            raise ProtocolContractError("evidence must contain non-empty strings")
        object.__setattr__(self, "evidence", evidence)

    def to_wire(self) -> dict[str, object]:
        return {
            "contract": PROTOCOL_TARGET_ADMISSION_RESULT_CONTRACT,
            "operation_ref": self.operation_ref,
            "provider_ref": self.provider_ref,
            "provider_distribution": self.provider_distribution,
            "provider_version": self.provider_version,
            "request": self.request.to_wire(),
            "admission": self.admission.to_wire(),
            "evidence": list(self.evidence),
        }


def snapshot_admission(value: ProtocolAdmissionResult) -> ProtocolAdmissionResult:
    """Reconstruct through the original value owners, not a second validator."""
    if type(value.diagnostics) not in (tuple, list):
        raise ProtocolContractError("diagnostics must be a tuple or list")
    manifest = value.manifest
    if manifest is not None:
        # Require owner types before traversing malformed provider objects.
        from aware_protocol_runtime import (
            ProtocolBootstrap,
            ProtocolIdentity,
            ProtocolManifest,
            ProtocolRecordBinding,
            ProtocolTarget,
        )

        if type(manifest) is not ProtocolManifest:
            raise ProtocolContractError("manifest must be ProtocolManifest")
        for child, expected in (
            (manifest.protocol, ProtocolIdentity),
            (manifest.target, ProtocolTarget),
            (manifest.bootstrap, ProtocolBootstrap),
        ):
            if type(child) is not expected:
                raise ProtocolContractError("invalid manifest child")
        if type(manifest.records) not in (tuple, list) or any(
            type(child) is not ProtocolRecordBinding for child in manifest.records
        ):
            raise ProtocolContractError("invalid record binding")
        manifest = replace(
            manifest,
            protocol=replace(manifest.protocol),
            target=replace(manifest.target),
            bootstrap=replace(manifest.bootstrap),
            records=tuple(replace(child) for child in manifest.records),
        )
    return replace(value, manifest=manifest)


class ProtocolTargetAdmissionProvider(Protocol):
    def admit_target(
        self,
        request: ProtocolTargetAdmissionRequest,
    ) -> ProtocolTargetAdmissionResult: ...


__all__ = [
    "PROTOCOL_ADMIT_TARGET_OPERATION_REF",
    "PROTOCOL_ADMIT_TARGET_PROVIDER_OPERATION_REF",
    "PROTOCOL_TARGET_ADMISSION_REQUEST_CONTRACT",
    "PROTOCOL_TARGET_ADMISSION_RESULT_CONTRACT",
    "ProtocolTargetAdmissionProvider",
    "ProtocolTargetAdmissionRequest",
    "ProtocolTargetAdmissionResult",
]
