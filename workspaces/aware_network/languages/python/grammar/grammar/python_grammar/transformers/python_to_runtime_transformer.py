"""Python -> Runtime IR transformer (composite, honest).

Honesty contract:
- Runtime IR is the shared, language-agnostic derived graph used for materialization.
- For Python inputs, we normalize Python -> canonical AWARE, then derive runtime IR from AWARE.
"""

from uuid import UUID

# Kernel Graph Ontology
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig

# Meta Runtime
from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer
from aware_meta.graph.config.builder import build_object_config_graph
from aware_meta.graph.config.namespace.builder import build_namespace_bundle_from_code_provenance
from aware_meta.fqn_resolver import NamespacePath


# Utils
from aware_utils.logging import logger
from aware_utils.string_transform import to_camel_case
from typing_extensions import override


class PythonToRuntimeTransformer(ObjectConfigGraphTransformer):
    """
    Composite transformer:
      Python -> AWARE (canonical)
      AWARE -> Runtime IR (FK/edge synthesis)
    """

    namespace_by_code_id: dict[UUID, NamespacePath] | None

    def __init__(self, *, namespace_by_code_id: dict[UUID, NamespacePath] | None = None) -> None:
        # NOTE: PythonToAwareTransformer has no __init__; keep this lightweight and explicit.
        self.namespace_by_code_id = namespace_by_code_id

    @override
    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: type[CodePrimitiveType] | None = None,
    ) -> ObjectConfigGraph:
        """
        Convert a Python ObjectConfigGraph to AWARE ObjectConfigGraph.

        Removes virtual edge attributes that were added for Python OOP traversal,
        collapsing them back to the canonical AWARE representation.
        Also normalizes attribute names from snake_case to camelCase.
        """
        # Create a copy of the Python graph
        class_configs: list[ClassConfig] = []
        enum_configs: list[EnumConfig] = []
        function_configs: list[FunctionConfig] = []

        # Copy all object configs
        for graph_node in object_config_graph.object_config_graph_nodes:
            if graph_node.type == ObjectConfigGraphNodeType.class_:
                if graph_node.class_config is None:
                    raise ValueError(f"Class config is None for node {graph_node.id}")
                class_configs.append(graph_node.class_config)
            elif graph_node.type == ObjectConfigGraphNodeType.enum:
                if graph_node.enum_config is None:
                    raise ValueError(f"Enum config is None for node {graph_node.id}")
                enum_configs.append(graph_node.enum_config)
            elif graph_node.type == ObjectConfigGraphNodeType.function:
                if graph_node.function_config is None:
                    raise ValueError(f"Function config is None for node {graph_node.id}")
                function_configs.append(graph_node.function_config)

        # Normalize attribute names to Aware conventions (snake_case → camelCase)
        self._normalize_attribute_names(class_configs)

        # Remove virtual edge attributes
        self._remove_virtual_edge_attributes(class_configs)

        # Build the AWARE object config graph
        namespace_bundle = build_namespace_bundle_from_code_provenance(
            namespace_by_code_id=self.namespace_by_code_id or {},
            class_configs=class_configs,
            enum_configs=enum_configs,
            function_configs=function_configs,
        )
        return build_object_config_graph(
            language=object_config_graph.language,
            fqn_prefix=object_config_graph.fqn_prefix,
            name=object_config_graph.name,
            description=object_config_graph.description,
            class_configs=class_configs,
            class_config_relationships=[],
            enum_configs=enum_configs,
            function_configs=function_configs,
            namespace_bundle=namespace_bundle,
            source_graph=object_config_graph,
        )

    def _normalize_attribute_names(self, class_configs: list[ClassConfig]):
        """
        Normalize attribute names from Python snake_case to Aware camelCase.

        Args:
            class_configs: List of class configs to process
        """
        for class_config in class_configs:
            for class_config_attribute_config in class_config.class_config_attribute_configs:
                attribute_config = class_config_attribute_config.attribute_config
                original_name = attribute_config.name

                # Convert snake_case to camelCase
                normalized_name = to_camel_case(original_name)

                if original_name != normalized_name:
                    attribute_config.name = normalized_name
                    logger.debug(
                        f"Normalized attribute name: '{original_name}' → '{normalized_name}' in {class_config.name}"
                    )

    def _remove_virtual_edge_attributes(self, class_configs: list[ClassConfig]):
        """
        Remove virtual edge attributes that reference association objects (edges).

        Args:
            class_configs: List of class configs to process
        """
        # Build a set of edge class config IDs for quick lookup
        edge_class_config_ids: set[UUID] = set()
        for class_config in class_configs:
            if class_config.is_edge:
                edge_class_config_ids.add(class_config.id)

        # Process each class config
        for class_config in class_configs:
            self._remove_edge_attributes_from_class(class_config, edge_class_config_ids)

    def _remove_edge_attributes_from_class(self, class_config: ClassConfig, edge_class_config_ids: set[UUID]):
        """
        Remove virtual edge attributes from a specific class config.

        Args:
            class_config: The class config to process
            edge_class_config_ids: Set of edge class config IDs for identification
        """
        # Find attributes to remove
        class_config_attribute_configs_to_remove: list[ClassConfigAttributeConfig] = []

        for class_config_attribute_config in class_config.class_config_attribute_configs:
            attribute_config = class_config_attribute_config.attribute_config

            # Check if this is a virtual edge attribute
            if self._is_virtual_edge_attribute(attribute_config, edge_class_config_ids):
                class_config_attribute_configs_to_remove.append(class_config_attribute_config)
                logger.debug(
                    f"Marking virtual edge attribute '{attribute_config.name}' for removal from {class_config.name}"
                )

        # Remove the identified attributes
        for class_config_attribute_config_to_remove in class_config_attribute_configs_to_remove:
            class_config.class_config_attribute_configs.remove(class_config_attribute_config_to_remove)
            removed_name = class_config_attribute_config_to_remove.attribute_config.name
            logger.debug(
                f"Removed virtual edge attribute '{removed_name}' from {class_config.name}"
            )

    def _is_virtual_edge_attribute(self, attribute_config: AttributeConfig, edge_class_config_ids: set[UUID]) -> bool:
        """
        Determine if an attribute is a virtual edge attribute.

        Args:
            attribute_config: The attribute config to check
            edge_class_config_ids: Set of edge class config IDs

        Returns:
            True if the attribute is a virtual edge attribute, False otherwise
        """
        # Must be a CLASS type attribute
        if (
            attribute_config.type_descriptor
            and attribute_config.type_descriptor.kind != AttributeTypeDescriptorKind.class_
        ):
            return False

        # Must reference an edge object
        # !! TODO: Resolve type descriptor recursively to get the class config id
        if (
            attribute_config.type_descriptor
            and attribute_config.type_descriptor.class_config_id is not None
            and attribute_config.type_descriptor.class_config is not None
        ):
            if attribute_config.type_descriptor.class_config.id in edge_class_config_ids:
                return True
        return False


__all__ = ["PythonToRuntimeTransformer"]
