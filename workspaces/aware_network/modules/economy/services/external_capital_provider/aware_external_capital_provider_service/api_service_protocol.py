from __future__ import annotations

import asyncio
from typing import Protocol
from uuid import UUID

from aware_economy_sdk import build_economy_sdk_client
from aware_economy_providers.external_capital import (
    wallet_funding_context_from_economy,
)
from aware_economy_providers.external_capital_provider_api import (
    ExternalCapitalProviderApi,
    external_capital_provider_api_from_env,
)
from aware_external_capital_provider_service_dto.external_capital.wallet_funding import (
    ExternalCapitalWalletFundingSessionRequest,
    ExternalCapitalWalletFundingSessionResponse,
)
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)


class EconomyWalletFundingContextResolver(Protocol):
    async def resolve_wallet_funding_context(
        self,
        *,
        transaction_intent_id: UUID,
        transaction_intent_commit_id: UUID,
    ) -> object: ...


def build_aware_external_capital_provider_service_protocol_handler(
    *,
    provider_api: ExternalCapitalProviderApi | None = None,
    economy_context_resolver: EconomyWalletFundingContextResolver | None = None,
) -> object:
    return _AwareExternalCapitalProviderServiceProtocolHandler(
        provider_api=provider_api or external_capital_provider_api_from_env(),
        economy_context_resolver=economy_context_resolver,
    )


class _ExternalCapitalWalletFundingSessionCapabilityHandler:
    def __init__(
        self,
        *,
        provider_api: ExternalCapitalProviderApi,
        economy_context_resolver: EconomyWalletFundingContextResolver | None,
    ) -> None:
        self._provider_api = provider_api
        self._economy_context_resolver = economy_context_resolver

    async def create_wallet_funding_session(
        self,
        request: ExternalCapitalWalletFundingSessionRequest,
        execution: object | None = None,
    ) -> ExternalCapitalWalletFundingSessionResponse:
        _ = execution
        resolver = self._economy_context_resolver or _require_economy_context_resolver()
        resolved = await resolver.resolve_wallet_funding_context(
            transaction_intent_id=request.transaction_intent_id,
            transaction_intent_commit_id=request.transaction_intent_commit_id,
        )
        context = wallet_funding_context_from_economy(resolved)
        receipt = await asyncio.to_thread(
            self._provider_api.create_wallet_funding_session,
            context,
        )
        return ExternalCapitalWalletFundingSessionResponse(
            transaction_intent_id=receipt.transaction_intent_id,
            transaction_intent_commit_id=receipt.transaction_intent_commit_id,
            provider_key=receipt.provider_key,
            provider_public_reference=receipt.provider_public_reference,
            idempotency_key=receipt.idempotency_key,
            continuation_kind=receipt.continuation_kind,
            continuation_url=receipt.continuation_url,
            continuation_expires_at=receipt.continuation_expires_at,
        )


class _ExternalCapitalApiServiceProtocolHandler:
    def __init__(
        self,
        *,
        provider_api: ExternalCapitalProviderApi,
        economy_context_resolver: EconomyWalletFundingContextResolver | None,
    ) -> None:
        self.wallet_funding_session = (
            _ExternalCapitalWalletFundingSessionCapabilityHandler(
                provider_api=provider_api,
                economy_context_resolver=economy_context_resolver,
            )
        )


class _AwareExternalCapitalProviderServiceProtocolHandler:
    def __init__(
        self,
        *,
        provider_api: ExternalCapitalProviderApi,
        economy_context_resolver: EconomyWalletFundingContextResolver | None,
    ) -> None:
        self.external_capital = _ExternalCapitalApiServiceProtocolHandler(
            provider_api=provider_api,
            economy_context_resolver=economy_context_resolver,
        )


def _require_economy_context_resolver() -> EconomyWalletFundingContextResolver:
    host_context = current_service_api_host_context()
    if host_context is None:
        raise RuntimeError(
            "external-capital provider service requires an active ServiceHost context"
        )
    api_invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name="economy-service-api",
        actor_id=host_context.operation_context.actor_id,
        invocation_context=(
            dict(host_context.invocation_context)
            if host_context.invocation_context is not None
            else None
        ),
    )
    if api_invoker is None:
        raise RuntimeError(
            "external-capital provider service requires an Economy Service API route"
        )
    return build_economy_sdk_client(api_invoker=api_invoker)


__all__ = [
    "EconomyWalletFundingContextResolver",
    "build_aware_external_capital_provider_service_protocol_handler",
]
