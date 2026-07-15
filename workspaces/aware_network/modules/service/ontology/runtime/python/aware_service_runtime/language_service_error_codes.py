from __future__ import annotations

from enum import StrEnum

from aware_service_runtime.error_codes import (
    ErrorCategory,
    ErrorCodeDefinition,
    ErrorSeverity,
)


class LanguageServiceErrorCode(StrEnum):
    unsupported_operation = "service.language_service.unsupported_operation"
    missing_stream_target_id = "service.language_service.missing_stream_target_id"
    missing_session_id = "service.language_service.missing_session_id"
    missing_message_json = "service.language_service.missing_message_json"
    missing_repository_delta = "service.language_service.missing_repository_delta"
    session_not_found = "service.language_service.session_not_found"
    start_failed = "service.language_service.start_failed"
    send_failed = "service.language_service.send_failed"
    analyze_failed = "service.language_service.analyze_failed"


def _definition(
    *,
    code: LanguageServiceErrorCode,
    category: ErrorCategory = ErrorCategory.runtime_invariant,
    title: str,
    description: str,
) -> ErrorCodeDefinition:
    return {
        "code": code.value,
        "category": category,
        "default_severity": ErrorSeverity.error,
        "title": title,
        "description": description,
        "owner_package": "aware_service_runtime",
    }


LANGUAGE_SERVICE_ERROR_CODE_DEFINITIONS = (
    _definition(
        code=LanguageServiceErrorCode.unsupported_operation,
        title="Unsupported language-service operation",
        description="The language service received an unsupported operation discriminator.",
    ),
    _definition(
        code=LanguageServiceErrorCode.missing_stream_target_id,
        title="Missing stream target",
        description="The language service operation requires a stream target id but none was provided.",
    ),
    _definition(
        code=LanguageServiceErrorCode.missing_session_id,
        title="Missing session id",
        description="The language service operation requires a session id but none was provided.",
    ),
    _definition(
        code=LanguageServiceErrorCode.missing_message_json,
        title="Missing JSON-RPC message",
        description="The language service send operation requires a non-empty JSON-RPC message payload.",
    ),
    _definition(
        code=LanguageServiceErrorCode.missing_repository_delta,
        title="Missing repository delta",
        description="The language service analyze operation requires a repository delta but none was provided.",
    ),
    _definition(
        code=LanguageServiceErrorCode.session_not_found,
        title="Session not found",
        description="The requested language service session does not exist.",
    ),
    _definition(
        code=LanguageServiceErrorCode.start_failed,
        category=ErrorCategory.internal_failure,
        title="Language service start failed",
        description="The language service process could not be started for the requested workspace.",
    ),
    _definition(
        code=LanguageServiceErrorCode.send_failed,
        category=ErrorCategory.internal_failure,
        title="Language service send failed",
        description="The language service could not forward the JSON-RPC message to the underlying server process.",
    ),
    _definition(
        code=LanguageServiceErrorCode.analyze_failed,
        category=ErrorCategory.internal_failure,
        title="Language service analyze failed",
        description="The language service analyze operation failed before producing a typed report.",
    ),
)


__all__ = [
    "LANGUAGE_SERVICE_ERROR_CODE_DEFINITIONS",
    "LanguageServiceErrorCode",
]
