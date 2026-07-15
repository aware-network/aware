"""Dependency-light structured evidence for semantic materialization failures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal


MATERIALIZATION_DIAGNOSTIC_SCHEMA = "aware.materialization.diagnostic.v1"


MaterializationDiagnosticClassification = Literal[
    "author_action_required",
    "compiler_error",
    "external_dependency",
    "unclassified_failure",
]


class MaterializationDiagnosticError(ValueError):
    """An error with stable, agent-actionable materialization evidence."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        classification: MaterializationDiagnosticClassification,
        phase: str,
        remediation: str,
        outputs_applied: bool | None,
        target_language: str | None = None,
        symbol: str | None = None,
        source_paths: Sequence[str] = (),
        output_path: str | None = None,
        context: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.classification = classification
        self.phase = phase
        self.remediation = remediation
        self.outputs_applied = outputs_applied
        self.target_language = target_language
        self.symbol = symbol
        self.source_paths = tuple(dict.fromkeys(source_paths))
        self.output_path = output_path
        self.context = dict(context or {})

    def attach_context(
        self,
        *,
        phase: str | None = None,
        target_language: str | None = None,
        source_paths: Sequence[str] = (),
        output_path: str | None = None,
    ) -> None:
        if phase:
            self.phase = phase
        if target_language:
            self.target_language = target_language
        if source_paths:
            self.source_paths = tuple(
                dict.fromkeys((*self.source_paths, *source_paths))
            )
        if output_path:
            self.output_path = output_path

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": MATERIALIZATION_DIAGNOSTIC_SCHEMA,
            "code": self.code,
            "classification": self.classification,
            "message": str(self),
            "phase": self.phase,
            "remediation": self.remediation,
            "outputs_applied": self.outputs_applied,
            "exception_type": type(self).__name__,
        }
        if self.target_language is not None:
            payload["target_language"] = self.target_language
        if self.symbol is not None:
            payload["symbol"] = self.symbol
        if self.source_paths:
            payload["source_paths"] = self.source_paths
        if self.output_path is not None:
            payload["output_path"] = self.output_path
        if self.context:
            payload["context"] = dict(self.context)
        return payload


def enrich_materialization_error(
    exc: Exception,
    *,
    phase: str,
    target_language: str | None = None,
    source_paths: Sequence[str] = (),
    output_path: str | None = None,
) -> MaterializationDiagnosticError:
    """Attach render coordinates or classify an otherwise unknown failure."""

    if isinstance(exc, MaterializationDiagnosticError):
        exc.attach_context(
            phase=phase,
            target_language=target_language,
            source_paths=source_paths,
            output_path=output_path,
        )
        return exc
    return MaterializationDiagnosticError(
        code="materialization.unclassified_error",
        message=str(exc),
        classification="unclassified_failure",
        phase=phase,
        remediation=(
            "Inspect the failed-step diagnostic and linked logs; no authored-source "
            "remediation was established."
        ),
        outputs_applied=None,
        target_language=target_language,
        source_paths=source_paths,
        output_path=output_path,
        context={"cause_exception_type": type(exc).__name__},
    )


def materialization_failure_details(exc: Exception) -> dict[str, object]:
    """Return receipt-safe structured evidence for any materialization error."""

    diagnostic = (
        exc
        if isinstance(exc, MaterializationDiagnosticError)
        else enrich_materialization_error(
            exc,
            phase="materialization_execution",
        )
    )
    return {"materialization_diagnostic": diagnostic.evidence_payload()}


__all__ = [
    "MATERIALIZATION_DIAGNOSTIC_SCHEMA",
    "MaterializationDiagnosticClassification",
    "MaterializationDiagnosticError",
    "enrich_materialization_error",
    "materialization_failure_details",
]
