from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_code.types import JsonObject

from .contracts import ServiceHostApiIngressRequest


class _ServiceHostApiIngressClient(Protocol):
    async def send_api_ingress_request(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        timeout_s: float | None = None,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class ServiceHostActionTerminalFulfillmentInvoker:
    """Service-owned local transport for one Experience action endpoint."""

    actor_id: UUID | None
    client_factory: Callable[[], _ServiceHostApiIngressClient]
    request_timeout_s: float = 10.0
    invocation_context: JsonObject | None = None

    async def invoke_action_endpoint(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_values: Mapping[str, object],
        api_call_key: UUID,
    ) -> object:
        request = ServiceHostApiIngressRequest(
            actor_id=self.actor_id,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=JsonObject(dict(request_values)),
            invocation_context=self.invocation_context,
            network_request_id=api_call_key,
            stream_requested=False,
        )
        return await self.client_factory().send_api_ingress_request(
            request=request,
            timeout_s=self.request_timeout_s,
        )


__all__ = ["ServiceHostActionTerminalFulfillmentInvoker"]
