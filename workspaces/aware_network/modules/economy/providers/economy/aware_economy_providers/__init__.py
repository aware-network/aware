"""Server-side Economy provider evidence helpers.

Provider packages verify external evidence for Economy-owned wallet funding.
They do not activate Service contracts, own subscriptions, or mutate wallets
directly. The canonical funding rail is provider evidence -> TransactionIntent
-> TransactionExternal -> internal Transaction -> FinanceEntity wallet balance.
"""

from __future__ import annotations

from aware_economy_providers.external_capital import (
    EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY,
    EXTERNAL_CAPITAL_PROVIDER_CONNECTOR_REF,
    EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY,
    WALLET_FUNDING_INTENT_PREPARED_EVENT_NAME,
    ExternalCapitalProviderError,
    ExternalCapitalProviderSensorEvidence,
    ExternalCapitalWalletFundingContext,
    ExternalCapitalWalletFundingSessionReceipt,
    create_fake_wallet_funding_session,
    fake_wallet_funding_sensor_evidence,
    wallet_funding_context_from_economy,
)
from aware_economy_providers.external_capital_provider_api import (
    ExternalCapitalProviderApi,
    ExternalCapitalProviderApiError,
    external_capital_provider_api_from_env,
)

__all__ = [
    "EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY",
    "EXTERNAL_CAPITAL_PROVIDER_CONNECTOR_REF",
    "EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY",
    "WALLET_FUNDING_INTENT_PREPARED_EVENT_NAME",
    "ExternalCapitalProviderError",
    "ExternalCapitalProviderApi",
    "ExternalCapitalProviderApiError",
    "external_capital_provider_api_from_env",
    "ExternalCapitalProviderSensorEvidence",
    "ExternalCapitalWalletFundingContext",
    "ExternalCapitalWalletFundingSessionReceipt",
    "create_fake_wallet_funding_session",
    "fake_wallet_funding_sensor_evidence",
    "wallet_funding_context_from_economy",
]
