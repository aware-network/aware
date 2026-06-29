from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class LanguageServiceDiagnosticSeverity(Enum):
    """Language-service report severity values.

    These are inline editor/report DTOs owned by the language service. They are
    not Structure repository models and do not participate in OIG truth.
    """

    error = "error"
    warning = "warning"
    info = "info"
    hint = "hint"


class LanguageServiceSnapshotMode(Enum):
    package = "package"
    fallback = "fallback"


class LanguageServicePosition(BaseModel):
    line: int
    character: int


class LanguageServiceRange(BaseModel):
    start: LanguageServicePosition
    end: LanguageServicePosition


class LanguageServiceDiagnostic(BaseModel):
    uri: str
    range: LanguageServiceRange
    severity: LanguageServiceDiagnosticSeverity
    code: str | None = Field(default=None)
    message: str
    source: str | None = Field(default=None)
    suggestions: list[str] = Field(default_factory=list)


class LanguageServiceTextEdit(BaseModel):
    uri: str
    range: LanguageServiceRange
    new_text: str


class LanguageServiceQuickFix(BaseModel):
    title: str
    edits: list[LanguageServiceTextEdit] = Field(default_factory=list)
    is_preferred: bool = Field(default=False)


class LanguageServicePerfMetric(BaseModel):
    name: str
    duration_ms: float
    note: str | None = Field(default=None)


class LanguageServiceSnapshotInfo(BaseModel):
    mode: LanguageServiceSnapshotMode | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    env_root: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    language_id: str | None = Field(default=None)


class LanguageServiceReport(BaseModel):
    diagnostics: list[LanguageServiceDiagnostic] = Field(default_factory=list)
    quick_fixes: list[LanguageServiceQuickFix] = Field(default_factory=list)
    perf_metrics: list[LanguageServicePerfMetric] = Field(default_factory=list)
    snapshot: LanguageServiceSnapshotInfo | None = Field(default=None)


__all__ = [
    "LanguageServiceDiagnostic",
    "LanguageServiceDiagnosticSeverity",
    "LanguageServicePerfMetric",
    "LanguageServicePosition",
    "LanguageServiceQuickFix",
    "LanguageServiceRange",
    "LanguageServiceReport",
    "LanguageServiceSnapshotInfo",
    "LanguageServiceSnapshotMode",
    "LanguageServiceTextEdit",
]
