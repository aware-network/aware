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
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta.graph.config.handlers import (
    build_object_config_graph_overlays_from_annotations,
)

from .models import ApiPublicPackagePlan


def build_api_public_package_dto_graph(
    *,
    plan: ApiPublicPackagePlan,
    accessible_graphs: Sequence[ObjectConfigGraph],
    root_class_refs: Sequence[str] | None = None,
) -> ObjectConfigGraph:
    class_nodes_by_id, enum_nodes_by_id = _index_accessible_nodes(
        accessible_graphs=accessible_graphs
    )
    selected_nodes: dict[UUID, ObjectConfigGraphNode] = {}

    selected_root_class_refs = (
        _collect_root_class_refs(plan=plan)
        if root_class_refs is None
        else tuple(
            sorted(
                {
                    class_ref.strip()
                    for class_ref in root_class_refs
                    if class_ref.strip()
                },
                key=str.casefold,
            )
        )
    )
    for class_ref in selected_root_class_refs:
        root_node = _resolve_class_node(
            class_ref=class_ref, class_nodes_by_id=class_nodes_by_id
        )
        _collect_class_node(
            node=root_node,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )

    selected_annotations = _collect_graph_annotations(
        accessible_graphs=accessible_graphs,
        selected_nodes=selected_nodes,
    )
    graph_digest = _build_graph_digest(
        plan=plan,
        selected_nodes=selected_nodes,
        selected_annotations=selected_annotations,
    )
    graph_id = uuid5(
        NAMESPACE_URL, f"aware.api.public_package.dto_graph:{graph_digest}"
    )
    copied_nodes = _copy_selected_nodes(
        graph_id=graph_id,
        selected_nodes=selected_nodes,
    )
    copied_annotations = _copy_selected_annotations(
        graph_id=graph_id,
        selected_annotations=selected_annotations,
    )
    graph = ObjectConfigGraph(
        id=graph_id,
        name=_build_graph_name(plan=plan),
        description=f"Synthetic public API package DTO graph for {plan.package_name}.",
        hash=f"sha256:{graph_digest}",
        fqn_prefix=plan.fqn_prefix,
        language=CodeLanguage.aware,
        object_config_graph_nodes=copied_nodes,
        object_config_graph_annotations=copied_annotations,
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


def _collect_root_class_refs(*, plan: ApiPublicPackagePlan) -> tuple[str, ...]:
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
            f"Could not resolve public API package DTO class ref {class_ref!r}"
        )
    if len(unique_matches) > 1:
        raise RuntimeError(f"Ambiguous public API package DTO class ref {class_ref!r}")
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
            "Invalid public API package DTO graph input: class node is missing class_config"
        )
    if class_config.parent_class_id is not None:
        parent_node = class_nodes_by_id.get(class_config.parent_class_id)
        if parent_node is None:
            raise RuntimeError(
                f"Could not resolve public API package DTO parent class id {class_config.parent_class_id} "
                + f"for {class_config.class_fqn}"
            )
        _collect_class_node(
            node=parent_node,
            selected_nodes=selected_nodes,
            class_nodes_by_id=class_nodes_by_id,
            enum_nodes_by_id=enum_nodes_by_id,
        )
    for link in class_config.class_config_attribute_configs:
        descriptor = link.attribute_config.type_descriptor
        _collect_descriptor_dependencies(
            descriptor=descriptor,
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
                f"Could not resolve public API package DTO nested class id {descriptor.class_config_id}"
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
                f"Could not resolve public API package DTO enum id {descriptor.enum_config_id}"
            )
        _ = selected_nodes.setdefault(node.id, node)

    for link in descriptor.child_links:
        _collect_descriptor_dependencies(
            descriptor=link.child,
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


def _collect_graph_annotations(
    *,
    accessible_graphs: Sequence[ObjectConfigGraph],
    selected_nodes: dict[UUID, ObjectConfigGraphNode],
) -> list[ObjectConfigGraphAnnotation]:
    selected_class_names_by_graph_id: dict[UUID, set[str]] = {}
    for node in selected_nodes.values():
        if node.class_config is None:
            continue
        selected_class_names_by_graph_id.setdefault(
            node.object_config_graph_id, set()
        ).add(node.class_config.name)

    selected_annotations: list[ObjectConfigGraphAnnotation] = []
    for graph in accessible_graphs:
        selected_class_names = selected_class_names_by_graph_id.get(graph.id)
        if not selected_class_names:
            continue
        for annotation in graph.object_config_graph_annotations:
            if _annotation_targets_selected_class(
                annotation=annotation,
                selected_class_names=selected_class_names,
            ):
                selected_annotations.append(annotation)
    return sorted(selected_annotations, key=_annotation_identity_key)


def _annotation_targets_selected_class(
    *,
    annotation: ObjectConfigGraphAnnotation,
    selected_class_names: set[str],
) -> bool:
    if annotation.kind != ObjectConfigGraphAnnotationKind.discriminate:
        return False
    discriminate = annotation.code_section_annotation_discriminate
    if discriminate is None:
        return False
    return discriminate.class_name in selected_class_names


def _copy_selected_annotations(
    *,
    graph_id: UUID,
    selected_annotations: Sequence[ObjectConfigGraphAnnotation],
) -> list[ObjectConfigGraphAnnotation]:
    copied_annotations: list[ObjectConfigGraphAnnotation] = []
    for annotation in selected_annotations:
        copied = deepcopy(annotation)
        copied.object_config_graph_id = graph_id
        copied_annotations.append(copied)
    return copied_annotations


def _build_graph_name(*, plan: ApiPublicPackagePlan) -> str:
    return f"{plan.package_name.replace('-', '_')}_public_package_dto"


def _build_graph_digest(
    *,
    plan: ApiPublicPackagePlan,
    selected_nodes: dict[UUID, ObjectConfigGraphNode],
    selected_annotations: Sequence[ObjectConfigGraphAnnotation],
) -> str:
    payload = {
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
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
        "annotation_keys": [
            _annotation_identity_key(annotation) for annotation in selected_annotations
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


def _annotation_identity_key(annotation: ObjectConfigGraphAnnotation) -> str:
    if (
        annotation.kind == ObjectConfigGraphAnnotationKind.discriminate
        and annotation.code_section_annotation_discriminate is not None
    ):
        discriminate = annotation.code_section_annotation_discriminate
        return ":".join(
            [
                "discriminate",
                discriminate.class_name,
                discriminate.attribute_name,
                discriminate.mode,
                discriminate.tag_value or "",
                str(discriminate.source_position or 0),
            ]
        )
    return f"{annotation.kind.value}:{annotation.id}"


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


__all__ = ["build_api_public_package_dto_graph"]
