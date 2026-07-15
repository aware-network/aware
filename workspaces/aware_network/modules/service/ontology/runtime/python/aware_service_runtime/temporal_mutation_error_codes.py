from __future__ import annotations

from enum import StrEnum

from aware_service_runtime.error_codes import (
    ErrorCategory,
    ErrorCodeDefinition,
    ErrorSeverity,
)


class TemporalMutationServiceErrorCode(StrEnum):
    unsupported_operation = "service.temporal_mutation.unsupported_operation"
    not_writer = "service.temporal_mutation.not_writer"
    no_head_commit = "service.temporal_mutation.no_head_commit"
    session_id_lane_mismatch = "service.temporal_mutation.session_id_lane_mismatch"
    base_commit_mismatch = "service.temporal_mutation.base_commit_mismatch"
    too_many_sessions = "service.temporal_mutation.too_many_sessions"
    head_advanced = "service.temporal_mutation.head_advanced"
    graph_context_unavailable = "service.temporal_mutation.graph_context_unavailable"
    missing_graph_hash = "service.temporal_mutation.missing_graph_hash"
    missing_session_id = "service.temporal_mutation.missing_session_id"
    session_not_found = "service.temporal_mutation.session_not_found"
    too_many_subscribers = "service.temporal_mutation.too_many_subscribers"
    invalid_from_revision = "service.temporal_mutation.invalid_from_revision"
    revision_mismatch = "service.temporal_mutation.revision_mismatch"
    replay_unavailable = "service.temporal_mutation.replay_unavailable"
    reconnect_too_old = "service.temporal_mutation.reconnect_too_old"
    replay_incomplete = "service.temporal_mutation.replay_incomplete"
    missing_function_id = "service.temporal_mutation.missing_function_id"
    missing_object_id = "service.temporal_mutation.missing_object_id"
    missing_attribution = "service.temporal_mutation.missing_attribution"
    admission_denied = "service.temporal_mutation.admission_denied"
    invocation_failed = "service.temporal_mutation.invocation_failed"
    rate_limited = "service.temporal_mutation.rate_limited"
    too_many_changes = "service.temporal_mutation.too_many_changes"
    frame_too_large = "service.temporal_mutation.frame_too_large"
    head_conflict = "service.temporal_mutation.head_conflict"


def _definition(
    *,
    code: TemporalMutationServiceErrorCode,
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


TEMPORAL_MUTATION_SERVICE_ERROR_CODE_DEFINITIONS = (
    _definition(
        code=TemporalMutationServiceErrorCode.unsupported_operation,
        title="Unsupported temporal mutation operation",
        description="The temporal mutation service received an unsupported operation discriminator.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.not_writer,
        title="Writer lease required",
        description="The temporal mutation operation was rejected because another actor owns the writer lease.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.no_head_commit,
        title="Missing lane head",
        description="The temporal mutation lane has no current head commit to anchor the session.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.session_id_lane_mismatch,
        title="Session lane mismatch",
        description="The requested temporal mutation session id does not match the active lane mapping.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.base_commit_mismatch,
        title="Base commit mismatch",
        description="The requested base commit does not match the temporal session base.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.too_many_sessions,
        title="Too many temporal sessions",
        description="The temporal mutation service rejected the request because the session limit was reached.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.head_advanced,
        title="Lane head advanced",
        description="The temporal session became stale because the underlying lane head advanced.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.graph_context_unavailable,
        category=ErrorCategory.internal_failure,
        title="Graph context unavailable",
        description="The temporal mutation service could not obtain a graph context for the requested apply.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.missing_graph_hash,
        title="Missing graph hash",
        description="The temporal mutation request is missing the graph hash required by the service contract.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.missing_session_id,
        title="Missing session id",
        description="The temporal mutation operation requires a session id but none was provided.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.session_not_found,
        title="Session not found",
        description="The requested temporal mutation session does not exist.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.too_many_subscribers,
        title="Too many subscribers",
        description="The temporal mutation session rejected a subscriber because the session subscriber limit was reached.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.invalid_from_revision,
        title="Invalid from revision",
        description="The temporal mutation subscription requested an invalid from_revision value.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.revision_mismatch,
        title="Revision mismatch",
        description="The temporal mutation request targeted a revision that does not match the session revision.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.replay_unavailable,
        title="Replay unavailable",
        description="The temporal mutation session cannot replay frames for the requested revision range.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.reconnect_too_old,
        title="Reconnect too old",
        description="The temporal mutation subscriber requested replay from a revision older than the retained frame window.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.replay_incomplete,
        title="Replay incomplete",
        description="The temporal mutation session could not provide a complete replay for the requested revision range.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.missing_function_id,
        title="Missing function id",
        description="Temporal apply requires a function id but none was provided.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.missing_object_id,
        title="Missing object id",
        description="Temporal apply requires an object id but none was provided.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.missing_attribution,
        title="Missing execution attribution",
        description="Temporal apply requires process and thread attribution but the request did not provide it.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.admission_denied,
        title="Temporal mutation admission denied",
        description="The temporal mutation operation was rejected by explicit admission policy before overlay mutation.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.invocation_failed,
        title="Temporal apply invocation failed",
        description="The underlying temporal function invocation failed during apply.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.rate_limited,
        title="Temporal apply rate limited",
        description="The temporal mutation service rejected apply because it exceeded the configured apply rate.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.too_many_changes,
        title="Too many changes",
        description="The temporal apply produced more change trees than the configured service limit.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.frame_too_large,
        title="Temporal frame too large",
        description="The temporal apply produced a frame larger than the configured service limit.",
    ),
    _definition(
        code=TemporalMutationServiceErrorCode.head_conflict,
        title="Lane head conflict",
        description="Temporal finalize detected that the lane head changed before the session could be committed.",
    ),
)


__all__ = [
    "TEMPORAL_MUTATION_SERVICE_ERROR_CODE_DEFINITIONS",
    "TemporalMutationServiceErrorCode",
]
