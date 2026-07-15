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
    MetaProviderDeltaSemanticOperationResolverRegistration,
)
from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
)


FEATURE_KEY = "object_config_graph_package"


def _resolve_object_config_graph_package_semantic_operation(**kwargs: object) -> object:
    from aware_meta.graph.package.deltas.semantic_operation_resolution import (  # noqa: WPS433,E501
        resolve_object_config_graph_package_semantic_operation,
    )

    return resolve_object_config_graph_package_semantic_operation(**kwargs)


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
    semantic_operation_resolver_registrations=(
        MetaProviderDeltaSemanticOperationResolverRegistration(
            handler_key="object_config_graph_package.semantic_operation_resolution",
            semantic_operation_types=(
                META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
                META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
            ),
            resolver=_resolve_object_config_graph_package_semantic_operation,
        ),
    ),
)


__all__ = [
    "FEATURE_KEY",
    "OBJECT_CONFIG_GRAPH_PACKAGE_DELTA_FEATURE_PROVIDER",
    "OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND",
]
