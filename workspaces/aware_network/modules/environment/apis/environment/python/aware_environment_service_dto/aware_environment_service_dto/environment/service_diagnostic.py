from __future__ import annotations

# Standard
from enum import Enum

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonValue


class ServiceDiagnosticCategory(Enum):
    """SSOT: `environment-service-dto` generated from `apis/environment/dto`."""

    runtime_invariant = "runtime_invariant"
    internal_failure = "internal_failure"


class ServiceDiagnosticSeverity(Enum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class ServiceDiagnosticResolutionStatus(Enum):
    unresolved = "unresolved"
    partial = "partial"
    resolved = "resolved"


class ServiceDiagnosticEntry(BaseModel):
    # Attributes
    key: str
    value: JsonValue


class ServiceDiagnosticSection(BaseModel):
    # Attributes
    title: str
    entries: list[ServiceDiagnosticEntry] = Field(default_factory=list)


class ServiceDiagnostic(BaseModel):
    # Attributes
    code: str
    category: ServiceDiagnosticCategory
    severity: ServiceDiagnosticSeverity
    summary: str
    detail: str | None = Field(default=None)
    hint: str | None = Field(default=None)
    semantic_refs: ServiceDiagnosticSection
    invocation_context: ServiceDiagnosticSection
    provenance: ServiceDiagnosticSection
    resolution_status: ServiceDiagnosticResolutionStatus = Field(default=ServiceDiagnosticResolutionStatus.unresolved)
    debug: ServiceDiagnosticSection | None = Field(default=None)
