from uuid import UUID

# Kernel Graph Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig

# Meta
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.namespace_index import build_namespace_index
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle


def build_namespace_bundle_from_code_provenance(
    *,
    namespace_by_code_id: dict[UUID, NamespacePath],
    class_configs: list[ClassConfig],
    enum_configs: list[EnumConfig],
    function_configs: list[FunctionConfig],
) -> ObjectConfigGraphNamespaceBundle:
    """
    Build a namespace bundle from canonical build-time provenance pointers.

    This is the *only* place in meta that should need `code_section_*.code_id`.
    """

    ns_by_class: dict[UUID, NamespacePath] = {}
    for cc in class_configs:
        cs = cc.code_section_class
        if cs is None or cs.code_section is None:
            continue
        ns = namespace_by_code_id.get(cs.code_section.code_id)
        if ns is not None:
            ns_by_class[cc.id] = ns

    ns_by_enum: dict[UUID, NamespacePath] = {}
    for ec in enum_configs:
        cs = ec.code_section_enum
        if cs is None or cs.code_section is None:
            continue
        ns = namespace_by_code_id.get(cs.code_section.code_id)
        if ns is not None:
            ns_by_enum[ec.id] = ns

    ns_by_function: dict[UUID, NamespacePath] = {}
    for fc in function_configs:
        cs = fc.code_section_function
        if cs is None or cs.code_section is None:
            continue
        ns = namespace_by_code_id.get(cs.code_section.code_id)
        if ns is not None:
            ns_by_function[fc.id] = ns

    return ObjectConfigGraphNamespaceBundle(
        namespace_by_class_config_id=ns_by_class,
        namespace_by_enum_config_id=ns_by_enum,
        namespace_by_function_config_id=ns_by_function,
    )


def build_namespace_bundle_from_ocg_topology(*, ocg: ObjectConfigGraph) -> ObjectConfigGraphNamespaceBundle:
    """
    Build a namespace bundle from canonical OCG node FQNs.
    """
    idx = build_namespace_index(ocg)
    by_class: dict[UUID, NamespacePath] = {}
    by_enum: dict[UUID, NamespacePath] = {}
    by_fn: dict[UUID, NamespacePath] = {}
    for node in ocg.object_config_graph_nodes:
        ns = idx.node_namespace_by_node_id.get(node.id)
        if ns is None:
            continue
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            by_class[node.class_config.id] = ns
        elif node.type == ObjectConfigGraphNodeType.enum and node.enum_config is not None:
            by_enum[node.enum_config.id] = ns
        elif node.type == ObjectConfigGraphNodeType.function:
            node_function_config = get_node_function_config(node)
            if node_function_config is not None:
                by_fn[node_function_config.id] = ns

    return ObjectConfigGraphNamespaceBundle(
        namespace_by_class_config_id=by_class,
        namespace_by_enum_config_id=by_enum,
        namespace_by_function_config_id=by_fn,
    )
