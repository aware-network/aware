"""Canonical transformer that projects Aware OCG into an OOP-ready runtime structure."""

from typing import override
from uuid import UUID

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.class_.config.relationship_side_loading_config import (
    ClassConfigRelationshipSideLoadingConfig,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from aware_grammar.transformers.runtime import (
    RuntimeFunctionSurfaceSupport,
    RuntimeTransformSupport,
    build_runtime_output_graph,
    build_runtime_transform_context,
    materialize_runtime_function_surface,
    materialize_runtime_topology,
)


class AwareToRuntimeTransformer(ObjectConfigGraphTransformer):
    """Thin environment over the staged Aware runtime-transform pipeline."""

    def __init__(
        self,
        *,
        relationship_loading_config: ClassConfigRelationshipSideLoadingConfig | None = None,
        namespace_by_code_id: dict[UUID, NamespacePath] | None = None,
        external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
    ):
        self.relationship_loading_config = relationship_loading_config
        self.namespace_by_code_id = namespace_by_code_id
        self.external_graphs_by_id = external_graphs_by_id
        self._runtime_support = RuntimeTransformSupport(
            relationship_loading_config=relationship_loading_config,
            namespace_by_code_id=namespace_by_code_id,
            external_graphs_by_id=external_graphs_by_id,
        )
        self._runtime_function_surface_support = RuntimeFunctionSurfaceSupport(
            support=self._runtime_support,
        )

    @override
    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: type[CodePrimitiveType] | None = None,
    ) -> ObjectConfigGraph:
        ctx = build_runtime_transform_context(
            support=self._runtime_support,
            function_surface_support=self._runtime_function_surface_support,
            source_graph=object_config_graph,
        )
        materialize_runtime_topology(
            ctx=ctx,
            code_primitive_type=code_primitive_type,
        )
        materialize_runtime_function_surface(ctx=ctx)
        return build_runtime_output_graph(ctx=ctx)


__all__ = ["AwareToRuntimeTransformer"]
