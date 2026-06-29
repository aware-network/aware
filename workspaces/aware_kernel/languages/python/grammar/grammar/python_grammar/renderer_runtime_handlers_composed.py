"""
Composed runtime-handlers renderer.

Default rail stays manual/dev-owned (`runtime_handlers`).
Optional rail enables FunctionImpl-derived logic rendering (`runtime_handlers_aware`).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from python_grammar.renderer_runtime_handlers import PythonRendererRuntimeHandlers
from python_grammar.renderer_runtime_handlers_aware import (
    PythonRendererRuntimeHandlersAware,
)


class PythonRendererRuntimeHandlersComposed:
    """
    Composition shell that keeps manual renderer as default and allows optional
    FunctionImpl-aware rendering through env selection.
    """

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        mode = (os.getenv("AWARE_PY_RUNTIME_HANDLERS_BACKEND") or "manual").strip().lower()
        self._env_mode = "aware" if mode == "aware" else "manual"
        self._selected_mode = self._env_mode
        self._delegate = self._build_delegate(mode=self._selected_mode, layout_strategy=layout_strategy)

    def _build_delegate(
        self, *, mode: str, layout_strategy: ObjectConfigGraphRenderLayoutStrategy
    ) -> PythonRendererRuntimeHandlers | PythonRendererRuntimeHandlersAware:
        if mode == "aware":
            return PythonRendererRuntimeHandlersAware(layout_strategy=layout_strategy)
        return PythonRendererRuntimeHandlers(layout_strategy=layout_strategy)

    def _switch_delegate(self, *, mode: str) -> None:
        mode_norm = "aware" if mode == "aware" else "manual"
        if mode_norm == self._selected_mode:
            return
        previous = self._delegate
        replacement = self._build_delegate(mode=mode_norm, layout_strategy=self.layout_strategy)
        replacement.import_overrides = previous.import_overrides
        replacement.bind_profile_inputs(previous.profile_inputs)
        replacement.overlays_by_entity_id = previous.overlays_by_entity_id
        replacement.external_class_lookup = previous.external_class_lookup
        replacement.external_graphs = previous.external_graphs
        self._delegate = replacement
        self._selected_mode = mode_norm

    @property
    def layout_strategy(self) -> ObjectConfigGraphRenderLayoutStrategy:
        return self._delegate.layout_strategy

    @layout_strategy.setter
    def layout_strategy(self, value: ObjectConfigGraphRenderLayoutStrategy) -> None:
        self._delegate.layout_strategy = value

    @property
    def import_overrides(self) -> dict[str, str] | None:
        return self._delegate.import_overrides

    @import_overrides.setter
    def import_overrides(self, value: dict[str, str] | None) -> None:
        self._delegate.import_overrides = value

    @property
    def profile_inputs(self) -> dict[str, object]:
        return self._delegate.profile_inputs

    @property
    def overlays_by_entity_id(self):
        return self._delegate.overlays_by_entity_id

    @overlays_by_entity_id.setter
    def overlays_by_entity_id(self, value) -> None:
        self._delegate.overlays_by_entity_id = value

    @property
    def external_class_lookup(self) -> dict[UUID, ClassConfig]:
        return self._delegate.external_class_lookup

    @external_class_lookup.setter
    def external_class_lookup(self, value: dict[UUID, ClassConfig]) -> None:
        self._delegate.external_class_lookup = value

    @property
    def external_graphs(self) -> list[ObjectConfigGraph]:
        return self._delegate.external_graphs

    @external_graphs.setter
    def external_graphs(self, value: list[ObjectConfigGraph]) -> None:
        self._delegate.external_graphs = value

    @property
    def language(self) -> CodeLanguage:
        return self._delegate.language

    @property
    def indent(self) -> int:
        return self._delegate.indent

    @property
    def comment_prefix(self) -> str:
        return self._delegate.comment_prefix

    def define_assemblers(self):
        return self._delegate.define_assemblers()

    def set_policy(self, policy) -> None:
        policy_map = policy if isinstance(policy, dict) else {}
        ownership_raw = policy_map.get("function_impl_ownership")
        ownership = str(ownership_raw).strip().lower() if ownership_raw is not None else None
        if ownership == "compiler":
            self._switch_delegate(mode="aware")
        elif ownership == "authored":
            self._switch_delegate(mode="manual")
        else:
            self._switch_delegate(mode=self._env_mode)
        self._delegate.set_policy(policy)

    def bind_profile_inputs(self, profile_inputs: Mapping[str, object]) -> None:
        self._delegate.bind_profile_inputs(profile_inputs)

    def set_external_class_lookup(self, external_class_lookup: dict[UUID, ClassConfig]) -> None:
        self._delegate.set_external_class_lookup(external_class_lookup)

    def set_external_graphs(self, external_graphs: list[ObjectConfigGraph]) -> None:
        self._delegate.set_external_graphs(external_graphs)

    def emit_file(
        self,
        meta_objects: list[Any],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        self._delegate.emit_file(
            meta_objects=meta_objects,
            writer=writer,
            schema=schema,
            class_to_class_config_map=class_to_class_config_map,
            base_class_module=base_class_module,
            base_class_name=base_class_name,
        )

    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._delegate.bind_object_config_graph(graph)

    def extra_output_paths(self) -> list[Path]:
        return self._delegate.extra_output_paths()

    def create_empty_code(self) -> Code:
        return self._delegate.create_empty_code()

    def clear_warnings(self) -> None:
        self._delegate.clear_warnings()

    def get_warnings(self) -> list[str]:
        return self._delegate.get_warnings()

    def validate_existing_output(
        self,
        *,
        relative_path: Path,
        output_path: Path,
        generated_source: str,
        existing_source: str,
    ) -> None:
        self._delegate.validate_existing_output(
            relative_path=relative_path,
            output_path=output_path,
            generated_source=generated_source,
            existing_source=existing_source,
        )

    def get_overlay_by_entity_id(self, entity, id: UUID):
        return self._delegate.get_overlay_by_entity_id(entity, id)

    def set_language_overlay(self, overlay) -> None:
        self._delegate.set_language_overlay(overlay)


__all__ = ["PythonRendererRuntimeHandlersComposed"]
