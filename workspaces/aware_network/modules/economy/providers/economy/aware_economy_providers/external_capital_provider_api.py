from __future__ import annotations

from dataclasses import dataclass

from aware_service_runtime.runtime_secrets import resolve_service_runtime_value

from aware_economy_providers.external_capital import (
    EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY,
    ExternalCapitalWalletFundingContext,
    ExternalCapitalWalletFundingSessionReceipt,
    create_fake_wallet_funding_session,
)
from aware_economy_providers.stripe.wallet_funding import STRIPE_PROVIDER_KEY
from aware_economy_providers.stripe.wallet_funding_provider_service import (
    STRIPE_WALLET_FUNDING_SECRET_KEY_ENV,
    StripeCheckoutSessionTransport,
    StripeWalletFundingProviderService,
    stripe_wallet_funding_provider_service_from_env,
)


class ExternalCapitalProviderApiError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExternalCapitalProviderApi:
    stripe_transport: StripeCheckoutSessionTransport | None = None
    stripe_success_url: str | None = None
    stripe_cancel_url: str | None = None
    stripe_description: str | None = "Aware wallet funding"

    def create_wallet_funding_session(
        self,
        context: ExternalCapitalWalletFundingContext,
    ) -> ExternalCapitalWalletFundingSessionReceipt:
        if context.provider_key == EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY:
            return create_fake_wallet_funding_session(context)
        if context.provider_key == STRIPE_PROVIDER_KEY:
            if self.stripe_transport is None or self.stripe_success_url is None or self.stripe_cancel_url is None:
                raise ExternalCapitalProviderApiError("Stripe wallet funding requires transport and hosted return URLs")
            return StripeWalletFundingProviderService(
                transport=self.stripe_transport,
                success_url=self.stripe_success_url,
                cancel_url=self.stripe_cancel_url,
                description=self.stripe_description,
            ).create_wallet_funding_session(context)
        raise ExternalCapitalProviderApiError(f"Unsupported external-capital provider_key: {context.provider_key}")


def external_capital_provider_api_from_env() -> ExternalCapitalProviderApi:
    secret_key = (resolve_service_runtime_value(STRIPE_WALLET_FUNDING_SECRET_KEY_ENV) or "").strip()
    if not secret_key:
        return ExternalCapitalProviderApi()
    stripe_service = stripe_wallet_funding_provider_service_from_env()
    return ExternalCapitalProviderApi(
        stripe_transport=stripe_service.transport,
        stripe_success_url=stripe_service.success_url,
        stripe_cancel_url=stripe_service.cancel_url,
        stripe_description=stripe_service.description,
    )
