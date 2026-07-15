# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF
from aware_external_capital_provider_service_dto.external_capital.wallet_funding import (
    ExternalCapitalWalletFundingSessionRequest,
    ExternalCapitalWalletFundingSessionResponse,
)


class ExternalCapitalWalletFundingSessionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def create_wallet_funding_session(
        self, request: ExternalCapitalWalletFundingSessionRequest
    ) -> ExternalCapitalWalletFundingSessionResponse:
        """Create an external-provider continuation for a committed Aware wallet-funding intent."""
        return cast(
            ExternalCapitalWalletFundingSessionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ExternalCapitalApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.wallet_funding_session = ExternalCapitalWalletFundingSessionCapabilityClient(client)


class AwareExternalCapitalProviderServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.external_capital = ExternalCapitalApiClient(client)


__all__ = [
    "AwareExternalCapitalProviderServiceApiClient",
    "ExternalCapitalApiClient",
    "ExternalCapitalWalletFundingSessionCapabilityClient",
]
