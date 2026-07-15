from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.language_plugin import MetaLanguagePlugin
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry


def test_meta_language_plugin_registry_uses_reload_stable_language_key() -> None:
    saved_plugins = dict(MetaLanguagePluginRegistry._plugins)
    saved_supported = set(MetaLanguagePluginRegistry._supported_languages)
    saved_file_filters = dict(MetaLanguagePluginRegistry._file_filter_overrides)
    saved_structural_filters = dict(
        MetaLanguagePluginRegistry._structural_filter_overrides
    )
    MetaLanguagePluginRegistry.clear()
    try:
        plugin = cast(
            MetaLanguagePlugin,
            SimpleNamespace(language=CodeLanguage.aware),
        )

        class ReloadedAwareLanguage:
            value = "aware"

        MetaLanguagePluginRegistry.register(plugin)

        assert (
            MetaLanguagePluginRegistry.get(cast(CodeLanguage, ReloadedAwareLanguage()))
            is plugin
        )
        assert MetaLanguagePluginRegistry.has_language(
            cast(CodeLanguage, ReloadedAwareLanguage())
        )
    finally:
        MetaLanguagePluginRegistry.clear()
        MetaLanguagePluginRegistry._plugins.update(saved_plugins)
        MetaLanguagePluginRegistry._supported_languages.update(saved_supported)
        MetaLanguagePluginRegistry._file_filter_overrides.update(saved_file_filters)
        MetaLanguagePluginRegistry._structural_filter_overrides.update(
            saved_structural_filters
        )
