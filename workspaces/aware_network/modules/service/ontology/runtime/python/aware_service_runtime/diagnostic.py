from __future__ import annotations

from typing import Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aware_service_runtime.error_codes import (
    ErrorCategory,
    ErrorSeverity,
    ResolutionStatus,
)


DiagnosticScalar: TypeAlias = str | int | float | bool | UUID
DiagnosticCollection: TypeAlias = (
    list[str] | list[int] | list[float] | list[bool] | list[UUID]
)
DiagnosticValue: TypeAlias = DiagnosticScalar | DiagnosticCollection
DiagnosticDumpMode: TypeAlias = Literal["json", "python"]


class RuntimeDiagnosticEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    value: DiagnosticValue


class RuntimeDiagnosticSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    entries: list[RuntimeDiagnosticEntry] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.entries


class RuntimeDiagnostic(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    summary: str
    detail: str | None = None
    hint: str | None = None
    semantic_refs: RuntimeDiagnosticSection = Field(
        default_factory=lambda: RuntimeDiagnosticSection(title="Semantic Refs")
    )
    invocation_context: RuntimeDiagnosticSection = Field(
        default_factory=lambda: RuntimeDiagnosticSection(title="Invocation")
    )
    provenance: RuntimeDiagnosticSection = Field(
        default_factory=lambda: RuntimeDiagnosticSection(title="Provenance")
    )
    resolution_status: ResolutionStatus = ResolutionStatus.unresolved
    debug: RuntimeDiagnosticSection | None = None

    @field_validator("code")
    @classmethod
    def _validate_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Runtime diagnostic code is required.")
        return normalized


class AwareDiagnosticError(PermissionError):
    def __init__(self, diagnostic: RuntimeDiagnostic):
        self.diagnostic = diagnostic
        super().__init__(diagnostic.summary)

    @property
    def summary(self) -> str:
        return self.diagnostic.summary

    def model_dump(self, *, mode: DiagnosticDumpMode = "python") -> dict[str, object]:
        return self.diagnostic.model_dump(mode=mode)


class AwareInternalError(RuntimeError):
    def __init__(self, diagnostic: RuntimeDiagnostic):
        self.diagnostic = diagnostic
        super().__init__(diagnostic.summary)

    def model_dump(self, *, mode: DiagnosticDumpMode = "python") -> dict[str, object]:
        return self.diagnostic.model_dump(mode=mode)


__all__ = [
    "AwareDiagnosticError",
    "AwareInternalError",
    "DiagnosticCollection",
    "DiagnosticDumpMode",
    "DiagnosticScalar",
    "DiagnosticValue",
    "RuntimeDiagnostic",
    "RuntimeDiagnosticEntry",
    "RuntimeDiagnosticSection",
]
