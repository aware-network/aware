from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True, order=True)
class TypeSchemaDiagnostic:
    path: str
    code: str
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR


@dataclass(frozen=True, slots=True)
class TypeSchemaValidationReport:
    diagnostics: tuple[TypeSchemaDiagnostic, ...]
    truncated: bool = False

    @property
    def is_valid(self) -> bool:
        return not any(
            item.severity is DiagnosticSeverity.ERROR for item in self.diagnostics
        )

    def by_code(self, code: str) -> tuple[TypeSchemaDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.code == code)


class DiagnosticCollector:
    def __init__(self, max_diagnostics: int) -> None:
        if not isinstance(max_diagnostics, int) or isinstance(max_diagnostics, bool):
            raise TypeError("max_diagnostics must be int")
        if max_diagnostics < 1 or max_diagnostics > 10_000:
            raise ValueError("max_diagnostics must be between 1 and 10000")
        self._limit = max_diagnostics
        self._items: list[TypeSchemaDiagnostic] = []
        self._truncated = False

    def add(
        self,
        path: str,
        code: str,
        message: str,
        severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
    ) -> None:
        if len(self._items) < self._limit:
            self._items.append(TypeSchemaDiagnostic(path, code, message, severity))
        else:
            self._truncated = True

    def report(self) -> TypeSchemaValidationReport:
        return TypeSchemaValidationReport(tuple(self._items), self._truncated)

    def extend(self, report: TypeSchemaValidationReport) -> None:
        for item in report.diagnostics:
            self.add(item.path, item.code, item.message, item.severity)
        if report.truncated:
            self._truncated = True


__all__ = [
    "DiagnosticSeverity",
    "TypeSchemaDiagnostic",
    "TypeSchemaValidationReport",
]
