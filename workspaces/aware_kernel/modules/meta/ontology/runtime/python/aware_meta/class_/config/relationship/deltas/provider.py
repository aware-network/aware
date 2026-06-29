from __future__ import annotations

from collections.abc import Mapping

from aware_meta.class_.config.relationship.deltas.ontology_execution import (
    HANDLER_KEY as RELATIONSHIP_HANDLER_KEY,
    plan_relationship_operation,
)
from aware_meta.class_.config.relationship.deltas.source_projection import (
    source_projection_feature_results_from_relationship_config_typed_operation,
)
from aware_meta.class_.config.relationship.deltas.generated_materialization import (
    generated_materialization_feature_results_from_relationship_config_typed_operation,
)
from aware_meta.class_.config.relationship.deltas.typed_operations import (
    relationship_config_dirty_entry,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
    MetaProviderDeltaSemanticOperationResolverRegistration,
    MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration,
)


FEATURE_KEY = "relationship_config"
RELATIONSHIP_SUBJECT_KIND = "relationship"
RELATIONSHIP_CREATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.relationship.create"
)
RELATIONSHIP_DELETE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.relationship.delete"
)
RELATIONSHIP_LOAD_POLICY_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.relationship.load_policy.update"
)


def _relationship_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return relationship_config_dirty_entry(entry)


def _resolve_relationship_config_semantic_operation(**kwargs: object) -> object:
    from aware_meta.class_.config.relationship.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_relationship_config_semantic_operation,
    )

    return resolve_relationship_config_semantic_operation(**kwargs)


RELATIONSHIP_CONFIG_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(RELATIONSHIP_SUBJECT_KIND,),
    typed_operation_dirty_entry_planner_registrations=(
        MetaProviderDeltaTypedOperationDirtyEntryPlannerRegistration(
            handler_key="relationship.scope_closure",
            ontology_subject_kind=RELATIONSHIP_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=_relationship_dirty_entry,
        ),
    ),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=RELATIONSHIP_HANDLER_KEY,
            ontology_subject_kind=RELATIONSHIP_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=plan_relationship_operation,
        ),
    ),
    semantic_operation_resolver_registrations=(
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="relationship_config.semantic_operation_resolution",
            semantic_operation_types=(
                RELATIONSHIP_CREATE_SEMANTIC_OPERATION_TYPE,
                RELATIONSHIP_DELETE_SEMANTIC_OPERATION_TYPE,
                RELATIONSHIP_LOAD_POLICY_UPDATE_SEMANTIC_OPERATION_TYPE,
            ),
            resolver=_resolve_relationship_config_semantic_operation,
        ),
    ),
    source_projection_builder=(
        source_projection_feature_results_from_relationship_config_typed_operation
    ),
    generated_materialization_builder=(
        generated_materialization_feature_results_from_relationship_config_typed_operation
    ),
)


__all__ = [
    "FEATURE_KEY",
    "RELATIONSHIP_CONFIG_DELTA_FEATURE_PROVIDER",
    "RELATIONSHIP_CREATE_SEMANTIC_OPERATION_TYPE",
    "RELATIONSHIP_DELETE_SEMANTIC_OPERATION_TYPE",
    "RELATIONSHIP_LOAD_POLICY_UPDATE_SEMANTIC_OPERATION_TYPE",
    "RELATIONSHIP_SUBJECT_KIND",
]
