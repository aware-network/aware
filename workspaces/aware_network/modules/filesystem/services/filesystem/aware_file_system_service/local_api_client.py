from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from aware_api.invocation import ApiInvocationIndex, LoadedApiInvocationManifest
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    AwareApiEndpointInvoker,
)
from aware_file_system_service_api import AwareFileSystemServiceApiClient
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaRequest,
    CollectFileSystemDeltaRequest,
    ResolveFileSystemBackendCapabilitiesRequest,
    ScanFileSystemSnapshotRequest,
    VerifyFileSystemRootRequest,
)
from aware_service_runtime.api_ingress.host_context import service_api_host_context
from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceOperationContext,
)
from pydantic import BaseModel

from .api_service_protocol import build_aware_file_system_service_protocol_handler


_REQUEST_MODEL_BY_ENDPOINT_REF: dict[str, type[BaseModel]] = {
    "filesystem.backend.capabilities": ResolveFileSystemBackendCapabilitiesRequest,
    "filesystem.delta.apply": ApplyFileSystemDeltaRequest,
    "filesystem.delta.collect": CollectFileSystemDeltaRequest,
    "filesystem.root.verify": VerifyFileSystemRootRequest,
    "filesystem.snapshot.scan": ScanFileSystemSnapshotRequest,
}


@dataclass(frozen=True, slots=True)
class LocalFileSystemServiceApiConfig:
    endpoint: str = "aware-file-system-service://local"
    request_timeout_s: float = 10.0
    service_name: str = "aware_file_system"


@dataclass(frozen=True, slots=True)
class _UnsupportedRawFileSystemTransport:
    endpoint: str

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        _ = (invocation, timeout_s)
        raise NotImplementedError(
            "Local FileSystem service API client routes generated endpoint calls "
            "through the FileSystem service protocol; raw transport invocation is "
            "intentionally unavailable."
        )


class LocalFileSystemServiceAwareApiClient(AwareApiEndpointInvoker):
    """Generated API invoker over one in-process FileSystem service protocol."""

    def __init__(
        self,
        *,
        handler: object | None = None,
        operation_context: ServiceOperationContext | None = None,
        graph_gateway: ServiceGraphGateway | None = None,
        endpoint: str = "aware-file-system-service://local",
        request_timeout_s: float = 10.0,
        service_name: str = "aware_file_system",
    ) -> None:
        self._handler = handler or build_aware_file_system_service_protocol_handler()
        self._operation_context = operation_context
        self._graph_gateway = graph_gateway
        self._local_config = LocalFileSystemServiceApiConfig(
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            service_name=service_name,
        )
        super().__init__(
            _UnsupportedRawFileSystemTransport(endpoint=self._local_config.endpoint)
        )

    @property
    def local_config(self) -> LocalFileSystemServiceApiConfig:
        return self._local_config

    def warm_rust_apply_backend(self) -> dict[str, Any]:
        warm = getattr(self._handler, "warm_rust_apply_backend", None)
        if not callable(warm):
            raise RuntimeError(
                "Local FileSystem service handler does not expose Rust apply "
                "backend warm-up."
            )
        return cast(dict[str, Any], warm())

    def close(self) -> dict[str, Any]:
        close = getattr(self._handler, "close", None)
        if not callable(close):
            return {
                "rust_apply_service_cached_before": False,
                "rust_apply_service_closed": False,
            }
        return cast(dict[str, Any], close())

    def __enter__(self) -> "LocalFileSystemServiceAwareApiClient":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    async def invoke_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> Any:
        _ = timeout_s or self._local_config.request_timeout_s
        prepared = self.prepare_api_endpoint_invocation(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        request_model = _REQUEST_MODEL_BY_ENDPOINT_REF.get(
            prepared.endpoint.endpoint_ref
        )
        if request_model is None:
            raise ValueError(
                "Unsupported FileSystem service endpoint ref: "
                f"{prepared.endpoint.endpoint_ref!r}"
            )
        request = request_model.model_validate(prepared.request_payload)
        response = await self._dispatch(
            endpoint_ref=prepared.endpoint.endpoint_ref,
            request=request,
        )
        return response

    async def _dispatch(
        self,
        *,
        endpoint_ref: str,
        request: BaseModel,
    ) -> object:
        if self._operation_context is None:
            return await dispatch_file_system_service_protocol_endpoint(
                handler=self._handler,
                endpoint_ref=endpoint_ref,
                request=request,
            )
        with service_api_host_context(
            operation_context=self._operation_context,
            graph_gateway=self._graph_gateway,
            service_name=self._local_config.service_name,
        ):
            return await dispatch_file_system_service_protocol_endpoint(
                handler=self._handler,
                endpoint_ref=endpoint_ref,
                request=request,
            )


async def dispatch_file_system_service_protocol_endpoint(
    *,
    handler: object,
    endpoint_ref: str,
    request: BaseModel,
) -> object:
    parts = tuple(part.strip() for part in endpoint_ref.split(".") if part.strip())
    if len(parts) != 3 or parts[0] != "filesystem":
        raise ValueError(
            "FileSystem service protocol endpoint refs must use "
            f"`filesystem.<capability>.<endpoint>`, got {endpoint_ref!r}."
        )
    _, capability_name, endpoint_name = parts
    filesystem_handler = getattr(handler, "filesystem", None)
    capability_handler = getattr(filesystem_handler, capability_name, None)
    endpoint_handler = getattr(capability_handler, endpoint_name, None)
    if not callable(endpoint_handler):
        raise ValueError(
            "FileSystem service protocol handler does not expose endpoint "
            f"{endpoint_ref!r}."
        )
    typed_endpoint_handler = cast(
        Callable[[BaseModel], Awaitable[object]],
        endpoint_handler,
    )
    return await typed_endpoint_handler(request)


@dataclass(frozen=True, slots=True)
class LocalFileSystemServiceApiSession:
    api_client: AwareFileSystemServiceApiClient
    local_client: LocalFileSystemServiceAwareApiClient

    def warm_rust_apply_backend(self) -> dict[str, Any]:
        return self.local_client.warm_rust_apply_backend()

    def close(self) -> dict[str, Any]:
        return self.local_client.close()

    def __enter__(self) -> "LocalFileSystemServiceApiSession":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


def build_local_file_system_service_api_session(
    *,
    handler: object | None = None,
    operation_context: ServiceOperationContext | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    endpoint: str = "aware-file-system-service://local",
    request_timeout_s: float = 10.0,
    service_name: str = "aware_file_system",
) -> LocalFileSystemServiceApiSession:
    """Build a generated API client plus explicit local lifecycle controls."""

    local_client = LocalFileSystemServiceAwareApiClient(
        handler=handler,
        operation_context=operation_context,
        graph_gateway=graph_gateway,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        service_name=service_name,
    )
    return LocalFileSystemServiceApiSession(
        api_client=AwareFileSystemServiceApiClient(client=local_client),
        local_client=local_client,
    )


def build_local_file_system_service_api_client(
    *,
    handler: object | None = None,
    operation_context: ServiceOperationContext | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    endpoint: str = "aware-file-system-service://local",
    request_timeout_s: float = 10.0,
    service_name: str = "aware_file_system",
) -> AwareFileSystemServiceApiClient:
    """Build a generated FileSystem API client backed by the local protocol."""

    return build_local_file_system_service_api_session(
        handler=handler,
        operation_context=operation_context,
        graph_gateway=graph_gateway,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        service_name=service_name,
    ).api_client


__all__ = [
    "LocalFileSystemServiceApiConfig",
    "LocalFileSystemServiceApiSession",
    "LocalFileSystemServiceAwareApiClient",
    "build_local_file_system_service_api_client",
    "build_local_file_system_service_api_session",
    "dispatch_file_system_service_protocol_endpoint",
]
