"""Neutral Goal SDK transport and source contracts."""

_PHASE_OPERATION_EXPORTS = {
    "GoalPhaseObserveEligibilityProvider",
    "GoalPhaseObserveEligibilityRequestV1",
    "GoalPhaseOperationClient",
    "decode_goal_phase_observe_eligibility_request",
    "decode_goal_phase_observe_eligibility_result",
}

_PHASE_DIRECTION_EXPORTS = {
    "GoalPhaseDirectionClient",
    "GoalPhaseDirectionCurrentnessRequestV1",
    "GoalPhaseDirectionCurrentnessV1",
    "GoalPhaseDirectionError",
    "GoalPhaseDirectionObserveRequestV1",
    "GoalPhaseDirectionProvider",
    "GoalPhaseDirectionReceiptV1",
}

_PHASE_MARKDOWN_EXPORTS = {
    "GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE",
    "GOAL_PHASE_MARKDOWN_SCHEMA",
    "GoalLegacyLaneProjectionV1",
    "GoalLegacyPhaseProjectionV1",
    "GoalLegacyPhaseWorkAssociationProjectionV1",
    "GoalPhaseMarkdownProjectionError",
    "GoalPhaseMarkdownProjectionV1",
    "load_goal_phase_markdown_projection",
    "project_goal_phase_markdown",
    "render_goal_phase_markdown_v1",
    "render_goal_phase_markdown_v2",
}

_NATIVE_PHASE_MARKDOWN_EXPORTS = {
    "END_MARKER",
    "GoalPhaseNativeMarkdownError",
    "START_MARKER",
    "attach_goal_phase_native_document",
    "extract_goal_phase_native_document",
    "repair_advanced_goal_phase_native_document",
}

_DEPENDENCY_VIEW_EXPORTS = {
    "GoalDependencyCrossGoalRelationshipV1",
    "GoalDependencyDocumentPresenceV1",
    "GoalDependencyEndpointPresence",
    "GoalDependencyLaneRelationshipV1",
    "GoalDependencyPresentationState",
    "GoalDependencyViewContractV1",
    "GoalDependencyViewItemV1",
    "GoalDependencyViewSourceV1",
    "compose_goal_dependency_view",
    "decode_goal_dependency_view",
}

_MARKDOWN_SOURCE_EXPORTS = {
    "GoalMarkdownImportError",
    "GoalMarkdownImportPlan",
    "GoalMarkdownLaneIssueSeed",
    "GoalMarkdownLaneSeed",
    "load_goal_markdown_import_plan",
    "parse_goal_markdown_import_plan",
}

__all__ = [
    "END_MARKER",
    "GOAL_PHASE_MARKDOWN_AUTHORITY_PROFILE",
    "GOAL_PHASE_MARKDOWN_SCHEMA",
    "GoalDependencyCrossGoalRelationshipV1",
    "GoalDependencyDocumentPresenceV1",
    "GoalDependencyEndpointPresence",
    "GoalDependencyLaneRelationshipV1",
    "GoalDependencyPresentationState",
    "GoalDependencyViewContractV1",
    "GoalDependencyViewItemV1",
    "GoalDependencyViewSourceV1",
    "GoalLegacyLaneProjectionV1",
    "GoalLegacyPhaseProjectionV1",
    "GoalLegacyPhaseWorkAssociationProjectionV1",
    "GoalMarkdownImportError",
    "GoalMarkdownImportPlan",
    "GoalMarkdownLaneIssueSeed",
    "GoalMarkdownLaneSeed",
    "GoalPhaseDirectionClient",
    "GoalPhaseDirectionCurrentnessRequestV1",
    "GoalPhaseDirectionCurrentnessV1",
    "GoalPhaseDirectionError",
    "GoalPhaseDirectionObserveRequestV1",
    "GoalPhaseDirectionProvider",
    "GoalPhaseDirectionReceiptV1",
    "GoalPhaseMarkdownProjectionError",
    "GoalPhaseMarkdownProjectionV1",
    "GoalPhaseNativeMarkdownError",
    "GoalPhaseObserveEligibilityProvider",
    "GoalPhaseObserveEligibilityRequestV1",
    "GoalPhaseOperationClient",
    "START_MARKER",
    "attach_goal_phase_native_document",
    "compose_goal_dependency_view",
    "decode_goal_dependency_view",
    "decode_goal_phase_observe_eligibility_request",
    "decode_goal_phase_observe_eligibility_result",
    "extract_goal_phase_native_document",
    "load_goal_markdown_import_plan",
    "load_goal_phase_markdown_projection",
    "parse_goal_markdown_import_plan",
    "project_goal_phase_markdown",
    "render_goal_phase_markdown_v1",
    "render_goal_phase_markdown_v2",
    "repair_advanced_goal_phase_native_document",
]

def __getattr__(name: str):
    if name in _PHASE_OPERATION_EXPORTS:
        from aware_goal_sdk import phase_operation

        value = getattr(phase_operation, name)
        globals()[name] = value
        return value
    if name in _PHASE_DIRECTION_EXPORTS:
        from aware_goal_sdk import phase_direction

        value = getattr(phase_direction, name)
        globals()[name] = value
        return value
    if name in _PHASE_MARKDOWN_EXPORTS:
        from aware_goal_sdk import phase_markdown_projection

        value = getattr(phase_markdown_projection, name)
        globals()[name] = value
        return value
    if name in _NATIVE_PHASE_MARKDOWN_EXPORTS:
        from aware_goal_sdk import native_phase_markdown

        value = getattr(native_phase_markdown, name)
        globals()[name] = value
        return value
    if name in _DEPENDENCY_VIEW_EXPORTS:
        from aware_goal_sdk import dependency_view

        value = getattr(dependency_view, name)
        globals()[name] = value
        return value
    if name in _MARKDOWN_SOURCE_EXPORTS:
        from aware_goal_sdk import markdown_source

        value = getattr(markdown_source, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'aware_goal_sdk' has no attribute {name!r}")
