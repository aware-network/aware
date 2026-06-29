from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from collections.abc import Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta.graph.config.handlers import (
    build_object_config_graph_overlays_from_annotations,
)

from .models import ApiServiceProtocolPlan


def build_api_service_protocol_render_graph(
    *,
    plan: ApiServiceProtocolPlan,
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> ObjectConfigGraph:
    class_nodes_by_id, enum_nodes_by_id = _index_accessible_nodes(
        accessible_graphs=accessible_graphs
    )
    selected_nodes: dict[UUID, ObjectConfigGraphNode] = {}

    for class_ref in _collect_root_class_refs(plan=plan):
        root_node = _resolve_class_node(
            class_ref=class_ref, class_nodes_by_id=class_nodes_by_id
        )
        _collect_class_node(
            node=root_node,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )

    graph_function_python_refs = _collect_graph_function_python_refs(plan=plan)
    for graph_function_python_ref in graph_function_python_refs:
        class_ref = _graph_function_class_ref(
            graph_function_python_ref=graph_function_python_ref
        )
        target_node = _resolve_class_node(
            class_ref=class_ref, class_nodes_by_id=class_nodes_by_id
        )
        _collect_class_node(
            node=target_node,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )

    graph_digest = _build_graph_digest(
        plan=plan,
        selected_nodes=selected_nodes,
        graph_function_python_refs=graph_function_python_refs,
    )
    graph_id = uuid5(
        NAMESPACE_URL, f"aware.api.service_protocol.render_graph:{graph_digest}"
    )
    copied_nodes = _copy_selected_nodes(
        graph_id=graph_id,
        selected_nodes=selected_nodes,
    )
    graph = ObjectConfigGraph(
        id=graph_id,
        name=_build_graph_name(plan=plan),
        description=f"Synthetic service protocol package render graph for {plan.package_name}.",
        hash=f"sha256:{graph_digest}",
        fqn_prefix=plan.fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=copied_nodes,
    )
    graph.object_config_graph_overlays = (
        build_object_config_graph_overlays_from_annotations(graph)
    )
    return graph


def _index_accessible_nodes(
    *,
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> tuple[dict[UUID, ObjectConfigGraphNode], dict[UUID, ObjectConfigGraphNode]]:
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode] = {}
    enum_nodes_by_id: dict[UUID, ObjectConfigGraphNode] = {}
    for graph in accessible_graphs:
        for node in graph.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
            ):
                class_nodes_by_id[node.class_config.id] = node
                continue
            if (
                node.type == ObjectConfigGraphNodeType.enum
                and node.enum_config is not None
            ):
                enum_nodes_by_id[node.enum_config.id] = node
    return class_nodes_by_id, enum_nodes_by_id


def _collect_root_class_refs(*, plan: ApiServiceProtocolPlan) -> tuple[str, ...]:
    refs: set[str] = set()
    for api in plan.apis:
        for capability in api.capabilities:
            for endpoint in capability.endpoints:
                refs.add(endpoint.request.class_ref)
                if endpoint.response is not None:
                    refs.add(endpoint.response.class_ref)
                if endpoint.stream is not None:
                    for event in endpoint.stream.events:
                        refs.add(event.class_ref)
    return tuple(sorted(refs, key=str.casefold))


def _collect_graph_function_python_refs(
    *, plan: ApiServiceProtocolPlan
) -> tuple[str, ...]:
    targets: set[str] = set()
    for api in plan.apis:
        for capability in api.capabilities:
            for endpoint in capability.endpoints:
                for binding in endpoint.fulfillment_bindings:
                    targets.add(binding.graph_function_python_ref)
    return tuple(sorted(targets, key=str.casefold))


def _graph_function_class_ref(*, graph_function_python_ref: str) -> str:
    token = graph_function_python_ref.strip()
    if not token or "." not in token:
        raise RuntimeError(
            "Invalid service protocol package render graph input: graph function target must include a class path "
            + f"(got {graph_function_python_ref!r})"
        )
    return token.rsplit(".", 1)[0]


def _resolve_class_node(
    *,
    class_ref: str,
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> ObjectConfigGraphNode:
    matches = tuple(
        node
        for node in class_nodes_by_id.values()
        if node.class_config is not None
        and _class_matches(class_config=node.class_config, target=class_ref)
    )
    unique_matches = _unique_nodes(matches=matches)
    if not unique_matches:
        raise RuntimeError(
            f"Could not resolve service protocol package render class ref {class_ref!r}"
        )
    if len(unique_matches) > 1:
        raise RuntimeError(
            f"Ambiguous service protocol package render class ref {class_ref!r}"
        )
    return next(iter(unique_matches))


def _collect_class_node(
    *,
    node: ObjectConfigGraphNode,
    selected_nodes: dict[UUID, ObjectConfigGraphNode],
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
    enum_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> None:
    if node.id in selected_nodes:
        return
    selected_nodes[node.id] = node
    class_config = node.class_config
    if class_config is None:
        raise RuntimeError(
            "Invalid service protocol package render graph input: class node is missing class_config"
        )
    for link in class_config.class_config_attribute_configs:
        descriptor = link.attribute_config.type_descriptor
        _collect_descriptor_dependencies(
            descriptor=descriptor,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )
    for function_link in class_config.class_config_function_configs:
        function_config = function_link.function_config
        if function_config is None:
            continue
        _collect_function_dependencies(
            function_config=function_config,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )


def _collect_function_dependencies(
    *,
    function_config: FunctionConfig,
    selected_nodes: dict[UUID, ObjectConfigGraphNode],
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
    enum_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> None:
    for attribute_link in function_config.function_config_attribute_configs:
        attribute_config = attribute_link.attribute_config
        if attribute_config is None:
            continue
        _collect_descriptor_dependencies(
            descriptor=attribute_config.type_descriptor,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )


def _collect_descriptor_dependencies(
    *,
    descriptor: AttributeTypeDescriptor,
    selected_nodes: dict[UUID, ObjectConfigGraphNode],
    class_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
    enum_nodes_by_id: dict[UUID, ObjectConfigGraphNode],
) -> None:
    if (
        descriptor.kind == AttributeTypeDescriptorKind.class_
        and descriptor.class_config_id is not None
    ):
        node = class_nodes_by_id.get(descriptor.class_config_id)
        if node is None:
            raise RuntimeError(
                f"Could not resolve service protocol package render nested class id {descriptor.class_config_id}"
            )
        _collect_class_node(
            node=node,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )
    elif (
        descriptor.kind == AttributeTypeDescriptorKind.enum
        and descriptor.enum_config_id is not None
    ):
        node = enum_nodes_by_id.get(descriptor.enum_config_id)
        if node is None:
            raise RuntimeError(
                f"Could not resolve service protocol package render enum id {descriptor.enum_config_id}"
            )
        selected_nodes.setdefault(node.id, node)

    for link in descriptor.child_links:
        child = link.child
        if child is not None:
            _collect_descriptor_dependencies(
                descriptor=child,
                selected_nodes=selected_nodes,
                class_nodes_by_id=class_nodes_by_id,
                enum_nodes_by_id=enum_nodes_by_id,
            )


def _copy_selected_nodes(
    *,
    graph_id: UUID,
    selected_nodes: dict[UUID, ObjectConfigGraphNode],
) -> list[ObjectConfigGraphNode]:
    copied_nodes: list[ObjectConfigGraphNode] = []
    for node in sorted(
        selected_nodes.values(),
        key=lambda item: (item.node_key.casefold(), item.type.value, str(item.id)),
    ):
        copied = deepcopy(node)
        copied.object_config_graph_id = graph_id
        if copied.class_config is not None:
            copied.class_config.object_config_graph_node_id = copied.id
        if copied.enum_config is not None:
            copied.enum_config.object_config_graph_node_id = copied.id
        copied_nodes.append(copied)
    return copied_nodes


def _build_graph_name(*, plan: ApiServiceProtocolPlan) -> str:
    return f"{plan.package_name.replace('-', '_')}_service_protocol_render"


def _build_graph_digest(
    *,
    plan: ApiServiceProtocolPlan,
    selected_nodes: dict[UUID, ObjectConfigGraphNode],
    graph_function_python_refs: tuple[str, ...],
) -> str:
    payload = {
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "graph_function_python_refs": list(graph_function_python_refs),
        "node_keys": [
            _node_identity_key(node=node)
            for node in sorted(
                selected_nodes.values(),
                key=lambda item: (
                    item.node_key.casefold(),
                    item.type.value,
                    str(item.id),
                ),
            )
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256(canonical).hexdigest()


def _node_identity_key(*, node: ObjectConfigGraphNode) -> str:
    if node.class_config is not None:
        return f"class:{node.class_config.class_fqn}"
    if node.enum_config is not None:
        return f"enum:{node.enum_config.enum_fqn}"
    return f"{node.type.value}:{node.node_key}"


def _unique_nodes(
    *, matches: Sequence[ObjectConfigGraphNode]
) -> tuple[ObjectConfigGraphNode, ...]:
    unique_by_key: dict[str, ObjectConfigGraphNode] = {}
    for node in matches:
        unique_by_key[_node_identity_key(node=node)] = node
    return tuple(unique_by_key[key] for key in sorted(unique_by_key, key=str.casefold))


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


def _normalize_token(value: str) -> str:
    return (value or "").strip().casefold()


def _leaf_token(value: str) -> str:
    normalized = _normalize_token(value)
    if "." not in normalized:
        return normalized
    return normalized.rsplit(".", 1)[-1]


def _normalized_variants(value: str) -> set[str]:
    normalized = _normalize_token(value)
    if not normalized:
        return set()

    variants = {normalized}
    parts = [part for part in normalized.split(".") if part]
    if "default" in parts[1:-1]:
        variants.add(".".join(part for part in parts if part != "default"))
    return {variant for variant in variants if variant}


__all__ = ["build_api_service_protocol_render_graph"]
