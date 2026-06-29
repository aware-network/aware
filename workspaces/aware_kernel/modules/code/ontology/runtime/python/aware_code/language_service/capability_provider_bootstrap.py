from __future__ import annotations

from aware_code.module_plugin_registry import AwareModulePluginRegistry


def ensure_builtin_language_service_capability_providers_registered() -> None:
    AwareModulePluginRegistry.ensure_builtin_plugins_registered()


__all__ = ["ensure_builtin_language_service_capability_providers_registered"]
