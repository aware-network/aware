from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from aware_environment_service.service_plugins.base import (
    EnvironmentServicePlugin,
    EnvironmentServiceTransport,
)
from aware_service_runtime.registry import (
    create_plugins as create_runtime_plugins,
    discover_plugins as discover_runtime_plugins,
    ensure_service_surface_paths_on_syspath as ensure_runtime_service_surface_paths_on_syspath,
    register_plugin as register_runtime_plugin,
    reset_plugin_registry_for_tests as reset_runtime_plugin_registry_for_tests,
)

_PluginT = TypeVar("_PluginT", bound=object)
_PLUGIN_PROVIDERS_ENV = "AWARE_ENVIRONMENT_SERVICE_PLUGIN_PROVIDERS"
_ENABLED_SERVICES_ENV = "AWARE_ENVIRONMENT_SERVICE_ENABLED_SERVICES"


def register_plugin(
    cls: type[_PluginT],
) -> type[_PluginT]:
    return register_runtime_plugin(cls)


def ensure_service_surface_paths_on_syspath(
    *,
    service_surface_paths: tuple[Path, ...],
) -> None:
    ensure_runtime_service_surface_paths_on_syspath(
        service_surface_paths=service_surface_paths
    )


def discover_plugins(
    *,
    provider_modules: tuple[str, ...],
    service_surface_paths: tuple[Path, ...],
) -> None:
    discover_runtime_plugins(
        provider_modules=provider_modules,
        service_surface_paths=service_surface_paths,
    )


def create_plugins(
    *,
    transport: EnvironmentServiceTransport,
    provider_modules: tuple[str, ...] | None = None,
    service_surface_paths: tuple[Path, ...] = (),
) -> dict[str, EnvironmentServicePlugin]:
    return create_runtime_plugins(
        transport=transport,
        provider_modules=provider_modules,
        service_surface_paths=service_surface_paths,
        providers_env_var=_PLUGIN_PROVIDERS_ENV,
        enabled_services_env_var=_ENABLED_SERVICES_ENV,
    )


def reset_plugin_registry_for_tests() -> None:
    reset_runtime_plugin_registry_for_tests()
