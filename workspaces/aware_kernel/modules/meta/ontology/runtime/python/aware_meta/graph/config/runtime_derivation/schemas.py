from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from aware_meta.graph.config.runtime_derivation.timer import RuntimeDerivationStep
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


@dataclass(frozen=True, slots=True)
class RuntimeObjectConfigGraphDerivationRequest:
    source_graph: ObjectConfigGraph
    target_language: CodeLanguage = CodeLanguage.aware
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = ()
    include_projection_graphs: bool = True
    derive_external_projection_graphs: bool = True
    source_is_runtime: bool = False
    reuse_external_runtime_graphs: bool = False
    progress_callback: Callable[[Mapping[str, object]], None] | None = field(
        default=None,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, slots=True)
class RuntimeObjectConfigGraphDerivationResult:
    source_graph: ObjectConfigGraph
    runtime_graph: ObjectConfigGraph
    runtime_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    source_graph_role: str = "compiler_ir"
    runtime_graph_role: str = "runtime_ocg"
    source_language: CodeLanguage = CodeLanguage.aware
    runtime_language: CodeLanguage = CodeLanguage.aware
    source_graph_hash: str | None = None
    runtime_graph_hash: str | None = None
    timings: tuple[RuntimeDerivationStep, ...] = field(default_factory=tuple)
    metrics: dict[str, object] = field(default_factory=dict)


__all__ = [
    "RuntimeObjectConfigGraphDerivationRequest",
    "RuntimeObjectConfigGraphDerivationResult",
]
