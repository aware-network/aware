from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
import os
from uuid import UUID

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

from aware_meta.graph.config.compose import compose_object_config_graphs
from aware_meta.graph.config.lane.errors import OcgSeedError
from aware_meta.graph.config.lane.telemetry import (
    SeedTimings,
    maybe_metric,
    maybe_timed,
)
from aware_meta.graph.config.model_bootstrap import (
    get_object_config_graph_node_class_config_id,
)


@dataclass(frozen=True, slots=True)
class SeedProjectionContext:
    schema_graph: ObjectConfigGraph
    opg: ObjectProjectionGraph


@dataclass(frozen=True, slots=True)
class PreparedSeedProjection:
    schema_graph: ObjectConfigGraph
    opg: ObjectProjectionGraph
    schema_view: ObjectConfigGraph
    external_graphs: tuple[ObjectConfigGraph, ...]


@dataclass(frozen=True, slots=True)
class _SeedSchemaViewPlan:
    cache_key: tuple[str, str, tuple[tuple[str, str], ...]] | None
    ocgs: tuple[ObjectConfigGraph, ...]


_SEED_SCHEMA_VIEW_CACHE_MAX = int(os.getenv("AWARE_SEED_SCHEMA_VIEW_CACHE_MAX") or "16")
_SEED_SCHEMA_VIEW_CACHE: (
    "OrderedDict[tuple[str, str, tuple[tuple[str, str], ...]], ObjectConfigGraph]"
) = OrderedDict()
_SEED_SCHEMA_VIEW_NODE_IDS_CACHE_MAX = int(
    os.getenv("AWARE_SEED_SCHEMA_VIEW_NODE_IDS_CACHE_MAX") or "64"
)
_SEED_SCHEMA_VIEW_NODE_IDS_CACHE: "OrderedDict[tuple[str, str], frozenset[UUID]]" = (
    OrderedDict()
)
_SEED_SCHEMA_VIEW_DEDUPE_COLLECTIONS = (
    "object_config_graph_annotations",
    "object_config_graph_mirrors",
    "object_config_graph_nodes",
    "object_config_graph_overlays",
    "object_config_graph_bindings",
    "object_config_graph_relationships",
    "object_projection_graph_declarations",
    "object_projection_graphs",
)


def schema_configs_by_id_from_schema_view(
    schema_view: ObjectConfigGraph,
) -> tuple[dict[UUID, ClassConfig], dict[UUID, AttributeConfig]]:
    """Extract schema-owned ClassConfig/AttributeConfig objects for OIG apply validation."""
    schema_class_configs_by_id: dict[UUID, ClassConfig] = {}
    schema_attribute_configs_by_id: dict[UUID, AttributeConfig] = {}
    for node in schema_view.object_config_graph_nodes or []:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        schema_class_configs_by_id[node.class_config.id] = node.class_config
        for link in node.class_config.class_config_attribute_configs or []:
            attribute_config = link.attribute_config
            schema_attribute_configs_by_id[attribute_config.id] = attribute_config
    return schema_class_configs_by_id, schema_attribute_configs_by_id


def resolve_ocg_seed_projection_context(
    *,
    ocg: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
    opg_name: str,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph]:
    """Resolve the seed schema graph and OPG identity for OCG lane orchestration."""
    ctx = _resolve_seed_projection_context(
        ocg=ocg,
        external_graphs=external_graphs,
        opg_name=opg_name,
    )
    return ctx.schema_graph, ctx.opg


def resolve_ocg_seed_schema_view(
    *,
    ocg: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
    opg_name: str,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph]:
    """Resolve the composed schema view used for OCG lane materialization."""
    ctx = _resolve_seed_projection_context(
        ocg=ocg,
        external_graphs=external_graphs,
        opg_name=opg_name,
    )
    schema_view = compose_ocg_seed_schema_graph(
        schema_graph=ctx.schema_graph,
        external_graphs=external_graphs,
        object_projection_graph=ctx.opg,
    )
    return schema_view, ctx.opg


def prepare_ocg_seed_projection(
    *,
    ocg: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
    opg_name: str,
    timings: SeedTimings | None = None,
) -> PreparedSeedProjection:
    """Resolve and compose the canonical seed projection exactly once for a caller."""
    external_graphs_list = list(external_graphs or ())
    ctx = _resolve_seed_projection_context(
        ocg=ocg,
        external_graphs=external_graphs_list,
        opg_name=opg_name,
    )
    schema_view = compose_ocg_seed_schema_graph(
        schema_graph=ctx.schema_graph,
        external_graphs=external_graphs_list,
        object_projection_graph=ctx.opg,
        timings=timings,
    )
    return PreparedSeedProjection(
        schema_graph=ctx.schema_graph,
        opg=ctx.opg,
        schema_view=schema_view,
        external_graphs=tuple(external_graphs_list),
    )


def compose_ocg_seed_schema_graph(
    *,
    schema_graph: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
    object_projection_graph: ObjectProjectionGraph | None = None,
    timings: SeedTimings | None = None,
) -> ObjectConfigGraph:
    """Compose the schema view used by the canonical OCG seed projection."""
    with maybe_timed(timings, "seed_schema_view.cache_key"):
        plan = _plan_seed_schema_view(
            schema_graph=schema_graph,
            external_graphs=external_graphs,
            object_projection_graph=object_projection_graph,
        )
    if plan.cache_key is not None:
        cached = _SEED_SCHEMA_VIEW_CACHE.get(plan.cache_key)
        if cached is not None:
            maybe_metric(timings, "seed_schema_view_cache_hit", True)
            _SEED_SCHEMA_VIEW_CACHE.move_to_end(plan.cache_key)
            return cached
    maybe_metric(timings, "seed_schema_view_cache_hit", False)

    maybe_metric(timings, "seed_schema_view_ocg_count", len(plan.ocgs))
    maybe_metric(
        timings,
        "seed_schema_view_effective_external_graph_count",
        max(len(plan.ocgs) - 1, 0),
    )
    if len(plan.ocgs) == 1:
        result = schema_graph
    else:
        with maybe_timed(timings, "seed_schema_view.compose"):
            result = compose_object_config_graphs(
                ocgs=list(plan.ocgs),
                composite_id=schema_graph.id,
                composite_name=schema_graph.name,
                composite_hash=schema_graph.hash,
                composite_fqn_prefix=schema_graph.fqn_prefix,
                validate_portals=False,
                timings=timings,
                timing_prefix="seed_schema_view.compose",
            )

    if plan.cache_key is not None:
        _SEED_SCHEMA_VIEW_CACHE[plan.cache_key] = result
        _SEED_SCHEMA_VIEW_CACHE.move_to_end(plan.cache_key)
        while len(_SEED_SCHEMA_VIEW_CACHE) > max(_SEED_SCHEMA_VIEW_CACHE_MAX, 1):
            _ = _SEED_SCHEMA_VIEW_CACHE.popitem(last=False)
    return result


def _seed_schema_view_cache_key(
    *,
    schema_graph: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
    object_projection_graph: ObjectProjectionGraph | None = None,
) -> tuple[str, str, tuple[tuple[str, str], ...]]:
    cache_key = _plan_seed_schema_view(
        schema_graph=schema_graph,
        external_graphs=external_graphs,
        object_projection_graph=object_projection_graph,
    ).cache_key
    if cache_key is None:
        raise OcgSeedError(
            "Schema view cache key requires hashes for effective external graphs"
        )
    return cache_key


def _plan_seed_schema_view(
    *,
    schema_graph: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
    object_projection_graph: ObjectProjectionGraph | None = None,
) -> _SeedSchemaViewPlan:
    schema_hash = (schema_graph.hash or "").strip()
    if not schema_hash:
        raise OcgSeedError("Schema view cache key requires schema_graph.hash")

    schema_node_ids = _seed_schema_view_graph_node_ids(schema_graph)
    required_class_config_ids, required_relationship_ids = (
        _seed_schema_view_required_schema_ids(object_projection_graph)
    )
    if required_class_config_ids or required_relationship_ids:
        schema_class_config_ids = _seed_schema_view_graph_class_config_ids(schema_graph)
        schema_relationship_ids = _seed_schema_view_graph_relationship_ids(schema_graph)
        missing_class_config_ids = required_class_config_ids - schema_class_config_ids
        missing_relationship_ids = required_relationship_ids - schema_relationship_ids
    else:
        missing_class_config_ids = set()
        missing_relationship_ids = set()

    ocgs: list[ObjectConfigGraph] = [schema_graph]
    seen: set[UUID] = {schema_graph.id}
    seen_entry_ids_by_collection = _seed_schema_view_entry_ids_by_collection(
        schema_graph
    )
    external_parts: list[tuple[str, str]] = []
    cacheable = True
    for graph in external_graphs:
        if graph.id in seen:
            continue
        candidate_graph = _seed_schema_view_graph_without_seen_entries(
            graph=graph,
            seen_entry_ids_by_collection=seen_entry_ids_by_collection,
        )
        if candidate_graph is None:
            continue
        if required_class_config_ids or required_relationship_ids:
            graph_class_config_ids = _seed_schema_view_graph_class_config_ids(
                candidate_graph
            )
            graph_relationship_ids = _seed_schema_view_graph_relationship_ids(
                candidate_graph
            )
            contributes_required_schema = bool(
                missing_class_config_ids.intersection(graph_class_config_ids)
                or missing_relationship_ids.intersection(graph_relationship_ids)
            )
            if not contributes_required_schema:
                continue
            missing_class_config_ids -= graph_class_config_ids
            missing_relationship_ids -= graph_relationship_ids
        else:
            graph_node_ids = _seed_schema_view_graph_node_ids(candidate_graph)
            if graph_node_ids and graph_node_ids.issubset(schema_node_ids):
                continue
        seen.add(graph.id)
        _seed_schema_view_remember_entry_ids(
            candidate_graph,
            seen_entry_ids_by_collection=seen_entry_ids_by_collection,
        )
        ocgs.append(candidate_graph)

        candidate_hash = (candidate_graph.hash or "").strip()
        if not candidate_hash:
            cacheable = False
            continue
        external_parts.append((str(graph.id), candidate_hash))
    external_parts.sort()
    cache_key = (
        str(schema_graph.id),
        schema_hash,
        tuple(external_parts),
    )
    return _SeedSchemaViewPlan(
        cache_key=(cache_key if cacheable else None),
        ocgs=tuple(ocgs),
    )


def _seed_schema_view_graph_node_ids(graph: ObjectConfigGraph) -> frozenset[UUID]:
    graph_hash = (graph.hash or "").strip()
    cache_key = (str(graph.id), graph_hash)
    if graph_hash:
        cached = _SEED_SCHEMA_VIEW_NODE_IDS_CACHE.get(cache_key)
        if cached is not None:
            _SEED_SCHEMA_VIEW_NODE_IDS_CACHE.move_to_end(cache_key)
            return cached

    node_ids = frozenset(node.id for node in graph.object_config_graph_nodes)
    if graph_hash:
        _SEED_SCHEMA_VIEW_NODE_IDS_CACHE[cache_key] = node_ids
        _SEED_SCHEMA_VIEW_NODE_IDS_CACHE.move_to_end(cache_key)
        while len(_SEED_SCHEMA_VIEW_NODE_IDS_CACHE) > max(
            _SEED_SCHEMA_VIEW_NODE_IDS_CACHE_MAX, 1
        ):
            _ = _SEED_SCHEMA_VIEW_NODE_IDS_CACHE.popitem(last=False)
    return node_ids


def _seed_schema_view_entry_ids_by_collection(
    graph: ObjectConfigGraph,
) -> dict[str, set[UUID]]:
    return {
        collection_name: _seed_schema_view_collection_ids(
            getattr(graph, collection_name, ())
        )
        for collection_name in _SEED_SCHEMA_VIEW_DEDUPE_COLLECTIONS
    }


def _seed_schema_view_graph_without_seen_entries(
    *,
    graph: ObjectConfigGraph,
    seen_entry_ids_by_collection: dict[str, set[UUID]],
) -> ObjectConfigGraph | None:
    filtered = graph.model_copy(deep=True)
    retained_entry_count = 0
    changed = False
    for collection_name in _SEED_SCHEMA_VIEW_DEDUPE_COLLECTIONS:
        seen_ids = seen_entry_ids_by_collection.get(collection_name, set())
        values = list(getattr(filtered, collection_name, ()) or ())
        retained = [
            value
            for value in values
            if not (
                isinstance((value_id := getattr(value, "id", None)), UUID)
                and value_id in seen_ids
            )
        ]
        if len(retained) != len(values):
            changed = True
        retained_entry_count += len(retained)
        setattr(filtered, collection_name, retained)
    if retained_entry_count == 0:
        return None
    if changed:
        filtered.hash = ""
    return filtered if changed else graph


def _seed_schema_view_remember_entry_ids(
    graph: ObjectConfigGraph,
    *,
    seen_entry_ids_by_collection: dict[str, set[UUID]],
) -> None:
    for collection_name in _SEED_SCHEMA_VIEW_DEDUPE_COLLECTIONS:
        seen_entry_ids_by_collection.setdefault(collection_name, set()).update(
            _seed_schema_view_collection_ids(getattr(graph, collection_name, ()) or ())
        )


def _seed_schema_view_collection_ids(values: Iterable[object]) -> set[UUID]:
    return {
        value_id
        for value in values
        for value_id in (getattr(value, "id", None),)
        if isinstance(value_id, UUID)
    }


def _seed_schema_view_required_schema_ids(
    object_projection_graph: ObjectProjectionGraph | None,
) -> tuple[set[UUID], set[UUID]]:
    if object_projection_graph is None:
        return set(), set()
    class_config_ids = {
        node.class_config_id
        for node in object_projection_graph.object_projection_graph_nodes
    }
    relationship_ids = {
        edge.class_config_relationship_id
        for edge in object_projection_graph.object_projection_graph_edges
    }
    return class_config_ids, relationship_ids


def _seed_schema_view_graph_class_config_ids(
    graph: ObjectConfigGraph,
) -> frozenset[UUID]:
    return frozenset(
        class_config_id
        for node in graph.object_config_graph_nodes
        for class_config_id in (get_object_config_graph_node_class_config_id(node),)
        if node.type == ObjectConfigGraphNodeType.class_ and class_config_id is not None
    )


def _seed_schema_view_graph_relationship_ids(
    graph: ObjectConfigGraph,
) -> frozenset[UUID]:
    return frozenset(rel.id for rel in graph.object_config_graph_relationships)


def _resolve_seed_projection_context(
    *,
    ocg: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph],
    opg_name: str,
) -> SeedProjectionContext:
    target = (opg_name or "").strip()
    if not target:
        raise OcgSeedError("OCG seed requires a non-empty opg_name")

    candidates: list[tuple[ObjectConfigGraph, ObjectProjectionGraph]] = []

    def scan(graph: ObjectConfigGraph) -> None:
        for opg in graph.object_projection_graphs:
            if (opg.name or "").strip() == target:
                candidates.append((graph, opg))

    scan(ocg)
    for external_graph in external_graphs:
        scan(external_graph)

    if not candidates:
        raise OcgSeedError(f"OCG seed OPG not found: {opg_name!r}")

    def _root_class_config_id(opg: ObjectProjectionGraph) -> UUID:
        roots = [node for node in opg.object_projection_graph_nodes if node.is_root]
        if not roots:
            raise OcgSeedError(f"OCG seed OPG {opg_name!r} has no root node")
        if len(roots) != 1:
            raise OcgSeedError(
                f"OCG seed OPG {opg_name!r} must have exactly one root node (got {len(roots)})"
            )
        return roots[0].class_config_id

    def _graph_has_class_config(
        graph: ObjectConfigGraph, class_config_id: UUID
    ) -> bool:
        for node in graph.object_config_graph_nodes:
            node_class_config_id = get_object_config_graph_node_class_config_id(node)
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node_class_config_id == class_config_id
            ):
                return True
        return False

    viable: list[tuple[ObjectConfigGraph, ObjectProjectionGraph]] = []
    for graph, opg in candidates:
        if _graph_has_class_config(graph, _root_class_config_id(opg)):
            viable.append((graph, opg))

    if not viable:
        raise OcgSeedError(
            "OCG seed OPG "
            + f"{opg_name!r} found, but none of the candidate graphs contain its root ClassConfig "
            + "(expected a meta graph in external_graphs)."
        )

    preferred = [(graph, opg) for graph, opg in viable if graph.id != ocg.id] or viable
    owner_preferred = [
        (graph, opg)
        for graph, opg in preferred
        if opg.object_config_graph_id == graph.id
    ]
    if owner_preferred:
        preferred = owner_preferred

    projection_hashes = {str(opg.projection_hash or "") for _, opg in preferred}
    opg_ids = {str(opg.id) for _, opg in preferred}
    if len(projection_hashes) != 1 or len(opg_ids) != 1:
        raise OcgSeedError(
            "Ambiguous OCG seed OPG resolution: "
            + "multiple candidate graphs define a different projection identity "
            + f"(opg_name={opg_name!r} projection_hashes={sorted(projection_hashes)} opg_ids={sorted(opg_ids)})"
        )

    schema_graph, opg = preferred[0]
    return SeedProjectionContext(schema_graph=schema_graph, opg=opg)


__all__ = [
    "PreparedSeedProjection",
    "SeedProjectionContext",
    "compose_ocg_seed_schema_graph",
    "prepare_ocg_seed_projection",
    "resolve_ocg_seed_projection_context",
    "resolve_ocg_seed_schema_view",
    "schema_configs_by_id_from_schema_view",
]
