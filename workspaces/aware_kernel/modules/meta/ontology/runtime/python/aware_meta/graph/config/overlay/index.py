from __future__ import annotations

# Standard
from dataclasses import dataclass
from uuid import UUID

# META
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.enum.enum_option import EnumOption

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.model_bootstrap import get_node_function_config

from aware_utils.logging import logger


@dataclass
class ObjectConfigGraphIndexForOverlay:
    # Path = {package}.{namespace}.{class_name}
    classes: dict[str, ClassConfig]
    # Path = {package}.{namespace}.{class_name}.{attribute_name}
    attributes: dict[str, AttributeConfig]
    # Path = {package}.{namespace}.{class_name}.{function_name}
    functions: dict[str, FunctionConfig]
    # Path = {package}.{namespace}.{class_name}.{function_name}.{attribute_name}
    function_attributes: dict[str, AttributeConfig]
    # Path = {package}.{namespace}.{enum_name}
    enums: dict[str, EnumConfig]
    # Path = {package}.{namespace}.{enum_name}.{enum_option_name}
    enum_options: dict[str, EnumOption]


def index_ocg_for_overlay(
    graph: ObjectConfigGraph,
    *,
    namespace_by_class_config_id: dict[UUID, NamespacePath] | None = None,
    namespace_by_enum_config_id: dict[UUID, NamespacePath] | None = None,
    namespace_by_function_config_id: dict[UUID, NamespacePath] | None = None,
) -> ObjectConfigGraphIndexForOverlay:
    classes: dict[str, ClassConfig] = {}
    enums: dict[str, EnumConfig] = {}
    attributes: dict[str, AttributeConfig] = {}
    functions: dict[str, FunctionConfig] = {}
    function_attributes: dict[str, AttributeConfig] = {}
    enum_options: dict[str, EnumOption] = {}
    for cls in get_class_configs(graph):
        if namespace_by_class_config_id is None:
            raise ValueError(
                "index_ocg_for_overlay requires namespace_by_class_config_id (meta-time namespaces). "
                "Callers must supply an ObjectConfigGraphNamespaceBundle."
            )
        ns = namespace_by_class_config_id.get(cls.id)
        if ns is None:
            raise ValueError(
                f"ClassConfig {cls.id} missing namespace for overlay indexing (class={cls.name}). "
                "This indicates incomplete namespace metadata on the graph."
            )
        prefix = ns.prefix()

        key = f"{prefix}.{cls.name}"
        classes.setdefault(key, cls)
        for link in cls.class_config_attribute_configs:
            attr = link.attribute_config
            if attr:
                key = f"{prefix}.{cls.name}.{attr.name}"
                attributes.setdefault(key, attr)
        for link in cls.class_config_function_configs:
            fn = link.function_config
            if fn:
                key = f"{prefix}.{cls.name}.{fn.name}"
                functions.setdefault(key, fn)
                # Index function argument/result AttributeConfigs so overlays can rename them
                # (e.g., to avoid reserved words like `schema` in Python BaseModel).
                for fn_attr_edge in fn.function_config_attribute_configs:
                    ac = fn_attr_edge.attribute_config
                    key = f"{prefix}.{cls.name}.{fn.name}.{ac.name}"
                    function_attributes.setdefault(key, ac)
    for ec in get_enum_configs(graph):
        if namespace_by_enum_config_id is None:
            raise ValueError(
                "index_ocg_for_overlay requires namespace_by_enum_config_id (meta-time namespaces). "
                "Callers must supply an ObjectConfigGraphNamespaceBundle."
            )
        ns = namespace_by_enum_config_id.get(ec.id)
        if ns is None:
            raise ValueError(
                f"EnumConfig {ec.id} missing namespace for overlay indexing (enum={ec.name}). "
                "This indicates incomplete namespace metadata on the graph."
            )
        prefix = ns.prefix()
        key = f"{prefix}.{ec.name}"
        enums.setdefault(key, ec)
        for opt in ec.enum_options:
            key = f"{prefix}.{ec.name}.{opt.value}"
            enum_options.setdefault(key, opt)

    # Note: function overlays are indexed through owning class prefixes.
    # `namespace_by_function_config_id` is reserved for future use when/if we allow global function overlays.
    return ObjectConfigGraphIndexForOverlay(
        classes=classes,
        enums=enums,
        attributes=attributes,
        functions=functions,
        function_attributes=function_attributes,
        enum_options=enum_options,
    )


def get_enum_configs(ocg: ObjectConfigGraph) -> list[EnumConfig]:
    enum_configs: list[EnumConfig] = []
    for node in ocg.object_config_graph_nodes:
        if node.enum_config is not None:
            enum_configs.append(node.enum_config)
    return enum_configs


def get_function_configs(ocg: ObjectConfigGraph) -> list[FunctionConfig]:
    return [
        function_config
        for n in ocg.object_config_graph_nodes
        if (function_config := get_node_function_config(n)) is not None
    ]


def get_class_configs(ocg: ObjectConfigGraph) -> list[ClassConfig]:
    return [n.class_config for n in ocg.object_config_graph_nodes if n.class_config is not None]


def get_class_config_relationshipships(
    ocg: ObjectConfigGraph,
) -> list[ClassConfigRelationship]:
    return [
        n.class_config_relationship for n in ocg.object_config_graph_nodes if n.class_config_relationship is not None
    ]
