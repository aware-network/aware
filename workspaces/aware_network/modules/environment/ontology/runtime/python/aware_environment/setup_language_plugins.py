"""Configuration for supported languages using the shared plugin registry."""

# Primitive Code Plugin Registry
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.module_plugin_registry import AwareModulePluginRegistry

# Meta Plugin System
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry


def setup_code_plugins() -> None:
    """
    Initialize and register all code language plugins.
    """
    for plugin in AwareModulePluginRegistry.get_builtin_code_language_plugins():
        CodeLanguagePluginRegistry.register(plugin)


def setup_meta_plugins() -> None:
    """
    Initialize and register all meta language plugins.

    This function should be called once at application startup to register
    all language-specific meta plugins with the MetaLanguagePluginRegistry.
    """

    for plugin in AwareModulePluginRegistry.get_builtin_meta_language_plugins():
        MetaLanguagePluginRegistry.register(plugin)


def setup_language_plugins() -> None:
    """
    Initialize and register all language plugins.
    """
    setup_code_plugins()
    setup_meta_plugins()
