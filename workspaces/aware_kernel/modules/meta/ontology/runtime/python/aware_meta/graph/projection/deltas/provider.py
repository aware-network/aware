from __future__ import annotations

from aware_meta.graph.projection.deltas.ontology_execution import (
    HANDLER_KEY as OBJECT_PROJECTION_GRAPH_HANDLER_KEY,
    plan_object_projection_graph_operation,
)
from aware_meta.graph.projection.deltas.typed_operations import (
    OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_SUBJECT_KIND,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
)


FEATURE_KEY = "object_projection_graph"


OBJECT_PROJECTION_GRAPH_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(
        OBJECT_PROJECTION_GRAPH_SUBJECT_KIND,
        OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND,
    ),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=OBJECT_PROJECTION_GRAPH_HANDLER_KEY,
            ontology_subject_kind=OBJECT_PROJECTION_GRAPH_SUBJECT_KIND,
            operation_families=("create",),
            planner=plan_object_projection_graph_operation,
        ),
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=OBJECT_PROJECTION_GRAPH_HANDLER_KEY,
            ontology_subject_kind=OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND,
            operation_families=("create",),
            planner=plan_object_projection_graph_operation,
        ),
    ),
)


__all__ = [
    "FEATURE_KEY",
    "OBJECT_PROJECTION_GRAPH_DELTA_FEATURE_PROVIDER",
    "OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND",
    "OBJECT_PROJECTION_GRAPH_SUBJECT_KIND",
]
