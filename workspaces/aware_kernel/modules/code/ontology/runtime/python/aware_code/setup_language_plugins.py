"""Configuration for supported code languages using the shared plugin registry."""

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.module_plugin_registry import AwareModulePluginRegistry


def setup_code_plugins() -> None:
    """Initialize and register all code language plugins."""
    for plugin in AwareModulePluginRegistry.get_builtin_code_language_plugins():
        CodeLanguagePluginRegistry.register(plugin)
