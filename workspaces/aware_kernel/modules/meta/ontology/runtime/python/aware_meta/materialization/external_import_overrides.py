from __future__ import annotations

from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


def language_external_import_overrides(
    *,
    target_language_plugin_id: CodeLanguage,
    materialization_source: str | None,
    language_external_graphs: tuple[ObjectConfigGraph, ...],
) -> dict[str, str]:
    """Resolve external graph entities to their generated language modules."""

    if not language_external_graphs:
        return {}
    overrides: dict[str, str] = {}
    for graph in sorted(language_external_graphs, key=lambda item: str(item.id)):
        import_root = external_language_import_root(
            graph=graph,
            target_language_plugin_id=target_language_plugin_id,
            materialization_source=materialization_source,
        )
        if not import_root:
            continue
        layout_strategy = MetaLanguagePluginRegistry.create_layout_strategy(
            target_language_plugin_id,
            Path("."),
            import_root=import_root,
        )
        layout_strategy.bind_graph(graph)
        for node in graph.object_config_graph_nodes:
            if node.class_config is not None:
                path = layout_strategy.get_class_file_path(node.class_config)
                path = _external_class_import_override_path(
                    target_language_plugin_id=target_language_plugin_id,
                    materialization_source=materialization_source,
                    path=path,
                )
                overrides[str(node.class_config.id)] = (
                    layout_strategy.get_module_import_path(path)
                )
            if node.enum_config is not None:
                path = layout_strategy.get_enum_file_path(node.enum_config)
                overrides[str(node.enum_config.id)] = (
                    layout_strategy.get_module_import_path(path)
                )
            function_config = get_node_function_config(node)
            if function_config is not None:
                path = layout_strategy.get_function_file_path(function_config)
                overrides[str(function_config.id)] = (
                    layout_strategy.get_module_import_path(path)
                )
    return dict(sorted(overrides.items()))


def external_language_import_root(
    *,
    graph: ObjectConfigGraph,
    target_language_plugin_id: CodeLanguage,
    materialization_source: str | None,
) -> str | None:
    if target_language_plugin_id not in {CodeLanguage.python, CodeLanguage.dart}:
        return None
    root = (graph.fqn_prefix or graph.name or "").strip().replace("-", "_")
    if not root:
        return None
    source = (materialization_source or "").strip().lower()
    if source == "ontology_dto":
        return f"{root}_ontology_dto"
    if source == "ontology_orm_models":
        return f"{root}_ontology_orm_models"
    if source in {"ontology", "runtime_handlers"}:
        return f"{root}_ontology"
    return root


def _external_class_import_override_path(
    *,
    target_language_plugin_id: CodeLanguage,
    materialization_source: str | None,
    path: Path,
) -> Path:
    if (
        target_language_plugin_id == CodeLanguage.dart
        and (materialization_source or "").strip().lower() == "ontology_dto"
        and path.suffix == ".dart"
        and not path.stem.endswith("_model")
    ):
        return path.with_name(f"{path.stem}_model{path.suffix}")
    return path


__all__ = [
    "external_language_import_root",
    "language_external_import_overrides",
]
