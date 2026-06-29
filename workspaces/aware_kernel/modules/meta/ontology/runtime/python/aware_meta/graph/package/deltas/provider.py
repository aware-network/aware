from __future__ import annotations

from aware_meta.graph.package.deltas.ontology_execution import (
    HANDLER_KEY as OBJECT_CONFIG_GRAPH_PACKAGE_HANDLER_KEY,
    plan_object_config_graph_package_operation,
)
from aware_meta.graph.package.deltas.typed_operations import (
    OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaFeatureProvider,
    MetaProviderDeltaOntologyOperationRegistration,
)


FEATURE_KEY = "object_config_graph_package"


OBJECT_CONFIG_GRAPH_PACKAGE_DELTA_FEATURE_PROVIDER = MetaProviderDeltaFeatureProvider(
    feature_key=FEATURE_KEY,
    ontology_subject_kinds=(OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND,),
    ontology_operation_registrations=(
        MetaProviderDeltaOntologyOperationRegistration(
            handler_key=OBJECT_CONFIG_GRAPH_PACKAGE_HANDLER_KEY,
            ontology_subject_kind=OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND,
            operation_families=("create", "update"),
            planner=plan_object_config_graph_package_operation,
        ),
    ),
)


__all__ = [
    "FEATURE_KEY",
    "OBJECT_CONFIG_GRAPH_PACKAGE_DELTA_FEATURE_PROVIDER",
    "OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND",
]
