"""Runtime-transform stage package for Aware -> runtime OCG derivation."""

from aware_grammar.transformers.runtime.context import (
    RuntimeTransformContext,
    build_runtime_transform_context,
)
from aware_grammar.transformers.runtime.function_surface import materialize_runtime_function_surface
from aware_grammar.transformers.runtime.function_surface_support import RuntimeFunctionSurfaceSupport
from aware_grammar.transformers.runtime.output import build_runtime_output_graph
from aware_grammar.transformers.runtime.support import RuntimeTransformSupport
from aware_grammar.transformers.runtime.topology import materialize_runtime_topology

__all__ = [
    "RuntimeFunctionSurfaceSupport",
    "RuntimeTransformSupport",
    "RuntimeTransformContext",
    "build_runtime_output_graph",
    "build_runtime_transform_context",
    "materialize_runtime_function_surface",
    "materialize_runtime_topology",
]
