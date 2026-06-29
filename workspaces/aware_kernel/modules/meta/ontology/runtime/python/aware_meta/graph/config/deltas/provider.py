from __future__ import annotations

from aware_meta.graph.config.deltas.ontology_execution import (
    HANDLER_KEY as OBJECT_CONFIG_GRAPH_HANDLER_KEY,
    plan_object_config_graph_operation,
)
from aware_meta.graph.config.deltas.typed_operations import (
    OBJECT_CONFIG_GRAPH_SUBJECT_KIND,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
)


FEATURE_KEY = "object_config_graph"


OBJECT_CONFIG_GRAPH_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(OBJECT_CONFIG_GRAPH_SUBJECT_KIND,),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=OBJECT_CONFIG_GRAPH_HANDLER_KEY,
            ontology_subject_kind=OBJECT_CONFIG_GRAPH_SUBJECT_KIND,
            operation_families=("create",),
            planner=plan_object_config_graph_operation,
        ),
    ),
)


__all__ = [
    "FEATURE_KEY",
    "OBJECT_CONFIG_GRAPH_DELTA_FEATURE_PROVIDER",
    "OBJECT_CONFIG_GRAPH_SUBJECT_KIND",
]
