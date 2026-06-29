from __future__ import annotations

from collections.abc import Mapping

from aware_meta.enum.config.deltas.generated_materialization import (
    generated_materialization_feature_results_from_enum_config_typed_operation,
)
from aware_meta.enum.config.deltas.ontology_execution import (
    HANDLER_KEY as ENUM_HANDLER_KEY,
    plan_enum_operation,
)
from aware_meta.enum.config.deltas.source_projection import (
    source_projection_feature_results_from_enum_config_typed_operation,
)
from aware_meta.enum.config.deltas.typed_operations import (
    enum_config_create_dirty_entry,
    enum_config_delete_dirty_entry,
    enum_config_update_dirty_entry,
    enum_option_create_dirty_entry,
    enum_option_delete_dirty_entry,
    enum_option_update_dirty_entry,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
    MetaProviderDeltaSemanticOperationResolverRegistration,
    MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
)


FEATURE_KEY = "enum_config"
ENUM_SUBJECT_KIND = "enum"
ENUM_OPTION_SUBJECT_KIND = "enum_option"
ENUM_CREATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.enum.create"
)
ENUM_DELETE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.enum.delete"
)
ENUM_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.enum.description.update"
)
ENUM_OPTION_CREATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.enum_option.create"
)
ENUM_OPTION_DELETE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.enum_option.delete"
)
ENUM_OPTION_POSITION_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.enum_option.position.update"
)


def _enum_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return enum_config_create_dirty_entry(entry)


def _enum_update_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return enum_config_update_dirty_entry(entry)


def _enum_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return enum_config_delete_dirty_entry(entry)


def _enum_option_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return enum_option_create_dirty_entry(entry)


def _enum_option_update_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return enum_option_update_dirty_entry(entry)


def _enum_option_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return enum_option_delete_dirty_entry(entry)


def _resolve_enum_config_semantic_operation(**kwargs: object) -> object:
    from aware_meta.enum.config.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_enum_config_semantic_operation,
    )

    return resolve_enum_config_semantic_operation(**kwargs)


def _resolve_enum_option_semantic_operation(**kwargs: object) -> object:
    from aware_meta.enum.config.deltas.enum_option_semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_enum_option_semantic_operation,
    )

    return resolve_enum_option_semantic_operation(**kwargs)


ENUM_CONFIG_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(ENUM_SUBJECT_KIND, ENUM_OPTION_SUBJECT_KIND),
    source_projection_builder=(
        source_projection_feature_results_from_enum_config_typed_operation
    ),
    generated_materialization_builder=(
        generated_materialization_feature_results_from_enum_config_typed_operation
    ),
    typed_operation_dirty_entry_planner_registrations=(
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="enum.create.scope_closure",
            ontology_subject_kind=ENUM_SUBJECT_KIND,
            operation_families=("create",),
            planner=_enum_create_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="enum.update.scope_closure",
            ontology_subject_kind=ENUM_SUBJECT_KIND,
            operation_families=("update",),
            planner=_enum_update_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="enum.delete.scope_closure",
            ontology_subject_kind=ENUM_SUBJECT_KIND,
            operation_families=("delete",),
            planner=_enum_delete_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="enum_option.create.scope_closure",
            ontology_subject_kind=ENUM_OPTION_SUBJECT_KIND,
            operation_families=("create",),
            planner=_enum_option_create_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="enum_option.update.scope_closure",
            ontology_subject_kind=ENUM_OPTION_SUBJECT_KIND,
            operation_families=("update",),
            planner=_enum_option_update_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="enum_option.delete.scope_closure",
            ontology_subject_kind=ENUM_OPTION_SUBJECT_KIND,
            operation_families=("delete",),
            planner=_enum_option_delete_dirty_entry,
        ),
    ),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=ENUM_HANDLER_KEY,
            ontology_subject_kind=ENUM_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=plan_enum_operation,
        ),
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=ENUM_HANDLER_KEY,
            ontology_subject_kind=ENUM_OPTION_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=plan_enum_operation,
        ),
    ),
    semantic_operation_resolver_registrations=(
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="enum_config.semantic_operation_resolution",
            semantic_operation_types=(
                ENUM_CREATE_SEMANTIC_OPERATION_TYPE,
                ENUM_DELETE_SEMANTIC_OPERATION_TYPE,
                ENUM_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE,
            ),
            resolver=_resolve_enum_config_semantic_operation,
        ),
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="enum_option.semantic_operation_resolution",
            semantic_operation_types=(
                ENUM_OPTION_CREATE_SEMANTIC_OPERATION_TYPE,
                ENUM_OPTION_DELETE_SEMANTIC_OPERATION_TYPE,
                ENUM_OPTION_POSITION_UPDATE_SEMANTIC_OPERATION_TYPE,
            ),
            resolver=_resolve_enum_option_semantic_operation,
        ),
    ),
)


__all__ = [
    "ENUM_CREATE_SEMANTIC_OPERATION_TYPE",
    "ENUM_CONFIG_DELTA_FEATURE_PROVIDER",
    "ENUM_DELETE_SEMANTIC_OPERATION_TYPE",
    "ENUM_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE",
    "ENUM_OPTION_CREATE_SEMANTIC_OPERATION_TYPE",
    "ENUM_OPTION_DELETE_SEMANTIC_OPERATION_TYPE",
    "ENUM_OPTION_POSITION_UPDATE_SEMANTIC_OPERATION_TYPE",
    "ENUM_OPTION_SUBJECT_KIND",
    "ENUM_SUBJECT_KIND",
    "FEATURE_KEY",
]
