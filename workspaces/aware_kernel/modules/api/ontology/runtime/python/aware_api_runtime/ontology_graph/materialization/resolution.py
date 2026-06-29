from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex


def _collect_accessible_object_config_graphs(
    *,
    index: MetaGraphRuntimeIndex,
    extra_graphs: Sequence[ObjectConfigGraph] = (),
) -> tuple[ObjectConfigGraph, ...]:
    graphs_by_id: dict[UUID, ObjectConfigGraph] = {}

    def _remember(graph: ObjectConfigGraph | None) -> None:
        if graph is None:
            return
        existing = graphs_by_id.get(graph.id)
        if existing is None or _object_config_graph_detail_score(
            graph
        ) > _object_config_graph_detail_score(existing):
            graphs_by_id[graph.id] = graph

    _remember(index.ocg)
    for graph in extra_graphs:
        _remember(graph)
    for relationship in index.ocg.object_config_graph_relationships:
        _remember(relationship.target_object_config_graph)
    for binding in index.ocg.object_config_graph_bindings:
        _remember(binding.target_object_config_graph)

    return tuple(
        sorted(
            graphs_by_id.values(),
            key=lambda item: (
                _normalize_token(item.fqn_prefix),
                _normalize_token(item.name),
                str(item.id),
            ),
        )
    )


def _object_config_graph_detail_score(
    graph: ObjectConfigGraph,
) -> tuple[int, int, int, int]:
    return (
        len(graph.object_projection_graphs),
        len(graph.object_config_graph_nodes),
        len(graph.object_config_graph_bindings),
        len(graph.object_config_graph_relationships),
    )


def _resolve_target_object_config_graph(
    *,
    index: MetaGraphRuntimeIndex,
    accessible_graphs: Sequence[ObjectConfigGraph],
    target: str,
    function_targets: Sequence[str] = (),
    projection_specs: Sequence[str] = (),
) -> ObjectConfigGraph:
    normalized_target = _normalize_token(target)
    if not normalized_target:
        raise RuntimeError(
            "Invalid api ontology materialization target graph: target is required"
        )

    exact_matches = tuple(
        graph
        for graph in accessible_graphs
        if normalized_target in _graph_lookup_tokens(graph)
    )
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise RuntimeError(
            "Ambiguous api ontology materialization target graph "
            + f"(target={target!r}, matches={[item.fqn_prefix for item in exact_matches]!r})"
        )

    suffix_matches = tuple(
        graph
        for graph in accessible_graphs
        if any(
            token.endswith(normalized_target) or normalized_target.endswith(token)
            for token in _graph_lookup_tokens(graph)
        )
    )
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        raise RuntimeError(
            "Ambiguous api ontology materialization target graph suffix match "
            + f"(target={target!r}, matches={[item.fqn_prefix for item in suffix_matches]!r})"
        )

    fallback_matches = tuple(
        graph
        for graph in accessible_graphs
        if _graph_supports_materialization_targets(
            index=index,
            accessible_graphs=accessible_graphs,
            graph=graph,
            function_targets=function_targets,
            projection_specs=projection_specs,
        )
    )
    if len(fallback_matches) == 1:
        return fallback_matches[0]
    if len(fallback_matches) > 1:
        raise RuntimeError(
            "Ambiguous api ontology materialization fallback graph "
            + f"(target={target!r}, matches={[item.fqn_prefix for item in fallback_matches]!r})"
        )

    raise RuntimeError(f"Could not resolve api ontology target graph {target!r}")


def _graph_supports_materialization_targets(
    *,
    index: MetaGraphRuntimeIndex,
    accessible_graphs: Sequence[ObjectConfigGraph],
    graph: ObjectConfigGraph,
    function_targets: Sequence[str],
    projection_specs: Sequence[str],
) -> bool:
    if not function_targets and not projection_specs:
        return False
    try:
        for function_target in function_targets:
            _ = _resolve_public_function_config_id_within_graph(
                target_graph=graph,
                function_target=function_target,
            )
        for projection_target in projection_specs:
            _ = _resolve_object_projection_graph(
                index=index,
                target_graph=graph,
                projection_target=projection_target,
                accessible_graphs=accessible_graphs,
            )
    except RuntimeError:
        return False
    return True


def _resolve_object_projection_graph(
    *,
    index: MetaGraphRuntimeIndex,
    target_graph: ObjectConfigGraph,
    projection_target: str,
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> ObjectProjectionGraph:
    exact_matches = tuple(
        opg
        for opg in target_graph.object_projection_graphs
        if _projection_matches(
            target_graph=target_graph, opg=opg, target=projection_target
        )
    )
    if len(exact_matches) == 1:
        return exact_matches[0]

    if len(exact_matches) > 1:
        raise RuntimeError(
            "Ambiguous api ontology materialization projection target "
            + f"(projection_target={projection_target!r}, matches={[item.name for item in exact_matches]!r})"
        )

    raise RuntimeError(
        f"Could not resolve api ontology projection target {projection_target!r}"
    )


def _resolve_public_function_config_id_within_graph(
    *,
    target_graph: ObjectConfigGraph,
    function_target: str,
) -> UUID:
    class_target, function_name = _split_class_function_target(function_target)
    matches: list[UUID] = []

    for node in target_graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        class_config = node.class_config
        if not _class_matches(class_config=class_config, target=class_target):
            continue
        for function_link in class_config.class_config_function_configs:
            function_config = function_link.function_config
            if not function_link.is_public:
                continue
            if _normalize_token(function_config.name) != _normalize_token(
                function_name
            ):
                continue
            matches.append(function_link.id)

    if not matches:
        raise RuntimeError(
            "Could not resolve api ontology graph function target "
            + f"(graph={target_graph.fqn_prefix!r}, target={function_target!r})"
        )
    unique_matches: tuple[UUID, ...] = tuple(dict.fromkeys(matches))
    if len(unique_matches) > 1:
        raise RuntimeError(
            "Ambiguous api ontology graph function target "
            + f"(graph={target_graph.fqn_prefix!r}, target={function_target!r})"
        )
    return next(iter(unique_matches))


def _resolve_class_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    accessible_graphs: Sequence[ObjectConfigGraph],
    class_ref: str,
    class_config_id: UUID | None = None,
) -> UUID:
    if class_config_id is not None:
        return class_config_id
    normalized_target = _normalize_token(class_ref)
    matches: list[UUID] = [
        class_config.id
        for class_config in index.class_configs_by_id.values()
        if _class_matches(class_config=class_config, target=normalized_target)
    ]
    for graph in accessible_graphs:
        for node in graph.object_config_graph_nodes:
            class_config = node.class_config
            if class_config is None:
                continue
            if _class_matches(class_config=class_config, target=normalized_target):
                matches.append(class_config.id)
    unique_matches: tuple[UUID, ...] = tuple(dict.fromkeys(matches))
    if not unique_matches:
        raise RuntimeError(f"Could not resolve api ontology class config {class_ref!r}")
    if len(unique_matches) > 1:
        raise RuntimeError(f"Ambiguous api ontology class config {class_ref!r}")
    return next(iter(unique_matches))


def _class_matches(*, class_config: ClassConfig, target: str) -> bool:
    target_variants = _normalized_variants(target)
    actual_variants = _normalized_variants(class_config.class_fqn)
    actual_variants.add(_normalize_token(class_config.name))
    actual_variants.add(_leaf_token(class_config.class_fqn))
    actual_variants.add(_leaf_token(class_config.name))

    for target_variant in target_variants:
        if target_variant in actual_variants:
            return True
        if any(actual.endswith(f".{target_variant}") for actual in actual_variants):
            return True
    return False


def _projection_matches(
    *, target_graph: ObjectConfigGraph, opg: ObjectProjectionGraph, target: str
) -> bool:
    projection_name = (opg.name or "").strip()
    projection_target = (target or "").strip()
    if not projection_name or not projection_target:
        return False

    exact_targets = {projection_name}
    graph_prefix = (target_graph.fqn_prefix or "").strip()
    if graph_prefix:
        exact_targets.add(f"{graph_prefix}.{projection_name}")
    return projection_target in exact_targets


def _graph_lookup_tokens(graph: ObjectConfigGraph) -> frozenset[str]:
    tokens = {
        _normalize_token(graph.name),
        _normalize_token(graph.fqn_prefix),
        _leaf_token(graph.name),
        _leaf_token(graph.fqn_prefix),
    }
    return frozenset(token for token in tokens if token)


def _split_class_function_target(target: str) -> tuple[str, str]:
    normalized_target = (target or "").strip()
    head, separator, tail = normalized_target.rpartition(".")
    if not separator or not head or not tail:
        raise RuntimeError(f"Invalid api ontology graph function target {target!r}")
    return head, tail


def _normalize_token(value: str | None) -> str:
    return (value or "").strip().casefold()


def _leaf_token(value: str | None) -> str:
    normalized = _normalize_token(value)
    if not normalized:
        return ""
    return normalized.rsplit(".", 1)[-1]


def _normalized_variants(value: str | None) -> set[str]:
    normalized = _normalize_token(value)
    if not normalized:
        return set()

    variants = {normalized}
    parts = [part for part in normalized.split(".") if part]
    if "default" in parts[1:-1]:
        variants.add(".".join(part for part in parts if part != "default"))
    return {variant for variant in variants if variant}
