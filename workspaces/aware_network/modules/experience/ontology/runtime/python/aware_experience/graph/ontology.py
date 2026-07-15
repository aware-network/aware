from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from aware_experience.compiler.models import (
    ExperienceGraphOwnership,
    ExperienceProjectionExperienceOwnership,
)


@dataclass(frozen=True, slots=True)
class ExperienceGraphOntologyGraphOperation:
    graph_name: str
    experience: str
    root_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceGraphOntologyIdentityOperation:
    graph_name: str
    experience: str
    ref: str
    node_name: str
    identity_key: str
    key: str
    is_root: bool
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceGraphOntologyNodeIdentityEdgeOperation:
    graph_name: str
    experience: str
    parent_ref: str
    child_ref: str
    parent_key: str
    child_key: str
    key: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceGraphOntologyGraphIdentityEdgeOperation:
    graph_name: str
    experience: str
    parent_ref: str
    child_ref: str
    parent_key: str
    child_key: str
    key: str
    source_path: str


@dataclass(frozen=True, slots=True)
class ExperienceGraphOntologyPlan:
    graph: ExperienceGraphOntologyGraphOperation
    identities: tuple[ExperienceGraphOntologyIdentityOperation, ...]
    node_identity_edges: tuple[ExperienceGraphOntologyNodeIdentityEdgeOperation, ...]
    graph_identity_edges: tuple[ExperienceGraphOntologyGraphIdentityEdgeOperation, ...]


def build_graph_ontology_plans(
    *,
    projection_experience_ownership: tuple[
        ExperienceProjectionExperienceOwnership, ...
    ],
    graph_ownership: tuple[ExperienceGraphOwnership, ...],
) -> tuple[ExperienceGraphOntologyPlan, ...]:
    identity_catalog = _build_identity_catalog(projection_experience_ownership)
    plans = tuple(
        _build_graph_plan(graph=graph, identity_catalog=identity_catalog)
        for graph in graph_ownership
    )
    return tuple(
        sorted(
            plans,
            key=lambda item: (
                item.graph.experience,
                item.graph.graph_name,
                item.graph.source_path,
            ),
        )
    )


def encode_graph_ontology_plan_payload(
    *,
    plans: tuple[ExperienceGraphOntologyPlan, ...],
) -> list[dict[str, object]]:
    return [
        {
            "graph": {
                "name": plan.graph.graph_name,
                "experience": plan.graph.experience,
                "root_ref": plan.graph.root_ref,
                "source_path": plan.graph.source_path,
            },
            "identities": [
                {
                    "ref": identity.ref,
                    "node_name": identity.node_name,
                    "identity_key": identity.identity_key,
                    "key": identity.key,
                    "is_root": identity.is_root,
                    "source_path": identity.source_path,
                }
                for identity in plan.identities
            ],
            "node_identity_edges": [
                {
                    "parent_ref": edge.parent_ref,
                    "child_ref": edge.child_ref,
                    "parent_key": edge.parent_key,
                    "child_key": edge.child_key,
                    "key": edge.key,
                    "source_path": edge.source_path,
                }
                for edge in plan.node_identity_edges
            ],
            "graph_identity_edges": [
                {
                    "parent_ref": edge.parent_ref,
                    "child_ref": edge.child_ref,
                    "parent_key": edge.parent_key,
                    "child_key": edge.child_key,
                    "key": edge.key,
                    "source_path": edge.source_path,
                }
                for edge in plan.graph_identity_edges
            ],
        }
        for plan in plans
    ]


def decode_graph_ontology_plan_payload(
    *,
    payload: Sequence[object],
) -> tuple[ExperienceGraphOntologyPlan, ...]:
    plans: list[ExperienceGraphOntologyPlan] = []
    for index, plan_obj in enumerate(payload):
        plan_row = _expect_mapping(plan_obj, field_name=f"graph_ontology[{index}]")
        plans.append(_decode_graph_ontology_plan_row(row=plan_row, row_index=index))
    return tuple(plans)


def _decode_graph_ontology_plan_row(
    *,
    row: Mapping[str, object],
    row_index: int,
) -> ExperienceGraphOntologyPlan:
    graph_row = _expect_mapping(
        row.get("graph"), field_name=f"graph_ontology[{row_index}].graph"
    )
    graph_name = _required_str_token(
        graph_row.get("name"),
        field_name=f"graph_ontology[{row_index}].graph.name",
    )
    experience = _required_str_token(
        graph_row.get("experience"),
        field_name=f"graph_ontology[{row_index}].graph.experience",
    )
    root_ref = _required_str_token(
        graph_row.get("root_ref"),
        field_name=f"graph_ontology[{row_index}].graph.root_ref",
    )
    graph_source_path = _required_str_token(
        graph_row.get("source_path"),
        field_name=f"graph_ontology[{row_index}].graph.source_path",
    )

    identity_rows = _expect_list(
        row.get("identities"), field_name=f"graph_ontology[{row_index}].identities"
    )
    if not identity_rows:
        raise ValueError(
            f"Invalid experience compile plan: graph_ontology[{row_index}].identities requires entries"
        )

    identities: list[ExperienceGraphOntologyIdentityOperation] = []
    seen_refs: set[str] = set()
    root_count = 0
    for identity_index, identity_obj in enumerate(identity_rows):
        identity_row = _expect_mapping(
            identity_obj,
            field_name=f"graph_ontology[{row_index}].identities[{identity_index}]",
        )
        ref = _required_str_token(
            identity_row.get("ref"),
            field_name=f"graph_ontology[{row_index}].identities[{identity_index}].ref",
        )
        node_name = _required_str_token(
            identity_row.get("node_name"),
            field_name=f"graph_ontology[{row_index}].identities[{identity_index}].node_name",
        )
        identity_key = _required_str_token(
            identity_row.get("identity_key"),
            field_name=f"graph_ontology[{row_index}].identities[{identity_index}].identity_key",
        )
        key = _required_str_token(
            identity_row.get("key"),
            field_name=f"graph_ontology[{row_index}].identities[{identity_index}].key",
        )
        is_root = _expect_bool(
            identity_row.get("is_root"),
            field_name=f"graph_ontology[{row_index}].identities[{identity_index}].is_root",
        )
        source_path = _required_str_token(
            identity_row.get("source_path"),
            field_name=f"graph_ontology[{row_index}].identities[{identity_index}].source_path",
        )

        if ref in seen_refs:
            raise ValueError(
                "Invalid experience compile plan: duplicate graph identity ref "
                + f"{ref!r} at graph_ontology[{row_index}]"
            )
        seen_refs.add(ref)

        if ref != identity_key:
            raise ValueError(
                "Invalid experience compile plan: graph identity tuple mismatch "
                + f"(ref={ref!r}, node_name={node_name!r}, identity_key={identity_key!r})"
            )

        if is_root:
            root_count += 1

        identities.append(
            ExperienceGraphOntologyIdentityOperation(
                graph_name=graph_name,
                experience=experience,
                ref=ref,
                node_name=node_name,
                identity_key=identity_key,
                key=key,
                is_root=is_root,
                source_path=source_path,
            )
        )

    if root_ref not in seen_refs:
        raise ValueError(
            "Invalid experience compile plan: graph root ref is missing from graph identities "
            + f"(graph={graph_name!r}, root_ref={root_ref!r})"
        )
    if root_count != 1:
        raise ValueError(
            "Invalid experience compile plan: graph identities require exactly one root entry "
            + f"(graph={graph_name!r}, roots={root_count})"
        )
    root_identity_ref = next(
        identity.ref for identity in identities if identity.is_root
    )
    if root_identity_ref != root_ref:
        raise ValueError(
            "Invalid experience compile plan: graph root ref must match root identity entry "
            + f"(graph={graph_name!r}, root_ref={root_ref!r}, root_identity_ref={root_identity_ref!r})"
        )

    identity_refs = frozenset(seen_refs)
    node_identity_edge_rows = _expect_list(
        row.get("node_identity_edges"),
        field_name=f"graph_ontology[{row_index}].node_identity_edges",
    )
    node_identity_edges = tuple(
        _decode_node_identity_edge_operation(
            edge_obj=edge_obj,
            row_index=row_index,
            edge_index=edge_index,
            graph_name=graph_name,
            experience=experience,
            identity_refs=identity_refs,
        )
        for edge_index, edge_obj in enumerate(node_identity_edge_rows)
    )

    graph_identity_edge_rows = _expect_list(
        row.get("graph_identity_edges"),
        field_name=f"graph_ontology[{row_index}].graph_identity_edges",
    )
    graph_identity_edges = tuple(
        _decode_graph_identity_edge_operation(
            edge_obj=edge_obj,
            row_index=row_index,
            edge_index=edge_index,
            graph_name=graph_name,
            experience=experience,
            identity_refs=identity_refs,
        )
        for edge_index, edge_obj in enumerate(graph_identity_edge_rows)
    )

    return ExperienceGraphOntologyPlan(
        graph=ExperienceGraphOntologyGraphOperation(
            graph_name=graph_name,
            experience=experience,
            root_ref=root_ref,
            source_path=graph_source_path,
        ),
        identities=tuple(identities),
        node_identity_edges=node_identity_edges,
        graph_identity_edges=graph_identity_edges,
    )


def _decode_node_identity_edge_operation(
    *,
    edge_obj: object,
    row_index: int,
    edge_index: int,
    graph_name: str,
    experience: str,
    identity_refs: frozenset[str],
) -> ExperienceGraphOntologyNodeIdentityEdgeOperation:
    edge_row = _expect_mapping(
        edge_obj,
        field_name=f"graph_ontology[{row_index}].node_identity_edges[{edge_index}]",
    )
    parent_ref = _required_str_token(
        edge_row.get("parent_ref"),
        field_name=f"graph_ontology[{row_index}].node_identity_edges[{edge_index}].parent_ref",
    )
    child_ref = _required_str_token(
        edge_row.get("child_ref"),
        field_name=f"graph_ontology[{row_index}].node_identity_edges[{edge_index}].child_ref",
    )
    parent_key = _required_str_token(
        edge_row.get("parent_key"),
        field_name=f"graph_ontology[{row_index}].node_identity_edges[{edge_index}].parent_key",
    )
    child_key = _required_str_token(
        edge_row.get("child_key"),
        field_name=f"graph_ontology[{row_index}].node_identity_edges[{edge_index}].child_key",
    )
    key = _required_str_token(
        edge_row.get("key"),
        field_name=f"graph_ontology[{row_index}].node_identity_edges[{edge_index}].key",
    )
    source_path = _required_str_token(
        edge_row.get("source_path"),
        field_name=f"graph_ontology[{row_index}].node_identity_edges[{edge_index}].source_path",
    )
    _assert_edge_refs_known(
        parent_ref=parent_ref,
        child_ref=child_ref,
        identity_refs=identity_refs,
        graph_name=graph_name,
        row_index=row_index,
        edge_kind="node_identity_edges",
    )
    return ExperienceGraphOntologyNodeIdentityEdgeOperation(
        graph_name=graph_name,
        experience=experience,
        parent_ref=parent_ref,
        child_ref=child_ref,
        parent_key=parent_key,
        child_key=child_key,
        key=key,
        source_path=source_path,
    )


def _decode_graph_identity_edge_operation(
    *,
    edge_obj: object,
    row_index: int,
    edge_index: int,
    graph_name: str,
    experience: str,
    identity_refs: frozenset[str],
) -> ExperienceGraphOntologyGraphIdentityEdgeOperation:
    edge_row = _expect_mapping(
        edge_obj,
        field_name=f"graph_ontology[{row_index}].graph_identity_edges[{edge_index}]",
    )
    parent_ref = _required_str_token(
        edge_row.get("parent_ref"),
        field_name=f"graph_ontology[{row_index}].graph_identity_edges[{edge_index}].parent_ref",
    )
    child_ref = _required_str_token(
        edge_row.get("child_ref"),
        field_name=f"graph_ontology[{row_index}].graph_identity_edges[{edge_index}].child_ref",
    )
    parent_key = _required_str_token(
        edge_row.get("parent_key"),
        field_name=f"graph_ontology[{row_index}].graph_identity_edges[{edge_index}].parent_key",
    )
    child_key = _required_str_token(
        edge_row.get("child_key"),
        field_name=f"graph_ontology[{row_index}].graph_identity_edges[{edge_index}].child_key",
    )
    key = _required_str_token(
        edge_row.get("key"),
        field_name=f"graph_ontology[{row_index}].graph_identity_edges[{edge_index}].key",
    )
    source_path = _required_str_token(
        edge_row.get("source_path"),
        field_name=f"graph_ontology[{row_index}].graph_identity_edges[{edge_index}].source_path",
    )
    _assert_edge_refs_known(
        parent_ref=parent_ref,
        child_ref=child_ref,
        identity_refs=identity_refs,
        graph_name=graph_name,
        row_index=row_index,
        edge_kind="graph_identity_edges",
    )
    return ExperienceGraphOntologyGraphIdentityEdgeOperation(
        graph_name=graph_name,
        experience=experience,
        parent_ref=parent_ref,
        child_ref=child_ref,
        parent_key=parent_key,
        child_key=child_key,
        key=key,
        source_path=source_path,
    )


def _assert_edge_refs_known(
    *,
    parent_ref: str,
    child_ref: str,
    identity_refs: frozenset[str],
    graph_name: str,
    row_index: int,
    edge_kind: str,
) -> None:
    if parent_ref in identity_refs and child_ref in identity_refs:
        return
    raise ValueError(
        "Invalid experience compile plan: graph identity edge refs must exist in graph identities "
        + f"(graph={graph_name!r}, row={row_index}, edge_kind={edge_kind!r}, "
        + f"parent_ref={parent_ref!r}, child_ref={child_ref!r})"
    )


def _expect_list(value: object, *, field_name: str) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    raise ValueError(f"Invalid experience compile plan: {field_name} must be a list")


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise ValueError(f"Invalid experience compile plan: {field_name} must be an object")


def _required_str_token(value: object, *, field_name: str) -> str:
    if isinstance(value, str):
        token = value.strip()
        if token:
            return token
    raise ValueError(f"Invalid experience compile plan: {field_name} is required")


def _expect_bool(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"Invalid experience compile plan: {field_name} must be a boolean")


def _build_graph_plan(
    *,
    graph: ExperienceGraphOwnership,
    identity_catalog: dict[str, dict[str, str]],
) -> ExperienceGraphOntologyPlan:
    experience_catalog = identity_catalog.get(graph.experience)
    if experience_catalog is None:
        raise ValueError(
            f"Graph ontology mapping requires known experience declaration: {graph.experience!r} ({graph.source_path})"
        )

    refs_seen: set[str] = {graph.root}
    adjacency: dict[str, set[str]] = {}
    sorted_edges = tuple(
        sorted(
            graph.edges, key=lambda item: (item.parent, item.child, item.source_path)
        )
    )
    for edge in sorted_edges:
        refs_seen.add(edge.parent)
        refs_seen.add(edge.child)
        adjacency.setdefault(edge.parent, set()).add(edge.child)

    for ref in sorted(refs_seen):
        _assert_ref_known(
            ref=ref, experience_catalog=experience_catalog, context=graph.name
        )

    root_identity_key = graph.root
    key_by_ref: dict[str, str] = {graph.root: root_identity_key}
    queue: list[str] = [graph.root]
    traversal_order: list[str] = [graph.root]
    while queue:
        parent_ref = queue.pop(0)
        parent_key = key_by_ref[parent_ref]
        for child_ref in sorted(adjacency.get(parent_ref, ())):
            child_identity_key = child_ref
            child_key = (
                f"{parent_key}.{child_identity_key}"
                if parent_key
                else child_identity_key
            )
            existing_key = key_by_ref.get(child_ref)
            if existing_key is None:
                key_by_ref[child_ref] = child_key
                queue.append(child_ref)
                traversal_order.append(child_ref)
                continue
            if existing_key != child_key:
                raise ValueError(
                    f"Graph ontology mapping key conflict for {child_ref!r}: {existing_key!r} vs {child_key!r}"
                )

    unresolved_refs = sorted(ref for ref in refs_seen if ref not in key_by_ref)
    if unresolved_refs:
        raise ValueError(
            "Graph ontology mapping requires root-connected refs only: "
            + f"graph={graph.name!r} unresolved={unresolved_refs}"
        )

    identities = tuple(
        ExperienceGraphOntologyIdentityOperation(
            graph_name=graph.name,
            experience=graph.experience,
            ref=ref,
            node_name=experience_catalog[ref],
            identity_key=ref,
            key=key_by_ref[ref],
            is_root=ref == graph.root,
            source_path=graph.source_path,
        )
        for ref in traversal_order
    )

    node_identity_edges = tuple(
        ExperienceGraphOntologyNodeIdentityEdgeOperation(
            graph_name=graph.name,
            experience=graph.experience,
            parent_ref=edge.parent,
            child_ref=edge.child,
            parent_key=key_by_ref[edge.parent],
            child_key=key_by_ref[edge.child],
            key=key_by_ref[edge.child],
            source_path=edge.source_path,
        )
        for edge in sorted_edges
    )
    graph_identity_edges = tuple(
        ExperienceGraphOntologyGraphIdentityEdgeOperation(
            graph_name=graph.name,
            experience=graph.experience,
            parent_ref=edge.parent,
            child_ref=edge.child,
            parent_key=key_by_ref[edge.parent],
            child_key=key_by_ref[edge.child],
            key=key_by_ref[edge.child],
            source_path=edge.source_path,
        )
        for edge in sorted_edges
    )
    return ExperienceGraphOntologyPlan(
        graph=ExperienceGraphOntologyGraphOperation(
            graph_name=graph.name,
            experience=graph.experience,
            root_ref=graph.root,
            source_path=graph.source_path,
        ),
        identities=identities,
        node_identity_edges=node_identity_edges,
        graph_identity_edges=graph_identity_edges,
    )


def _build_identity_catalog(
    projection_experience_ownership: tuple[
        ExperienceProjectionExperienceOwnership, ...
    ],
) -> dict[str, dict[str, str]]:
    catalog: dict[str, dict[str, str]] = {}
    for ownership in projection_experience_ownership:
        identities: dict[str, str] = {}
        for node in ownership.nodes:
            node_name = (node.name or "").strip()
            if not node_name:
                continue
            for identity in node.identities:
                identity_key = (identity.key or "").strip()
                if not identity_key:
                    continue
                prior_node = identities.get(identity_key)
                if prior_node is not None and prior_node != node_name:
                    raise ValueError(
                        "Graph ontology mapping requires node identity refs to be unique within "
                        + f"one experience: experience={ownership.name!r} identity={identity_key!r}"
                    )
                identities[identity_key] = node_name
        catalog[ownership.name] = identities
    return catalog


def _assert_ref_known(
    *,
    ref: str,
    experience_catalog: dict[str, str],
    context: str,
) -> None:
    if ref not in experience_catalog:
        raise ValueError(
            f"Graph ontology mapping requires known node identity ref {ref!r} (graph={context!r})"
        )


__all__ = [
    "ExperienceGraphOntologyGraphOperation",
    "ExperienceGraphOntologyIdentityOperation",
    "ExperienceGraphOntologyNodeIdentityEdgeOperation",
    "ExperienceGraphOntologyGraphIdentityEdgeOperation",
    "ExperienceGraphOntologyPlan",
    "build_graph_ontology_plans",
    "decode_graph_ontology_plan_payload",
    "encode_graph_ontology_plan_payload",
]
