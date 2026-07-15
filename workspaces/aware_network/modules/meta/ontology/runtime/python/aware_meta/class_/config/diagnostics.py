from __future__ import annotations

from collections.abc import Iterable, Mapping
from uuid import UUID

from aware_meta.semantic_diagnostics import MetaSemanticDiagnostic
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)


def collect_class_constructor_completeness_diagnostics(
    *,
    object_config_graph: ObjectConfigGraph,
    external_graphs: Iterable[ObjectConfigGraph] = (),
    severity: str = "warning",
    source_path_by_code_id: Mapping[UUID, str] | None = None,
) -> tuple[MetaSemanticDiagnostic, ...]:
    diagnostics: list[MetaSemanticDiagnostic] = []
    for class_config in _iter_concrete_class_configs(
        object_config_graph,
        external_graphs=external_graphs,
    ):
        if _has_constructor(class_config):
            continue
        diagnostics.append(
            MetaSemanticDiagnostic(
                severity=severity,
                code="aware_meta.completeness.class_missing_constructor",
                message=(
                    "ClassConfig has no constructor function: "
                    f"{_class_label(class_config)}"
                ),
                source_path=_source_path_for_class(
                    class_config=class_config,
                    source_path_by_code_id=source_path_by_code_id or {},
                ),
            )
        )
    return tuple(diagnostics)


def _iter_concrete_class_configs(
    object_config_graph: ObjectConfigGraph,
    *,
    external_graphs: Iterable[ObjectConfigGraph],
) -> tuple[ClassConfig, ...]:
    class_configs: list[ClassConfig] = []
    seen: set[UUID] = set()
    for graph in (object_config_graph, *tuple(external_graphs)):
        for node in graph.object_config_graph_nodes or []:
            if node.type != ObjectConfigGraphNodeType.class_:
                continue
            class_config = node.class_config
            if class_config is None:
                continue
            if class_config.id in seen:
                continue
            if _is_constructor_exempt(class_config):
                continue
            seen.add(class_config.id)
            class_configs.append(class_config)
    return tuple(class_configs)


def _is_constructor_exempt(class_config: ClassConfig) -> bool:
    if class_config.value_mode == ClassValueMode.inline_value:
        return True
    return False


def _has_constructor(class_config: ClassConfig) -> bool:
    return any(
        bool(function_link.is_constructor)
        for function_link in (class_config.class_config_function_configs or [])
    )


def _source_path_for_class(
    *,
    class_config: ClassConfig,
    source_path_by_code_id: Mapping[UUID, str],
) -> str | None:
    code_section_class = getattr(class_config, "code_section_class", None)
    code_section = getattr(code_section_class, "code_section", None)
    code_id = getattr(code_section, "code_id", None)
    if not isinstance(code_id, UUID):
        return None
    return source_path_by_code_id.get(code_id)


def _class_label(class_config: ClassConfig) -> str:
    return (class_config.class_fqn or class_config.name or str(class_config.id)).strip()


__all__ = [
    "collect_class_constructor_completeness_diagnostics",
]
