from __future__ import annotations

from aware_service_runtime.diagnostic import (
    RuntimeDiagnostic,
    RuntimeDiagnosticEntry,
    RuntimeDiagnosticSection,
)
from aware_service_runtime.error_codes import (
    ErrorCategory,
    ErrorSeverity,
)
from aware_service_runtime.diagnostic_transport import (
    build_registered_service_diagnostic,
    runtime_diagnostic_to_service_diagnostic,
)
from aware_service_runtime.language_service_error_codes import (
    LanguageServiceErrorCode,
)
from aware_service_runtime.temporal_mutation_error_codes import (
    TemporalMutationServiceErrorCode,
)


def test_runtime_diagnostic_to_service_diagnostic_preserves_structure() -> None:
    runtime_diagnostic = RuntimeDiagnostic(
        code="function_call.mutation_boundary.cross_object_relationship",
        category=ErrorCategory.runtime_invariant,
        severity=ErrorSeverity.error,
        summary="Cross-object mutation detected",
        detail="Relationship changed without invoking the owning instance handler.",
        semantic_refs=RuntimeDiagnosticSection(
            title="Semantic Refs",
            entries=[
                RuntimeDiagnosticEntry(
                    key="owner",
                    value="aware_code.default.code.Code.content_part_text",
                )
            ],
        ),
    )

    diagnostic = runtime_diagnostic_to_service_diagnostic(runtime_diagnostic)

    assert diagnostic.code == runtime_diagnostic.code
    assert diagnostic.category.value == runtime_diagnostic.category.value
    assert diagnostic.severity.value == runtime_diagnostic.severity.value
    assert diagnostic.summary == runtime_diagnostic.summary
    assert diagnostic.semantic_refs.entries[0].value == (
        "aware_code.default.code.Code.content_part_text"
    )


def test_build_registered_service_diagnostic_uses_registry_defaults() -> None:
    diagnostic = build_registered_service_diagnostic(
        code=TemporalMutationServiceErrorCode.missing_session_id.value,
        summary="TemporalMutationServiceOperation.session_id is required for apply",
    )

    assert diagnostic.code == TemporalMutationServiceErrorCode.missing_session_id.value
    assert diagnostic.category.value == "runtime_invariant"
    assert diagnostic.severity.value == "error"
    assert (
        diagnostic.summary
        == "TemporalMutationServiceOperation.session_id is required for apply"
    )


def test_build_registered_service_diagnostic_supports_language_service_codes() -> None:
    diagnostic = build_registered_service_diagnostic(
        code=LanguageServiceErrorCode.missing_repository_delta.value,
        summary="LanguageServiceOperation.repository_delta is required for analyze",
    )

    assert diagnostic.code == LanguageServiceErrorCode.missing_repository_delta.value
    assert diagnostic.category.value == "runtime_invariant"
    assert diagnostic.severity.value == "error"
    assert diagnostic.summary == (
        "LanguageServiceOperation.repository_delta is required for analyze"
    )
