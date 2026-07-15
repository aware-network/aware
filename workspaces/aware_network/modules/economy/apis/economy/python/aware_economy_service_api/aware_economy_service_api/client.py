# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF,
    ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF,
    ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF,
    ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF,
    ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF,
    ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF,
    ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
    ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
    ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF,
    ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF,
    ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF,
    ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF,
    ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF,
    ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF,
    ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF,
    ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF,
)
from aware_economy_service_dto.economy.service import (
    EconomyActorStatusRequest,
    EconomyActorStatusResponse,
    EconomyEnsureFinanceEntityRequest,
    EconomyEnsureFinanceEntityResponse,
    EconomyPriceReservationFinalizeRequest,
    EconomyPriceReservationFinalizeResponse,
    EconomyPriceReservationReserveRequest,
    EconomyPriceReservationReserveResponse,
    EconomyProviderLifecycleRecordRequest,
    EconomyProviderLifecycleRecordResponse,
    EconomyServiceOperationPermitEnsureRequest,
    EconomyServiceOperationPermitEnsureResponse,
    EconomySmartContractReservationPrepareRequest,
    EconomySmartContractReservationPrepareResponse,
    EconomySmartContractReservationReleaseRequest,
    EconomySmartContractReservationReleaseResponse,
    EconomySmartContractSettlementFinalizeRequest,
    EconomySmartContractSettlementFinalizeResponse,
    EconomyWalletBalanceDescribeRequest,
    EconomyWalletBalanceDescribeResponse,
    EconomyWalletCapitalFrameResolveRequest,
    EconomyWalletCapitalFrameResolveResponse,
    EconomyWalletCapitalViewStateResolveRequest,
    EconomyWalletFundingCancelRequest,
    EconomyWalletFundingCancelResponse,
    EconomyWalletFundingContextResolveRequest,
    EconomyWalletFundingContextResolveResponse,
    EconomyWalletFundingPrepareRequest,
    EconomyWalletFundingPrepareResponse,
    EconomyWalletFundingRecordRequest,
    EconomyWalletFundingRecordResponse,
)
from aware_economy_service_dto.economy.view import EconomyWalletCapitalViewStateV1


class EconomyEconomyActorStatusCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def economy_actor_status(self, request: EconomyActorStatusRequest) -> EconomyActorStatusResponse:
        """Read the actor's finance and product-readiness state."""
        return cast(
            EconomyActorStatusResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyEnsureFinanceEntityCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_finance_entity(
        self, request: EconomyEnsureFinanceEntityRequest
    ) -> EconomyEnsureFinanceEntityResponse:
        """Ensure the actor has a canonical FinanceEntity and wallet."""
        return cast(
            EconomyEnsureFinanceEntityResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyPriceReservationFinalizeCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def price_reservation_finalize(
        self, request: EconomyPriceReservationFinalizeRequest
    ) -> EconomyPriceReservationFinalizeResponse:
        """Finalize one canonical Economy price reservation. Economy derives settled value from the committed schedule and actual provider-neutral metering evidence."""
        return cast(
            EconomyPriceReservationFinalizeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyPriceReservationReserveCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def price_reservation_reserve(
        self, request: EconomyPriceReservationReserveRequest
    ) -> EconomyPriceReservationReserveResponse:
        """Reserve one canonical Economy price receipt. Dynamic prices require a provider-neutral upper-bound cost basis and evidence reference."""
        return cast(
            EconomyPriceReservationReserveResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyProviderLifecycleRecordCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def record_provider_lifecycle_event(
        self, request: EconomyProviderLifecycleRecordRequest
    ) -> EconomyProviderLifecycleRecordResponse:
        """Record verified external provider lifecycle evidence as Aware wallet receipt truth."""
        return cast(
            EconomyProviderLifecycleRecordResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyServiceOperationPermitEnsureCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_service_operation_permit(
        self, request: EconomyServiceOperationPermitEnsureRequest
    ) -> EconomyServiceOperationPermitEnsureResponse:
        """Ensure or refresh the admitted actor's Economy permit for one priced Service operation contract."""
        return cast(
            EconomyServiceOperationPermitEnsureResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomySmartContractReservationPrepareCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def prepare_smart_contract_reservation(
        self, request: EconomySmartContractReservationPrepareRequest
    ) -> EconomySmartContractReservationPrepareResponse:
        """Reserve service capital from a committed Aware Wallet through a smart-contract escrow receipt."""
        return cast(
            EconomySmartContractReservationPrepareResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomySmartContractReservationReleaseCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def release_smart_contract_reservation(
        self, request: EconomySmartContractReservationReleaseRequest
    ) -> EconomySmartContractReservationReleaseResponse:
        """Cancel or expire a pending smart-contract reservation and release its held wallet capital."""
        return cast(
            EconomySmartContractReservationReleaseResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomySmartContractSettlementFinalizeCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def finalize_smart_contract_settlement(
        self, request: EconomySmartContractSettlementFinalizeRequest
    ) -> EconomySmartContractSettlementFinalizeResponse:
        """Finalize a smart-contract settlement and reconcile payer/receiver Aware Wallet balances."""
        return cast(
            EconomySmartContractSettlementFinalizeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyWalletBalanceDescribeCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_wallet_balance(
        self, request: EconomyWalletBalanceDescribeRequest
    ) -> EconomyWalletBalanceDescribeResponse:
        """Read the current Economy wallet balance for a wallet and coin."""
        return cast(
            EconomyWalletBalanceDescribeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyWalletCapitalFrameResolveCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_wallet_capital_frame(
        self, request: EconomyWalletCapitalFrameResolveRequest
    ) -> EconomyWalletCapitalFrameResolveResponse:
        """Resolve an operator-safe wallet capital read frame from Economy replica truth."""
        return cast(
            EconomyWalletCapitalFrameResolveResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyWalletCapitalViewStateResolveCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_wallet_capital_view_state(
        self, request: EconomyWalletCapitalViewStateResolveRequest
    ) -> EconomyWalletCapitalViewStateV1:
        """Resolve the wallet-capital API view state from Economy replica truth."""
        return cast(
            EconomyWalletCapitalViewStateV1,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyWalletFundingCancelCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def record_wallet_funding_expiration(
        self, request: EconomyWalletFundingCancelRequest
    ) -> EconomyWalletFundingCancelResponse:
        """Record verified terminal no-credit evidence and cancel the funding intent."""
        return cast(
            EconomyWalletFundingCancelResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyWalletFundingContextResolveCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_wallet_funding_context(
        self, request: EconomyWalletFundingContextResolveRequest
    ) -> EconomyWalletFundingContextResolveResponse:
        """Resolve provider-neutral committed wallet-funding context by intent and commit identity."""
        return cast(
            EconomyWalletFundingContextResolveResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyWalletFundingPrepareCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def prepare_wallet_funding(
        self, request: EconomyWalletFundingPrepareRequest
    ) -> EconomyWalletFundingPrepareResponse:
        """Prepare an Aware-owned wallet funding intent before external provider confirmation."""
        return cast(
            EconomyWalletFundingPrepareResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyWalletFundingRecordCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def record_verified_wallet_funding(
        self, request: EconomyWalletFundingRecordRequest
    ) -> EconomyWalletFundingRecordResponse:
        """Record verified external funding evidence as Economy transaction and wallet balance truth."""
        return cast(
            EconomyWalletFundingRecordResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class EconomyApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.economy_actor_status = EconomyEconomyActorStatusCapabilityClient(client)
        self.ensure_finance_entity = EconomyEnsureFinanceEntityCapabilityClient(client)
        self.price_reservation_finalize = EconomyPriceReservationFinalizeCapabilityClient(client)
        self.price_reservation_reserve = EconomyPriceReservationReserveCapabilityClient(client)
        self.provider_lifecycle_record = EconomyProviderLifecycleRecordCapabilityClient(client)
        self.service_operation_permit_ensure = EconomyServiceOperationPermitEnsureCapabilityClient(client)
        self.smart_contract_reservation_prepare = EconomySmartContractReservationPrepareCapabilityClient(client)
        self.smart_contract_reservation_release = EconomySmartContractReservationReleaseCapabilityClient(client)
        self.smart_contract_settlement_finalize = EconomySmartContractSettlementFinalizeCapabilityClient(client)
        self.wallet_balance_describe = EconomyWalletBalanceDescribeCapabilityClient(client)
        self.wallet_capital_frame_resolve = EconomyWalletCapitalFrameResolveCapabilityClient(client)
        self.wallet_capital_view_state_resolve = EconomyWalletCapitalViewStateResolveCapabilityClient(client)
        self.wallet_funding_cancel = EconomyWalletFundingCancelCapabilityClient(client)
        self.wallet_funding_context_resolve = EconomyWalletFundingContextResolveCapabilityClient(client)
        self.wallet_funding_prepare = EconomyWalletFundingPrepareCapabilityClient(client)
        self.wallet_funding_record = EconomyWalletFundingRecordCapabilityClient(client)


class AwareEconomyServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.economy = EconomyApiClient(client)


__all__ = [
    "AwareEconomyServiceApiClient",
    "EconomyApiClient",
    "EconomyEconomyActorStatusCapabilityClient",
    "EconomyEnsureFinanceEntityCapabilityClient",
    "EconomyPriceReservationFinalizeCapabilityClient",
    "EconomyPriceReservationReserveCapabilityClient",
    "EconomyProviderLifecycleRecordCapabilityClient",
    "EconomyServiceOperationPermitEnsureCapabilityClient",
    "EconomySmartContractReservationPrepareCapabilityClient",
    "EconomySmartContractReservationReleaseCapabilityClient",
    "EconomySmartContractSettlementFinalizeCapabilityClient",
    "EconomyWalletBalanceDescribeCapabilityClient",
    "EconomyWalletCapitalFrameResolveCapabilityClient",
    "EconomyWalletCapitalViewStateResolveCapabilityClient",
    "EconomyWalletFundingCancelCapabilityClient",
    "EconomyWalletFundingContextResolveCapabilityClient",
    "EconomyWalletFundingPrepareCapabilityClient",
    "EconomyWalletFundingRecordCapabilityClient",
]
