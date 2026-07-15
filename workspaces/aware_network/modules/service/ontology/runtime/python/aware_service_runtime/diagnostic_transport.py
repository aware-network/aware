from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from aware_environment_service_dto.environment.service_diagnostic import (
    ServiceDiagnostic,
)
from aware_environment_service_dto.environment.service_diagnostic import (
    ServiceDiagnosticCategory,
)
from aware_environment_service_dto.environment.service_diagnostic import (
    ServiceDiagnosticEntry,
)
from aware_environment_service_dto.environment.service_diagnostic import (
    ServiceDiagnosticResolutionStatus,
)
from aware_environment_service_dto.environment.service_diagnostic import (
    ServiceDiagnosticSection,
)
from aware_environment_service_dto.environment.service_diagnostic import (
    ServiceDiagnosticSeverity,
)
from aware_service_runtime.diagnostic import (
    RuntimeDiagnostic,
    RuntimeDiagnosticEntry,
    RuntimeDiagnosticSection,
)
from aware_service_runtime.error_codes import ErrorCodeRegistry
from aware_service_runtime.language_service_error_codes import (
    LANGUAGE_SERVICE_ERROR_CODE_DEFINITIONS,
)
from aware_service_runtime.temporal_mutation_error_codes import (
    TEMPORAL_MUTATION_SERVICE_ERROR_CODE_DEFINITIONS,
)


TransportDiagnosticScalar = str | int | float | bool
TransportDiagnosticValue = (
    TransportDiagnosticScalar | list[str] | list[int] | list[float] | list[bool]
)
_service_error_code_registry = ErrorCodeRegistry(
    definitions=(
        *LANGUAGE_SERVICE_ERROR_CODE_DEFINITIONS,
        *TEMPORAL_MUTATION_SERVICE_ERROR_CODE_DEFINITIONS,
    ),
)


def make_service_diagnostic_section(
    *,
    title: str,
    entries: Iterable[tuple[str, object | None]],
) -> ServiceDiagnosticSection:
    return ServiceDiagnosticSection(
        title=title,
        entries=[
            ServiceDiagnosticEntry(key=key, value=_transport_value(value))
            for key, value in entries
            if value is not None
        ],
    )


def runtime_diagnostic_to_service_diagnostic(
    value: RuntimeDiagnostic,
) -> ServiceDiagnostic:
    return ServiceDiagnostic(
        code=value.code,
        category=ServiceDiagnosticCategory(value.category.value),
        severity=ServiceDiagnosticSeverity(value.severity.value),
        summary=value.summary,
        detail=value.detail,
        hint=value.hint,
        semantic_refs=_runtime_section_to_service_section(value.semantic_refs),
        invocation_context=_runtime_section_to_service_section(
            value.invocation_context
        ),
        provenance=_runtime_section_to_service_section(value.provenance),
        resolution_status=ServiceDiagnosticResolutionStatus(
            value.resolution_status.value
        ),
        debug=(
            _runtime_section_to_service_section(value.debug)
            if value.debug is not None
            else None
        ),
    )


def build_registered_service_diagnostic(
    *,
    code: str,
    summary: str,
    detail: str | None = None,
    hint: str | None = None,
    semantic_refs: ServiceDiagnosticSection | None = None,
    invocation_context: ServiceDiagnosticSection | None = None,
    provenance: ServiceDiagnosticSection | None = None,
    resolution_status: ServiceDiagnosticResolutionStatus = ServiceDiagnosticResolutionStatus.unresolved,
    debug: ServiceDiagnosticSection | None = None,
) -> ServiceDiagnostic:
    definition = _service_error_code_registry.definition_for(code)
    return ServiceDiagnostic(
        code=definition.code,
        category=ServiceDiagnosticCategory(definition.category.value),
        severity=ServiceDiagnosticSeverity(definition.default_severity.value),
        summary=summary,
        detail=detail,
        hint=hint,
        semantic_refs=semantic_refs or ServiceDiagnosticSection(title="Semantic Refs"),
        invocation_context=invocation_context
        or ServiceDiagnosticSection(title="Invocation"),
        provenance=provenance or ServiceDiagnosticSection(title="Provenance"),
        resolution_status=resolution_status,
        debug=debug,
    )


def _runtime_section_to_service_section(
    section: RuntimeDiagnosticSection,
) -> ServiceDiagnosticSection:
    return ServiceDiagnosticSection(
        title=section.title,
        entries=[_runtime_entry_to_service_entry(entry) for entry in section.entries],
    )


def _runtime_entry_to_service_entry(
    entry: RuntimeDiagnosticEntry,
) -> ServiceDiagnosticEntry:
    return ServiceDiagnosticEntry(key=entry.key, value=_transport_value(entry.value))


def _transport_value(value: object) -> TransportDiagnosticValue:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_transport_scalar(item) for item in value]
    return _transport_scalar(value)


def _transport_scalar(value: object) -> TransportDiagnosticScalar:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, int, float)):
        return value
    raise TypeError(f"Unsupported diagnostic transport value: {value!r}")


__all__ = [
    "build_registered_service_diagnostic",
    "make_service_diagnostic_section",
    "runtime_diagnostic_to_service_diagnostic",
]
