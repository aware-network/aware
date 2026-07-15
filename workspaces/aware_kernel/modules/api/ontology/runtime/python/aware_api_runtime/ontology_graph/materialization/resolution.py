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
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph_observable import (
    ObjectProjectionGraphObservable,
)
from aware_meta_ontology.stable_ids import stable_object_projection_graph_identity_id

from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
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
) -> tuple[int, int, int, int, int, int]:
    return (
        len(graph.object_projection_graphs),
        _object_config_graph_identity_observable_count(graph),
        _object_config_graph_identity_projection_count(graph),
        len(graph.object_config_graph_nodes),
        len(graph.object_config_graph_bindings),
        len(graph.object_config_graph_relationships),
    )


def _object_config_graph_identity_projection_count(graph: ObjectConfigGraph) -> int:
    ocgi = getattr(graph, "object_config_graph_identity", None)
    if ocgi is None:
        return 0
    return len(ocgi.object_projection_graph_identities)


def _object_config_graph_identity_observable_count(graph: ObjectConfigGraph) -> int:
    ocgi = getattr(graph, "object_config_graph_identity", None)
    if ocgi is None:
        return 0
    return sum(
        len(identity.object_projection_graph_observables)
        for identity in ocgi.object_projection_graph_identities
        if isinstance(identity, ObjectProjectionGraphIdentity)
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


def _resolve_object_projection_graph_observable(
    *,
    index: MetaGraphRuntimeIndex,
    accessible_graphs: Sequence[ObjectConfigGraph],
    observable_ref: str,
) -> ObjectProjectionGraphObservable:
    normalized_ref = _normalize_token(observable_ref)
    if not normalized_ref:
        raise RuntimeError(
            "Invalid api ontology view observable: observable_ref is required"
        )

    matches: list[ObjectProjectionGraphObservable] = []
    for projection_ref, observable_key in _observable_ref_candidates(observable_ref):
        for graph in accessible_graphs:
            for opg in graph.object_projection_graphs:
                if projection_ref and not _projection_matches(
                    target_graph=graph,
                    opg=opg,
                    target=projection_ref,
                ):
                    continue
                opgi = _resolve_object_projection_graph_identity_for_graph(
                    index=index,
                    graph=graph,
                    opg=opg,
                )
                if opgi is None:
                    continue
                for observable in opgi.object_projection_graph_observables or ():
                    if _observable_matches(
                        observable=observable,
                        observable_ref=observable_ref,
                        observable_key=observable_key,
                        projection_ref=projection_ref,
                        projection_name=opgi.projection_name,
                    ):
                        matches.append(observable)

    unique_matches = tuple(
        {observable.id: observable for observable in matches}.values()
    )
    if len(unique_matches) == 1:
        return unique_matches[0]
    if len(unique_matches) > 1:
        raise RuntimeError(
            "Ambiguous api ontology view observable "
            + f"(observable_ref={observable_ref!r}, matches={[item.key for item in unique_matches]!r})"
        )
    raise RuntimeError(
        f"Could not resolve api ontology view observable {observable_ref!r}"
    )


def _resolve_object_projection_graph_identity_for_graph(
    *,
    index: MetaGraphRuntimeIndex,
    graph: ObjectConfigGraph,
    opg: ObjectProjectionGraph,
) -> ObjectProjectionGraphIdentity | None:
    ocgi = graph.object_config_graph_identity
    if ocgi is not None:
        matching_identities = tuple(
            identity
            for identity in ocgi.object_projection_graph_identities
            if isinstance(identity, ObjectProjectionGraphIdentity)
            and identity.object_projection_graph_id == opg.id
        )
        if len(matching_identities) == 1:
            return matching_identities[0]
        if len(matching_identities) > 1:
            expected_identity_id = stable_object_projection_graph_identity_id(
                object_config_graph_identity_id=ocgi.id,
                object_projection_graph_id=opg.id,
            )
            exact_matches = tuple(
                identity
                for identity in matching_identities
                if identity.id == expected_identity_id
            )
            if len(exact_matches) == 1:
                return exact_matches[0]
            raise RuntimeError(
                "Ambiguous api ontology view observable projection identity "
                + f"(graph={graph.fqn_prefix!r}, projection={opg.name!r})"
            )

    _ocgi, indexed_opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=opg.projection_hash,
    )
    return indexed_opgi


def _split_observable_ref(observable_ref: str) -> tuple[str | None, str]:
    normalized_ref = (observable_ref or "").strip()
    head, separator, tail = normalized_ref.rpartition(".")
    if separator and head and tail:
        return head, tail
    return None, normalized_ref


def _observable_ref_candidates(
    observable_ref: str,
) -> tuple[tuple[str | None, str], ...]:
    normalized_ref = (observable_ref or "").strip()
    if not normalized_ref:
        return ()
    candidates: list[tuple[str | None, str]] = []
    parts = normalized_ref.split(".")
    if len(parts) > 1:
        for split_index in range(len(parts) - 1, 0, -1):
            projection_ref = ".".join(parts[:split_index])
            observable_key = ".".join(parts[split_index:])
            if projection_ref and observable_key:
                candidates.append((projection_ref, observable_key))
    candidates.append((None, normalized_ref))
    return tuple(dict.fromkeys(candidates))


def _observable_matches(
    *,
    observable: ObjectProjectionGraphObservable,
    observable_ref: str,
    observable_key: str,
    projection_ref: str | None,
    projection_name: str | None,
) -> bool:
    target_key = _normalize_token(observable_key)
    actual_observable_key = _normalize_token(observable.observable_key)
    actual_key = _normalize_token(observable.key)
    if projection_ref:
        return target_key in {actual_observable_key, actual_key}

    ref_variants = _observable_ref_variants(
        observable_ref=observable_ref,
        projection_name=projection_name,
    )
    actual_variants = _observable_ref_variants(
        observable_ref=observable.key,
        projection_name=projection_name,
    )
    actual_variants.add(actual_observable_key)
    return any(candidate in actual_variants for candidate in ref_variants)


def _observable_ref_variants(
    *, observable_ref: str | None, projection_name: str | None
) -> set[str]:
    normalized = _normalize_token(observable_ref)
    variants = {normalized, normalized.replace(":", ".")}
    if projection_name:
        projection = _normalize_token(projection_name)
        if normalized and projection:
            variants.add(f"{projection}:{normalized}")
            variants.add(f"{projection}.{normalized}")
    return {variant for variant in variants if variant}


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
