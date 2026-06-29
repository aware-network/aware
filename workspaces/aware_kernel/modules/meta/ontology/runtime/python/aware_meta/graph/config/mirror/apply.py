"""Apply ObjectConfigGraph mirror directives onto a built graph."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)
from aware_meta_ontology.graph.config.object_config_graph_mirror_enums import (
    ObjectConfigGraphMirrorTargetKind,
)
from aware_meta_ontology.graph.config.object_config_graph_mirror import (
    ObjectConfigGraphMirror,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_meta_ontology.function.function_config import FunctionConfig

# Meta Runtime
from aware_meta.attribute.config.type_descriptor_builder import (
    ensure_stable_descriptor_tree_ids,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id
from aware_meta.graph.config.model_bootstrap import (
    build_class_config,
    build_enum_config,
    build_object_config_graph_node,
    get_class_config_fqn,
    get_node_function_config,
)
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.stable_ids import (
    stable_attribute_config_id,
    stable_class_config_attribute_config_id,
    stable_class_config_id,
    stable_enum_config_id,
    stable_join_id,
    stable_ocg_node_layout_id,
    stable_object_config_graph_node_id,
)
from aware_meta_ontology.stable_ids import (
    stable_enum_option_id,
)


@dataclass(frozen=True, slots=True)
class _ExternalSymbolRef:
    entity_id: UUID
    kind: str  # "class" | "enum"
    target_namespace: NamespacePath
    layout_kind: str = "aware"
    relative_path: str | None = None
    source_position: int | None = None


@dataclass(frozen=True, slots=True)
class _ApiMirrorRewriteTarget:
    target_id: UUID
    owner_fqn_prefix: str


def _class_attr_supports_identity_key() -> bool:
    return "is_identity_key" in ClassConfigAttributeConfig.model_fields


def _class_attr_identity_key_flag(link: ClassConfigAttributeConfig) -> bool:
    if _class_attr_supports_identity_key():
        try:
            return bool(link.is_identity_key)
        except AttributeError:
            return False
    try:
        return bool(link.is_primary)
    except AttributeError:
        return False


def _build_class_attr_link_payload(
    *,
    link_id: UUID,
    class_config_id: UUID,
    attribute_config: AttributeConfig,
    position: int,
    is_identity_key: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": link_id,
        "class_config_id": class_config_id,
        "attribute_config": attribute_config,
        "attribute_config_id": attribute_config.id,
        "name": attribute_config.name,
        "position": position,
    }
    if _class_attr_supports_identity_key():
        payload["is_identity_key"] = is_identity_key
    return payload


def _namespace_by_entity_id(
    ocg: ObjectConfigGraph,
) -> tuple[dict[UUID, NamespacePath], dict[UUID, NamespacePath], dict[UUID, NamespacePath]]:
    ns_by_node_id = build_node_namespace_by_node_id(ocg)
    class_ns: dict[UUID, NamespacePath] = {}
    enum_ns: dict[UUID, NamespacePath] = {}
    fn_ns: dict[UUID, NamespacePath] = {}
    for node in ocg.object_config_graph_nodes:
        node_id = node.id
        ns = ns_by_node_id.get(node_id)
        if ns is None:
            continue
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            _ = class_ns.setdefault(node.class_config.id, ns)
        elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
            _ = enum_ns.setdefault(node.enum_config.id, ns)
        elif node.type == ObjectConfigGraphNodeType.function:
            node_function_config = get_node_function_config(node)
            if node_function_config is not None:
                _ = fn_ns.setdefault(node_function_config.id, ns)
    return class_ns, enum_ns, fn_ns


def _iter_attribute_configs_with_owner_namespace(
    ocg: ObjectConfigGraph,
) -> Iterable[tuple[AttributeConfig, NamespacePath]]:
    class_ns, _enum_ns, fn_ns = _namespace_by_entity_id(ocg)

    for node in ocg.object_config_graph_nodes:
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            ns = class_ns.get(node.class_config.id)
            if ns is None:
                continue
            for link in node.class_config.class_config_attribute_configs:
                yield link.attribute_config, ns
            for fn_link in node.class_config.class_config_function_configs:
                fn_cfg = fn_link.function_config
                fn_ns_path = class_ns.get(node.class_config.id)
                if fn_ns_path is None:
                    continue
                for fn_attr in fn_cfg.function_config_attribute_configs:
                    yield fn_attr.attribute_config, fn_ns_path

        if node.type == ObjectConfigGraphNodeType.function:
            node_function_config = get_node_function_config(node)
            if node_function_config is None:
                continue
            ns = fn_ns.get(node_function_config.id)
            if ns is None:
                continue
            for link in node_function_config.function_config_attribute_configs:
                yield link.attribute_config, ns


def _iter_type_descriptors(
    root: AttributeTypeDescriptor,
) -> Iterable[AttributeTypeDescriptor]:
    stack = [root]
    while stack:
        cur = stack.pop()
        yield cur
        for link in cur.child_links:
            stack.append(link.child)


def _clone_type_descriptor(
    root: AttributeTypeDescriptor,
    *,
    class_by_id: dict[UUID, ClassConfig],
    enum_by_id: dict[UUID, EnumConfig],
    class_id_remap: dict[UUID, UUID],
    enum_id_remap: dict[UUID, UUID],
    mirrored_source_class_ids: set[UUID] | None = None,
    mirrored_source_enum_ids: set[UUID] | None = None,
    api_class_id_rewrite: dict[UUID, UUID] | None = None,
    api_enum_id_rewrite: dict[UUID, UUID] | None = None,
) -> AttributeTypeDescriptor:
    mirrored_source_class_ids = mirrored_source_class_ids or set()
    mirrored_source_enum_ids = mirrored_source_enum_ids or set()
    api_class_id_rewrite = api_class_id_rewrite or {}
    api_enum_id_rewrite = api_enum_id_rewrite or {}

    cloned = root.model_copy(deep=True)
    for node in _iter_type_descriptors(cloned):
        if node.kind == AttributeTypeDescriptorKind.enum and node.enum_config_id is not None:
            mapped = enum_id_remap.get(node.enum_config_id)
            if mapped is not None:
                node.enum_config_id = mapped
            elif node.enum_config_id not in mirrored_source_enum_ids:
                rewritten = api_enum_id_rewrite.get(node.enum_config_id)
                if rewritten is not None:
                    node.enum_config_id = rewritten
            node.enum_config = enum_by_id.get(node.enum_config_id)
        if node.kind == AttributeTypeDescriptorKind.class_ and node.class_config_id is not None:
            mapped = class_id_remap.get(node.class_config_id)
            if mapped is not None:
                node.class_config_id = mapped
            elif node.class_config_id not in mirrored_source_class_ids:
                rewritten = api_class_id_rewrite.get(node.class_config_id)
                if rewritten is not None:
                    node.class_config_id = rewritten
            node.class_config = class_by_id.get(node.class_config_id)

    return ensure_stable_descriptor_tree_ids(cloned)


def _build_layouts_for_ref(
    ref: _ExternalSymbolRef,
    ocg: ObjectConfigGraph,
    *,
    node_type: str,
    node_key: str,
) -> list[ObjectConfigGraphNodeLayout]:
    if not ref.relative_path:
        return []
    node_id = stable_object_config_graph_node_id(
        object_config_graph_id=ocg.id,
        type=node_type,
        node_key=node_key,
    )
    return [
        ObjectConfigGraphNodeLayout(
            id=stable_ocg_node_layout_id(
                object_config_graph_node_id=node_id,
                layout_kind=ref.layout_kind or "aware",
            ),
            object_config_graph_node_id=node_id,
            layout_kind=ref.layout_kind or "aware",
            relative_path=ref.relative_path,
            source_position=ref.source_position,
        )
    ]


def _mirror_target_namespace(mirror: ObjectConfigGraphMirror) -> NamespacePath:
    namespace = getattr(mirror, "namespace", None)
    namespace_text = (str(namespace).strip() if namespace is not None else "")
    if not namespace_text:
        raise ValueError(
            "ObjectConfigGraphMirror requires namespace."
        )
    return NamespacePath(package=mirror.fqn_prefix, namespace=namespace_text)


def _collect_mirror_refs(*, ocg: ObjectConfigGraph) -> list[_ExternalSymbolRef]:
    refs: list[_ExternalSymbolRef] = []
    for mirror in ocg.object_config_graph_mirrors:
        target_ns = _mirror_target_namespace(mirror)
        if mirror.target_kind == ObjectConfigGraphMirrorTargetKind.class_:
            cls = mirror.class_config
            if cls is None:
                raise ValueError("Mirror missing class_config")
            refs.append(
                _ExternalSymbolRef(
                    entity_id=cls.id,
                    kind="class",
                    target_namespace=target_ns,
                    layout_kind=mirror.layout_kind or "aware",
                    relative_path=mirror.relative_path,
                    source_position=mirror.source_position,
                )
            )
        elif mirror.target_kind == ObjectConfigGraphMirrorTargetKind.enum:
            enum = mirror.enum_config
            if enum is None:
                raise ValueError("Mirror missing enum_config")
            refs.append(
                _ExternalSymbolRef(
                    entity_id=enum.id,
                    kind="enum",
                    target_namespace=target_ns,
                    layout_kind=mirror.layout_kind or "aware",
                    relative_path=mirror.relative_path,
                    source_position=mirror.source_position,
                )
            )
        else:
            raise ValueError(f"Mirror target kind unsupported: {mirror.target_kind}")

    refs.sort(key=lambda r: (r.kind, str(r.entity_id)))
    return refs


def _index_external_symbols(
    *,
    external_graphs_by_id: dict[UUID, ObjectConfigGraph],
) -> tuple[dict[UUID, ClassConfig], dict[UUID, EnumConfig]]:
    external_classes: dict[UUID, ClassConfig] = {}
    external_enums: dict[UUID, EnumConfig] = {}
    for ext in external_graphs_by_id.values():
        for node in ext.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                _ = external_classes.setdefault(node.class_config.id, node.class_config)
            elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
                _ = external_enums.setdefault(node.enum_config.id, node.enum_config)
    return external_classes, external_enums


def _index_api_mirror_rewrites(
    *,
    external_graphs_by_id: dict[UUID, ObjectConfigGraph],
) -> tuple[dict[UUID, _ApiMirrorRewriteTarget], dict[UUID, _ApiMirrorRewriteTarget]]:
    """
    Build rewrite maps from ontology type IDs to the owning API mirror type IDs.

    Canonical contract:
    - API packages may depend on ontology packages for mirror *sources* only.
    - Any transitive external ontology references inside mirrored payload types must be rewritten to reference the owning
      API mirror package (API->API), not copied and not left pointing at ontology.
    """
    class_target_by_source_id: dict[UUID, _ApiMirrorRewriteTarget] = {}
    enum_target_by_source_id: dict[UUID, _ApiMirrorRewriteTarget] = {}

    for graph in external_graphs_by_id.values():
        mirrors = graph.object_config_graph_mirrors or []
        if not mirrors:
            continue

        graph_class_ids: set[UUID] = set()
        graph_enum_ids: set[UUID] = set()
        graph_class_ids_by_fqn: dict[str, UUID] = {}
        graph_enum_ids_by_fqn: dict[str, UUID] = {}
        graph_ns_by_node_id = build_node_namespace_by_node_id(graph)
        for node in graph.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
                graph_class_ids.add(node.class_config.id)
                class_fqn = get_class_config_fqn(node.class_config)
                if not class_fqn:
                    ns = graph_ns_by_node_id.get(node.id)
                    class_name = (node.class_config.name or "").strip()
                    if ns is not None and class_name:
                        class_fqn = ns.fqn(class_name)
                if class_fqn:
                    prev = graph_class_ids_by_fqn.get(class_fqn)
                    if prev is not None and prev != node.class_config.id:
                        raise ValueError(
                            "Mirror rewrite index encountered duplicate class FQNs in the owning API graph. "
                            + f"owner={graph.fqn_prefix!r} class_fqn={class_fqn!r} ids={prev},{node.class_config.id}"
                        )
                    graph_class_ids_by_fqn[class_fqn] = node.class_config.id
            elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
                graph_enum_ids.add(node.enum_config.id)
                enum_fqn = (node.enum_config.enum_fqn or "").strip()
                if not enum_fqn:
                    ns = graph_ns_by_node_id.get(node.id)
                    enum_name = (node.enum_config.name or "").strip()
                    if ns is not None and enum_name:
                        enum_fqn = ns.fqn(enum_name)
                if enum_fqn:
                    prev = graph_enum_ids_by_fqn.get(enum_fqn)
                    if prev is not None and prev != node.enum_config.id:
                        raise ValueError(
                            "Mirror rewrite index encountered duplicate enum FQNs in the owning API graph. "
                            + f"owner={graph.fqn_prefix!r} enum_fqn={enum_fqn!r} ids={prev},{node.enum_config.id}"
                        )
                    graph_enum_ids_by_fqn[enum_fqn] = node.enum_config.id

        for mirror in mirrors:
            if mirror.fqn_prefix != graph.fqn_prefix:
                raise ValueError(
                    "Mirror rewrite index encountered an inconsistent API graph: "
                    + f"graph.fqn_prefix={graph.fqn_prefix!r} mirror.fqn_prefix={mirror.fqn_prefix!r}"
                )

            target_name = (mirror.target_text or "").strip().split(".")[-1].strip()
            if not target_name:
                raise ValueError("Mirror rewrite index encountered a mirror with empty target_text")

            target_ns = _mirror_target_namespace(mirror)
            owner = graph.fqn_prefix

            if mirror.target_kind == ObjectConfigGraphMirrorTargetKind.enum:
                source_id = mirror.enum_config_id
                if source_id is None:
                    raise ValueError("Mirror rewrite index encountered an enum mirror with no enum_config_id")
                enum_fqn = target_ns.fqn(target_name)
                expected_target_node_id = stable_object_config_graph_node_id(
                    object_config_graph_id=graph.id,
                    type="enum",
                    node_key=enum_fqn,
                )
                expected_target_id = stable_enum_config_id(
                    object_config_graph_node_id=expected_target_node_id,
                    enum_fqn=enum_fqn,
                )
                target_id = graph_enum_ids_by_fqn.get(enum_fqn, expected_target_id)
                if target_id not in graph_enum_ids:
                    raise ValueError(
                        "Mirror rewrite index could not find the mirrored enum in the owning API graph. "
                        + f"owner={owner!r} enum_fqn={enum_fqn!r} target_id={target_id} "
                        + f"expected_target_id={expected_target_id} source_id={source_id}"
                    )
                prev = enum_target_by_source_id.get(source_id)
                if prev is not None and prev.target_id != target_id:
                    raise ValueError(
                        "Ambiguous API mirror ownership for enum_config_id. "
                        + f"source_id={source_id} owners={prev.owner_fqn_prefix!r},{owner!r}"
                    )
                enum_target_by_source_id[source_id] = _ApiMirrorRewriteTarget(
                    target_id=target_id,
                    owner_fqn_prefix=owner,
                )
                continue

            if mirror.target_kind == ObjectConfigGraphMirrorTargetKind.class_:
                source_id = mirror.class_config_id
                if source_id is None:
                    raise ValueError("Mirror rewrite index encountered a class mirror with no class_config_id")
                class_fqn = target_ns.fqn(target_name)
                expected_target_node_id = stable_object_config_graph_node_id(
                    object_config_graph_id=graph.id,
                    type="class",
                    node_key=class_fqn,
                )
                expected_target_id = stable_class_config_id(
                    object_config_graph_node_id=expected_target_node_id,
                    class_fqn=class_fqn,
                )
                target_id = graph_class_ids_by_fqn.get(class_fqn, expected_target_id)
                if target_id not in graph_class_ids:
                    raise ValueError(
                        "Mirror rewrite index could not find the mirrored class in the owning API graph. "
                        + f"owner={owner!r} class_fqn={class_fqn!r} target_id={target_id} "
                        + f"expected_target_id={expected_target_id} source_id={source_id}"
                    )
                prev = class_target_by_source_id.get(source_id)
                if prev is not None and prev.target_id != target_id:
                    raise ValueError(
                        "Ambiguous API mirror ownership for class_config_id. "
                        + f"source_id={source_id} owners={prev.owner_fqn_prefix!r},{owner!r}"
                    )
                class_target_by_source_id[source_id] = _ApiMirrorRewriteTarget(
                    target_id=target_id,
                    owner_fqn_prefix=owner,
                )
                continue

            raise ValueError(f"Mirror rewrite index encountered unsupported target kind: {mirror.target_kind}")

    return class_target_by_source_id, enum_target_by_source_id


def _validate_no_unresolved_mirror_types(
    *,
    attribute_configs: Iterable[AttributeConfig],
    mirrored_source_class_ids: set[UUID],
    mirrored_source_enum_ids: set[UUID],
) -> None:
    for attr in attribute_configs:
        for node in _iter_type_descriptors(attr.type_descriptor):
            if node.kind == AttributeTypeDescriptorKind.enum:
                if node.enum_config_id is None or node.enum_config is None:
                    raise ValueError(
                        "Mirror application produced an unresolved enum type reference. "
                        + f"attribute_config_id={attr.id} attribute_name={attr.name!r} enum_config_id={node.enum_config_id}"
                    )
                if node.enum_config_id in mirrored_source_enum_ids:
                    raise ValueError(
                        "Mirror application leaked a source ontology enum into an API graph. "
                        + "Add an explicit `mirror` for the enum or ensure it is reachable from mirrored roots. "
                        + f"attribute_config_id={attr.id} attribute_name={attr.name!r} enum_config_id={node.enum_config_id}"
                    )
            if node.kind == AttributeTypeDescriptorKind.class_:
                if node.class_config_id is None or node.class_config is None:
                    raise ValueError(
                        "Mirror application produced an unresolved class type reference. "
                        + f"attribute_config_id={attr.id} attribute_name={attr.name!r} class_config_id={node.class_config_id}"
                    )
                if node.class_config_id in mirrored_source_class_ids:
                    raise ValueError(
                        "Mirror application leaked a source ontology class into an API graph. "
                        + "Add an explicit `mirror` for the class or ensure it is reachable from mirrored roots. "
                        + f"attribute_config_id={attr.id} attribute_name={attr.name!r} class_config_id={node.class_config_id}"
                    )


def _iter_attribute_configs(
    *,
    class_configs: Iterable[ClassConfig],
    function_configs: Iterable[FunctionConfig],
) -> Iterable[AttributeConfig]:
    for cls in class_configs:
        for link in cls.class_config_attribute_configs:
            yield link.attribute_config
        for fn_link in cls.class_config_function_configs:
            fn = fn_link.function_config
            for fn_attr in fn.function_config_attribute_configs:
                yield fn_attr.attribute_config

    for fn in function_configs:
        for fn_attr in fn.function_config_attribute_configs:
            yield fn_attr.attribute_config


def apply_object_config_graph_mirrors_to_build_inputs(
    *,
    ocg_id: UUID,
    fqn_prefix: str,
    class_configs: list[ClassConfig],
    enum_configs: list[EnumConfig],
    function_configs: list[FunctionConfig],
    namespace_bundle: ObjectConfigGraphNamespaceBundle,
    object_config_graph_mirrors: list[ObjectConfigGraphMirror],
    external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
    node_layouts_by_node_key: dict[tuple[str, str], list[ObjectConfigGraphNodeLayout]] | None = None,
) -> ObjectConfigGraphNamespaceBundle:
    """
    Apply mirror directives to *build inputs* before OCG hashing/build.

    Mutates `class_configs`/`enum_configs` in-place by appending copied external payload types, and rewrites all local
    AttributeTypeDescriptors to reference the copied local ids.

    Returns an updated namespace bundle including copied entities.
    """
    if not object_config_graph_mirrors:
        return namespace_bundle
    if not external_graphs_by_id:
        raise ValueError("Mirror application requires external_graphs_by_id for resolution")

    mirrored_source_ocg_ids = {mirror.source_object_config_graph_id for mirror in object_config_graph_mirrors}
    missing = mirrored_source_ocg_ids.difference(external_graphs_by_id.keys())
    if missing:
        raise ValueError(f"Mirror application missing required source graphs: {sorted(str(x) for x in missing)}")

    mirrored_source_graphs_by_id = {gid: external_graphs_by_id[gid] for gid in mirrored_source_ocg_ids}
    source_classes, source_enums = _index_external_symbols(external_graphs_by_id=mirrored_source_graphs_by_id)
    source_class_ids = set(source_classes.keys())
    source_enum_ids = set(source_enums.keys())

    local_classes: dict[UUID, ClassConfig] = {c.id: c for c in class_configs}
    local_enums: dict[UUID, EnumConfig] = {e.id: e for e in enum_configs}

    dep_classes, dep_enums = _index_external_symbols(external_graphs_by_id=external_graphs_by_id)
    api_class_rewrites, api_enum_rewrites = _index_api_mirror_rewrites(external_graphs_by_id=external_graphs_by_id)
    api_class_id_rewrite = {k: v.target_id for k, v in api_class_rewrites.items()}
    api_enum_id_rewrite = {k: v.target_id for k, v in api_enum_rewrites.items()}

    known_classes: dict[UUID, ClassConfig] = dict(dep_classes)
    known_enums: dict[UUID, EnumConfig] = dict(dep_enums)
    known_classes.update(local_classes)
    known_enums.update(local_enums)

    refs: list[_ExternalSymbolRef] = []
    for mirror in object_config_graph_mirrors:
        target_ns = _mirror_target_namespace(mirror)
        if mirror.target_kind == ObjectConfigGraphMirrorTargetKind.class_:
            cls = mirror.class_config
            if cls is None:
                raise ValueError("Mirror missing class_config")
            refs.append(
                _ExternalSymbolRef(
                    entity_id=cls.id,
                    kind="class",
                    target_namespace=target_ns,
                    layout_kind=mirror.layout_kind or "aware",
                    relative_path=mirror.relative_path,
                    source_position=mirror.source_position,
                )
            )
        elif mirror.target_kind == ObjectConfigGraphMirrorTargetKind.enum:
            enum = mirror.enum_config
            if enum is None:
                raise ValueError("Mirror missing enum_config")
            refs.append(
                _ExternalSymbolRef(
                    entity_id=enum.id,
                    kind="enum",
                    target_namespace=target_ns,
                    layout_kind=mirror.layout_kind or "aware",
                    relative_path=mirror.relative_path,
                    source_position=mirror.source_position,
                )
            )
        else:
            raise ValueError(f"Mirror target kind unsupported: {mirror.target_kind}")

    refs.sort(key=lambda r: (r.kind, str(r.entity_id)))
    if not refs:
        return namespace_bundle

    layout_map = node_layouts_by_node_key if node_layouts_by_node_key is not None else {}
    class_id_remap: dict[UUID, UUID] = {}
    enum_id_remap: dict[UUID, UUID] = {}

    ns_by_class = dict(namespace_bundle.namespace_by_class_config_id)
    ns_by_enum = dict(namespace_bundle.namespace_by_enum_config_id)

    queue: deque[_ExternalSymbolRef] = deque(refs)
    seen: set[tuple[str, UUID]] = set()

    def _enqueue(entity_id: UUID, kind: str, ns: NamespacePath, ref: _ExternalSymbolRef) -> None:
        key = (kind, entity_id)
        if key in seen:
            return
        queue.append(
            _ExternalSymbolRef(
                entity_id=entity_id,
                kind=kind,
                target_namespace=ns,
                layout_kind=ref.layout_kind,
                relative_path=ref.relative_path,
                source_position=ref.source_position,
            )
        )
        seen.add(key)

    def _set_layout(kind: str, node_key: str, ref: _ExternalSymbolRef) -> None:
        key = (kind, node_key)
        if key in layout_map or not ref.relative_path:
            return
        node_id = stable_object_config_graph_node_id(
            object_config_graph_id=ocg_id,
            type=kind,
            node_key=node_key,
        )
        layout_map[key] = [
            ObjectConfigGraphNodeLayout(
                id=stable_ocg_node_layout_id(
                    object_config_graph_node_id=node_id,
                    layout_kind=ref.layout_kind or "aware",
                ),
                object_config_graph_node_id=node_id,
                layout_kind=ref.layout_kind or "aware",
                relative_path=ref.relative_path,
                source_position=ref.source_position,
            )
        ]

    while queue:
        ref = queue.popleft()

        if ref.kind == "enum":
            if ref.entity_id in enum_id_remap:
                continue
            ext_enum = source_enums.get(ref.entity_id)
            if ext_enum is None:
                raise ValueError(f"Mirror copy: external enum_config_id not found: {ref.entity_id}")

            enum_ns = NamespacePath(
                package=fqn_prefix,
                namespace=ref.target_namespace.namespace,
            )
            enum_fqn = enum_ns.fqn(ext_enum.name)
            enum_node_id = stable_object_config_graph_node_id(
                object_config_graph_id=ocg_id,
                type="enum",
                node_key=enum_fqn,
            )
            new_enum_id = stable_enum_config_id(
                object_config_graph_node_id=enum_node_id,
                enum_fqn=enum_fqn,
            )
            enum_id_remap[ref.entity_id] = new_enum_id
            _ = ns_by_enum.setdefault(new_enum_id, enum_ns)
            _set_layout("enum", enum_fqn, ref)

            if new_enum_id not in local_enums:
                new_enum = build_enum_config(
                    enum_config_id=new_enum_id,
                    object_config_graph_node_id=enum_node_id,
                    enum_fqn=enum_fqn,
                    name=ext_enum.name,
                    description=ext_enum.description,
                )
                for opt in sorted(ext_enum.enum_options, key=lambda o: (o.position, o.value)):
                    new_enum.enum_options.append(
                        EnumOption(
                            id=stable_enum_option_id(enum_config_id=new_enum_id, value=opt.value),
                            enum_config_id=new_enum_id,
                            value=opt.value,
                            label=opt.label,
                            description=opt.description,
                            position=opt.position,
                        )
                    )
                local_enums[new_enum_id] = new_enum
                known_enums[new_enum_id] = new_enum
                enum_configs.append(new_enum)
            continue

        if ref.kind == "class":
            if ref.entity_id in class_id_remap:
                continue
            ext_cls = source_classes.get(ref.entity_id)
            if ext_cls is None:
                raise ValueError(f"Mirror copy: external class_config_id not found: {ref.entity_id}")
            if ext_cls.value_mode != ClassValueMode.inline_value:
                raise ValueError(
                    "Mirror copy forbids referencing GRAPH_REF classes as payload types. "
                    + f"class_config_id={ref.entity_id} name={ext_cls.name} value_mode={ext_cls.value_mode}"
                )

            cls_ns = NamespacePath(
                package=fqn_prefix,
                namespace=ref.target_namespace.namespace,
            )
            cls_fqn = cls_ns.fqn(ext_cls.name)
            class_node_id = stable_object_config_graph_node_id(
                object_config_graph_id=ocg_id,
                type="class",
                node_key=cls_fqn,
            )
            new_cls_id = stable_class_config_id(
                object_config_graph_node_id=class_node_id,
                class_fqn=cls_fqn,
            )
            class_id_remap[ref.entity_id] = new_cls_id
            _ = ns_by_class.setdefault(new_cls_id, cls_ns)
            _set_layout("class", cls_fqn, ref)

            for link in sorted(ext_cls.class_config_attribute_configs, key=lambda l: l.position):
                ext_attr = link.attribute_config
                for td_node in _iter_type_descriptors(ext_attr.type_descriptor):
                    if td_node.kind == AttributeTypeDescriptorKind.enum and td_node.enum_config_id is not None:
                        if td_node.enum_config_id in source_enum_ids:
                            _enqueue(td_node.enum_config_id, "enum", cls_ns, ref)
                    if td_node.kind == AttributeTypeDescriptorKind.class_ and td_node.class_config_id is not None:
                        if td_node.class_config_id in source_class_ids:
                            _enqueue(td_node.class_config_id, "class", cls_ns, ref)

            if new_cls_id not in local_classes:
                new_cls = build_class_config(
                    class_config_id=new_cls_id,
                    object_config_graph_node_id=class_node_id,
                    class_fqn=cls_fqn,
                    name=ext_cls.name,
                    description=ext_cls.description,
                    is_base=True,
                    is_edge=False,
                    value_mode=ClassValueMode.inline_value,
                    parent_class_id=None,
                    class_config_relationships=[],
                    class_config_attribute_configs=[],
                    class_config_function_configs=[],
                )

                new_attr_links: list[ClassConfigAttributeConfig] = []
                for link in sorted(ext_cls.class_config_attribute_configs, key=lambda l: l.position):
                    ext_attr = link.attribute_config
                    cloned_td = _clone_type_descriptor(
                        ext_attr.type_descriptor,
                        class_by_id=known_classes,
                        enum_by_id=known_enums,
                        class_id_remap=class_id_remap,
                        enum_id_remap=enum_id_remap,
                        mirrored_source_class_ids=source_class_ids,
                        mirrored_source_enum_ids=source_enum_ids,
                        api_class_id_rewrite=api_class_id_rewrite,
                        api_enum_id_rewrite=api_enum_id_rewrite,
                    )
                    new_attr = AttributeConfig(
                        id=stable_attribute_config_id(owner_key=cls_fqn, name=ext_attr.name),
                        owner_key=cls_fqn,
                        name=ext_attr.name,
                        description=ext_attr.description,
                        default_value=ext_attr.default_value,
                        is_primary=ext_attr.is_primary,
                        is_public=ext_attr.is_public,
                        is_required=ext_attr.is_required,
                        is_unique=ext_attr.is_unique,
                        is_virtual=False,
                        exclude_serialization=ext_attr.exclude_serialization,
                        type_descriptor=cloned_td,
                        type_descriptor_id=cloned_td.id,
                    )
                    new_attr_links.append(
                        ClassConfigAttributeConfig(
                            **_build_class_attr_link_payload(
                                link_id=stable_class_config_attribute_config_id(
                                    class_config_id=new_cls_id,
                                    attribute_config_id=new_attr.id,
                                ),
                                class_config_id=new_cls_id,
                                attribute_config=new_attr,
                                position=link.position,
                                is_identity_key=_class_attr_identity_key_flag(link),
                            )
                        )
                    )

                new_cls.class_config_attribute_configs = new_attr_links
                local_classes[new_cls_id] = new_cls
                known_classes[new_cls_id] = new_cls
                class_configs.append(new_cls)
            continue

        raise ValueError(f"Mirror copy: unsupported kind: {ref.kind}")

    for attr_config in _iter_attribute_configs(class_configs=class_configs, function_configs=function_configs):
        td = attr_config.type_descriptor
        attr_config.type_descriptor = _clone_type_descriptor(
            td,
            class_by_id=known_classes,
            enum_by_id=known_enums,
            class_id_remap=class_id_remap,
            enum_id_remap=enum_id_remap,
            mirrored_source_class_ids=source_class_ids,
            mirrored_source_enum_ids=source_enum_ids,
            api_class_id_rewrite=api_class_id_rewrite,
            api_enum_id_rewrite=api_enum_id_rewrite,
        )
        attr_config.type_descriptor_id = attr_config.type_descriptor.id

    _validate_no_unresolved_mirror_types(
        attribute_configs=_iter_attribute_configs(class_configs=class_configs, function_configs=function_configs),
        mirrored_source_class_ids=source_class_ids,
        mirrored_source_enum_ids=source_enum_ids,
    )

    return ObjectConfigGraphNamespaceBundle(
        namespace_by_class_config_id=ns_by_class,
        namespace_by_enum_config_id=ns_by_enum,
        namespace_by_function_config_id=dict(namespace_bundle.namespace_by_function_config_id),
    )


def apply_object_config_graph_mirrors(
    *,
    object_config_graph: ObjectConfigGraph,
    external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
) -> None:
    """
    Apply `object_config_graph.object_config_graph_mirrors` in-place.

    Contract:
    - Mirrors copy external INLINE_VALUE classes/enums into the local graph using stable meta IDs.
    - All local AttributeTypeDescriptors are rewritten to point at the local copies.
    - New nodes are identified by canonical namespace FQNs.
    """
    if not object_config_graph.object_config_graph_mirrors:
        return
    if not external_graphs_by_id:
        raise ValueError("Mirror application requires external_graphs_by_id for resolution")
    mirrored_source_ocg_ids = {
        mirror.source_object_config_graph_id for mirror in object_config_graph.object_config_graph_mirrors
    }
    missing = mirrored_source_ocg_ids.difference(external_graphs_by_id.keys())
    if missing:
        raise ValueError(f"Mirror application missing required source graphs: {sorted(str(x) for x in missing)}")

    mirrored_source_graphs_by_id = {gid: external_graphs_by_id[gid] for gid in mirrored_source_ocg_ids}
    source_classes, source_enums = _index_external_symbols(external_graphs_by_id=mirrored_source_graphs_by_id)
    source_class_ids = set(source_classes.keys())
    source_enum_ids = set(source_enums.keys())

    dep_classes, dep_enums = _index_external_symbols(external_graphs_by_id=external_graphs_by_id)
    api_class_rewrites, api_enum_rewrites = _index_api_mirror_rewrites(external_graphs_by_id=external_graphs_by_id)
    api_class_id_rewrite = {k: v.target_id for k, v in api_class_rewrites.items()}
    api_enum_id_rewrite = {k: v.target_id for k, v in api_enum_rewrites.items()}

    local_classes: dict[UUID, ClassConfig] = {}
    local_enums: dict[UUID, EnumConfig] = {}
    node_by_id: dict[UUID, ObjectConfigGraphNode] = {}
    for node in object_config_graph.object_config_graph_nodes:
        prev = node_by_id.get(node.id)
        if prev is not None and prev is not node:
            raise ValueError(f"Duplicate ObjectConfigGraphNode id={node.id}")
        node_by_id[node.id] = node
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            local_classes[node.class_config.id] = node.class_config
        elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
            local_enums[node.enum_config.id] = node.enum_config

    known_classes: dict[UUID, ClassConfig] = dict(dep_classes)
    known_enums: dict[UUID, EnumConfig] = dict(dep_enums)
    known_classes.update(local_classes)
    known_enums.update(local_enums)

    refs = _collect_mirror_refs(ocg=object_config_graph)
    if not refs:
        return

    class_id_remap: dict[UUID, UUID] = {}
    enum_id_remap: dict[UUID, UUID] = {}

    queue: deque[_ExternalSymbolRef] = deque(refs)
    seen: set[tuple[str, UUID]] = set()

    def _enqueue(entity_id: UUID, kind: str, ns: NamespacePath, ref: _ExternalSymbolRef) -> None:
        key = (kind, entity_id)
        if key in seen:
            return
        queue.append(
            _ExternalSymbolRef(
                entity_id=entity_id,
                kind=kind,
                target_namespace=ns,
                layout_kind=ref.layout_kind,
                relative_path=ref.relative_path,
                source_position=ref.source_position,
            )
        )
        seen.add(key)

    while queue:
        ref = queue.popleft()

        if ref.kind == "enum":
            if ref.entity_id in enum_id_remap:
                continue
            ext_enum = source_enums.get(ref.entity_id)
            if ext_enum is None:
                raise ValueError(f"Mirror copy: external enum_config_id not found: {ref.entity_id}")

            enum_ns = NamespacePath(
                package=object_config_graph.fqn_prefix,
                namespace=ref.target_namespace.namespace,
            )
            enum_fqn = enum_ns.fqn(ext_enum.name)
            enum_node_id = stable_object_config_graph_node_id(
                object_config_graph_id=object_config_graph.id,
                type="enum",
                node_key=enum_fqn,
            )
            new_enum_id = stable_enum_config_id(
                object_config_graph_node_id=enum_node_id,
                enum_fqn=enum_fqn,
            )
            enum_id_remap[ref.entity_id] = new_enum_id

            if new_enum_id not in local_enums:
                new_enum = build_enum_config(
                    enum_config_id=new_enum_id,
                    object_config_graph_node_id=enum_node_id,
                    enum_fqn=enum_fqn,
                    name=ext_enum.name,
                    description=ext_enum.description,
                )
                for opt in sorted(ext_enum.enum_options, key=lambda o: o.position):
                    new_enum.enum_options.append(
                        EnumOption(
                            id=stable_enum_option_id(enum_config_id=new_enum_id, value=opt.value),
                            enum_config_id=new_enum_id,
                            value=opt.value,
                            label=opt.label,
                            description=opt.description,
                            position=opt.position,
                        )
                    )
                local_enums[new_enum_id] = new_enum
                known_enums[new_enum_id] = new_enum

            node_id = enum_node_id
            node = node_by_id.get(node_id)
            if node is None:
                node = build_object_config_graph_node(
                    object_config_graph_node_id=node_id,
                    object_config_graph_id=object_config_graph.id,
                    type=ObjectConfigGraphNodeType.enum,
                    node_key=enum_fqn,
                    enum_config=local_enums[new_enum_id],
                    layouts=_build_layouts_for_ref(
                        ref,
                        object_config_graph,
                        node_type="enum",
                        node_key=enum_fqn,
                    ),
                )
                object_config_graph.object_config_graph_nodes.append(node)
                node_by_id[node_id] = node
            continue

        if ref.kind == "class":
            if ref.entity_id in class_id_remap:
                continue
            ext_cls = source_classes.get(ref.entity_id)
            if ext_cls is None:
                raise ValueError(f"Mirror copy: external class_config_id not found: {ref.entity_id}")
            if ext_cls.value_mode != ClassValueMode.inline_value:
                raise ValueError(
                    "Mirror copy forbids referencing GRAPH_REF classes as payload types. "
                    + f"class_config_id={ref.entity_id} name={ext_cls.name} value_mode={ext_cls.value_mode}"
                )

            cls_ns = NamespacePath(
                package=object_config_graph.fqn_prefix,
                namespace=ref.target_namespace.namespace,
            )
            cls_fqn = cls_ns.fqn(ext_cls.name)
            class_node_id = stable_object_config_graph_node_id(
                object_config_graph_id=object_config_graph.id,
                type="class",
                node_key=cls_fqn,
            )
            new_cls_id = stable_class_config_id(
                object_config_graph_node_id=class_node_id,
                class_fqn=cls_fqn,
            )
            class_id_remap[ref.entity_id] = new_cls_id

            for link in sorted(ext_cls.class_config_attribute_configs, key=lambda l: l.position):
                ext_attr = link.attribute_config
                for td_node in _iter_type_descriptors(ext_attr.type_descriptor):
                    if td_node.kind == AttributeTypeDescriptorKind.enum and td_node.enum_config_id is not None:
                        if td_node.enum_config_id in source_enum_ids:
                            _enqueue(td_node.enum_config_id, "enum", cls_ns, ref)
                    if td_node.kind == AttributeTypeDescriptorKind.class_ and td_node.class_config_id is not None:
                        if td_node.class_config_id in source_class_ids:
                            _enqueue(td_node.class_config_id, "class", cls_ns, ref)

            if new_cls_id not in local_classes:
                new_cls = build_class_config(
                    class_config_id=new_cls_id,
                    object_config_graph_node_id=class_node_id,
                    class_fqn=cls_fqn,
                    name=ext_cls.name,
                    description=ext_cls.description,
                    is_base=True,
                    is_edge=False,
                    value_mode=ClassValueMode.inline_value,
                    parent_class_id=None,
                    class_config_relationships=[],
                    class_config_attribute_configs=[],
                    class_config_function_configs=[],
                )

                new_attr_links: list[ClassConfigAttributeConfig] = []
                for link in sorted(ext_cls.class_config_attribute_configs, key=lambda l: l.position):
                    ext_attr = link.attribute_config
                    cloned_td = _clone_type_descriptor(
                        ext_attr.type_descriptor,
                        class_by_id=known_classes,
                        enum_by_id=known_enums,
                        class_id_remap=class_id_remap,
                        enum_id_remap=enum_id_remap,
                        mirrored_source_class_ids=source_class_ids,
                        mirrored_source_enum_ids=source_enum_ids,
                        api_class_id_rewrite=api_class_id_rewrite,
                        api_enum_id_rewrite=api_enum_id_rewrite,
                    )
                    new_attr = AttributeConfig(
                        id=stable_attribute_config_id(owner_key=cls_fqn, name=ext_attr.name),
                        owner_key=cls_fqn,
                        name=ext_attr.name,
                        description=ext_attr.description,
                        default_value=ext_attr.default_value,
                        is_primary=ext_attr.is_primary,
                        is_public=ext_attr.is_public,
                        is_required=ext_attr.is_required,
                        is_unique=ext_attr.is_unique,
                        is_virtual=False,
                        exclude_serialization=ext_attr.exclude_serialization,
                        type_descriptor=cloned_td,
                        type_descriptor_id=cloned_td.id,
                    )
                    new_attr_links.append(
                        ClassConfigAttributeConfig(
                            **_build_class_attr_link_payload(
                                link_id=stable_class_config_attribute_config_id(
                                    class_config_id=new_cls_id,
                                    attribute_config_id=new_attr.id,
                                ),
                                class_config_id=new_cls_id,
                                attribute_config=new_attr,
                                position=link.position,
                                is_identity_key=_class_attr_identity_key_flag(link),
                            )
                        )
                    )

                new_cls.class_config_attribute_configs = new_attr_links
                local_classes[new_cls_id] = new_cls
                known_classes[new_cls_id] = new_cls

            node_id = class_node_id
            node = node_by_id.get(node_id)
            if node is None:
                node = build_object_config_graph_node(
                    object_config_graph_node_id=node_id,
                    object_config_graph_id=object_config_graph.id,
                    type=ObjectConfigGraphNodeType.class_,
                    node_key=cls_fqn,
                    class_config=local_classes[new_cls_id],
                    layouts=_build_layouts_for_ref(
                        ref,
                        object_config_graph,
                        node_type="class",
                        node_key=cls_fqn,
                    ),
                )
                object_config_graph.object_config_graph_nodes.append(node)
                node_by_id[node_id] = node
            continue

        raise ValueError(f"Mirror copy: unsupported kind: {ref.kind}")

    for attr_config, _ns in _iter_attribute_configs_with_owner_namespace(object_config_graph):
        td = attr_config.type_descriptor
        attr_config.type_descriptor = _clone_type_descriptor(
            td,
            class_by_id=known_classes,
            enum_by_id=known_enums,
            class_id_remap=class_id_remap,
            enum_id_remap=enum_id_remap,
            mirrored_source_class_ids=source_class_ids,
            mirrored_source_enum_ids=source_enum_ids,
            api_class_id_rewrite=api_class_id_rewrite,
            api_enum_id_rewrite=api_enum_id_rewrite,
        )
        attr_config.type_descriptor_id = attr_config.type_descriptor.id

    _validate_no_unresolved_mirror_types(
        attribute_configs=(ac for ac, _ns in _iter_attribute_configs_with_owner_namespace(object_config_graph)),
        mirrored_source_class_ids=source_class_ids,
        mirrored_source_enum_ids=source_enum_ids,
    )


__all__ = [
    "apply_object_config_graph_mirrors",
    "apply_object_config_graph_mirrors_to_build_inputs",
]
