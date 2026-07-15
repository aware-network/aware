from __future__ import annotations

from aware_meta.function.impl.deltas.ontology_execution import (
    HANDLER_KEY,
    plan_function_impl_operation,
)
from aware_meta.function.impl.deltas.source_projection import (
    source_projection_feature_results_from_function_impl_typed_operation,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
    MetaProviderDeltaSemanticOperationResolverRegistration,
)
from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyExecutionPlanningContext,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
)


FEATURE_KEY = "function_impl"
ONTOLOGY_SUBJECT_KIND = "function_impl"
FUNCTION_IMPL_BODY_UPDATE_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.function_impl.body.update"
)


def _plan_ontology_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    del context
    return plan_function_impl_operation(operation)


def _resolve_function_impl_semantic_operation(**kwargs: object) -> object:
    from aware_meta.function.impl.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_function_impl_semantic_operation,
    )

    return resolve_function_impl_semantic_operation(**kwargs)


FUNCTION_IMPL_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(ONTOLOGY_SUBJECT_KIND,),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=HANDLER_KEY,
            ontology_subject_kind=ONTOLOGY_SUBJECT_KIND,
            operation_families=("create", "update", "delete"),
            planner=_plan_ontology_operation,
        ),
    ),
    semantic_operation_resolver_registrations=(
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="function_impl.semantic_operation_resolution",
            semantic_operation_types=(
                FUNCTION_IMPL_BODY_UPDATE_SEMANTIC_OPERATION_TYPE,
            ),
            resolver=_resolve_function_impl_semantic_operation,
        ),
    ),
    source_projection_builder=(
        source_projection_feature_results_from_function_impl_typed_operation
    ),
)


__all__ = [
    "FEATURE_KEY",
    "FUNCTION_IMPL_DELTA_FEATURE_PROVIDER",
    "FUNCTION_IMPL_BODY_UPDATE_SEMANTIC_OPERATION_TYPE",
    "ONTOLOGY_SUBJECT_KIND",
]
