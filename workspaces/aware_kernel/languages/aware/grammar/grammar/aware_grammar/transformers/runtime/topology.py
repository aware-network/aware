"""Runtime topology stage for the Aware runtime transformer."""

from __future__ import annotations

from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

from aware_grammar.transformers.runtime.context import RuntimeTransformContext


def materialize_runtime_topology(
    *,
    ctx: RuntimeTransformContext,
    code_primitive_type: type[CodePrimitiveType] | None = None,
) -> None:
    """Materialize honest runtime topology before function-surface lowering."""

    reference_ports = ctx.support.index_reference_ports(ctx.source_graph)
    reference_binds = ctx.support.index_reference_binds(ctx.source_graph)

    ctx.support.apply_relationship_loading_overrides(ctx.analyses)
    ctx.support.apply_forward_pointer_representation_semantics(ctx.analyses)
    ctx.support.materialize_reverse_views(ctx.analyses)
    ctx.support.materialize_foreign_keys_and_edges(
        ctx.analyses,
        code_primitive_type=code_primitive_type,
        fk_overrides_by_key=ctx.fk_overrides_by_key,
        rel_name_overrides_by_key=ctx.rel_name_overrides_by_key,
        local_class_ids=ctx.local_class_ids,
        reference_ports=reference_ports,
        reference_binds=reference_binds,
    )
    ctx.relationships, ctx.object_config_graph_relationships = ctx.support.reify_association_edges(
        analyses=ctx.analyses,
        relationships=ctx.relationships,
        object_config_graph_relationships=ctx.object_config_graph_relationships,
        local_class_ids=ctx.local_class_ids,
    )
    ctx.support.sync_class_relationship_views(
        class_configs=ctx.class_configs,
        relationships=ctx.relationships,
        analyses=ctx.analyses,
        object_config_graph_relationships=ctx.object_config_graph_relationships,
    )
    ctx.support.normalize_attribute_positions(
        class_configs=ctx.class_configs,
        analyses=ctx.analyses,
    )


__all__ = ["materialize_runtime_topology"]
