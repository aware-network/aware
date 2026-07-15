from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

from aware_service_runtime.api_ingress.graph_execution import (
    ServiceApiGraphExecutionBinding,
    ServiceApiGraphExecutionPlan,
)
from aware_service_runtime.contracts import (
    ServiceGraphCatalog,
    ServiceGraphContextLike,
)


@dataclass(frozen=True, slots=True)
class ResolvedServiceApiGraphFunctionTarget:
    class_config: ClassConfig
    function_link: ClassConfigFunctionConfig
    function_config: FunctionConfig


def resolve_service_api_execution_binding(
    *,
    execution_plan: ServiceApiGraphExecutionPlan,
    fulfillment_name: str,
    execution_label: str,
) -> ServiceApiGraphExecutionBinding:
    matches = [
        binding
        for binding in execution_plan.bindings
        if binding.name == fulfillment_name
    ]
    if not matches:
        raise RuntimeError(
            f"{execution_label} could not resolve fulfillment binding from the committed execution plan: "
            f"endpoint_ref={execution_plan.endpoint_ref!r} fulfillment_name={fulfillment_name!r}"
        )
    if len(matches) != 1:
        raise RuntimeError(
            f"{execution_label} resolved multiple fulfillment bindings for one fulfillment name: "
            f"endpoint_ref={execution_plan.endpoint_ref!r} fulfillment_name={fulfillment_name!r}"
        )
    return matches[0]


def resolve_service_api_graph_function_target(
    *,
    graph_context: ServiceGraphContextLike,
    graph_function_runtime_target: str,
    execution_label: str,
) -> ResolvedServiceApiGraphFunctionTarget:
    graph_catalog = service_graph_catalog(graph_context)
    target = graph_function_runtime_target.strip()
    class_ref, separator, function_name = target.rpartition(".")
    if not class_ref or not separator or not function_name:
        raise RuntimeError(
            f"{execution_label} requires a qualified graph_function_runtime_target: "
            f"{graph_function_runtime_target!r}"
        )

    class_matches = [
        class_config
        for class_config in graph_catalog.class_configs_by_id.values()
        if (class_config.class_fqn or "").strip() == class_ref
    ]
    if not class_matches:
        raise RuntimeError(
            f"{execution_label} could not resolve exact ClassConfig for graph_function_runtime_target: "
            f"{graph_function_runtime_target!r}"
        )
    if len(class_matches) != 1:
        raise RuntimeError(
            f"{execution_label} found ambiguous exact ClassConfig matches for graph_function_runtime_target: "
            f"{graph_function_runtime_target!r}"
        )
    class_config = class_matches[0]

    link_matches = [
        link
        for link in class_config.class_config_function_configs
        if link.function_config is not None
        and (link.function_config.name or "").strip() == function_name
    ]
    if not link_matches:
        raise RuntimeError(
            f"{execution_label} could not resolve ClassConfigFunctionConfig for graph_function_runtime_target: "
            f"{graph_function_runtime_target!r}"
        )
    if len(link_matches) != 1:
        raise RuntimeError(
            f"{execution_label} found ambiguous ClassConfigFunctionConfig matches for "
            f"graph_function_runtime_target: {graph_function_runtime_target!r}"
        )
    function_link = link_matches[0]
    function_config = function_link.function_config
    if function_config is None:
        raise RuntimeError(
            f"{execution_label} resolved a function link without FunctionConfig payload: "
            f"{graph_function_runtime_target!r}"
        )
    return ResolvedServiceApiGraphFunctionTarget(
        class_config=class_config,
        function_link=function_link,
        function_config=function_config,
    )


def resolve_service_api_constructor_projection(
    *,
    graph_context: ServiceGraphContextLike,
    class_config_id: UUID,
    function_constructor_link_id: UUID,
    graph_function_runtime_target: str,
    execution_label: str,
    allow_class_only_fallback: bool = False,
) -> ObjectProjectionGraph:
    graph_catalog = service_graph_catalog(graph_context)
    matches = []
    fallback_matches = []
    for projection in graph_catalog.ocg.object_projection_graphs:
        root_nodes = [
            node
            for node in projection.object_projection_graph_nodes
            if bool(node.is_root)
        ]
        if len(root_nodes) != 1 or root_nodes[0].class_config_id != class_config_id:
            continue
        constructor_matches = [
            entry
            for entry in projection.object_projection_graph_constructors
            if entry.function_constructor_id == function_constructor_link_id
        ]
        if constructor_matches:
            matches.append(projection)
            continue
        if (
            allow_class_only_fallback
            and projection.object_projection_graph_constructors
        ):
            fallback_matches.append(projection)

    if not matches and allow_class_only_fallback:
        matches = fallback_matches

    if not matches:
        raise RuntimeError(
            f"{execution_label} could not resolve a constructor-enabled projection for "
            f"graph_function_runtime_target: {graph_function_runtime_target!r}"
        )
    if len(matches) != 1:
        raise RuntimeError(
            f"{execution_label} found ambiguous constructor-enabled projections for "
            f"graph_function_runtime_target: {graph_function_runtime_target!r}"
        )
    projection = matches[0]
    if not (projection.projection_hash or "").strip():
        raise RuntimeError(
            f"{execution_label} resolved a projection without projection_hash for "
            f"graph_function_runtime_target: {graph_function_runtime_target!r}"
        )
    return projection


def service_graph_catalog(
    graph_context: ServiceGraphContextLike,
) -> ServiceGraphCatalog:
    """Return the class/projection catalog from a graph context object."""

    catalog = getattr(graph_context, "index", None)
    if catalog is not None:
        return cast(ServiceGraphCatalog, catalog)
    return cast(ServiceGraphCatalog, graph_context)


__all__ = [
    "ResolvedServiceApiGraphFunctionTarget",
    "resolve_service_api_constructor_projection",
    "resolve_service_api_execution_binding",
    "resolve_service_api_graph_function_target",
    "service_graph_catalog",
]
