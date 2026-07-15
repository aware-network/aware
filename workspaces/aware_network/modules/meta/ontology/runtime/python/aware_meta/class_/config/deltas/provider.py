from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from aware_meta.class_.config.deltas.ontology_execution import (
    HANDLER_KEY as CLASS_HANDLER_KEY,
    plan_class_operation,
)
from aware_meta.class_.config.deltas.source_projection import (
    source_projection_feature_results_from_class_config_typed_operation,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
    MetaProviderDeltaSemanticOperationResolverRegistration,
    MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
)
from aware_meta.materialization.deltas.generated_materialization_dispatch import (
    target_language_generated_materialization_feature_results,
)
from aware_meta.class_.config.deltas.typed_operations import (
    class_config_create_dirty_entry,
    class_config_delete_dirty_entry,
    class_config_update_dirty_entry,
)


FEATURE_KEY = "class_config"
CLASS_SUBJECT_KIND = "class"
CLASS_CREATE_SEMANTIC_OPERATION_TYPE = "aware_meta.object_config_graph.class.create"
CLASS_DELETE_SEMANTIC_OPERATION_TYPE = "aware_meta.object_config_graph.class.delete"
CLASS_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.class.description.update"
)
CLASS_PARENT_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.class.parent.update"
)


def _class_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return class_config_create_dirty_entry(entry)


def _class_update_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return class_config_update_dirty_entry(entry)


def _class_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return class_config_delete_dirty_entry(entry)


def _resolve_class_config_semantic_operation(**kwargs: object) -> object:
    from aware_meta.class_.config.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_class_config_semantic_operation,
    )

    return resolve_class_config_semantic_operation(**cast(dict[str, Any], kwargs))


CLASS_CONFIG_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(CLASS_SUBJECT_KIND,),
    typed_operation_dirty_entry_planner_registrations=(
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="class.create.feature_owned_identity",
            ontology_subject_kind=CLASS_SUBJECT_KIND,
            operation_families=("create",),
            planner=_class_create_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="class.update.scope_closure",
            ontology_subject_kind=CLASS_SUBJECT_KIND,
            operation_families=("update",),
            planner=_class_update_dirty_entry,
        ),
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="class.delete.feature_owned_identity",
            ontology_subject_kind=CLASS_SUBJECT_KIND,
            operation_families=("delete",),
            planner=_class_delete_dirty_entry,
        ),
    ),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=CLASS_HANDLER_KEY,
            ontology_subject_kind=CLASS_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=plan_class_operation,
        ),
    ),
    semantic_operation_resolver_registrations=(
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="class_config.semantic_operation_resolution",
            semantic_operation_types=(
                CLASS_CREATE_SEMANTIC_OPERATION_TYPE,
                CLASS_DELETE_SEMANTIC_OPERATION_TYPE,
                CLASS_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE,
                CLASS_PARENT_UPDATE_SEMANTIC_OPERATION_TYPE,
            ),
            resolver=_resolve_class_config_semantic_operation,
        ),
    ),
    source_projection_builder=(
        source_projection_feature_results_from_class_config_typed_operation
    ),
    generated_materialization_builder=(
        target_language_generated_materialization_feature_results(
            feature_key=FEATURE_KEY,
            ontology_subject_kinds=(CLASS_SUBJECT_KIND,),
            subject_not_supported_reason=(
                "meta_generated_materialization_class_subject_not_supported"
            ),
        )
    ),
)


__all__ = [
    "CLASS_CREATE_SEMANTIC_OPERATION_TYPE",
    "CLASS_CONFIG_DELTA_FEATURE_PROVIDER",
    "CLASS_DELETE_SEMANTIC_OPERATION_TYPE",
    "CLASS_DESCRIPTION_UPDATE_SEMANTIC_OPERATION_TYPE",
    "CLASS_PARENT_UPDATE_SEMANTIC_OPERATION_TYPE",
    "CLASS_SUBJECT_KIND",
    "FEATURE_KEY",
]
