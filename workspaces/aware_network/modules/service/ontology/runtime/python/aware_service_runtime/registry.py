from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Final, TypeVar, cast

from aware_service_runtime.contracts import (
    ServiceHostTransport,
    ServiceOperationPluginHandler,
)
from aware_utils.logging import logger

_plugin_classes: dict[str, type[object]] = {}
_discovered: bool = False

_PluginT = TypeVar("_PluginT", bound=object)
DEFAULT_PLUGIN_PROVIDERS_ENV: Final[str] = "AWARE_SERVICE_PLUGIN_PROVIDERS"
DEFAULT_ENABLED_SERVICES_ENV: Final[str] = "AWARE_SERVICE_ENABLED_SERVICES"


def register_plugin(
    cls: type[_PluginT],
) -> type[_PluginT]:
    service = getattr(cls, "service", None)
    if not isinstance(service, str) or not service:
        raise ValueError(f"Invalid plugin service name for {cls}")

    existing = _plugin_classes.get(service)
    if existing is not None and existing is not cls:
        raise ValueError(
            f"Duplicate ServiceOperationPlugin registration for service={service}: {existing} vs {cls}"
        )

    _plugin_classes[service] = cls
    return cls


def ensure_service_surface_paths_on_syspath(
    *,
    service_surface_paths: tuple[Path, ...],
) -> None:
    """Ensure declared service-surface roots are importable."""
    for service_surface_path in service_surface_paths:
        resolved = service_surface_path.resolve()
        if not resolved.exists() or not resolved.is_dir():
            continue
        service_root_str = resolved.as_posix()
        if service_root_str in sys.path:
            continue
        sys.path.insert(0, service_root_str)


def discover_plugins(
    *,
    provider_modules: tuple[str, ...],
    service_surface_paths: tuple[Path, ...],
) -> None:
    global _discovered
    if _discovered:
        return
    ensure_service_surface_paths_on_syspath(
        service_surface_paths=service_surface_paths
    )

    for module_name in provider_modules:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name != module_name:
                raise
            logger.warning("Service plugin provider module not found: %s", module_name)
            continue
        register_plugins = getattr(module, "register_plugins", None)
        if callable(register_plugins):
            _ = register_plugins(register_plugin)

    if provider_modules and not _plugin_classes:
        raise RuntimeError(
            "No ServiceOperationPlugin implementations discovered. "
            f"Configured providers={provider_modules!r}"
        )

    _discovered = True


def create_plugins(
    *,
    transport: ServiceHostTransport,
    provider_modules: tuple[str, ...] | None = None,
    service_surface_paths: tuple[Path, ...] = (),
    providers_env_var: str = DEFAULT_PLUGIN_PROVIDERS_ENV,
    enabled_services_env_var: str = DEFAULT_ENABLED_SERVICES_ENV,
) -> dict[str, ServiceOperationPluginHandler]:
    provider_modules_resolved = _provider_modules(
        manifest_provider_modules=provider_modules,
        providers_env_var=providers_env_var,
    )
    discover_plugins(
        provider_modules=provider_modules_resolved,
        service_surface_paths=service_surface_paths,
    )
    plugin_classes = dict(sorted(_plugin_classes.items()))
    enabled_services = _enabled_services_filter(
        enabled_services_env_var=enabled_services_env_var
    )
    if enabled_services is None:
        selected_classes = plugin_classes
    else:
        selected_classes = {
            service: cls
            for service, cls in plugin_classes.items()
            if service in enabled_services
        }
    plugins: dict[str, ServiceOperationPluginHandler] = {}
    for service, cls in selected_classes.items():
        plugin = cast(
            ServiceOperationPluginHandler,
            cls(transport=transport),  # pyright: ignore[reportCallIssue]
        )
        plugins[service] = plugin
    if enabled_services is None:
        return plugins
    missing_services = sorted(enabled_services.difference(plugin_classes))
    if missing_services:
        logger.warning(
            "Configured service filter has unknown services: %s",
            missing_services,
        )
    filtered = {
        service: plugin
        for service, plugin in plugins.items()
        if service in enabled_services
    }
    logger.info(
        "Service plugin filter enabled (%s=%s): loaded=%s",
        enabled_services_env_var,
        sorted(enabled_services),
        sorted(filtered),
    )
    return filtered


def reset_plugin_registry_for_tests() -> None:
    """Test-only helper to isolate provider discovery state between cases."""
    global _discovered
    _plugin_classes.clear()
    _discovered = False


def _provider_modules(
    *,
    manifest_provider_modules: tuple[str, ...] | None,
    providers_env_var: str,
) -> tuple[str, ...]:
    raw = (os.environ.get(providers_env_var) or "").strip()
    if not raw:
        return _dedupe_modules(manifest_provider_modules or ())
    configured = tuple(token.strip() for token in raw.split(",") if token.strip())
    return _dedupe_modules(configured)


def _enabled_services_filter(
    *,
    enabled_services_env_var: str,
) -> set[str] | None:
    raw = (os.environ.get(enabled_services_env_var) or "").strip()
    if not raw:
        return None
    enabled = {token.strip() for token in raw.split(",") if token.strip()}
    return enabled or None


def _dedupe_modules(modules: tuple[str, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for module in modules:
        token = str(module).strip()
        if not token or token in seen:
            continue
        deduped.append(token)
        seen.add(token)
    return tuple(deduped)
