# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta.graph.config.namespace_index import build_node_namespace_by_node_id
from aware_meta.graph.config.model_bootstrap import get_node_function_config


def describe_object_config_graph(ocg: ObjectConfigGraph) -> list[str]:
    descriptions: list[str] = []

    class_configs: list[ClassConfig] = []
    function_configs: list[FunctionConfig] = []
    enum_configs: list[EnumConfig] = []
    namespace_counts: dict[str, int] = {}
    namespace_by_node_id = build_node_namespace_by_node_id(ocg)
    for node in ocg.object_config_graph_nodes:
        if node.type == ObjectConfigGraphNodeType.class_:
            if node.class_config is None:
                raise ValueError(f"ClassConfig not found for node {node.id}")
            class_configs.append(node.class_config)
        elif node.type == ObjectConfigGraphNodeType.function:
            node_function_config = get_node_function_config(node)
            if node_function_config is None:
                raise ValueError(f"FunctionConfig not found for node {node.id}")
            function_configs.append(node_function_config)
        elif node.type == ObjectConfigGraphNodeType.enum:
            if node.enum_config is None:
                raise ValueError(f"EnumConfig not found for node {node.id}")
            enum_configs.append(node.enum_config)
        namespace = namespace_by_node_id.get(node.id)
        if namespace is not None:
            namespace_counts[namespace.prefix()] = (
                namespace_counts.get(namespace.prefix(), 0) + 1
            )

    descriptions.append(f"Total class configs: {len(class_configs)}")
    descriptions.append(f"Total enum configs: {len(enum_configs)}")
    if len(function_configs) > 0:
        descriptions.append(f"Total function configs: {len(function_configs)}")
    if namespace_counts:
        descriptions.append(f"Total namespaces: {len(namespace_counts)}")
        for namespace, count in sorted(namespace_counts.items()):
            descriptions.append(f"- Namespace: {namespace} ({count} nodes)")
    return descriptions
