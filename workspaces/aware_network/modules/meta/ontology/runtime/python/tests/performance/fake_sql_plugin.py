from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, ClassVar, cast

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_file_system.config import FilterConfig
from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer
from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


class PerfRuntimeToSqlTransformer(ObjectConfigGraphTransformer):
    calls: ClassVar[list[dict[str, object]]] = []

    def __init__(self, **kwargs: object) -> None:
        type(self).calls.append(dict(kwargs))

    def transform(
        self,
        object_config_graph: ObjectConfigGraph,
        code_primitive_type: object | None = None,
    ) -> ObjectConfigGraph:
        _ = code_primitive_type
        out = object_config_graph.model_copy(deep=True)
        out.language = CodeLanguage.sql
        out.hash = f"{object_config_graph.hash}:sql"
        return out

    def get_generated_ocg_node_manifest(self) -> None:
        return None

    def set_policy(self, policy: object | None) -> None:
        _ = policy


@contextmanager
def isolated_meta_language_plugin_registries() -> Iterator[None]:
    saved_plugins = dict(MetaLanguagePluginRegistry._plugins)
    saved_supported = set(MetaLanguagePluginRegistry._supported_languages)
    saved_file_filters = dict(MetaLanguagePluginRegistry._file_filter_overrides)
    saved_structural_filters = dict(
        MetaLanguagePluginRegistry._structural_filter_overrides
    )
    saved_code_plugins = dict(CodeLanguagePluginRegistry._plugins)
    saved_code_supported = set(CodeLanguagePluginRegistry._supported_languages)
    MetaLanguagePluginRegistry.clear()
    CodeLanguagePluginRegistry.clear()
    try:
        yield
    finally:
        MetaLanguagePluginRegistry.clear()
        CodeLanguagePluginRegistry.clear()
        MetaLanguagePluginRegistry._plugins.update(saved_plugins)
        MetaLanguagePluginRegistry._supported_languages.update(saved_supported)
        MetaLanguagePluginRegistry._file_filter_overrides.update(saved_file_filters)
        MetaLanguagePluginRegistry._structural_filter_overrides.update(
            saved_structural_filters
        )
        CodeLanguagePluginRegistry._plugins.update(saved_code_plugins)
        CodeLanguagePluginRegistry._supported_languages.update(saved_code_supported)


def register_perf_sql_plugin() -> None:
    PerfRuntimeToSqlTransformer.calls = []
    MetaLanguagePluginRegistry.register(
        MetaLanguagePlugin(
            language=CodeLanguage.sql,
            file_filter_config_factory=lambda: FilterConfig.model_validate({}),
            code_plugin=cast(
                Any,
                SimpleNamespace(
                    comment_prefix="--",
                    materialization_artifact_outputs=(),
                ),
            ),
            surgical_renderers={},
            language_renderers={},
            default_renderer_names=(),
            runtime_to_language_transformer=PerfRuntimeToSqlTransformer,
        )
    )


__all__ = [
    "PerfRuntimeToSqlTransformer",
    "isolated_meta_language_plugin_registries",
    "register_perf_sql_plugin",
]
