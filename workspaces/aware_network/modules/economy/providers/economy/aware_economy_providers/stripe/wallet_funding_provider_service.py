from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
import os
from typing import Protocol
from urllib.parse import urlparse

from aware_service_runtime.runtime_secrets import (
    ServiceRuntimeSecretError,
    require_service_runtime_secret,
    require_service_runtime_value,
)

from aware_economy_providers.external_capital import (
    ExternalCapitalWalletFundingContext,
    ExternalCapitalWalletFundingSessionReceipt,
)
from aware_economy_providers.stripe.wallet_funding import (
    STRIPE_PROVIDER_KEY,
    StripeWalletFundingCheckoutSessionRequest,
    build_wallet_funding_checkout_session_request,
)


STRIPE_CHECKOUT_SESSIONS_ENDPOINT = "https://api.stripe.com/v1/checkout/sessions"
STRIPE_WALLET_FUNDING_SECRET_KEY_ENV = "AWARE_STRIPE_WALLET_FUNDING_SECRET_KEY"
STRIPE_WALLET_FUNDING_CHECKOUT_SESSIONS_ENDPOINT_ENV = "AWARE_STRIPE_WALLET_FUNDING_CHECKOUT_SESSIONS_ENDPOINT"
STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV = "AWARE_STRIPE_WALLET_FUNDING_SUCCESS_URL"
STRIPE_WALLET_FUNDING_CANCEL_URL_ENV = "AWARE_STRIPE_WALLET_FUNDING_CANCEL_URL"
STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_ENV = "AWARE_STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_S"
DEFAULT_STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_S = 30.0


class StripeWalletFundingProviderServiceError(ValueError):
    pass


class StripeCheckoutSessionTransport(Protocol):
    def create_checkout_session(
        self,
        request: StripeWalletFundingCheckoutSessionRequest,
    ) -> StripeCheckoutSessionCreationResult: ...


@dataclass(frozen=True, slots=True)
class StripeCheckoutSessionCreationResult:
    checkout_session_id: str
    url: str
    status: str
    livemode: bool
    expires_at: int
    request_id: str | None = None

    @classmethod
    def from_stripe_payload(
        cls,
        payload: Mapping[str, object],
        *,
        request_id: str | None = None,
    ) -> StripeCheckoutSessionCreationResult:
        object_type = _optional_text(payload.get("object"))
        if object_type not in (None, "checkout.session"):
            raise StripeWalletFundingProviderServiceError("Stripe wallet-funding actuator expected Checkout Session")
        status = _required_text(payload.get("status"), "checkout_session.status")
        if status != "open":
            raise StripeWalletFundingProviderServiceError(f"Stripe Checkout Session must be open: {status}")
        return cls(
            checkout_session_id=_required_text(
                payload.get("id"),
                "checkout_session.id",
            ),
            url=_required_https_url(payload.get("url"), "checkout_session.url"),
            status=status,
            livemode=bool(payload.get("livemode", False)),
            expires_at=_positive_int(
                payload.get("expires_at"),
                "checkout_session.expires_at",
            ),
            request_id=_optional_text(request_id),
        )

    @property
    def expires_at_iso(self) -> str:
        return datetime.fromtimestamp(self.expires_at, tz=UTC).isoformat()


@dataclass(frozen=True, slots=True)
class HttpxStripeCheckoutSessionTransport:
    secret_key: str
    endpoint: str = STRIPE_CHECKOUT_SESSIONS_ENDPOINT
    timeout_s: float = DEFAULT_STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_S

    def __post_init__(self) -> None:
        _require_test_secret_key(self.secret_key)
        _required_https_url(self.endpoint, "checkout_sessions_endpoint")
        if self.timeout_s <= 0:
            raise StripeWalletFundingProviderServiceError("Stripe wallet-funding timeout must be positive")

    def create_checkout_session(
        self,
        request: StripeWalletFundingCheckoutSessionRequest,
    ) -> StripeCheckoutSessionCreationResult:
        import httpx

        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            **request.to_stripe_headers(),
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(
                self.endpoint,
                data=request.to_stripe_form_fields(),
                headers=headers,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise StripeWalletFundingProviderServiceError(
                "Stripe Checkout Session response was not JSON: " f"{response.status_code}"
            ) from exc
        if response.status_code >= 400:
            raise StripeWalletFundingProviderServiceError(
                "Stripe Checkout Session creation failed: " f"{response.status_code} {_stripe_error_message(payload)}"
            )
        return StripeCheckoutSessionCreationResult.from_stripe_payload(
            payload,
            request_id=(response.headers.get("request-id") or response.headers.get("Request-Id")),
        )


@dataclass(frozen=True, slots=True)
class StripeWalletFundingProviderService:
    transport: StripeCheckoutSessionTransport
    success_url: str
    cancel_url: str
    product_name: str = "Aware wallet funding"
    description: str | None = "Fund an Aware Wallet"

    def create_wallet_funding_session(
        self,
        context: ExternalCapitalWalletFundingContext,
    ) -> ExternalCapitalWalletFundingSessionReceipt:
        if context.provider_key != STRIPE_PROVIDER_KEY:
            raise StripeWalletFundingProviderServiceError("Stripe wallet-funding provider requires provider_key=stripe")
        checkout_request = build_wallet_funding_checkout_session_request(
            context=context,
            success_url=self.success_url,
            cancel_url=self.cancel_url,
            product_name=self.product_name,
            description=self.description,
        )
        creation = self.transport.create_checkout_session(checkout_request)
        if creation.livemode:
            raise StripeWalletFundingProviderServiceError("Stripe wallet-funding provider requires test-mode Checkout")
        return ExternalCapitalWalletFundingSessionReceipt(
            transaction_intent_id=context.transaction_intent_id,
            transaction_intent_commit_id=context.transaction_intent_commit_id,
            provider_key=context.provider_key,
            provider_public_reference=creation.checkout_session_id,
            idempotency_key=checkout_request.idempotency_key,
            continuation_kind="open_external_url",
            continuation_url=creation.url,
            continuation_expires_at=creation.expires_at_iso,
        )


def stripe_wallet_funding_provider_service_from_env() -> StripeWalletFundingProviderService:
    endpoint = os.getenv(STRIPE_WALLET_FUNDING_CHECKOUT_SESSIONS_ENDPOINT_ENV) or STRIPE_CHECKOUT_SESSIONS_ENDPOINT
    timeout_s = _optional_float(
        os.getenv(STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_ENV),
        default=DEFAULT_STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_S,
        field_name=STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_ENV,
    )
    return StripeWalletFundingProviderService(
        transport=HttpxStripeCheckoutSessionTransport(
            secret_key=_required_service_runtime_value(STRIPE_WALLET_FUNDING_SECRET_KEY_ENV),
            endpoint=endpoint,
            timeout_s=timeout_s,
        ),
        success_url=_required_service_runtime_value(STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV),
        cancel_url=_required_service_runtime_value(STRIPE_WALLET_FUNDING_CANCEL_URL_ENV),
    )


def _require_test_secret_key(secret_key: str) -> None:
    key = _required_text(secret_key, "secret_key")
    if not key.startswith("sk_test_"):
        raise StripeWalletFundingProviderServiceError("Stripe wallet-funding provider requires a test-mode secret key")


def _required_service_runtime_value(name: str) -> str:
    try:
        if name == STRIPE_WALLET_FUNDING_SECRET_KEY_ENV:
            return require_service_runtime_secret(name)
        return require_service_runtime_value(name)
    except ServiceRuntimeSecretError as exc:
        raise StripeWalletFundingProviderServiceError(str(exc)) from exc


def _optional_float(value: object, *, default: float, field_name: str) -> float:
    text = _optional_text(value)
    if text is None:
        return default
    try:
        parsed = float(text)
    except ValueError as exc:
        raise StripeWalletFundingProviderServiceError(f"{field_name} must be a number") from exc
    if parsed <= 0:
        raise StripeWalletFundingProviderServiceError(f"{field_name} must be positive")
    return parsed


def _required_text(value: object, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise StripeWalletFundingProviderServiceError(f"Missing Stripe wallet-funding field: {field_name}")
    return text


def _required_https_url(value: object, field_name: str) -> str:
    url = _required_text(value, field_name)
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise StripeWalletFundingProviderServiceError(f"{field_name} must be an HTTPS URL")
    return url


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise StripeWalletFundingProviderServiceError(f"{field_name} must be a positive integer")
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise StripeWalletFundingProviderServiceError(f"{field_name} must be a positive integer") from exc
    if parsed <= 0:
        raise StripeWalletFundingProviderServiceError(f"{field_name} must be a positive integer")
    return parsed


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _stripe_error_message(payload: object) -> str:
    if isinstance(payload, Mapping):
        error = payload.get("error")
        if isinstance(error, Mapping):
            message = _optional_text(error.get("message"))
            if message:
                return message
        message = _optional_text(payload.get("message"))
        if message:
            return message
    return "unknown_error"


__all__ = [
    "DEFAULT_STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_S",
    "HttpxStripeCheckoutSessionTransport",
    "STRIPE_CHECKOUT_SESSIONS_ENDPOINT",
    "STRIPE_WALLET_FUNDING_CANCEL_URL_ENV",
    "STRIPE_WALLET_FUNDING_CHECKOUT_SESSIONS_ENDPOINT_ENV",
    "STRIPE_WALLET_FUNDING_REQUEST_TIMEOUT_ENV",
    "STRIPE_WALLET_FUNDING_SECRET_KEY_ENV",
    "STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV",
    "StripeCheckoutSessionCreationResult",
    "StripeCheckoutSessionTransport",
    "StripeWalletFundingProviderService",
    "StripeWalletFundingProviderServiceError",
    "stripe_wallet_funding_provider_service_from_env",
]
