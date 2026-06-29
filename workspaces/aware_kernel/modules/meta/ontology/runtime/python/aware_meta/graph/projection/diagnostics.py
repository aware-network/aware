from __future__ import annotations

from collections.abc import Iterable, Mapping
from uuid import UUID

from aware_meta.semantic_diagnostics import MetaSemanticDiagnostic
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInvokeKind,
)


def collect_projection_completeness_diagnostics(
    *,
    source_graph: ObjectConfigGraph,
    object_config_graph: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    severity: str = "warning",
    source_path_by_code_id: Mapping[UUID, str] | None = None,
) -> tuple[MetaSemanticDiagnostic, ...]:
    del source_graph  # reserved for source/runtime mapping once diagnostics carry spans.
    source_paths = source_path_by_code_id or {}
    graphs = (object_config_graph, *tuple(external_graphs))
    concrete_classes = _concrete_class_configs_by_id(graphs)
    membership_by_class_id = _projection_membership_by_class_id(graphs)
    reachable_by_class_id = _projection_reachability_by_class_id(graphs)
    constructor_owner_by_function_id = _constructor_owner_by_function_id(graphs)
    diagnostics: list[MetaSemanticDiagnostic] = []

    for class_config_id, class_config in sorted(
        concrete_classes.items(),
        key=lambda item: _class_label(item[1]),
    ):
        if class_config_id not in membership_by_class_id:
            diagnostics.append(
                MetaSemanticDiagnostic(
                    severity=severity,
                    code=(
                        "aware_meta.completeness."
                        "projection_membership_missing"
                    ),
                    message=(
                        "ClassConfig is not a member of any "
                        "ObjectProjectionGraph: "
                        f"{_class_label(class_config)}"
                    ),
                    source_path=_source_path_for_class(
                        class_config=class_config,
                        source_path_by_code_id=source_paths,
                    ),
                )
            )
            continue
        if class_config_id not in reachable_by_class_id:
            diagnostics.append(
                MetaSemanticDiagnostic(
                    severity=severity,
                    code=(
                        "aware_meta.completeness."
                        "projection_node_unreachable"
                    ),
                    message=(
                        "ClassConfig is present in an ObjectProjectionGraph "
                        "but is not reachable from a projection root: "
                        f"{_class_label(class_config)}"
                    ),
                    source_path=_source_path_for_class(
                        class_config=class_config,
                        source_path_by_code_id=source_paths,
                    ),
                )
            )

    for class_config_id, class_config in sorted(
        concrete_classes.items(),
        key=lambda item: _class_label(item[1]),
    ):
        if not _has_constructor(class_config):
            continue
        if class_config_id in reachable_by_class_id:
            continue
        diagnostics.append(
            MetaSemanticDiagnostic(
                severity=severity,
                code=(
                    "aware_meta.completeness."
                    "constructor_projection_unreachable"
                ),
                message=(
                    "Constructor target class is not reachable from any "
                    "ObjectProjectionGraph root: "
                    f"{_class_label(class_config)}"
                ),
                source_path=_source_path_for_class(
                    class_config=class_config,
                    source_path_by_code_id=source_paths,
                ),
            )
        )
    diagnostics.extend(
        _constructor_path_diagnostics(
            object_config_graph=object_config_graph,
            external_graphs=tuple(external_graphs),
            concrete_classes=concrete_classes,
            constructor_owner_by_function_id=constructor_owner_by_function_id,
            severity=severity,
            source_path_by_code_id=source_paths,
        )
    )
    return tuple(diagnostics)


def _concrete_class_configs_by_id(
    graphs: Iterable[ObjectConfigGraph],
) -> dict[UUID, ClassConfig]:
    classes: dict[UUID, ClassConfig] = {}
    for graph in graphs:
        for node in graph.object_config_graph_nodes or []:
            if node.type != ObjectConfigGraphNodeType.class_:
                continue
            class_config = node.class_config
            if class_config is None:
                continue
            if class_config.value_mode == ClassValueMode.inline_value:
                continue
            classes.setdefault(class_config.id, class_config)
    return classes


def _projection_membership_by_class_id(
    graphs: Iterable[ObjectConfigGraph],
) -> dict[UUID, set[str]]:
    membership: dict[UUID, set[str]] = {}
    for graph in graphs:
        for opg in graph.object_projection_graphs or []:
            opg_name = opg.name or str(opg.id)
            for node in opg.object_projection_graph_nodes or []:
                membership.setdefault(node.class_config_id, set()).add(opg_name)
    return membership


def _projection_reachability_by_class_id(
    graphs: Iterable[ObjectConfigGraph],
) -> dict[UUID, set[str]]:
    reachable: dict[UUID, set[str]] = {}
    for graph in graphs:
        relationships = _relationships_by_id((graph, *tuple(g for g in graphs if g is not graph)))
        for opg in graph.object_projection_graphs or []:
            for class_config_id in _reachable_classes_for_opg(
                opg=opg,
                relationships_by_id=relationships,
            ):
                reachable.setdefault(class_config_id, set()).add(opg.name or str(opg.id))
    return reachable


def _constructor_path_diagnostics(
    *,
    object_config_graph: ObjectConfigGraph,
    external_graphs: tuple[ObjectConfigGraph, ...],
    concrete_classes: Mapping[UUID, ClassConfig],
    constructor_owner_by_function_id: Mapping[UUID, UUID],
    severity: str,
    source_path_by_code_id: Mapping[UUID, str],
) -> list[MetaSemanticDiagnostic]:
    current_package_class_ids = set(
        _concrete_class_configs_by_id((object_config_graph,)).keys()
    )
    relationships = _relationships_by_id((object_config_graph, *external_graphs))
    diagnostics: list[MetaSemanticDiagnostic] = []
    diagnosed_edges: set[tuple[UUID, UUID, UUID]] = set()
    for opg in object_config_graph.object_projection_graphs or []:
        reachable_edges = _reachable_edges_for_opg(
            opg=opg,
            relationships_by_id=relationships,
        )
        for parent_id, child_id, relationship in sorted(
            reachable_edges,
            key=lambda item: (
                _class_label(concrete_classes.get(item[0]))
                if concrete_classes.get(item[0]) is not None
                else str(item[0]),
                _class_label(concrete_classes.get(item[1]))
                if concrete_classes.get(item[1]) is not None
                else str(item[1]),
                _relationship_label(item[2]),
            ),
        ):
            if child_id not in current_package_class_ids:
                continue
            parent_class = concrete_classes.get(parent_id)
            child_class = concrete_classes.get(child_id)
            if parent_class is None or child_class is None:
                continue
            if not _has_constructor(child_class):
                continue
            edge_key = (parent_id, child_id, relationship.id)
            if edge_key in diagnosed_edges:
                continue
            if _class_functions_construct_child(
                parent_class=parent_class,
                child_class_id=child_id,
                constructor_owner_by_function_id=constructor_owner_by_function_id,
            ):
                continue
            diagnosed_edges.add(edge_key)
            diagnostics.append(
                MetaSemanticDiagnostic(
                    severity=severity,
                    code=(
                        "aware_meta.completeness."
                        "constructor_path_missing"
                    ),
                    message=(
                        "Projected relationship has no parent-owned "
                        "constructor path to materialize its child: "
                        f"{_class_label(parent_class)}::"
                        f"{_relationship_label(relationship)} -> "
                        f"{_class_label(child_class)}"
                    ),
                    source_path=_source_path_for_class(
                        class_config=parent_class,
                        source_path_by_code_id=source_path_by_code_id,
                    ),
                )
            )
    return diagnostics


def _reachable_classes_for_opg(
    *,
    opg: ObjectProjectionGraph,
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> set[UUID]:
    node_ids = {
        node.class_config_id
        for node in (opg.object_projection_graph_nodes or [])
        if node.class_config_id is not None
    }
    roots = {
        node.class_config_id
        for node in (opg.object_projection_graph_nodes or [])
        if node.is_root and node.class_config_id is not None
    }
    adjacency: dict[UUID, set[UUID]] = {}
    for edge in opg.object_projection_graph_edges or []:
        relationship = relationships_by_id.get(edge.class_config_relationship_id)
        if relationship is None:
            continue
        source_id = relationship.class_config_id
        target_id = relationship.target_class_config_id
        if source_id is None or target_id is None:
            continue
        traversal_direction = edge.traversal_direction
        if traversal_direction == ClassConfigRelationshipDirection.reverse:
            parent_id, child_id = target_id, source_id
        else:
            parent_id, child_id = source_id, target_id
        if parent_id not in node_ids or child_id not in node_ids:
            continue
        adjacency.setdefault(parent_id, set()).add(child_id)

    reachable: set[UUID] = set()
    stack = list(roots)
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        stack.extend(sorted(adjacency.get(current, ()), key=str))
    return reachable


def _reachable_edges_for_opg(
    *,
    opg: ObjectProjectionGraph,
    relationships_by_id: Mapping[UUID, ClassConfigRelationship],
) -> tuple[tuple[UUID, UUID, ClassConfigRelationship], ...]:
    node_ids = {
        node.class_config_id
        for node in (opg.object_projection_graph_nodes or [])
        if node.class_config_id is not None
    }
    roots = {
        node.class_config_id
        for node in (opg.object_projection_graph_nodes or [])
        if node.is_root and node.class_config_id is not None
    }
    adjacency: dict[UUID, list[tuple[UUID, ClassConfigRelationship]]] = {}
    for edge in opg.object_projection_graph_edges or []:
        relationship = relationships_by_id.get(edge.class_config_relationship_id)
        if relationship is None:
            continue
        source_id = relationship.class_config_id
        target_id = relationship.target_class_config_id
        if source_id is None or target_id is None:
            continue
        if edge.traversal_direction == ClassConfigRelationshipDirection.reverse:
            parent_id, child_id = target_id, source_id
        else:
            parent_id, child_id = source_id, target_id
        if parent_id not in node_ids or child_id not in node_ids:
            continue
        adjacency.setdefault(parent_id, []).append((child_id, relationship))

    reachable_edges: list[tuple[UUID, UUID, ClassConfigRelationship]] = []
    reachable_edge_ids: set[tuple[UUID, UUID, UUID]] = set()
    reachable_nodes: set[UUID] = set()
    stack = list(roots)
    while stack:
        current = stack.pop()
        if current in reachable_nodes:
            continue
        reachable_nodes.add(current)
        for child_id, relationship in sorted(
            adjacency.get(current, ()),
            key=lambda item: (str(item[0]), str(item[1].id)),
        ):
            edge_key = (current, child_id, relationship.id)
            if edge_key not in reachable_edge_ids:
                reachable_edge_ids.add(edge_key)
                reachable_edges.append((current, child_id, relationship))
            stack.append(child_id)
    return tuple(reachable_edges)


def _relationships_by_id(
    graphs: Iterable[ObjectConfigGraph],
) -> dict[UUID, ClassConfigRelationship]:
    relationships: dict[UUID, ClassConfigRelationship] = {}
    for graph in graphs:
        for node in graph.object_config_graph_nodes or []:
            rel = node.class_config_relationship
            if node.type == ObjectConfigGraphNodeType.relationship and rel is not None:
                relationships.setdefault(rel.id, rel)
        for node in graph.object_config_graph_nodes or []:
            class_config = node.class_config
            if node.type != ObjectConfigGraphNodeType.class_ or class_config is None:
                continue
            for rel in class_config.class_config_relationships or []:
                relationships.setdefault(rel.id, rel)
        for ocg_rel in graph.object_config_graph_relationships or []:
            for rel in ocg_rel.class_config_relationships or []:
                relationships.setdefault(rel.id, rel)
    return relationships


def _has_constructor(class_config: ClassConfig) -> bool:
    return any(
        bool(function_link.is_constructor)
        for function_link in (class_config.class_config_function_configs or [])
    )


def _constructor_owner_by_function_id(
    graphs: Iterable[ObjectConfigGraph],
) -> dict[UUID, UUID]:
    constructor_owner: dict[UUID, UUID] = {}
    for class_config in _concrete_class_configs_by_id(graphs).values():
        for function_link in class_config.class_config_function_configs or []:
            function_config_id = function_link.function_config_id
            if (
                not function_link.is_constructor
                or function_config_id is None
            ):
                continue
            constructor_owner.setdefault(function_config_id, class_config.id)
    return constructor_owner


def _class_functions_construct_child(
    *,
    parent_class: ClassConfig,
    child_class_id: UUID,
    constructor_owner_by_function_id: Mapping[UUID, UUID],
) -> bool:
    for function_link in parent_class.class_config_function_configs or []:
        function_config = function_link.function_config
        if function_config is None:
            continue
        if child_class_id in _constructed_class_ids(
            function_config=function_config,
            constructor_owner_by_function_id=constructor_owner_by_function_id,
        ):
            return True
    return False


def _constructed_class_ids(
    *,
    function_config: FunctionConfig,
    constructor_owner_by_function_id: Mapping[UUID, UUID],
) -> set[UUID]:
    function_impl = function_config.function_impl
    if function_impl is None:
        return set()
    constructed: set[UUID] = set()
    for instruction in function_impl.instructions or []:
        construct_instruction = instruction.instruction_construct
        if construct_instruction is not None:
            constructed.add(construct_instruction.target_class_config_id)
        invoke_instruction = instruction.instruction_invoke
        if invoke_instruction is None:
            continue
        if invoke_instruction.kind != FunctionImplInvokeKind.construct:
            continue
        target_owner_id = constructor_owner_by_function_id.get(
            invoke_instruction.target_function_config_id
        )
        if target_owner_id is not None:
            constructed.add(target_owner_id)
    return constructed


def _source_path_for_class(
    *,
    class_config: ClassConfig,
    source_path_by_code_id: Mapping[UUID, str],
) -> str | None:
    code_section_class = getattr(class_config, "code_section_class", None)
    code_section = getattr(code_section_class, "code_section", None)
    code_id = getattr(code_section, "code_id", None)
    if not isinstance(code_id, UUID):
        return None
    return source_path_by_code_id.get(code_id)


def _class_label(class_config: ClassConfig) -> str:
    if class_config is None:
        return ""
    return (class_config.class_fqn or class_config.name or str(class_config.id)).strip()


def _relationship_label(relationship: ClassConfigRelationship) -> str:
    return (
        relationship.relationship_key
        or relationship.relationship_type
        or str(relationship.id)
    ).strip()


__all__ = [
    "collect_projection_completeness_diagnostics",
]
