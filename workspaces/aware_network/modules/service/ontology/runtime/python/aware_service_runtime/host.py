from __future__ import annotations

from pathlib import Path

from aware_service_runtime.adapters.environment import (
    build_service_operation_result_from_response,
)
from aware_service_runtime.contracts import (
    ServiceHostTransport,
    ServiceOperationInvocation,
    ServiceOperationPluginHandler,
    ServiceOperationRequest,
    ServiceOperationResponse,
    ServiceOperationResult,
)
from aware_service_runtime.registry import (
    DEFAULT_ENABLED_SERVICES_ENV,
    DEFAULT_PLUGIN_PROVIDERS_ENV,
    create_plugins,
)
from aware_service_runtime.router import ServiceOperationRouter


class ServiceRuntimeHost:
    """Shared runtime core for service plugin discovery and dispatch."""

    def __init__(
        self,
        *,
        transport: ServiceHostTransport,
        providers_env_var: str = DEFAULT_PLUGIN_PROVIDERS_ENV,
        enabled_services_env_var: str = DEFAULT_ENABLED_SERVICES_ENV,
    ) -> None:
        self._transport = transport
        self._providers_env_var = providers_env_var
        self._enabled_services_env_var = enabled_services_env_var
        self._plugins: dict[str, ServiceOperationPluginHandler] = {}
        self._router = ServiceOperationRouter(plugins=self._plugins)

    def configure(
        self,
        *,
        provider_modules: tuple[str, ...] | None = None,
        service_surface_paths: tuple[Path, ...] = (),
    ) -> dict[str, ServiceOperationPluginHandler]:
        self._plugins = create_plugins(
            transport=self._transport,
            provider_modules=provider_modules,
            service_surface_paths=service_surface_paths,
            providers_env_var=self._providers_env_var,
            enabled_services_env_var=self._enabled_services_env_var,
        )
        self._router = ServiceOperationRouter(plugins=self._plugins)
        return dict(self._plugins)

    @property
    def plugin_services(self) -> tuple[str, ...]:
        return self._router.list_services()

    async def handle_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse:
        return await self._router.handle_request(request=request)

    async def handle_notification(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        await self._router.handle_notification(request=request)

    async def handle_invocation(
        self,
        *,
        invocation: ServiceOperationInvocation,
    ) -> ServiceOperationResult:
        response = await self.handle_request(request=invocation.request)
        return build_service_operation_result_from_response(response=response)

    async def handle_invocation_notification(
        self,
        *,
        invocation: ServiceOperationInvocation,
    ) -> None:
        await self.handle_notification(request=invocation.request)
