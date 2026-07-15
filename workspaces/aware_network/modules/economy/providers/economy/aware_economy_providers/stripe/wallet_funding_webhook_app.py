from __future__ import annotations

import argparse
import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aware_economy_providers.stripe.provider_lifecycle import (
    StripeProviderLifecycleError,
    StripeProviderLifecycleIgnored,
    verified_provider_lifecycle_evidence_from_webhook,
)
from aware_economy_providers.stripe.stripe_verifier import StripeSignatureError
from aware_economy_providers.stripe.wallet_funding import (
    StripeWalletFundingError,
    verified_wallet_funding_evidence_from_webhook,
    verified_wallet_funding_expiration_evidence_from_webhook,
)


DEFAULT_WEBHOOK_PATH = "/webhook/stripe/wallet-funding"
DEFAULT_BIND_HOST = "127.0.0.1"
DEFAULT_BIND_PORT = 18080
DEFAULT_REQUEST_TIMEOUT_S = 30.0
DEFAULT_MAX_BODY_BYTES = 1024 * 1024
DEFAULT_ECONOMY_API_ENDPOINT = "aware-service-host://aware-economy-service"

SIGNING_SECRET_ENV = "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_SECRET"
PUBLIC_URL_ENV = "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PUBLIC_URL"
ECONOMY_SERVICE_HOST_SOCKET_PATH_ENV = "AWARE_ECONOMY_SERVICE_HOST_SOCKET_PATH"
PROVIDER_IDENTITY_ID_ENV = "AWARE_STRIPE_WALLET_FUNDING_PROVIDER_IDENTITY_ID"
REQUEST_TIMEOUT_ENV = "AWARE_ECONOMY_SERVICE_HOST_REQUEST_TIMEOUT_S"
WEBHOOK_PATH_ENV = "AWARE_STRIPE_WALLET_FUNDING_WEBHOOK_PATH"


class EconomyWebhookRecorder(Protocol):
    async def record_verified_wallet_funding(self, **kwargs: object) -> object: ...

    async def record_wallet_funding_expiration(self, **kwargs: object) -> object: ...

    async def record_provider_lifecycle_event(self, **kwargs: object) -> object: ...


@dataclass(frozen=True, slots=True)
class StripeWalletFundingWebhookConfig:
    signing_secret: str
    path: str = DEFAULT_WEBHOOK_PATH
    provider_identity_id: UUID | None = None
    tolerance_seconds: int | None = 300
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES
    public_url: str | None = None


@dataclass(frozen=True, slots=True)
class StripeWalletFundingWebhookReceipt:
    status: str
    operation: str
    provider_event_id: str
    provider_public_reference: str | None
    economy_response: object | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "operation": self.operation,
            "provider_event_id": self.provider_event_id,
            "provider_public_reference": self.provider_public_reference,
        }
        if self.economy_response is not None:
            payload["economy_response"] = _response_payload(self.economy_response)
        return payload


class StripeWalletFundingWebhookRejected(ValueError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


async def dispatch_stripe_wallet_funding_webhook(
    *,
    raw_body: bytes,
    headers: Mapping[str, str],
    config: StripeWalletFundingWebhookConfig,
    economy: EconomyWebhookRecorder,
) -> StripeWalletFundingWebhookReceipt:
    normalized_headers = _stripe_headers(headers)
    try:
        evidence = verified_wallet_funding_evidence_from_webhook(
            raw_body=raw_body,
            headers=normalized_headers,
            signing_secret=config.signing_secret,
            tolerance_seconds=config.tolerance_seconds,
        )
    except StripeSignatureError as exc:
        raise StripeWalletFundingWebhookRejected(str(exc), status_code=400) from exc
    except StripeWalletFundingError as wallet_error:
        try:
            expiration_evidence = verified_wallet_funding_expiration_evidence_from_webhook(
                raw_body=raw_body,
                headers=normalized_headers,
                signing_secret=config.signing_secret,
                tolerance_seconds=config.tolerance_seconds,
            )
        except StripeSignatureError as exc:
            raise StripeWalletFundingWebhookRejected(str(exc), status_code=400) from exc
        except StripeWalletFundingError as expiration_error:
            try:
                lifecycle_evidence = verified_provider_lifecycle_evidence_from_webhook(
                    raw_body=raw_body,
                    headers=normalized_headers,
                    signing_secret=config.signing_secret,
                    tolerance_seconds=config.tolerance_seconds,
                )
            except StripeProviderLifecycleIgnored as ignored:
                return StripeWalletFundingWebhookReceipt(
                    status="ignored",
                    operation="ignore_provider_lifecycle_event",
                    provider_event_id=ignored.provider_event_id,
                    provider_public_reference=(ignored.provider_lifecycle_object_id),
                )
            except StripeSignatureError as exc:
                raise StripeWalletFundingWebhookRejected(str(exc), status_code=400) from exc
            except StripeProviderLifecycleError as lifecycle_error:
                raise StripeWalletFundingWebhookRejected(
                    "Unsupported Stripe wallet-funding event: "
                    f"{wallet_error}; {expiration_error}; {lifecycle_error}",
                    status_code=400,
                ) from lifecycle_error
            economy_response = await economy.record_provider_lifecycle_event(
                **lifecycle_evidence.to_economy_record_kwargs()
            )
            return StripeWalletFundingWebhookReceipt(
                status="recorded",
                operation="record_provider_lifecycle_event",
                provider_event_id=lifecycle_evidence.provider_event_id,
                provider_public_reference=(lifecycle_evidence.provider_payment_reference),
                economy_response=economy_response,
            )

        economy_response = await economy.record_wallet_funding_expiration(
            **expiration_evidence.to_economy_record_kwargs()
        )
        return StripeWalletFundingWebhookReceipt(
            status="recorded",
            operation="record_wallet_funding_expiration",
            provider_event_id=expiration_evidence.provider_event_id,
            provider_public_reference=(expiration_evidence.provider_public_reference),
            economy_response=economy_response,
        )

    economy_response = await economy.record_verified_wallet_funding(**evidence.to_economy_record_kwargs())
    return StripeWalletFundingWebhookReceipt(
        status="recorded",
        operation="record_verified_wallet_funding",
        provider_event_id=evidence.provider_event_id,
        provider_public_reference=evidence.provider_public_reference,
        economy_response=economy_response,
    )


@dataclass(frozen=True, slots=True)
class EconomySdkWebhookRecorder:
    sdk_client: Any

    async def record_verified_wallet_funding(self, **kwargs: object) -> object:
        return await self.sdk_client.record_verified_wallet_funding(**kwargs)

    async def record_wallet_funding_expiration(self, **kwargs: object) -> object:
        return await self.sdk_client.record_wallet_funding_expiration(**kwargs)

    async def record_provider_lifecycle_event(self, **kwargs: object) -> object:
        return await self.sdk_client.record_provider_lifecycle_event(**kwargs)


def build_service_host_economy_webhook_recorder(
    *,
    socket_path: str | Path,
    actor_id: UUID | None = None,
    request_timeout_s: float = DEFAULT_REQUEST_TIMEOUT_S,
    endpoint: str = DEFAULT_ECONOMY_API_ENDPOINT,
) -> EconomySdkWebhookRecorder:
    from aware_comms import DuplexIpcEndpoint
    from aware_economy_sdk import build_economy_sdk_client
    from aware_service_runtime.duplex_client import ServiceHostDuplexClient
    from aware_service_runtime.local_service_host_api_client import (
        LocalServiceHostAwareApiClient,
    )

    resolved_socket_path = Path(socket_path).expanduser().resolve()

    def _client_factory() -> ServiceHostDuplexClient:
        return ServiceHostDuplexClient(
            endpoint=DuplexIpcEndpoint.unix_socket(socket_path=resolved_socket_path.as_posix())
        )

    api_invoker = LocalServiceHostAwareApiClient(
        actor_id=actor_id,
        client_factory=_client_factory,
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        invocation_context={
            "source": "aware_economy_providers.stripe.wallet_funding_webhook_app",
            "provider": "stripe",
            "operation": "wallet_funding_webhook",
        },
    )
    return EconomySdkWebhookRecorder(sdk_client=build_economy_sdk_client(api_invoker=api_invoker))


def config_from_env() -> StripeWalletFundingWebhookConfig:
    signing_secret = _required_env(SIGNING_SECRET_ENV)
    return StripeWalletFundingWebhookConfig(
        signing_secret=signing_secret,
        path=_clean_path(os.getenv(WEBHOOK_PATH_ENV) or DEFAULT_WEBHOOK_PATH),
        provider_identity_id=_optional_uuid(os.getenv(PROVIDER_IDENTITY_ID_ENV)),
        tolerance_seconds=300,
        public_url=_optional_text(os.getenv(PUBLIC_URL_ENV)),
    )


def economy_recorder_from_env(
    *,
    actor_id: UUID | None = None,
) -> EconomySdkWebhookRecorder:
    return build_service_host_economy_webhook_recorder(
        socket_path=_required_env(ECONOMY_SERVICE_HOST_SOCKET_PATH_ENV),
        actor_id=actor_id,
        request_timeout_s=_optional_float(
            os.getenv(REQUEST_TIMEOUT_ENV),
            default=DEFAULT_REQUEST_TIMEOUT_S,
            field_name=REQUEST_TIMEOUT_ENV,
        ),
    )


def build_http_handler(
    *,
    config: StripeWalletFundingWebhookConfig,
    economy: EconomyWebhookRecorder,
) -> type[BaseHTTPRequestHandler]:
    class _StripeWalletFundingWebhookHandler(BaseHTTPRequestHandler):
        server_version = "AwareStripeWalletFundingWebhook/1.0"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            if self.path == "/health":
                self._write_json(200, {"status": "ok"})
                return
            self._write_json(404, {"status": "not_found"})

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
            if self.path != config.path:
                self._write_json(404, {"status": "not_found"})
                return
            try:
                raw_body = self._read_body()
                receipt = asyncio.run(
                    dispatch_stripe_wallet_funding_webhook(
                        raw_body=raw_body,
                        headers={key: value for key, value in self.headers.items()},
                        config=config,
                        economy=economy,
                    )
                )
            except StripeWalletFundingWebhookRejected as exc:
                self._write_json(
                    exc.status_code,
                    {"status": "rejected", "error": str(exc)},
                )
                return
            except Exception as exc:
                self._write_json(
                    500,
                    {
                        "status": "failed",
                        "error": exc.__class__.__name__,
                    },
                )
                return
            self._write_json(200, receipt.to_payload())

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_body(self) -> bytes:
            raw_length = self.headers.get("Content-Length") or "0"
            try:
                length = int(raw_length)
            except ValueError as exc:
                raise StripeWalletFundingWebhookRejected(
                    "Invalid Content-Length",
                    status_code=400,
                ) from exc
            if length > config.max_body_bytes:
                raise StripeWalletFundingWebhookRejected(
                    "Stripe webhook body too large",
                    status_code=413,
                )
            return self.rfile.read(length)

        def _write_json(self, status_code: int, payload: Mapping[str, object]) -> None:
            body = json.dumps(dict(payload), sort_keys=True).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return _StripeWalletFundingWebhookHandler


def run_http_server(
    *,
    host: str,
    port: int,
    config: StripeWalletFundingWebhookConfig,
    economy: EconomyWebhookRecorder,
) -> None:
    server = ThreadingHTTPServer(
        (host, port),
        build_http_handler(config=config, economy=economy),
    )
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stripe wallet-funding webhook ingress.")
    parser.add_argument("--host", default=os.getenv("HOST", DEFAULT_BIND_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", str(DEFAULT_BIND_PORT))))
    args = parser.parse_args(argv)

    config = config_from_env()
    economy = economy_recorder_from_env(actor_id=config.provider_identity_id)
    run_http_server(
        host=args.host,
        port=args.port,
        config=config,
        economy=economy,
    )
    return 0


def _stripe_headers(headers: Mapping[str, str]) -> dict[str, str]:
    normalized = {str(key): str(value) for key, value in headers.items()}
    if "Stripe-Signature" in normalized:
        return normalized
    for key, value in normalized.items():
        if key.casefold() == "stripe-signature":
            normalized["Stripe-Signature"] = value
            return normalized
    return normalized


def _required_env(name: str) -> str:
    value = _optional_text(os.getenv(name))
    if value is None:
        raise RuntimeError(f"{name} is required")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_uuid(value: object) -> UUID | None:
    text = _optional_text(value)
    if text is None:
        return None
    return UUID(text)


def _optional_float(value: object, *, default: float, field_name: str) -> float:
    text = _optional_text(value)
    if text is None:
        return default
    try:
        parsed = float(text)
    except ValueError as exc:
        raise RuntimeError(f"{field_name} must be a number") from exc
    if parsed <= 0:
        raise RuntimeError(f"{field_name} must be positive")
    return parsed


def _clean_path(value: str) -> str:
    path = value.strip()
    if not path.startswith("/"):
        raise RuntimeError("Stripe wallet-funding webhook path must start with '/'")
    return path


def _response_payload(value: object) -> object:
    if hasattr(value, "model_dump"):
        return cast(Any, value).model_dump(mode="json")
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, tuple | list):
        return list(value)
    if hasattr(value, "__dict__"):
        return dict(cast(Any, value).__dict__)
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
