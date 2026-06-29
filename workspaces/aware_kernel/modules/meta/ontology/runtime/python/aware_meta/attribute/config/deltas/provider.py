from __future__ import annotations

from collections.abc import Mapping

from aware_meta.attribute.config.deltas.membership_ontology_execution import (
    HANDLER_KEY as ATTRIBUTE_MEMBERSHIP_HANDLER_KEY,
    plan_attribute_membership_operation,
)
from aware_meta.attribute.config.deltas.ontology_execution import (
    HANDLER_KEY as ATTRIBUTE_HANDLER_KEY,
    plan_attribute_operation,
)
from aware_meta.attribute.config.deltas.source_projection import (
    source_projection_feature_results_from_attribute_config_typed_operation,
)
from aware_meta.attribute.config.deltas.generated_materialization import (
    generated_materialization_feature_results_from_attribute_config_typed_operation,
)
from aware_meta.attribute.config.deltas.typed_operations import (
    split_attribute_update_entry,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
    MetaProviderDeltaSemanticOperationResolverRegistration,
    MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
)


FEATURE_KEY = "attribute_config"
ATTRIBUTE_SUBJECT_KIND = "attribute"
ATTRIBUTE_MEMBERSHIP_SUBJECT_KIND = "attribute_membership"
ATTRIBUTE_TYPE_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.attribute.type.update"
)
ATTRIBUTE_DEFAULT_VALUE_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.attribute.default_value.update"
)
ATTRIBUTE_MEMBERSHIP_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.attribute.membership.update"
)
ATTRIBUTE_CREATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.attribute.create"
)
ATTRIBUTE_DELETE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.attribute.delete"
)
ATTRIBUTE_IDENTITY_RENAME_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.attribute.identity.rename"
)


def _split_attribute_update_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return split_attribute_update_entry(entry=entry)


def _resolve_attribute_config_semantic_operation(**kwargs: object) -> object:
    from aware_meta.attribute.config.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_attribute_config_semantic_operation,
    )

    return resolve_attribute_config_semantic_operation(**kwargs)


ATTRIBUTE_CONFIG_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(
        ATTRIBUTE_SUBJECT_KIND,
        ATTRIBUTE_MEMBERSHIP_SUBJECT_KIND,
    ),
    typed_operation_dirty_entry_planner_registrations=(
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="attribute.update.split_scalar_and_membership",
            ontology_subject_kind=ATTRIBUTE_SUBJECT_KIND,
            operation_families=("update",),
            planner=_split_attribute_update_entry,
        ),
    ),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=ATTRIBUTE_HANDLER_KEY,
            ontology_subject_kind=ATTRIBUTE_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=plan_attribute_operation,
        ),
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=ATTRIBUTE_MEMBERSHIP_HANDLER_KEY,
            ontology_subject_kind=ATTRIBUTE_MEMBERSHIP_SUBJECT_KIND,
            operation_families=("update",),
            planner=plan_attribute_membership_operation,
        ),
    ),
    semantic_operation_resolver_registrations=(
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="attribute_config.semantic_operation_resolution",
            semantic_operation_types=(
                ATTRIBUTE_TYPE_UPDATE_SEMANTIC_OPERATION_TYPE,
                ATTRIBUTE_DEFAULT_VALUE_UPDATE_SEMANTIC_OPERATION_TYPE,
                ATTRIBUTE_MEMBERSHIP_UPDATE_SEMANTIC_OPERATION_TYPE,
                ATTRIBUTE_CREATE_SEMANTIC_OPERATION_TYPE,
                ATTRIBUTE_DELETE_SEMANTIC_OPERATION_TYPE,
                ATTRIBUTE_IDENTITY_RENAME_SEMANTIC_OPERATION_TYPE,
            ),
            resolver=_resolve_attribute_config_semantic_operation,
        ),
    ),
    source_projection_builder=(
        source_projection_feature_results_from_attribute_config_typed_operation
    ),
    generated_materialization_builder=(
        generated_materialization_feature_results_from_attribute_config_typed_operation
    ),
)


__all__ = [
    "ATTRIBUTE_CREATE_SEMANTIC_OPERATION_TYPE",
    "ATTRIBUTE_CONFIG_DELTA_FEATURE_PROVIDER",
    "ATTRIBUTE_DEFAULT_VALUE_UPDATE_SEMANTIC_OPERATION_TYPE",
    "ATTRIBUTE_DELETE_SEMANTIC_OPERATION_TYPE",
    "ATTRIBUTE_IDENTITY_RENAME_SEMANTIC_OPERATION_TYPE",
    "ATTRIBUTE_MEMBERSHIP_UPDATE_SEMANTIC_OPERATION_TYPE",
    "ATTRIBUTE_MEMBERSHIP_SUBJECT_KIND",
    "ATTRIBUTE_SUBJECT_KIND",
    "ATTRIBUTE_TYPE_UPDATE_SEMANTIC_OPERATION_TYPE",
    "FEATURE_KEY",
]
