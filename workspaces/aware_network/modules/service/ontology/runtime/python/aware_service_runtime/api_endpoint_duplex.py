"""Service-owned duplex transport for remote API endpoint forwarding."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from aware_comms.duplex.client import DuplexClient
from aware_comms.duplex.messenger import DuplexMessenger


class ApiEndpointDuplexClient(DuplexClient):
    """Thin websocket duplex client used by service runtime API transports."""

    endpoint: str
    session_token: str | None = None
    connection_id: UUID = Field(default_factory=uuid4)
    request_timeout: float = 10.0

    @model_validator(mode="after")
    def _configure_request_timeout(self) -> "ApiEndpointDuplexClient":
        self._messenger = DuplexMessenger(
            send_data_fn=self._send_data,
            default_timeout=self.request_timeout,
        )
        return self

    async def ensure_connection(
        self,
        connection_id: UUID | None = None,
        *,
        external_url: str | None = None,
        auth_token: str | None = None,
    ) -> None:
        await super().ensure_connection(
            connection_id or self.connection_id,
            external_url=_normalize_ws_endpoint(external_url or self.endpoint),
            auth_token=auth_token or self.session_token,
        )


def _normalize_ws_endpoint(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("API endpoint duplex external_url is required.")
    if "://" not in raw:
        raw = f"ws://{raw}"
    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()
    if scheme == "http":
        parsed = parsed._replace(scheme="ws")
    elif scheme == "https":
        parsed = parsed._replace(scheme="wss")
    elif scheme not in {"ws", "wss"}:
        raise ValueError(
            "Unsupported API endpoint duplex scheme "
            f"{parsed.scheme!r}; expected ws, wss, http, or https."
        )
    return urlunparse(parsed)


__all__ = ["ApiEndpointDuplexClient"]
