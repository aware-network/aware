from typing import Type, Protocol

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)


class ObjectConfigGraphTransformerPolicy(Protocol):
    """Base type for transformer policies (language-specific concrete policies live in language plugins)."""


class ObjectConfigGraphTransformer(Protocol):
    """Pure graph-to-graph transformer."""

    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: type[CodePrimitiveType] | None = None,
    ) -> ObjectConfigGraph:
        """
        Transform the given object config graph.

        Args:
            object_config_graph: The object config graph to transform
            code_primitive_type: The target code primitive type to use for the transformation

        Returns: The transformed object config graph
        """
        ...

    def set_policy(self, policy: ObjectConfigGraphTransformerPolicy | None) -> None:
        """Inject a language-specific transformer policy (DTO vs ORM, etc.)."""
        return None

    def get_generated_ocg_node_manifest(
        self,
    ) -> GeneratedObjectConfigGraphNodeManifest | None:
        """Return an explicit manifest of generated OCG nodes (if any)."""
        return None
