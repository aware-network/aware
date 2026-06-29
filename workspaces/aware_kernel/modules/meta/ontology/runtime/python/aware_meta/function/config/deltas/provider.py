from __future__ import annotations

from collections.abc import Mapping

from aware_meta.function.config.deltas.membership_ontology_execution import (
    HANDLER_KEY as FUNCTION_MEMBERSHIP_HANDLER_KEY,
    plan_function_membership_operation,
)
from aware_meta.function.config.deltas.ontology_execution import (
    HANDLER_KEY as FUNCTION_HANDLER_KEY,
    FUNCTION_INVOCATION_HANDLER_KEY,
    plan_function_invocation_operation,
    plan_function_operation,
)
from aware_meta.function.config.deltas.source_projection import (
    source_projection_feature_results_from_function_config_typed_operation,
)
from aware_meta.function.config.deltas.generated_materialization import (
    generated_materialization_feature_results_from_function_config_typed_operation,
)
from aware_meta.function.config.deltas.typed_operations import (
    function_config_create_dirty_entry,
    function_config_delete_dirty_entry,
    function_config_update_dirty_entry,
    function_invocation_create_dirty_entry,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
    MetaProviderDeltaSemanticOperationResolverRegistration,
    MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
)


FEATURE_KEY = "function_config"
FUNCTION_SUBJECT_KIND = "function"
FUNCTION_MEMBERSHIP_SUBJECT_KIND = "function_membership"
FUNCTION_INVOCATION_SUBJECT_KIND = "function_invocation"
FUNCTION_CREATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.function.create"
)
FUNCTION_DELETE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.function.delete"
)
FUNCTION_SIGNATURE_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.function.signature.update"
)


def _split_function_update_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return function_config_update_dirty_entry(entry=entry)


def _function_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return function_config_create_dirty_entry(entry)


def _function_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return function_config_delete_dirty_entry(entry)


def _function_invocation_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return function_invocation_create_dirty_entry(entry)


def _resolve_function_config_semantic_operation(**kwargs: object) -> object:
    from aware_meta.function.config.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_function_config_semantic_operation,
    )

    return resolve_function_config_semantic_operation(**kwargs)


FUNCTION_CONFIG_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(
        FUNCTION_SUBJECT_KIND,
        FUNCTION_MEMBERSHIP_SUBJECT_KIND,
        FUNCTION_INVOCATION_SUBJECT_KIND,
    ),
    typed_operation_dirty_entry_planner_registrations=(
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="function.create.scope_closure",
            ontology_subject_kind=FUNCTION_SUBJECT_KIND,
            operation_families=("create",),
            planner=_function_create_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="function.update.scope_closure_and_split_membership",
            ontology_subject_kind=FUNCTION_SUBJECT_KIND,
            operation_families=("update",),
            planner=_split_function_update_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="function.delete.scope_closure",
            ontology_subject_kind=FUNCTION_SUBJECT_KIND,
            operation_families=("delete",),
            planner=_function_delete_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="function.invocation_plan.create",
            ontology_subject_kind=FUNCTION_INVOCATION_SUBJECT_KIND,
            operation_families=("create",),
            planner=_function_invocation_create_dirty_entry,
        ),
    ),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=FUNCTION_HANDLER_KEY,
            ontology_subject_kind=FUNCTION_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=plan_function_operation,
        ),
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=FUNCTION_MEMBERSHIP_HANDLER_KEY,
            ontology_subject_kind=FUNCTION_MEMBERSHIP_SUBJECT_KIND,
            operation_families=("update",),
            planner=plan_function_membership_operation,
        ),
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=FUNCTION_INVOCATION_HANDLER_KEY,
            ontology_subject_kind=FUNCTION_INVOCATION_SUBJECT_KIND,
            operation_families=("create",),
            planner=plan_function_invocation_operation,
        ),
    ),
    semantic_operation_resolver_registrations=(
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="function_config.semantic_operation_resolution",
            semantic_operation_types=(
                FUNCTION_CREATE_SEMANTIC_OPERATION_TYPE,
                FUNCTION_DELETE_SEMANTIC_OPERATION_TYPE,
                FUNCTION_SIGNATURE_UPDATE_SEMANTIC_OPERATION_TYPE,
            ),
            resolver=_resolve_function_config_semantic_operation,
        ),
    ),
    source_projection_builder=(
        source_projection_feature_results_from_function_config_typed_operation
    ),
    generated_materialization_builder=(
        generated_materialization_feature_results_from_function_config_typed_operation
    ),
)


__all__ = [
    "FEATURE_KEY",
    "FUNCTION_CONFIG_DELTA_FEATURE_PROVIDER",
    "FUNCTION_CREATE_SEMANTIC_OPERATION_TYPE",
    "FUNCTION_DELETE_SEMANTIC_OPERATION_TYPE",
    "FUNCTION_INVOCATION_SUBJECT_KIND",
    "FUNCTION_MEMBERSHIP_SUBJECT_KIND",
    "FUNCTION_SIGNATURE_UPDATE_SEMANTIC_OPERATION_TYPE",
    "FUNCTION_SUBJECT_KIND",
]
