from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from collections import defaultdict
from contextlib import contextmanager
from time import perf_counter
from typing import cast
from uuid import UUID

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id
from aware_meta.graph.config.handlers import (
    build_object_config_graph_overlays_from_annotations,
    build_object_projection_graphs,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.runtime_derivation.clone import (
    clone_runtime_graph_for_stage_mutation,
    clone_source_graph_for_runtime_handoff,
)
from aware_meta.graph.config.runtime_derivation.schemas import (
    RuntimeObjectConfigGraphDerivationRequest,
    RuntimeObjectConfigGraphDerivationResult,
)
from aware_meta.graph.config.stable_ids import stable_object_config_graph_binding_id
from aware_meta.graph.config.runtime_derivation.timer import RuntimeDerivationTimer
from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer
from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)


def derive_runtime_object_config_graph(
    source_graph: ObjectConfigGraph,
    *,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
    include_projection_graphs: bool = True,
) -> RuntimeObjectConfigGraphDerivationResult:
    return RuntimeObjectConfigGraphDerivationService().derive(
        RuntimeObjectConfigGraphDerivationRequest(
            source_graph=source_graph,
            target_language=CodeLanguage.aware,
            external_runtime_graphs=external_runtime_graphs,
            include_projection_graphs=include_projection_graphs,
            source_is_runtime=False,
        )
    )


def derive_runtime_object_config_graphs(
    source_graphs: Iterable[ObjectConfigGraph],
    *,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
    include_projection_graphs: bool = True,
) -> tuple[ObjectConfigGraph, ...]:
    source_graph_tuple = tuple(source_graphs)
    external_runtime_graph_tuple = tuple(external_runtime_graphs)
    bootstrap_runtime_graphs_by_source_id: dict[UUID, ObjectConfigGraph] = {}
    for graph in source_graph_tuple:
        bootstrap_runtime_graphs_by_source_id[graph.id] = (
            derive_runtime_object_config_graph(
                graph,
                external_runtime_graphs=external_runtime_graph_tuple,
                include_projection_graphs=False,
            ).runtime_graph
        )

    runtime_graphs_by_source_id: dict[UUID, ObjectConfigGraph] = {}
    for graph in source_graph_tuple:
        runtime_graphs_by_source_id[graph.id] = derive_runtime_object_config_graph(
            graph,
            external_runtime_graphs=(
                *external_runtime_graph_tuple,
                *(
                    runtime_graph
                    for source_id, runtime_graph in (
                        bootstrap_runtime_graphs_by_source_id.items()
                    )
                    if source_id != graph.id
                ),
            ),
            include_projection_graphs=False,
        ).runtime_graph

    runtime_graphs = tuple(
        runtime_graphs_by_source_id[graph.id] for graph in source_graph_tuple
    )
    if not include_projection_graphs:
        return runtime_graphs
    return _ensure_runtime_projection_graphs(
        runtime_graphs,
        external_runtime_graphs=external_runtime_graph_tuple,
    )


class RuntimeObjectConfigGraphDerivationService:
    def derive(
        self,
        request: RuntimeObjectConfigGraphDerivationRequest,
    ) -> RuntimeObjectConfigGraphDerivationResult:
        if request.target_language != CodeLanguage.aware:
            raise ValueError(
                "Meta runtime OCG derivation boundary only supports "
                "CodeLanguage.aware in this slice."
            )
        timer = RuntimeDerivationTimer()
        with _runtime_derivation_progress_step(
            request,
            "derive_runtime_graph.ensure_plugins",
        ):
            _ensure_meta_language_plugins()
        source_graph = request.source_graph
        reuse_external_runtime_graphs = (
            request.source_is_runtime and request.reuse_external_runtime_graphs
        )
        with _runtime_derivation_progress_step(
            request,
            "derive_runtime_graph.external_runtime_graphs",
            detail_payload={
                "external_graph_count": len(request.external_runtime_graphs),
                "reuse_external_runtime_graphs": reuse_external_runtime_graphs,
            },
        ):
            if reuse_external_runtime_graphs:
                runtime_external_graphs = tuple(request.external_runtime_graphs)
                timer.metric("runtime_external_graphs_reused", True)
                timer.metric(
                    "runtime_external_graph_reuse_count",
                    len(runtime_external_graphs),
                )
            else:
                runtime_external_graphs = tuple(
                    clone_runtime_graph_for_stage_mutation(graph, timer=timer)
                    for graph in request.external_runtime_graphs
                )
        with _runtime_derivation_progress_step(
            request,
            "derive_runtime_graph.derive_graph",
            detail_payload=_runtime_derivation_graph_detail(
                source_graph,
                source_is_runtime=request.source_is_runtime,
            ),
        ):
            with timer.step("derive_graph"):
                if request.source_is_runtime:
                    runtime_graph = clone_runtime_graph_for_stage_mutation(
                        source_graph,
                        timer=timer,
                    )
                else:
                    runtime_graph = _language_to_runtime(
                        source_graph=source_graph,
                        external_runtime_graphs=runtime_external_graphs,
                        timer=timer,
                        progress_request=request,
                    )
        with _runtime_derivation_progress_step(
            request,
            "derive_runtime_graph.rebind_relationship_targets",
        ):
            with timer.step("rebind_relationship_targets"):
                _rebind_relationship_targets_to_runtime_closure(
                    runtime_graph=runtime_graph,
                    runtime_external_graphs=runtime_external_graphs,
                    mutate_external_graphs=not reuse_external_runtime_graphs,
                )
        with _runtime_derivation_progress_step(
            request,
            "derive_runtime_graph.attach_relationships",
            detail_payload={
                "runtime_graph_node_count": len(
                    runtime_graph.object_config_graph_nodes
                ),
                "external_graph_count": len(runtime_external_graphs),
            },
        ):
            with timer.step("attach_relationships"):
                _attach_relationships_to_class_configs(runtime_graph)
                if not reuse_external_runtime_graphs:
                    for external_graph in runtime_external_graphs:
                        _attach_relationships_to_class_configs(
                            external_graph,
                            preserve_existing_attached=True,
                        )
        with _runtime_derivation_progress_step(
            request,
            "derive_runtime_graph.overlays",
        ):
            _refresh_runtime_overlays(runtime_graph=runtime_graph, timer=timer)
        if request.include_projection_graphs:
            with _runtime_derivation_progress_step(
                request,
                "derive_runtime_graph.derive_opgs",
                detail_payload={
                    "declaration_count": len(
                        runtime_graph.object_projection_graph_declarations
                    ),
                    "external_graph_count": len(runtime_external_graphs),
                    "source_is_runtime": request.source_is_runtime,
                    "derive_external_projection_graphs": (
                        request.derive_external_projection_graphs
                    ),
                },
            ):
                _derive_runtime_projection_graphs(
                    runtime_graph=runtime_graph,
                    runtime_external_graphs=runtime_external_graphs,
                    derive_external_projection_graphs=(
                        request.derive_external_projection_graphs
                    ),
                    source_is_runtime=request.source_is_runtime,
                    timer=timer,
                )
        return RuntimeObjectConfigGraphDerivationResult(
            source_graph=source_graph,
            runtime_graph=runtime_graph,
            runtime_external_graphs=runtime_external_graphs,
            source_language=source_graph.language,
            runtime_language=runtime_graph.language,
            source_graph_hash=source_graph.hash,
            runtime_graph_hash=runtime_graph.hash,
            timings=timer.steps(),
            metrics=timer.metrics(),
        )


@contextmanager
def _runtime_derivation_progress_step(
    request: RuntimeObjectConfigGraphDerivationRequest | None,
    subphase_name: str,
    *,
    detail_payload: Mapping[str, object] | None = None,
) -> Iterator[None]:
    started_at = perf_counter()
    _emit_runtime_derivation_progress(
        request=request,
        subphase_name=subphase_name,
        status="running",
        detail_payload=detail_payload,
    )
    try:
        yield
    except Exception as exc:
        _emit_runtime_derivation_progress(
            request=request,
            subphase_name=subphase_name,
            status="failed",
            duration_s=perf_counter() - started_at,
            error=str(exc),
            detail_payload={
                **dict(detail_payload or {}),
                "error_type": type(exc).__name__,
            },
        )
        raise
    else:
        _emit_runtime_derivation_progress(
            request=request,
            subphase_name=subphase_name,
            status="succeeded",
            duration_s=perf_counter() - started_at,
            detail_payload=detail_payload,
        )


def _emit_runtime_derivation_progress(
    *,
    request: RuntimeObjectConfigGraphDerivationRequest | None,
    subphase_name: str,
    status: str,
    duration_s: float | None = None,
    error: str | None = None,
    detail_payload: Mapping[str, object] | None = None,
) -> None:
    if request is None or request.progress_callback is None:
        return
    payload: dict[str, object] = {
        "subphase_name": subphase_name,
        "status": status,
        "detail_payload": dict(detail_payload or {}),
    }
    if duration_s is not None:
        payload["duration_s"] = round(max(duration_s, 0.0), 6)
    if error:
        payload["error"] = error
    try:
        request.progress_callback(payload)
    except Exception:
        return


def _runtime_derivation_graph_detail(
    graph: ObjectConfigGraph,
    *,
    source_is_runtime: bool | None = None,
) -> Mapping[str, object]:
    detail: dict[str, object] = {
        "source_graph_id": str(graph.id),
        "source_graph_hash": graph.hash,
        "source_graph_fqn_prefix": graph.fqn_prefix,
        "source_graph_language": graph.language.value,
        "node_count": len(graph.object_config_graph_nodes),
        "relationship_count": len(graph.object_config_graph_relationships),
        "projection_declaration_count": len(graph.object_projection_graph_declarations),
    }
    if source_is_runtime is not None:
        detail["source_is_runtime"] = source_is_runtime
    return detail


def _ensure_meta_language_plugins() -> None:
    if MetaLanguagePluginRegistry.has_language(CodeLanguage.aware):
        return
    for plugin in AwareModulePluginRegistry.get_builtin_meta_language_plugins():
        MetaLanguagePluginRegistry.register(cast(MetaLanguagePlugin, plugin))


def _language_to_runtime(
    *,
    source_graph: ObjectConfigGraph,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...],
    timer: RuntimeDerivationTimer,
    progress_request: RuntimeObjectConfigGraphDerivationRequest | None = None,
) -> ObjectConfigGraph:
    with _runtime_derivation_progress_step(
        progress_request,
        "derive_runtime_graph.language_to_runtime.clone_source_graph",
        detail_payload=_runtime_derivation_graph_detail(source_graph),
    ):
        graph = clone_source_graph_for_runtime_handoff(source_graph, timer=timer)
    with _runtime_derivation_progress_step(
        progress_request,
        "derive_runtime_graph.language_to_runtime.namespace_index",
    ):
        namespace_by_code_id = _build_namespace_by_code_id_from_graph(graph)
    kwargs: dict[str, object] = {"namespace_by_code_id": namespace_by_code_id}
    if graph.language == CodeLanguage.aware and external_runtime_graphs:
        kwargs["external_graphs_by_id"] = (
            _external_runtime_graphs_by_id_for_language_transform(
                source_graph=graph,
                external_runtime_graphs=external_runtime_graphs,
            )
        )
    with _runtime_derivation_progress_step(
        progress_request,
        "derive_runtime_graph.language_to_runtime.transformer_resolve",
        detail_payload={
            "source_language": graph.language.value,
            "external_graph_count": len(external_runtime_graphs),
            "namespace_entry_count": len(namespace_by_code_id),
        },
    ):
        transformer = cast(
            ObjectConfigGraphTransformer | None,
            MetaLanguagePluginRegistry.get_language_to_runtime_transformer(
                graph.language,
                **kwargs,
            ),
        )
    if transformer is None:
        raise ValueError(
            f"No language_to_runtime_transformer registered for {graph.language}."
        )
    with _runtime_derivation_progress_step(
        progress_request,
        "derive_runtime_graph.language_to_runtime.transform",
        detail_payload={
            "source_language": graph.language.value,
            "external_graph_count": len(external_runtime_graphs),
            "namespace_entry_count": len(namespace_by_code_id),
        },
    ):
        return transformer.transform(graph, code_primitive_type=None)


def _external_runtime_graphs_by_id_for_language_transform(
    *,
    source_graph: ObjectConfigGraph,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...],
) -> dict[UUID, ObjectConfigGraph]:
    external_by_id = {
        external_graph.id: external_graph
        for external_graph in external_runtime_graphs
    }
    external_by_fqn: dict[str, ObjectConfigGraph | None] = {}
    for external_graph in external_runtime_graphs:
        fqn_prefix = (external_graph.fqn_prefix or "").strip()
        if not fqn_prefix:
            continue
        if fqn_prefix in external_by_fqn:
            external_by_fqn[fqn_prefix] = None
            continue
        external_by_fqn[fqn_prefix] = external_graph

    for relationship in source_graph.object_config_graph_relationships:
        target_graph = relationship.target_object_config_graph
        if target_graph is None:
            continue
        target_fqn_prefix = (target_graph.fqn_prefix or "").strip()
        if not target_fqn_prefix:
            continue
        runtime_graph = external_by_fqn.get(target_fqn_prefix)
        if runtime_graph is None:
            continue
        external_by_id.setdefault(
            relationship.target_object_config_graph_id,
            runtime_graph,
        )
    return external_by_id


def _rebind_relationship_targets_to_runtime_closure(
    *,
    runtime_graph: ObjectConfigGraph,
    runtime_external_graphs: tuple[ObjectConfigGraph, ...],
    mutate_external_graphs: bool = True,
) -> None:
    runtime_graphs = (runtime_graph, *runtime_external_graphs)
    runtime_graph_by_id = {graph.id: graph for graph in runtime_graphs}
    runtime_graph_by_fqn: dict[str, ObjectConfigGraph] = {}
    for graph in runtime_graphs:
        fqn_prefix = (graph.fqn_prefix or "").strip()
        if not fqn_prefix:
            continue
        existing = runtime_graph_by_fqn.get(fqn_prefix)
        if existing is not None and existing.id != graph.id:
            raise ValueError(
                "Runtime OCG derivation received duplicate runtime graph FQN "
                f"{fqn_prefix!r}: {existing.id} and {graph.id}"
            )
        runtime_graph_by_fqn[fqn_prefix] = graph

    graphs_to_update = runtime_graphs if mutate_external_graphs else (runtime_graph,)
    for graph in graphs_to_update:
        for relationship in graph.object_config_graph_relationships:
            canonical = runtime_graph_by_id.get(
                relationship.target_object_config_graph_id
            )
            if (
                canonical is None
                and relationship.target_object_config_graph is not None
            ):
                target_fqn_prefix = (
                    relationship.target_object_config_graph.fqn_prefix or ""
                ).strip()
                canonical = runtime_graph_by_fqn.get(target_fqn_prefix)
            if canonical is None:
                continue
            relationship.target_object_config_graph = canonical
            relationship.target_object_config_graph_id = canonical.id
            relationship.id = stable_object_config_graph_binding_id(
                object_config_graph_id=relationship.object_config_graph_id,
                target_object_config_graph_id=canonical.id,
            )


def build_namespace_by_code_id_from_graph(
    graph: ObjectConfigGraph,
) -> dict[UUID, NamespacePath]:
    namespace_bundle = build_namespace_bundle_from_ocg_topology(ocg=graph)
    namespace_by_code_id: dict[UUID, NamespacePath] = {}
    for node in graph.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
        ):
            code_section_class = node.class_config.code_section_class
            code_section = (
                code_section_class.code_section
                if code_section_class is not None
                else None
            )
            namespace = namespace_bundle.namespace_for_class(node.class_config.id)
        elif (
            node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None
        ):
            code_section_enum = node.enum_config.code_section_enum
            code_section = (
                code_section_enum.code_section
                if code_section_enum is not None
                else None
            )
            namespace = namespace_bundle.namespace_for_enum(node.enum_config.id)
        elif node.type == ObjectConfigGraphNodeType.function:
            function_config = get_node_function_config(node)
            code_section_function = (
                function_config.code_section_function
                if function_config is not None
                else None
            )
            code_section = (
                code_section_function.code_section
                if code_section_function is not None
                else None
            )
            namespace = (
                namespace_bundle.namespace_for_function(function_config.id)
                if function_config is not None
                else None
            )
        else:
            code_section = None
            namespace = None
        if code_section is None or namespace is None:
            continue
        namespace_by_code_id[code_section.code_id] = namespace
    return namespace_by_code_id


def _build_namespace_by_code_id_from_graph(
    graph: ObjectConfigGraph,
) -> dict[UUID, NamespacePath]:
    return build_namespace_by_code_id_from_graph(graph)


def _refresh_runtime_overlays(
    *,
    runtime_graph: ObjectConfigGraph,
    timer: RuntimeDerivationTimer,
) -> None:
    with timer.step("overlays"):
        runtime_bundle = build_namespace_bundle_from_ocg_topology(ocg=runtime_graph)
        runtime_graph.object_config_graph_overlays = (
            build_object_config_graph_overlays_from_annotations(
                runtime_graph,
                namespace_bundle=runtime_bundle,
            )
        )


def _derive_runtime_projection_graphs(
    *,
    runtime_graph: ObjectConfigGraph,
    runtime_external_graphs: tuple[ObjectConfigGraph, ...],
    derive_external_projection_graphs: bool = True,
    source_is_runtime: bool,
    timer: RuntimeDerivationTimer,
) -> None:
    if source_is_runtime:
        return
    if not runtime_graph.object_projection_graph_declarations:
        return
    with timer.step("derive_opgs"):
        externals = list(runtime_external_graphs)
        derive_external_opgs = (
            derive_external_projection_graphs
            or _projection_declarations_have_portal_targets(
                runtime_graph.object_projection_graph_declarations
            )
        )
        if not derive_external_opgs:
            runtime_graph.object_projection_graphs = build_object_projection_graphs(
                runtime_graph,
                external_graphs=externals,
            )
            return

        graph_closure = [*externals, runtime_graph]
        graph_ids_requiring_opgs = {
            graph.id
            for graph in graph_closure
            if graph.object_projection_graph_declarations
            and not graph.object_projection_graphs
        }

        def external_graphs_for(graph: ObjectConfigGraph) -> list[ObjectConfigGraph]:
            if graph.id == runtime_graph.id:
                return externals
            return [
                runtime_graph,
                *(
                    external_graph
                    for external_graph in externals
                    if external_graph.id != graph.id
                ),
            ]

        for graph in graph_closure:
            if graph.id not in graph_ids_requiring_opgs:
                continue
            graph.object_projection_graphs = build_object_projection_graphs(
                graph,
                external_graphs=external_graphs_for(graph),
                provision_portals=False,
            )
        for graph in graph_closure:
            if graph.id not in graph_ids_requiring_opgs:
                continue
            graph.object_projection_graphs = build_object_projection_graphs(
                graph,
                external_graphs=external_graphs_for(graph),
            )
        _rebind_runtime_portal_targets(graphs=graph_closure)


def _projection_declarations_have_portal_targets(
    declarations: Iterable[ObjectProjectionGraphDeclaration] | None,
) -> bool:
    for declaration in declarations or ():
        for binding in declaration.object_projection_graph_bindings or ():
            if (binding.target_projection_name or "").strip():
                return True
    return False


def _ensure_runtime_projection_graphs(
    runtime_graphs: tuple[ObjectConfigGraph, ...],
    *,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
) -> tuple[ObjectConfigGraph, ...]:
    graph_ids_requiring_opgs = {
        graph.id
        for graph in runtime_graphs
        if graph.object_projection_graph_declarations
        and not graph.object_projection_graphs
    }
    if not graph_ids_requiring_opgs:
        return runtime_graphs

    graphs = [graph.model_copy(deep=True) for graph in runtime_graphs]
    external_graphs = [
        graph.model_copy(deep=True)
        for graph in external_runtime_graphs
        if graph.id not in graph_ids_requiring_opgs
    ]
    graph_closure = [*external_graphs, *graphs]
    for graph in graphs:
        if graph.id not in graph_ids_requiring_opgs:
            continue
        graph.object_projection_graphs = build_object_projection_graphs(
            graph,
            external_graphs=[
                external_graph
                for external_graph in graph_closure
                if external_graph.id != graph.id
            ],
            provision_portals=False,
        )
    for graph in graphs:
        if graph.id not in graph_ids_requiring_opgs:
            continue
        graph.object_projection_graphs = build_object_projection_graphs(
            graph,
            external_graphs=[
                external_graph
                for external_graph in graph_closure
                if external_graph.id != graph.id
            ],
        )
    _rebind_runtime_portal_targets(graphs=graph_closure)
    return tuple(graphs)


def _extend_bundle_for_derived_graph(
    *,
    base: ObjectConfigGraphNamespaceBundle,
    derived_graph: ObjectConfigGraph,
) -> ObjectConfigGraphNamespaceBundle:
    by_class = dict(base.namespace_by_class_config_id)
    by_enum = dict(base.namespace_by_enum_config_id)
    by_function = dict(base.namespace_by_function_config_id)

    def maybe_assign_association_namespace(rel: ClassConfigRelationship) -> None:
        association_edge = rel.class_config_relationship_association_edge
        association_class_id = (
            association_edge.class_config_id if association_edge is not None else None
        )
        if association_class_id is None or association_class_id in by_class:
            return
        source_namespace = by_class.get(rel.class_config_id)
        target_namespace = by_class.get(rel.target_class_config_id)
        inferred = source_namespace or target_namespace
        if inferred is not None:
            by_class[association_class_id] = inferred

    for node in derived_graph.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.relationship
            and node.class_config_relationship is not None
        ):
            maybe_assign_association_namespace(node.class_config_relationship)
    for ocg_relationship in derived_graph.object_config_graph_relationships:
        for relationship in ocg_relationship.class_config_relationships:
            maybe_assign_association_namespace(relationship)
    for node in derived_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        for relationship in node.class_config.class_config_relationships or []:
            maybe_assign_association_namespace(relationship)

    try:
        node_namespace_by_node_id = build_node_namespace_by_node_id(derived_graph)
    except Exception:
        node_namespace_by_node_id = {}
    for node in derived_graph.object_config_graph_nodes:
        namespace = node_namespace_by_node_id.get(node.id)
        if namespace is None:
            continue
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
        ):
            by_class.setdefault(node.class_config.id, namespace)
        elif (
            node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None
        ):
            by_enum.setdefault(node.enum_config.id, namespace)
        elif node.type == ObjectConfigGraphNodeType.function:
            function_config = get_node_function_config(node)
            if function_config is not None:
                by_function.setdefault(function_config.id, namespace)

    fallback_namespace = next(iter(by_class.values()), None)
    if fallback_namespace is not None:
        for node in derived_graph.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                by_class.setdefault(node.class_config.id, fallback_namespace)
            elif (
                node.type == ObjectConfigGraphNodeType.enum
                and node.enum_config is not None
            ):
                by_enum.setdefault(node.enum_config.id, fallback_namespace)
            elif node.type == ObjectConfigGraphNodeType.function:
                function_config = get_node_function_config(node)
                if function_config is not None:
                    by_function.setdefault(function_config.id, fallback_namespace)

    return ObjectConfigGraphNamespaceBundle(
        namespace_by_class_config_id=by_class,
        namespace_by_enum_config_id=by_enum,
        namespace_by_function_config_id=by_function,
    )


def _attach_relationships_to_class_configs(
    graph: ObjectConfigGraph,
    *,
    preserve_existing_attached: bool = False,
) -> None:
    class_by_id: dict[UUID, ClassConfig] = {}
    for node in graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_:
            continue
        class_config = node.class_config
        if class_config is None:
            raise ValueError(f"Class config is None for node {node.id}")
        class_by_id[class_config.id] = class_config

    if not class_by_id:
        return

    rels_by_class_id: dict[UUID, list[ClassConfigRelationship]] = defaultdict(list)
    if preserve_existing_attached:
        for class_config in class_by_id.values():
            for relationship in class_config.class_config_relationships or []:
                _attach_rel(relationship, class_by_id, rels_by_class_id)
    for node in graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.relationship:
            continue
        relationship = node.class_config_relationship
        if relationship is None:
            raise ValueError(f"Relationship is None for node {node.id}")
        _attach_rel(relationship, class_by_id, rels_by_class_id)
    for ocg_relationship in graph.object_config_graph_relationships:
        for relationship in ocg_relationship.class_config_relationships:
            _attach_rel(relationship, class_by_id, rels_by_class_id)
    for class_id, class_config in class_by_id.items():
        deduped: list[ClassConfigRelationship] = []
        seen: set[UUID] = set()
        for relationship in rels_by_class_id.get(class_id, []):
            if relationship.id in seen:
                continue
            seen.add(relationship.id)
            deduped.append(relationship)
        class_config.class_config_relationships = deduped


def _attach_rel(
    rel: ClassConfigRelationship,
    class_by_id: dict[UUID, ClassConfig],
    rels_by_class_id: dict[UUID, list[ClassConfigRelationship]],
) -> None:
    if rel.class_config_id in class_by_id:
        rels_by_class_id[rel.class_config_id].append(rel)
    if rel.target_class_config_id in class_by_id:
        rels_by_class_id[rel.target_class_config_id].append(rel)
    association_edge = rel.class_config_relationship_association_edge
    association_class_id = (
        association_edge.class_config_id if association_edge is not None else None
    )
    if association_class_id is not None and association_class_id in class_by_id:
        rels_by_class_id[association_class_id].append(rel)


def _rebind_runtime_portal_targets(
    *,
    graphs: list[ObjectConfigGraph],
) -> None:
    opg_by_id: dict[UUID, ObjectProjectionGraph] = {}
    node_by_id: dict[UUID, ObjectProjectionGraphNode] = {}
    for graph in graphs:
        for opg in graph.object_projection_graphs:
            opg_by_id[opg.id] = opg
            for node in opg.object_projection_graph_nodes:
                node_by_id[node.id] = node
    for graph in graphs:
        for opg in graph.object_projection_graphs:
            for relationship in opg.object_projection_graph_relationships or []:
                target_opg = opg_by_id.get(
                    relationship.target_object_projection_graph_id
                )
                if target_opg is None:
                    raise ValueError(
                        "Runtime OPG rebind: missing target OPG "
                        + f"target_object_projection_graph_id={relationship.target_object_projection_graph_id}"
                    )
                relationship.target_object_projection_graph = target_opg
                target_node = node_by_id.get(
                    relationship.target_object_projection_graph_node_id
                )
                if target_node is None:
                    target_node_id = relationship.target_object_projection_graph_node_id
                    raise ValueError(
                        "Runtime OPG rebind: missing target node "
                        + f"target_object_projection_graph_node_id={target_node_id}"
                    )
                relationship.target_object_projection_graph_node = target_node


__all__ = [
    "RuntimeObjectConfigGraphDerivationService",
    "derive_runtime_object_config_graph",
    "derive_runtime_object_config_graphs",
]
