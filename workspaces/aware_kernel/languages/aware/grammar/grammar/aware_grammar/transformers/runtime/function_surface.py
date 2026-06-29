"""Runtime function-surface stage for the Aware runtime transformer."""

from __future__ import annotations

from aware_grammar.transformers.runtime.context import RuntimeTransformContext


def materialize_runtime_function_surface(
    *,
    ctx: RuntimeTransformContext,
) -> None:
    """Lower runtime invocation truth and `_via_*` constructor surface."""

    ctx.function_surface_support.complete_runtime_function_resolution(
        class_configs=ctx.class_configs,
        replace_existing_body_lowering=True,
    )
    ctx.function_surface_support.materialize_path_scoped_constructors(
        source_graph=ctx.source_graph,
        class_configs=ctx.class_configs,
        function_configs=ctx.function_configs,
        relationships=ctx.relationships,
    )
    ctx.function_surface_support.complete_runtime_function_resolution(class_configs=ctx.class_configs)


__all__ = ["materialize_runtime_function_surface"]
