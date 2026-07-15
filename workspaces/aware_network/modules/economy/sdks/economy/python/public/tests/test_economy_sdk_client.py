from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from aware_economy_sdk import (
    EconomyGateStatus,
    EconomySdkClient,
    EconomyServiceCapitalContractCompileReceipt,
    EconomyServiceOperationPermitReceipt,
    build_economy_gate_snapshot,
    wallet_capital_view_state_from_frame,
)
from aware_economy_service_dto.economy.service import (
    EconomyActorStatusRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyActorStatusResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyEnsureFinanceEntityRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyEnsureFinanceEntityResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationFinalizeRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationFinalizeResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationReserveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyPriceReservationReserveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyProviderLifecycleRecordRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyProviderLifecycleRecordResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyServiceOperationPermitEnsureRequest,
    EconomyServiceOperationPermitEnsureResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationPrepareRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationPrepareResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationReleaseRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractReservationReleaseResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractSettlementFinalizeRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomySmartContractSettlementFinalizeResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletBalanceDescribeRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletBalanceDescribeResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalBalanceSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalConversionQuoteSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFundingProviderSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalViewStateResolveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalTransactionIntentSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingContextResolveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingContextResolveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingPrepareRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingPrepareResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingRecordRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingRecordResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingCancelRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletFundingCancelResponse,
)


class _RecordingActorStatusClient:
    def __init__(self, response: EconomyActorStatusResponse) -> None:
        self.requests: list[EconomyActorStatusRequest] = []
        self.response = response

    async def economy_actor_status(
        self,
        request: EconomyActorStatusRequest,
    ) -> EconomyActorStatusResponse:
        self.requests.append(request)
        return self.response


class _RecordingEnsureFinanceEntityClient:
    def __init__(self) -> None:
        self.requests: list[EconomyEnsureFinanceEntityRequest] = []
        self.response = EconomyEnsureFinanceEntityResponse(
            finance_role_key="primary",
            finance_entity_id=str(uuid4()),
            wallet_id=str(uuid4()),
            wallet_public_id=str(uuid4()),
        )

    async def ensure_finance_entity(
        self,
        request: EconomyEnsureFinanceEntityRequest,
    ) -> EconomyEnsureFinanceEntityResponse:
        self.requests.append(request)
        return self.response


class _RecordingPriceReservationReserveClient:
    def __init__(self) -> None:
        self.requests: list[EconomyPriceReservationReserveRequest] = []
        self.response = EconomyPriceReservationReserveResponse(
            price_id=str(uuid4()),
            price_schedule_id=str(uuid4()),
            rate_snapshot_id=str(uuid4()),
            price_reservation_id=str(uuid4()),
            quoted_amount=Decimal("12.5"),
            status="reserved",
        )

    async def price_reservation_reserve(
        self,
        request: EconomyPriceReservationReserveRequest,
    ) -> EconomyPriceReservationReserveResponse:
        self.requests.append(request)
        return self.response


class _RecordingPriceReservationFinalizeClient:
    def __init__(self) -> None:
        self.requests: list[EconomyPriceReservationFinalizeRequest] = []
        self.response = EconomyPriceReservationFinalizeResponse(
            price_reservation_id=str(uuid4()),
            status="settled",
            final_amount=Decimal("12.5"),
            actual_cost_basis_amount=Decimal("10"),
            actual_markup_amount=Decimal("2.5"),
            meter_evidence_ref="meter://actual/1",
        )

    async def price_reservation_finalize(
        self,
        request: EconomyPriceReservationFinalizeRequest,
    ) -> EconomyPriceReservationFinalizeResponse:
        self.requests.append(request)
        return self.response


class _RecordingServiceOperationPermitEnsureClient:
    def __init__(self) -> None:
        self.requests: list[EconomyServiceOperationPermitEnsureRequest] = []
        self.response = EconomyServiceOperationPermitEnsureResponse(
            actor_id=str(uuid4()),
            finance_role_key="primary",
            smart_contract_id=str(uuid4()),
            permit_id=str(uuid4()),
            parent_permit_id=None,
            permit_nonce=1,
            finance_entity_id=str(uuid4()),
            wallet_id=str(uuid4()),
            wallet_public_id=str(uuid4()),
            price_schedule_id=str(uuid4()),
            coin_id=str(uuid4()),
            cap_amount=Decimal("10"),
            expires_at="2026-07-13T08:30:00+00:00",
            status="active",
            refreshed=False,
            idempotent_replay=False,
        )

    async def ensure_service_operation_permit(
        self,
        request: EconomyServiceOperationPermitEnsureRequest,
    ) -> EconomyServiceOperationPermitEnsureResponse:
        self.requests.append(request)
        return self.response


class _RecordingSmartContractReservationPrepareClient:
    def __init__(self) -> None:
        self.requests: list[EconomySmartContractReservationPrepareRequest] = []
        self.response = EconomySmartContractReservationPrepareResponse(
            smart_contract_id=str(uuid4()),
            permit_id=str(uuid4()),
            reservation_id=str(uuid4()),
            escrow_id=str(uuid4()),
            payer_finance_entity_id=str(uuid4()),
            payer_wallet_id=str(uuid4()),
            payer_wallet_public_id=str(uuid4()),
            op_nonce=1,
            coin_id=str(uuid4()),
            max_cost=Decimal("10"),
            payer_balance=Decimal("30"),
            payer_held_balance=Decimal("10"),
            payer_available_balance=Decimal("20"),
            status="pending",
            idempotent_replay=False,
        )

    async def prepare_smart_contract_reservation(
        self,
        request: EconomySmartContractReservationPrepareRequest,
    ) -> EconomySmartContractReservationPrepareResponse:
        self.requests.append(request)
        return self.response


class _RecordingSmartContractReservationReleaseClient:
    def __init__(self) -> None:
        self.requests: list[EconomySmartContractReservationReleaseRequest] = []
        self.response = EconomySmartContractReservationReleaseResponse(
            smart_contract_id=str(uuid4()),
            permit_id=str(uuid4()),
            reservation_id=str(uuid4()),
            escrow_id=str(uuid4()),
            payer_finance_entity_id=str(uuid4()),
            payer_wallet_id=str(uuid4()),
            payer_wallet_public_id=str(uuid4()),
            payer_wallet_balance_id=str(uuid4()),
            coin_id=str(uuid4()),
            released_amount=Decimal("10"),
            payer_balance=Decimal("30"),
            payer_previous_held_balance=Decimal("10"),
            payer_new_held_balance=Decimal("0"),
            payer_previous_available_balance=Decimal("20"),
            payer_new_available_balance=Decimal("30"),
            status="cancelled",
            idempotent_replay=False,
        )

    async def release_smart_contract_reservation(
        self,
        request: EconomySmartContractReservationReleaseRequest,
    ) -> EconomySmartContractReservationReleaseResponse:
        self.requests.append(request)
        return self.response


class _RecordingSmartContractSettlementFinalizeClient:
    def __init__(self) -> None:
        self.requests: list[EconomySmartContractSettlementFinalizeRequest] = []
        self.response = EconomySmartContractSettlementFinalizeResponse(
            smart_contract_id=str(uuid4()),
            permit_id=str(uuid4()),
            reservation_id=str(uuid4()),
            settlement_id=str(uuid4()),
            transaction_id=str(uuid4()),
            payer_finance_entity_id=str(uuid4()),
            payer_wallet_id=str(uuid4()),
            payer_wallet_public_id=str(uuid4()),
            payer_wallet_balance_id=str(uuid4()),
            payer_previous_balance=Decimal("30"),
            payer_new_balance=Decimal("23"),
            payer_previous_held_balance=Decimal("10"),
            payer_new_held_balance=Decimal("0"),
            payer_previous_available_balance=Decimal("20"),
            payer_new_available_balance=Decimal("23"),
            receiver_finance_entity_id=str(uuid4()),
            receiver_wallet_id=str(uuid4()),
            receiver_wallet_public_id=str(uuid4()),
            receiver_wallet_balance_id=str(uuid4()),
            receiver_previous_balance=Decimal("1"),
            receiver_new_balance=Decimal("8"),
            coin_id=str(uuid4()),
            final_cost=Decimal("7"),
            status="settled",
            idempotent_replay=False,
        )

    async def finalize_smart_contract_settlement(
        self,
        request: EconomySmartContractSettlementFinalizeRequest,
    ) -> EconomySmartContractSettlementFinalizeResponse:
        self.requests.append(request)
        return self.response


class _RecordingWalletFundingPrepareClient:
    def __init__(self) -> None:
        self.requests: list[EconomyWalletFundingPrepareRequest] = []
        self.response = EconomyWalletFundingPrepareResponse(
            transaction_intent_id=str(uuid4()),
            transaction_intent_commit_id=str(uuid4()),
            funding_intent_key="funding-intent-1",
            idempotency_key="idem-prepare-1",
            provider_key="stripe",
            provider_config_id=str(uuid4()),
            provider_route_id=str(uuid4()),
            provider_finance_entity_id=str(uuid4()),
            recipient_finance_entity_id=str(uuid4()),
            recipient_wallet_id=str(uuid4()),
            recipient_wallet_public_id=str(uuid4()),
            coin_id=str(uuid4()),
            amount=Decimal("25"),
            capital_conversion_quote_id=str(uuid4()),
            quote_hash="a" * 64,
            external_amount_minor=2500,
            external_currency="USD",
            conversion_mode="direct_denomination",
            quote_captured_at="2026-07-10T08:30:00+00:00",
            status="created",
            idempotent_replay=False,
        )

    async def prepare_wallet_funding(
        self,
        request: EconomyWalletFundingPrepareRequest,
    ) -> EconomyWalletFundingPrepareResponse:
        self.requests.append(request)
        return self.response


class _RecordingWalletFundingContextResolveClient:
    def __init__(self) -> None:
        self.requests: list[EconomyWalletFundingContextResolveRequest] = []
        self.response = EconomyWalletFundingContextResolveResponse(
            transaction_intent_id=str(uuid4()),
            transaction_intent_commit_id=str(uuid4()),
            funding_intent_key="funding-intent-1",
            idempotency_key="idem-prepare-1",
            provider_key="stripe",
            provider_config_id=str(uuid4()),
            provider_route_id=str(uuid4()),
            provider_finance_entity_id=str(uuid4()),
            recipient_finance_entity_id=str(uuid4()),
            recipient_wallet_id=str(uuid4()),
            recipient_wallet_public_id=str(uuid4()),
            coin_id=str(uuid4()),
            amount=Decimal("25"),
            status="created",
            capital_conversion_quote_id=str(uuid4()),
            quote_hash="a" * 64,
            external_amount_minor=2500,
            external_currency="USD",
            target_amount=Decimal("25"),
            conversion_mode="direct_denomination",
            quote_source="external_capital_provider_route",
            quote_captured_at="2026-07-10T08:30:00+00:00",
        )

    async def resolve_wallet_funding_context(
        self,
        request: EconomyWalletFundingContextResolveRequest,
    ) -> EconomyWalletFundingContextResolveResponse:
        self.requests.append(request)
        return self.response


class _RecordingWalletFundingRecordClient:
    def __init__(self) -> None:
        self.requests: list[EconomyWalletFundingRecordRequest] = []
        self.response = EconomyWalletFundingRecordResponse(
            transaction_intent_id=str(uuid4()),
            transaction_intent_commit_id=str(uuid4()),
            capital_conversion_quote_id=str(uuid4()),
            quote_hash="a" * 64,
            transaction_external_id=str(uuid4()),
            transaction_id=str(uuid4()),
            transaction_nonce=23,
            wallet_external_ingress_application_id=str(uuid4()),
            wallet_balance_id=str(uuid4()),
            provider_finance_entity_id=str(uuid4()),
            recipient_finance_entity_id=str(uuid4()),
            recipient_wallet_id=str(uuid4()),
            recipient_wallet_public_id=str(uuid4()),
            coin_id=str(uuid4()),
            amount=Decimal("25"),
            previous_balance=Decimal("5"),
            new_balance=Decimal("30"),
            status="processed",
            idempotent_replay=False,
        )

    async def record_verified_wallet_funding(
        self,
        request: EconomyWalletFundingRecordRequest,
    ) -> EconomyWalletFundingRecordResponse:
        self.requests.append(request)
        return self.response


class _RecordingWalletFundingCancelClient:
    def __init__(self) -> None:
        self.requests: list[EconomyWalletFundingCancelRequest] = []
        self.response = EconomyWalletFundingCancelResponse(
            transaction_intent_id=str(uuid4()),
            transaction_intent_commit_id=str(uuid4()),
            transaction_intent_external_expiration_id=str(uuid4()),
            provider_config_id=str(uuid4()),
            capital_conversion_quote_id=str(uuid4()),
            quote_hash="a" * 64,
            provider_key="stripe",
            provider_event_id="evt_checkout_expired_1",
            provider_public_reference="cs_test_expired_1",
            status="canceled",
            idempotent_replay=False,
        )

    async def record_wallet_funding_expiration(
        self,
        request: EconomyWalletFundingCancelRequest,
    ) -> EconomyWalletFundingCancelResponse:
        self.requests.append(request)
        return self.response


class _RecordingProviderLifecycleRecordClient:
    def __init__(self) -> None:
        self.requests: list[EconomyProviderLifecycleRecordRequest] = []
        self.response = EconomyProviderLifecycleRecordResponse(
            provider_lifecycle_receipt_id=str(uuid4()),
            wallet_balance_id=str(uuid4()),
            provider_finance_entity_id=str(uuid4()),
            provider_key="stripe",
            provider_event_id="evt_refund_1",
            provider_lifecycle_object_id="re_wallet_1",
            provider_lifecycle_effect_key="refund",
            idempotency_key="stripe:lifecycle:re_wallet_1:refund",
            wallet_finance_entity_id=str(uuid4()),
            wallet_id=str(uuid4()),
            wallet_public_id=str(uuid4()),
            coin_id=str(uuid4()),
            amount=Decimal("5"),
            event_kind="refund",
            status="applied",
            previous_balance=Decimal("30"),
            new_balance=Decimal("25"),
            previous_held_balance=Decimal("0"),
            new_held_balance=Decimal("0"),
            previous_available_balance=Decimal("30"),
            new_available_balance=Decimal("25"),
            provider_payment_reference="pi_wallet_1",
            provider_payload_hash="payload-hash",
            transaction_id=str(uuid4()),
            transaction_external_id=str(uuid4()),
            idempotent_replay=False,
        )

    async def record_provider_lifecycle_event(
        self,
        request: EconomyProviderLifecycleRecordRequest,
    ) -> EconomyProviderLifecycleRecordResponse:
        self.requests.append(request)
        return self.response


class _RecordingWalletBalanceDescribeClient:
    def __init__(self) -> None:
        self.requests: list[EconomyWalletBalanceDescribeRequest] = []
        self.response = EconomyWalletBalanceDescribeResponse(
            wallet_balance_id=str(uuid4()),
            wallet_id=str(uuid4()),
            coin_id=str(uuid4()),
            balance=Decimal("30"),
            held_balance=Decimal("10"),
            available_balance=Decimal("20"),
            ready=True,
            last_transaction_id=str(uuid4()),
        )

    async def describe_wallet_balance(
        self,
        request: EconomyWalletBalanceDescribeRequest,
    ) -> EconomyWalletBalanceDescribeResponse:
        self.requests.append(request)
        return self.response


class _RecordingWalletCapitalFrameResolveClient:
    def __init__(self) -> None:
        self.requests: list[EconomyWalletCapitalFrameResolveRequest] = []
        wallet_id = uuid4()
        wallet_public_id = uuid4()
        finance_entity_id = uuid4()
        coin_id = uuid4()
        provider_config_id = uuid4()
        provider_route_id = uuid4()
        self.response = EconomyWalletCapitalFrameResolveResponse(
            wallet_id=str(wallet_id),
            wallet_public_id=str(wallet_public_id),
            finance_entity_id=str(finance_entity_id),
            coin_id=str(coin_id),
            ready=True,
            balances=[
                EconomyWalletCapitalBalanceSummary(
                    wallet_balance_id=str(uuid4()),
                    wallet_id=str(wallet_id),
                    wallet_public_id=str(wallet_public_id),
                    finance_entity_id=str(finance_entity_id),
                    coin_id=str(coin_id),
                    balance=Decimal("30"),
                    held_balance=Decimal("10"),
                    available_balance=Decimal("20"),
                )
            ],
            funding_providers=[
                EconomyWalletCapitalFundingProviderSummary(
                    provider_config_id=str(provider_config_id),
                    provider_route_id=str(provider_route_id),
                    provider_finance_entity_id=str(uuid4()),
                    provider_key="external_provider",
                    label="External provider",
                    route_key="external-provider-usd",
                    target_coin_id=str(coin_id),
                    external_currency="USD",
                    external_minor_unit_exponent=2,
                    conversion_mode="direct_denomination",
                    status="active",
                )
            ],
            transaction_intents=[
                EconomyWalletCapitalTransactionIntentSummary(
                    transaction_intent_id=str(uuid4()),
                    provider_config_id=str(provider_config_id),
                    recipient_finance_entity_id=str(finance_entity_id),
                    recipient_wallet_id=str(wallet_id),
                    recipient_wallet_public_id=str(wallet_public_id),
                    coin_id=str(coin_id),
                    amount=Decimal("25"),
                    funding_intent_key="wallet-topup-1",
                    idempotency_key="prepare-wallet-topup-1",
                    provider_key="external_provider",
                    status="created",
                    created_at="2026-07-10T08:30:00+00:00",
                    capital_conversion_quote=(
                        EconomyWalletCapitalConversionQuoteSummary(
                            capital_conversion_quote_id=str(uuid4()),
                            provider_route_id=str(provider_route_id),
                            target_coin_id=str(coin_id),
                            external_amount_minor=2500,
                            external_currency="USD",
                            target_amount=Decimal("25"),
                            conversion_mode="direct_denomination",
                            quote_source="external_capital_provider_route",
                            quote_hash="a" * 64,
                            quote_captured_at="2026-07-10T08:30:00+00:00",
                        )
                    ),
                )
            ],
            activity_count=1,
            info="economy wallet capital frame resolved",
        )

    async def resolve_wallet_capital_frame(
        self,
        request: EconomyWalletCapitalFrameResolveRequest,
    ) -> EconomyWalletCapitalFrameResolveResponse:
        self.requests.append(request)
        return self.response


class _RecordingWalletCapitalViewStateResolveClient:
    def __init__(self, frame_client: _RecordingWalletCapitalFrameResolveClient) -> None:
        self.requests: list[EconomyWalletCapitalViewStateResolveRequest] = []
        response = wallet_capital_view_state_from_frame(frame_client.response)
        self.response = response.model_copy(
            update={
                "provenance": {
                    **response.provenance,
                    "sdk_method": "resolve_wallet_capital_view_state",
                },
            }
        )

    async def resolve_wallet_capital_view_state(
        self,
        request: EconomyWalletCapitalViewStateResolveRequest,
    ) -> object:
        self.requests.append(request)
        return self.response


class _RecordingEconomyApiNamespace:
    def __init__(self, actor_status: EconomyActorStatusResponse) -> None:
        self.economy_actor_status = _RecordingActorStatusClient(actor_status)
        self.ensure_finance_entity = _RecordingEnsureFinanceEntityClient()
        self.price_reservation_reserve = _RecordingPriceReservationReserveClient()
        self.price_reservation_finalize = _RecordingPriceReservationFinalizeClient()
        self.service_operation_permit_ensure = (
            _RecordingServiceOperationPermitEnsureClient()
        )
        self.smart_contract_reservation_prepare = (
            _RecordingSmartContractReservationPrepareClient()
        )
        self.smart_contract_reservation_release = (
            _RecordingSmartContractReservationReleaseClient()
        )
        self.smart_contract_settlement_finalize = (
            _RecordingSmartContractSettlementFinalizeClient()
        )
        self.wallet_funding_prepare = _RecordingWalletFundingPrepareClient()
        self.wallet_funding_context_resolve = (
            _RecordingWalletFundingContextResolveClient()
        )
        self.wallet_funding_record = _RecordingWalletFundingRecordClient()
        self.wallet_funding_cancel = _RecordingWalletFundingCancelClient()
        self.provider_lifecycle_record = _RecordingProviderLifecycleRecordClient()
        self.wallet_balance_describe = _RecordingWalletBalanceDescribeClient()
        self.wallet_capital_frame_resolve = _RecordingWalletCapitalFrameResolveClient()
        self.wallet_capital_view_state_resolve = (
            _RecordingWalletCapitalViewStateResolveClient(
                self.wallet_capital_frame_resolve
            )
        )


class _RecordingGeneratedEconomyApiClient:
    def __init__(self, actor_status: EconomyActorStatusResponse) -> None:
        self.economy = _RecordingEconomyApiNamespace(actor_status)


@pytest.mark.asyncio
async def test_economy_sdk_wraps_generated_product_a_client() -> None:
    actor_id = uuid4()
    price_id = uuid4()
    price_reservation_id = uuid4()
    smart_contract_id = uuid4()
    permit_id = uuid4()
    reservation_id = uuid4()
    rate_snapshot_id = uuid4()
    provider_finance_entity_id = uuid4()
    payer_finance_entity_id = uuid4()
    payer_wallet_id = uuid4()
    payer_wallet_public_id = uuid4()
    receiver_finance_entity_id = uuid4()
    receiver_wallet_id = uuid4()
    receiver_wallet_public_id = uuid4()
    recipient_finance_entity_id = uuid4()
    recipient_wallet_id = uuid4()
    recipient_wallet_public_id = uuid4()
    coin_id = uuid4()
    transaction_intent_id = uuid4()
    transaction_intent_commit_id = uuid4()
    capital_conversion_quote_id = uuid4()
    api_client = _RecordingGeneratedEconomyApiClient(_actor_status())
    sdk = EconomySdkClient(api_client=api_client)

    ensure = await sdk.ensure_finance_entity(actor_id=actor_id)
    reserve = await sdk.reserve_price_reservation(
        actor_id=actor_id,
        price_id=price_id,
        request_hash="request-hash-1",
        operation_key="operation-1",
    )
    smart_prepare = await sdk.prepare_smart_contract_reservation(
        actor_id=actor_id,
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        permit_nonce=1,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        args_hash="args-hash-3",
        max_cost=Decimal("10.0"),
        rate_snapshot_id=rate_snapshot_id,
        deadline="2026-07-07T12:30:00Z",
        coin_id=coin_id,
    )
    smart_release = await sdk.release_smart_contract_reservation(
        actor_id=actor_id,
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        reservation_id=reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        coin_id=coin_id,
        status="cancelled",
    )
    smart_finalize = await sdk.finalize_smart_contract_settlement(
        actor_id=actor_id,
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        reservation_id=reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=Decimal("7.0"),
    )
    prepare = await sdk.prepare_wallet_funding(
        target_wallet_id=recipient_wallet_id,
        coin_id=coin_id,
        amount=Decimal("25.0"),
        funding_intent_key="funding-intent-1",
        idempotency_key="idem-prepare-1",
        provider_key="stripe",
    )
    funding_context = await sdk.resolve_wallet_funding_context(
        transaction_intent_id=transaction_intent_id,
        transaction_intent_commit_id=transaction_intent_commit_id,
    )
    record = await sdk.record_verified_wallet_funding(
        transaction_intent_id=transaction_intent_id,
        transaction_intent_commit_id=transaction_intent_commit_id,
        provider_key="stripe",
        provider_event_id="evt_wallet_1",
        idempotency_key="idem-record-1",
        capital_conversion_quote_id=capital_conversion_quote_id,
        quote_hash="a" * 64,
        external_amount_minor=2500,
        external_currency="USD",
        provider_public_reference="pi_wallet_1",
        provider_payload_hash="payload-hash",
        external_created_at="2026-07-07T09:45:00Z",
    )
    lifecycle_record = await sdk.record_provider_lifecycle_event(
        provider_key="stripe",
        provider_event_id="evt_refund_1",
        provider_lifecycle_object_id="re_wallet_1",
        provider_lifecycle_effect_key="refund",
        provider_payment_reference="pi_wallet_1",
        external_amount_minor=500,
        external_currency="USD",
        event_kind="refund",
        provider_payload_hash="payload-hash",
        external_created_at="2026-07-07T10:00:00Z",
        metadata_json={"rail": "wallet", "kind": "refund"},
    )
    balance = await sdk.describe_wallet_balance(
        actor_id=actor_id,
        wallet_id=recipient_wallet_id,
        coin_id=coin_id,
    )
    capital_frame = await sdk.resolve_wallet_capital_frame(
        actor_id=actor_id,
        wallet_id=recipient_wallet_id,
        coin_id=coin_id,
        limit=25,
        include_transaction_externals=False,
    )
    finalize = await sdk.finalize_price_reservation(
        actor_id=None,
        price_reservation_id=price_reservation_id,
        status="settled",
        actual_cost_basis_amount=Decimal("10"),
        cost_basis_coin_id=coin_id,
        meter_evidence_ref="meter://actual/1",
    )
    gate = await sdk.gate_snapshot(actor_id=actor_id)

    assert ensure is api_client.economy.ensure_finance_entity.response
    assert reserve is api_client.economy.price_reservation_reserve.response
    assert smart_prepare is (
        api_client.economy.smart_contract_reservation_prepare.response
    )
    assert smart_release is (
        api_client.economy.smart_contract_reservation_release.response
    )
    assert smart_finalize is (
        api_client.economy.smart_contract_settlement_finalize.response
    )
    assert prepare is api_client.economy.wallet_funding_prepare.response
    assert funding_context is api_client.economy.wallet_funding_context_resolve.response
    assert record is api_client.economy.wallet_funding_record.response
    assert lifecycle_record is api_client.economy.provider_lifecycle_record.response
    assert balance is api_client.economy.wallet_balance_describe.response
    assert capital_frame is api_client.economy.wallet_capital_frame_resolve.response
    assert finalize is api_client.economy.price_reservation_finalize.response
    assert gate.status is EconomyGateStatus.ready
    assert api_client.economy.ensure_finance_entity.requests == [
        EconomyEnsureFinanceEntityRequest(
            actor_id=str(actor_id),
            finance_role_key="primary",
        )
    ]
    assert api_client.economy.economy_actor_status.requests == [
        EconomyActorStatusRequest(
            actor_id=str(actor_id),
            finance_role_key="primary",
        )
    ]
    assert api_client.economy.price_reservation_reserve.requests == [
        EconomyPriceReservationReserveRequest(
            actor_id=str(actor_id),
            price_id=str(price_id),
            request_hash="request-hash-1",
            operation_key="operation-1",
        )
    ]
    assert api_client.economy.smart_contract_reservation_prepare.requests == [
        EconomySmartContractReservationPrepareRequest(
            actor_id=str(actor_id),
            smart_contract_id=str(smart_contract_id),
            permit_id=str(permit_id),
            permit_nonce=1,
            payer_finance_entity_id=str(payer_finance_entity_id),
            payer_wallet_id=str(payer_wallet_id),
            payer_wallet_public_id=str(payer_wallet_public_id),
            args_hash="args-hash-3",
            max_cost=Decimal("10"),
            rate_snapshot_id=str(rate_snapshot_id),
            deadline="2026-07-07T12:30:00Z",
            coin_id=str(coin_id),
        )
    ]
    assert api_client.economy.smart_contract_reservation_release.requests == [
        EconomySmartContractReservationReleaseRequest(
            actor_id=str(actor_id),
            smart_contract_id=str(smart_contract_id),
            permit_id=str(permit_id),
            reservation_id=str(reservation_id),
            payer_finance_entity_id=str(payer_finance_entity_id),
            payer_wallet_id=str(payer_wallet_id),
            payer_wallet_public_id=str(payer_wallet_public_id),
            coin_id=str(coin_id),
            status="cancelled",
        )
    ]
    assert api_client.economy.smart_contract_settlement_finalize.requests == [
        EconomySmartContractSettlementFinalizeRequest(
            actor_id=str(actor_id),
            smart_contract_id=str(smart_contract_id),
            permit_id=str(permit_id),
            reservation_id=str(reservation_id),
            payer_finance_entity_id=str(payer_finance_entity_id),
            payer_wallet_id=str(payer_wallet_id),
            payer_wallet_public_id=str(payer_wallet_public_id),
            receiver_finance_entity_id=str(receiver_finance_entity_id),
            receiver_wallet_id=str(receiver_wallet_id),
            receiver_wallet_public_id=str(receiver_wallet_public_id),
            coin_id=str(coin_id),
            final_cost=Decimal("7"),
        )
    ]
    assert api_client.economy.wallet_funding_prepare.requests == [
        EconomyWalletFundingPrepareRequest(
            target_wallet_id=str(recipient_wallet_id),
            coin_id=str(coin_id),
            amount=Decimal("25"),
            funding_intent_key="funding-intent-1",
            idempotency_key="idem-prepare-1",
            provider_key="stripe",
        )
    ]
    assert api_client.economy.wallet_funding_context_resolve.requests == [
        EconomyWalletFundingContextResolveRequest(
            transaction_intent_id=str(transaction_intent_id),
            transaction_intent_commit_id=str(transaction_intent_commit_id),
        )
    ]
    assert api_client.economy.wallet_funding_record.requests == [
        EconomyWalletFundingRecordRequest(
            transaction_intent_id=str(transaction_intent_id),
            transaction_intent_commit_id=str(transaction_intent_commit_id),
            provider_key="stripe",
            provider_event_id="evt_wallet_1",
            idempotency_key="idem-record-1",
            capital_conversion_quote_id=str(capital_conversion_quote_id),
            quote_hash="a" * 64,
            external_amount_minor=2500,
            external_currency="USD",
            provider_public_reference="pi_wallet_1",
            provider_payload_hash="payload-hash",
            external_created_at="2026-07-07T09:45:00Z",
        )
    ]
    assert api_client.economy.provider_lifecycle_record.requests == [
        EconomyProviderLifecycleRecordRequest(
            provider_key="stripe",
            provider_event_id="evt_refund_1",
            provider_lifecycle_object_id="re_wallet_1",
            provider_lifecycle_effect_key="refund",
            provider_payment_reference="pi_wallet_1",
            external_amount_minor=500,
            external_currency="USD",
            event_kind="refund",
            provider_payload_hash="payload-hash",
            external_created_at="2026-07-07T10:00:00Z",
            metadata_json={"rail": "wallet", "kind": "refund"},
        )
    ]
    assert api_client.economy.wallet_balance_describe.requests == [
        EconomyWalletBalanceDescribeRequest(
            actor_id=str(actor_id),
            wallet_id=str(recipient_wallet_id),
            coin_id=str(coin_id),
        )
    ]
    assert api_client.economy.wallet_capital_frame_resolve.requests == [
        EconomyWalletCapitalFrameResolveRequest(
            actor_id=str(actor_id),
            wallet_id=str(recipient_wallet_id),
            coin_id=str(coin_id),
            limit=25,
            include_transaction_externals=False,
        )
    ]
    assert api_client.economy.price_reservation_finalize.requests == [
        EconomyPriceReservationFinalizeRequest(
            actor_id=None,
            price_reservation_id=str(price_reservation_id),
            status="settled",
            actual_cost_basis_amount=Decimal("10"),
            cost_basis_coin_id=str(coin_id),
            meter_evidence_ref="meter://actual/1",
        )
    ]


def test_wallet_capital_view_state_from_frame_maps_action_state() -> None:
    api_client = _RecordingGeneratedEconomyApiClient(_actor_status())

    state = wallet_capital_view_state_from_frame(
        api_client.economy.wallet_capital_frame_resolve.response
    )

    assert state.view_ref == "economy.wallet_capital"
    assert state.operation == "refresh_wallet_capital"
    assert state.status == "ready"
    assert state.action_keys == ["refresh_wallet_capital", "fund_wallet"]
    assert state.can_fund_wallet is True
    assert state.balances[0].available_balance == Decimal("20")
    assert state.pending_funding_intents[0].provider_key == "external_provider"
    assert state.pending_funding_intents[0].quote_hash == "a" * 64
    assert state.provenance["source_kind"] == "economy_sdk"


@pytest.mark.asyncio
async def test_economy_sdk_refresh_wallet_capital_returns_view_state() -> None:
    actor_id = uuid4()
    wallet_id = uuid4()
    coin_id = uuid4()
    api_client = _RecordingGeneratedEconomyApiClient(_actor_status())
    sdk = EconomySdkClient(api_client=api_client)

    state = await sdk.refresh_wallet_capital(
        actor_id=actor_id,
        wallet_id=wallet_id,
        coin_id=coin_id,
        limit=10,
        include_reservations=False,
    )

    assert state.view_ref == "economy.wallet_capital"
    assert state.provenance["sdk_method"] == "resolve_wallet_capital_view_state"
    assert state.action_keys == ["refresh_wallet_capital", "fund_wallet"]
    assert api_client.economy.wallet_capital_view_state_resolve.requests == [
        EconomyWalletCapitalViewStateResolveRequest(
            actor_id=str(actor_id),
            wallet_id=str(wallet_id),
            coin_id=str(coin_id),
            limit=10,
            include_reservations=False,
        )
    ]
    assert api_client.economy.wallet_capital_frame_resolve.requests == []


def test_economy_service_dto_exports_wallet_capital_view_state_request() -> None:
    request = EconomyWalletCapitalViewStateResolveRequest(wallet_id="wallet-1")

    assert request.operation == "resolve_wallet_capital_view_state"
    assert request.wallet_id == "wallet-1"
    assert request.include_settlements is True


@pytest.mark.asyncio
async def test_economy_sdk_records_wallet_funding_expiration_exactly() -> None:
    transaction_intent_id = uuid4()
    transaction_intent_commit_id = uuid4()
    capital_conversion_quote_id = uuid4()
    api_client = _RecordingGeneratedEconomyApiClient(_actor_status())
    sdk = EconomySdkClient(api_client=api_client)

    response = await sdk.record_wallet_funding_expiration(
        transaction_intent_id=transaction_intent_id,
        transaction_intent_commit_id=transaction_intent_commit_id,
        provider_key="stripe",
        provider_event_id="evt_checkout_expired_1",
        idempotency_key="stripe:event:evt_checkout_expired_1",
        capital_conversion_quote_id=capital_conversion_quote_id,
        quote_hash="b" * 64,
        provider_public_reference="cs_test_expired_1",
        provider_payload_hash="sha256:" + "a" * 64,
        external_created_at="2026-07-10T09:45:00Z",
    )

    assert response is api_client.economy.wallet_funding_cancel.response
    assert api_client.economy.wallet_funding_cancel.requests == [
        EconomyWalletFundingCancelRequest(
            transaction_intent_id=str(transaction_intent_id),
            transaction_intent_commit_id=str(transaction_intent_commit_id),
            provider_key="stripe",
            provider_event_id="evt_checkout_expired_1",
            idempotency_key="stripe:event:evt_checkout_expired_1",
            capital_conversion_quote_id=str(capital_conversion_quote_id),
            quote_hash="b" * 64,
            provider_public_reference="cs_test_expired_1",
            provider_payload_hash="sha256:" + "a" * 64,
            external_created_at="2026-07-10T09:45:00Z",
        )
    ]


@pytest.mark.asyncio
async def test_economy_sdk_fund_wallet_routes_to_prepare_wallet_funding() -> None:
    target_wallet_id = uuid4()
    coin_id = uuid4()
    api_client = _RecordingGeneratedEconomyApiClient(_actor_status())
    sdk = EconomySdkClient(api_client=api_client)

    response = await sdk.fund_wallet(
        target_wallet_id=target_wallet_id,
        coin_id=coin_id,
        amount=Decimal("25.0"),
        funding_intent_key="wallet-topup-1",
        idempotency_key="idem-fund-1",
        provider_key="external_provider",
    )

    assert response is api_client.economy.wallet_funding_prepare.response
    assert api_client.economy.wallet_funding_prepare.requests == [
        EconomyWalletFundingPrepareRequest(
            target_wallet_id=str(target_wallet_id),
            coin_id=str(coin_id),
            amount=Decimal("25"),
            funding_intent_key="wallet-topup-1",
            idempotency_key="idem-fund-1",
            provider_key="external_provider",
        )
    ]


@pytest.mark.asyncio
async def test_economy_sdk_ensures_service_operation_permit() -> None:
    actor_id = uuid4()
    smart_contract_id = uuid4()
    permit_id = uuid4()
    parent_permit_id = uuid4()
    finance_entity_id = uuid4()
    wallet_id = uuid4()
    wallet_public_id = uuid4()
    price_schedule_id = uuid4()
    coin_id = uuid4()
    requested_expiry = datetime.now(UTC) + timedelta(hours=1)
    response_expiry = requested_expiry + timedelta(hours=1)
    api_client = _RecordingGeneratedEconomyApiClient(_actor_status())
    api_client.economy.service_operation_permit_ensure.response = (
        EconomyServiceOperationPermitEnsureResponse(
            actor_id=str(actor_id),
            finance_role_key="primary",
            smart_contract_id=str(smart_contract_id),
            permit_id=str(permit_id),
            parent_permit_id=str(parent_permit_id),
            permit_nonce=6,
            finance_entity_id=str(finance_entity_id),
            wallet_id=str(wallet_id),
            wallet_public_id=str(wallet_public_id),
            price_schedule_id=str(price_schedule_id),
            coin_id=str(coin_id),
            cap_amount=Decimal("30"),
            expires_at=response_expiry.isoformat(),
            status="active",
            refreshed=True,
            idempotent_replay=False,
        )
    )
    sdk = EconomySdkClient(api_client=api_client)

    receipt = await sdk.ensure_service_operation_permit(
        actor_id=actor_id,
        smart_contract_id=smart_contract_id,
        price_schedule_id=price_schedule_id,
        coin_id=coin_id,
        cap_amount=Decimal("25"),
        expires_at=requested_expiry,
    )

    assert isinstance(receipt, EconomyServiceOperationPermitReceipt)
    assert receipt.actor_id == actor_id
    assert receipt.smart_contract_id == smart_contract_id
    assert receipt.permit_id == permit_id
    assert receipt.parent_permit_id == parent_permit_id
    assert receipt.permit_nonce == 6
    assert receipt.finance_entity_id == finance_entity_id
    assert receipt.wallet_id == wallet_id
    assert receipt.wallet_public_id == wallet_public_id
    assert receipt.cap_amount == Decimal("30")
    assert receipt.expires_at == response_expiry
    assert receipt.refreshed is True
    assert receipt.idempotent_replay is False
    assert api_client.economy.service_operation_permit_ensure.requests == [
        EconomyServiceOperationPermitEnsureRequest(
            actor_id=str(actor_id),
            finance_role_key="primary",
            smart_contract_id=str(smart_contract_id),
            price_schedule_id=str(price_schedule_id),
            coin_id=str(coin_id),
            cap_amount=Decimal("25"),
            expires_at=requested_expiry.isoformat(),
        )
    ]


@pytest.mark.asyncio
async def test_economy_sdk_compiles_service_capital_contract() -> None:
    actor_id = uuid4()
    price_id = uuid4()
    price_schedule_id = uuid4()
    rate_snapshot_id = uuid4()
    price_reservation_id = uuid4()
    smart_contract_id = uuid4()
    permit_id = uuid4()
    reservation_id = uuid4()
    escrow_id = uuid4()
    payer_finance_entity_id = uuid4()
    payer_wallet_id = uuid4()
    payer_wallet_public_id = uuid4()
    receiver_finance_entity_id = uuid4()
    receiver_wallet_id = uuid4()
    receiver_wallet_public_id = uuid4()
    coin_id = uuid4()
    api_client = _RecordingGeneratedEconomyApiClient(_actor_status())
    api_client.economy.price_reservation_reserve.response = (
        EconomyPriceReservationReserveResponse(
            price_id=str(price_id),
            price_schedule_id=str(price_schedule_id),
            rate_snapshot_id=str(rate_snapshot_id),
            price_reservation_id=str(price_reservation_id),
            quoted_amount=Decimal("12.5"),
            status="reserved",
        )
    )
    api_client.economy.smart_contract_reservation_prepare.response = (
        EconomySmartContractReservationPrepareResponse(
            smart_contract_id=str(smart_contract_id),
            permit_id=str(permit_id),
            reservation_id=str(reservation_id),
            escrow_id=str(escrow_id),
            payer_finance_entity_id=str(payer_finance_entity_id),
            payer_wallet_id=str(payer_wallet_id),
            payer_wallet_public_id=str(payer_wallet_public_id),
            op_nonce=9,
            coin_id=str(coin_id),
            max_cost=Decimal("12.5"),
            payer_balance=Decimal("30"),
            payer_held_balance=Decimal("12.5"),
            payer_available_balance=Decimal("17.5"),
            status="pending",
            idempotent_replay=False,
        )
    )
    sdk = EconomySdkClient(api_client=api_client)

    receipt = await sdk.compile_service_capital_contract(
        actor_id=actor_id,
        price_id=price_id,
        request_hash="request-hash-service-1",
        operation_key="service-operation-1",
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        permit_nonce=2,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        deadline="2026-07-08T12:30:00Z",
    )

    assert isinstance(receipt, EconomyServiceCapitalContractCompileReceipt)
    assert receipt.price_id == price_id
    assert receipt.price_schedule_id == price_schedule_id
    assert receipt.rate_snapshot_id == rate_snapshot_id
    assert receipt.price_reservation_id == price_reservation_id
    assert receipt.quoted_amount == Decimal("12.5")
    assert receipt.smart_contract_id == smart_contract_id
    assert receipt.permit_id == permit_id
    assert receipt.reservation_id == reservation_id
    assert receipt.escrow_id == escrow_id
    assert receipt.op_nonce == 9
    assert receipt.payer_finance_entity_id == payer_finance_entity_id
    assert receipt.receiver_finance_entity_id == receiver_finance_entity_id
    assert receipt.max_cost == Decimal("12.5")
    assert receipt.payer_balance == Decimal("30")
    assert receipt.payer_held_balance == Decimal("12.5")
    assert receipt.payer_available_balance == Decimal("17.5")
    assert receipt.status == "pending"
    assert api_client.economy.price_reservation_reserve.requests == [
        EconomyPriceReservationReserveRequest(
            actor_id=str(actor_id),
            price_id=str(price_id),
            request_hash="request-hash-service-1",
            operation_key="service-operation-1",
        )
    ]
    assert api_client.economy.smart_contract_reservation_prepare.requests == [
        EconomySmartContractReservationPrepareRequest(
            actor_id=str(actor_id),
            smart_contract_id=str(smart_contract_id),
            permit_id=str(permit_id),
            permit_nonce=2,
            payer_finance_entity_id=str(payer_finance_entity_id),
            payer_wallet_id=str(payer_wallet_id),
            payer_wallet_public_id=str(payer_wallet_public_id),
            args_hash="request-hash-service-1",
            max_cost=Decimal("12.5"),
            rate_snapshot_id=str(rate_snapshot_id),
            deadline="2026-07-08T12:30:00Z",
            coin_id=str(coin_id),
        )
    ]


def test_build_economy_gate_snapshot_reports_missing_finance_entity() -> None:
    actor_id = uuid4()

    snapshot = build_economy_gate_snapshot(
        actor_id=actor_id,
        status=EconomyActorStatusResponse(
            finance_role_key="primary",
            finance_entity_ready=False,
            wallet_ready=False,
            next_step="ensure_finance_entity",
            finance_entity_id=None,
            wallet_id=None,
            wallet_public_id=None,
        ),
    )

    assert snapshot.status is EconomyGateStatus.missing_finance_entity
    assert snapshot.crossed is False
    assert snapshot.finance_role_key == "primary"
    assert snapshot.next_step == "ensure_finance_entity"


def test_build_economy_gate_snapshot_reports_missing_wallet() -> None:
    actor_id = uuid4()
    finance_entity_id = uuid4()

    snapshot = build_economy_gate_snapshot(
        actor_id=actor_id,
        status=EconomyActorStatusResponse(
            finance_role_key="primary",
            finance_entity_ready=True,
            wallet_ready=False,
            next_step="ensure_finance_entity",
            finance_entity_id=str(finance_entity_id),
            wallet_id=None,
            wallet_public_id=None,
        ),
    )

    assert snapshot.status is EconomyGateStatus.missing_wallet
    assert snapshot.crossed is False
    assert snapshot.finance_entity_id == finance_entity_id


def test_economy_sdk_boundary_avoids_service_protocol_runtime_and_membership_imports() -> (
    None
):
    client_source = (
        Path(__file__).parents[1] / "aware_economy_sdk" / "client.py"
    ).read_text(encoding="utf-8")

    assert "aware_economy_service_protocol" not in client_source
    assert "aware_economy_service_service" not in client_source
    assert "aware_service_runtime" not in client_source
    assert "aware_runtime" not in client_source
    assert "membership_" not in client_source
    assert "EconomyMembership" not in client_source


def _actor_status() -> EconomyActorStatusResponse:
    return EconomyActorStatusResponse(
        finance_role_key="primary",
        finance_entity_ready=True,
        wallet_ready=True,
        next_step="ready",
        finance_entity_id=str(uuid4()),
        wallet_id=str(uuid4()),
        wallet_public_id=str(uuid4()),
    )
