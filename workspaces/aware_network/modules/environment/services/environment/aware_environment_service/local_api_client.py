from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from aware_api.invocation import ApiInvocationIndex, LoadedApiInvocationManifest
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    AwareApiEndpointInvoker,
    decode_api_endpoint_response_payload,
    resolve_api_endpoint_model_class,
)
from aware_environment_service_api import AwareEnvironmentServiceApiClient


class EnvironmentServiceProtocolDispatcher(Protocol):
    async def dispatch_environment_service_protocol_endpoint(
        self,
        *,
        endpoint_ref: str,
        request: BaseModel,
    ) -> object | None: ...


@dataclass(frozen=True, slots=True)
class LocalEnvironmentServiceApiConfig:
    endpoint: str = "aware-environment-service://local"
    request_timeout_s: float = 10.0


@dataclass(frozen=True, slots=True)
class _UnsupportedRawEnvironmentTransport:
    endpoint: str

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        _ = (invocation, timeout_s)
        raise NotImplementedError(
            "Local Environment service API client routes generated endpoint calls "
            "through EnvironmentServiceApp.dispatch_environment_service_protocol_endpoint; "
            "raw transport invocation is intentionally unavailable."
        )


class LocalEnvironmentServiceAwareApiClient(AwareApiEndpointInvoker):
    """Generated API invoker over one in-process EnvironmentServiceApp boundary."""

    def __init__(
        self,
        *,
        app: EnvironmentServiceProtocolDispatcher,
        endpoint: str = "aware-environment-service://local",
        request_timeout_s: float = 10.0,
    ) -> None:
        self._app = app
        self._local_config = LocalEnvironmentServiceApiConfig(
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
        )
        super().__init__(
            _UnsupportedRawEnvironmentTransport(endpoint=self._local_config.endpoint)
        )

    @property
    def local_config(self) -> LocalEnvironmentServiceApiConfig:
        return self._local_config

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
        request_model = resolve_api_endpoint_model_class(prepared.request_class_ref)
        request = request_model.model_validate(dict(prepared.request_payload))
        response = await self._app.dispatch_environment_service_protocol_endpoint(
            endpoint_ref=prepared.endpoint.endpoint_ref,
            request=request,
        )
        response_payload = (
            response.model_dump(mode="json") if isinstance(response, BaseModel) else response
        )
        return decode_api_endpoint_response_payload(
            prepared=prepared,
            response_payload=response_payload,
        )


def build_local_environment_service_api_client(
    *,
    app: EnvironmentServiceProtocolDispatcher,
    endpoint: str = "aware-environment-service://local",
    request_timeout_s: float = 10.0,
) -> AwareEnvironmentServiceApiClient:
    """Build a generated Environment API client backed by a local service app."""

    return AwareEnvironmentServiceApiClient(
        client=LocalEnvironmentServiceAwareApiClient(
            app=app,
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
        )
    )


__all__ = [
    "EnvironmentServiceProtocolDispatcher",
    "LocalEnvironmentServiceApiConfig",
    "LocalEnvironmentServiceAwareApiClient",
    "build_local_environment_service_api_client",
]
