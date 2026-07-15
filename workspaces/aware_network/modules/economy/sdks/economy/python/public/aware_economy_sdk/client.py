from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Protocol, TypeAlias
from uuid import UUID

from aware_economy_service_api import AwareEconomyServiceApiClient
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
    EconomyWalletCapitalFrameResolveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalViewStateResolveRequest,
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
from aware_economy_service_dto.economy.view import EconomyWalletCapitalViewStateV1

from .view_state import wallet_capital_view_state_from_frame

MoneyInput: TypeAlias = Decimal | int | str


class _EconomyActorStatusCapabilityClient(Protocol):
    async def economy_actor_status(
        self,
        request: EconomyActorStatusRequest,
    ) -> EconomyActorStatusResponse: ...


class _EconomyEnsureFinanceEntityCapabilityClient(Protocol):
    async def ensure_finance_entity(
        self,
        request: EconomyEnsureFinanceEntityRequest,
    ) -> EconomyEnsureFinanceEntityResponse: ...


class _EconomyPriceReservationReserveCapabilityClient(Protocol):
    async def price_reservation_reserve(
        self,
        request: EconomyPriceReservationReserveRequest,
    ) -> EconomyPriceReservationReserveResponse: ...


class _EconomyPriceReservationFinalizeCapabilityClient(Protocol):
    async def price_reservation_finalize(
        self,
        request: EconomyPriceReservationFinalizeRequest,
    ) -> EconomyPriceReservationFinalizeResponse: ...


class _EconomyServiceOperationPermitEnsureCapabilityClient(Protocol):
    async def ensure_service_operation_permit(
        self,
        request: EconomyServiceOperationPermitEnsureRequest,
    ) -> EconomyServiceOperationPermitEnsureResponse: ...


class _EconomyWalletFundingPrepareCapabilityClient(Protocol):
    async def prepare_wallet_funding(
        self,
        request: EconomyWalletFundingPrepareRequest,
    ) -> EconomyWalletFundingPrepareResponse: ...


class _EconomyWalletFundingContextResolveCapabilityClient(Protocol):
    async def resolve_wallet_funding_context(
        self,
        request: EconomyWalletFundingContextResolveRequest,
    ) -> EconomyWalletFundingContextResolveResponse: ...


class _EconomyWalletFundingRecordCapabilityClient(Protocol):
    async def record_verified_wallet_funding(
        self,
        request: EconomyWalletFundingRecordRequest,
    ) -> EconomyWalletFundingRecordResponse: ...


class _EconomyWalletFundingCancelCapabilityClient(Protocol):
    async def record_wallet_funding_expiration(
        self,
        request: EconomyWalletFundingCancelRequest,
    ) -> EconomyWalletFundingCancelResponse: ...


class _EconomyProviderLifecycleRecordCapabilityClient(Protocol):
    async def record_provider_lifecycle_event(
        self,
        request: EconomyProviderLifecycleRecordRequest,
    ) -> EconomyProviderLifecycleRecordResponse: ...


class _EconomyWalletBalanceDescribeCapabilityClient(Protocol):
    async def describe_wallet_balance(
        self,
        request: EconomyWalletBalanceDescribeRequest,
    ) -> EconomyWalletBalanceDescribeResponse: ...


class _EconomyWalletCapitalFrameResolveCapabilityClient(Protocol):
    async def resolve_wallet_capital_frame(
        self,
        request: EconomyWalletCapitalFrameResolveRequest,
    ) -> EconomyWalletCapitalFrameResolveResponse: ...


class _EconomyWalletCapitalViewStateResolveCapabilityClient(Protocol):
    async def resolve_wallet_capital_view_state(
        self,
        request: EconomyWalletCapitalViewStateResolveRequest,
    ) -> EconomyWalletCapitalViewStateV1: ...


class _EconomySmartContractReservationPrepareCapabilityClient(Protocol):
    async def prepare_smart_contract_reservation(
        self,
        request: EconomySmartContractReservationPrepareRequest,
    ) -> EconomySmartContractReservationPrepareResponse: ...


class _EconomySmartContractReservationReleaseCapabilityClient(Protocol):
    async def release_smart_contract_reservation(
        self,
        request: EconomySmartContractReservationReleaseRequest,
    ) -> EconomySmartContractReservationReleaseResponse: ...


class _EconomySmartContractSettlementFinalizeCapabilityClient(Protocol):
    async def finalize_smart_contract_settlement(
        self,
        request: EconomySmartContractSettlementFinalizeRequest,
    ) -> EconomySmartContractSettlementFinalizeResponse: ...


class _EconomyApiNamespaceClient(Protocol):
    @property
    def economy_actor_status(self) -> _EconomyActorStatusCapabilityClient: ...

    @property
    def ensure_finance_entity(self) -> _EconomyEnsureFinanceEntityCapabilityClient: ...

    @property
    def price_reservation_reserve(
        self,
    ) -> _EconomyPriceReservationReserveCapabilityClient: ...

    @property
    def price_reservation_finalize(
        self,
    ) -> _EconomyPriceReservationFinalizeCapabilityClient: ...

    @property
    def service_operation_permit_ensure(
        self,
    ) -> _EconomyServiceOperationPermitEnsureCapabilityClient: ...

    @property
    def wallet_funding_prepare(
        self,
    ) -> _EconomyWalletFundingPrepareCapabilityClient: ...

    @property
    def wallet_funding_context_resolve(
        self,
    ) -> _EconomyWalletFundingContextResolveCapabilityClient: ...

    @property
    def wallet_funding_record(
        self,
    ) -> _EconomyWalletFundingRecordCapabilityClient: ...

    @property
    def wallet_funding_cancel(
        self,
    ) -> _EconomyWalletFundingCancelCapabilityClient: ...

    @property
    def provider_lifecycle_record(
        self,
    ) -> _EconomyProviderLifecycleRecordCapabilityClient: ...

    @property
    def wallet_balance_describe(
        self,
    ) -> _EconomyWalletBalanceDescribeCapabilityClient: ...

    @property
    def wallet_capital_frame_resolve(
        self,
    ) -> _EconomyWalletCapitalFrameResolveCapabilityClient: ...

    @property
    def wallet_capital_view_state_resolve(
        self,
    ) -> _EconomyWalletCapitalViewStateResolveCapabilityClient: ...

    @property
    def smart_contract_reservation_prepare(
        self,
    ) -> _EconomySmartContractReservationPrepareCapabilityClient: ...

    @property
    def smart_contract_reservation_release(
        self,
    ) -> _EconomySmartContractReservationReleaseCapabilityClient: ...

    @property
    def smart_contract_settlement_finalize(
        self,
    ) -> _EconomySmartContractSettlementFinalizeCapabilityClient: ...


class EconomyApiClient(Protocol):
    @property
    def economy(self) -> _EconomyApiNamespaceClient: ...


class EconomyGateStatus(str, Enum):
    ready = "ready"
    missing_finance_entity = "missing_finance_entity"
    missing_wallet = "missing_wallet"


@dataclass(frozen=True, slots=True)
class EconomyGateSnapshot:
    status: EconomyGateStatus
    actor_id: UUID
    finance_role_key: str = "primary"
    finance_entity_id: UUID | None = None
    wallet_id: UUID | None = None
    wallet_public_id: UUID | None = None
    next_step: str | None = None

    @property
    def crossed(self) -> bool:
        return self.status is EconomyGateStatus.ready


@dataclass(frozen=True, slots=True)
class EconomyServiceOperationPermitReceipt:
    actor_id: UUID
    finance_role_key: str
    smart_contract_id: UUID
    permit_id: UUID
    parent_permit_id: UUID | None
    permit_nonce: int
    finance_entity_id: UUID
    wallet_id: UUID
    wallet_public_id: UUID
    price_schedule_id: UUID
    coin_id: UUID
    cap_amount: Decimal
    expires_at: datetime
    status: str
    refreshed: bool
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class EconomyServiceCapitalContractCompileReceipt:
    price_id: UUID
    price_schedule_id: UUID
    rate_snapshot_id: UUID
    price_reservation_id: UUID
    quoted_amount: Decimal
    smart_contract_id: UUID
    permit_id: UUID
    reservation_id: UUID
    escrow_id: UUID
    op_nonce: int
    payer_finance_entity_id: UUID
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID
    max_cost: Decimal
    payer_balance: Decimal
    payer_held_balance: Decimal
    payer_available_balance: Decimal
    status: str
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class EconomySdkClient:
    api_client: EconomyApiClient

    async def actor_status(
        self,
        *,
        actor_id: UUID,
        finance_role_key: str = "primary",
    ) -> EconomyActorStatusResponse:
        return await self.api_client.economy.economy_actor_status.economy_actor_status(
            EconomyActorStatusRequest(
                actor_id=str(actor_id),
                finance_role_key=finance_role_key,
            )
        )

    async def fund_wallet(
        self,
        *,
        target_wallet_id: UUID,
        coin_id: UUID,
        amount: MoneyInput,
        funding_intent_key: str,
        idempotency_key: str,
        provider_key: str,
    ) -> EconomyWalletFundingPrepareResponse:
        return await self.prepare_wallet_funding(
            target_wallet_id=target_wallet_id,
            coin_id=coin_id,
            amount=amount,
            funding_intent_key=funding_intent_key,
            idempotency_key=idempotency_key,
            provider_key=provider_key,
        )

    async def ensure_finance_entity(
        self,
        *,
        actor_id: UUID,
        finance_role_key: str = "primary",
    ) -> EconomyEnsureFinanceEntityResponse:
        return (
            await self.api_client.economy.ensure_finance_entity.ensure_finance_entity(
                EconomyEnsureFinanceEntityRequest(
                    actor_id=str(actor_id),
                    finance_role_key=finance_role_key,
                )
            )
        )

    async def reserve_price_reservation(
        self,
        *,
        actor_id: UUID | None,
        price_id: UUID,
        request_hash: str,
        operation_key: str,
        pricing_policy_id: UUID | None = None,
        upper_bound_cost_basis_amount: MoneyInput | None = None,
        cost_basis_coin_id: UUID | None = None,
        meter_evidence_ref: str | None = None,
    ) -> EconomyPriceReservationReserveResponse:
        return await self.api_client.economy.price_reservation_reserve.price_reservation_reserve(
            EconomyPriceReservationReserveRequest(
                actor_id=_dump_optional_uuid(actor_id),
                price_id=str(price_id),
                request_hash=request_hash,
                operation_key=operation_key,
                pricing_policy_id=_dump_optional_uuid(pricing_policy_id),
                upper_bound_cost_basis_amount=_sdk_optional_amount(
                    upper_bound_cost_basis_amount,
                    field_name="upper_bound_cost_basis_amount",
                ),
                cost_basis_coin_id=_dump_optional_uuid(cost_basis_coin_id),
                meter_evidence_ref=meter_evidence_ref,
            )
        )

    async def ensure_service_operation_permit(
        self,
        *,
        actor_id: UUID,
        smart_contract_id: UUID,
        price_schedule_id: UUID,
        coin_id: UUID,
        cap_amount: MoneyInput,
        expires_at: datetime | str,
        finance_role_key: str = "primary",
    ) -> EconomyServiceOperationPermitReceipt:
        requested_cap = _capital_amount(cap_amount, field_name="cap_amount")
        if requested_cap <= Decimal("0"):
            raise ValueError("cap_amount must be > 0")
        requested_expiry = _sdk_datetime(expires_at, field_name="expires_at")
        response = await self.api_client.economy.service_operation_permit_ensure.ensure_service_operation_permit(
            EconomyServiceOperationPermitEnsureRequest(
                actor_id=str(actor_id),
                finance_role_key=finance_role_key,
                smart_contract_id=str(smart_contract_id),
                price_schedule_id=str(price_schedule_id),
                coin_id=str(coin_id),
                cap_amount=requested_cap,
                expires_at=requested_expiry.isoformat(),
            )
        )
        _require_response_uuid(
            response.actor_id, expected=actor_id, field_name="actor_id"
        )
        _require_response_uuid(
            response.smart_contract_id,
            expected=smart_contract_id,
            field_name="smart_contract_id",
        )
        _require_response_uuid(
            response.price_schedule_id,
            expected=price_schedule_id,
            field_name="price_schedule_id",
        )
        _require_response_uuid(response.coin_id, expected=coin_id, field_name="coin_id")
        if response.finance_role_key != finance_role_key:
            raise RuntimeError(
                "Economy permit finance_role_key mismatch: "
                f"expected={finance_role_key!r} actual={response.finance_role_key!r}"
            )
        response_cap = _capital_amount(response.cap_amount, field_name="cap_amount")
        if response_cap < requested_cap:
            raise RuntimeError(
                "Economy permit cap is below the requested envelope: "
                f"requested={requested_cap} actual={response_cap}"
            )
        response_expiry = _sdk_datetime(response.expires_at, field_name="expires_at")
        if response_expiry < requested_expiry:
            raise RuntimeError("Economy permit expiry is below the requested envelope")
        _require_status(
            response.status, field_name="permit.status", allowed=("active",)
        )
        return EconomyServiceOperationPermitReceipt(
            actor_id=actor_id,
            finance_role_key=response.finance_role_key,
            smart_contract_id=smart_contract_id,
            permit_id=_required_uuid(response.permit_id, field_name="permit_id"),
            parent_permit_id=_optional_uuid(response.parent_permit_id),
            permit_nonce=_positive_int(
                response.permit_nonce, field_name="permit_nonce"
            ),
            finance_entity_id=_required_uuid(
                response.finance_entity_id,
                field_name="finance_entity_id",
            ),
            wallet_id=_required_uuid(response.wallet_id, field_name="wallet_id"),
            wallet_public_id=_required_uuid(
                response.wallet_public_id,
                field_name="wallet_public_id",
            ),
            price_schedule_id=price_schedule_id,
            coin_id=coin_id,
            cap_amount=response_cap,
            expires_at=response_expiry,
            status=response.status,
            refreshed=response.refreshed,
            idempotent_replay=response.idempotent_replay,
        )

    async def prepare_smart_contract_reservation(
        self,
        *,
        actor_id: UUID | None,
        smart_contract_id: UUID,
        permit_id: UUID,
        permit_nonce: int,
        payer_finance_entity_id: UUID,
        payer_wallet_id: UUID,
        payer_wallet_public_id: UUID,
        args_hash: str,
        max_cost: MoneyInput,
        rate_snapshot_id: UUID,
        deadline: str,
        coin_id: UUID,
    ) -> EconomySmartContractReservationPrepareResponse:
        return await self.api_client.economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation(
            EconomySmartContractReservationPrepareRequest(
                actor_id=_dump_optional_uuid(actor_id),
                smart_contract_id=str(smart_contract_id),
                permit_id=str(permit_id),
                permit_nonce=permit_nonce,
                payer_finance_entity_id=str(payer_finance_entity_id),
                payer_wallet_id=str(payer_wallet_id),
                payer_wallet_public_id=str(payer_wallet_public_id),
                args_hash=args_hash,
                max_cost=_sdk_amount(max_cost, field_name="max_cost"),
                rate_snapshot_id=str(rate_snapshot_id),
                deadline=deadline,
                coin_id=str(coin_id),
            )
        )

    async def compile_service_capital_contract(
        self,
        *,
        actor_id: UUID | None,
        price_id: UUID,
        request_hash: str,
        operation_key: str,
        smart_contract_id: UUID,
        permit_id: UUID,
        permit_nonce: int,
        payer_finance_entity_id: UUID,
        payer_wallet_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
        deadline: str,
        pricing_policy_id: UUID | None = None,
        upper_bound_cost_basis_amount: MoneyInput | None = None,
        cost_basis_coin_id: UUID | None = None,
        meter_evidence_ref: str | None = None,
    ) -> EconomyServiceCapitalContractCompileReceipt:
        price_response = await self.reserve_price_reservation(
            actor_id=actor_id,
            price_id=price_id,
            request_hash=request_hash,
            operation_key=operation_key,
            pricing_policy_id=pricing_policy_id,
            upper_bound_cost_basis_amount=upper_bound_cost_basis_amount,
            cost_basis_coin_id=cost_basis_coin_id,
            meter_evidence_ref=meter_evidence_ref,
        )
        _require_status(
            price_response.status,
            field_name="price_reservation.status",
            allowed=("reserved",),
        )
        resolved_price_id = _required_uuid(
            price_response.price_id,
            field_name="price_id",
        )
        if resolved_price_id != price_id:
            raise RuntimeError(
                "Economy capital compiler price_id mismatch: "
                f"expected={price_id} actual={resolved_price_id}"
            )
        price_schedule_id = _required_uuid(
            price_response.price_schedule_id,
            field_name="price_schedule_id",
        )
        rate_snapshot_id = _required_uuid(
            price_response.rate_snapshot_id,
            field_name="rate_snapshot_id",
        )
        price_reservation_id = _required_uuid(
            price_response.price_reservation_id,
            field_name="price_reservation_id",
        )
        quoted_amount = _capital_amount(
            price_response.quoted_amount,
            field_name="quoted_amount",
        )

        smart_response = await self.prepare_smart_contract_reservation(
            actor_id=actor_id,
            smart_contract_id=smart_contract_id,
            permit_id=permit_id,
            permit_nonce=permit_nonce,
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=payer_wallet_public_id,
            args_hash=request_hash,
            max_cost=quoted_amount,
            rate_snapshot_id=rate_snapshot_id,
            deadline=deadline,
            coin_id=coin_id,
        )
        _require_status(
            smart_response.status,
            field_name="smart_contract_reservation.status",
            allowed=("pending",),
        )
        _require_response_uuid(
            smart_response.smart_contract_id,
            expected=smart_contract_id,
            field_name="smart_contract_id",
        )
        _require_response_uuid(
            smart_response.permit_id,
            expected=permit_id,
            field_name="permit_id",
        )
        _require_response_uuid(
            smart_response.payer_finance_entity_id,
            expected=payer_finance_entity_id,
            field_name="payer_finance_entity_id",
        )
        _require_response_uuid(
            smart_response.payer_wallet_id,
            expected=payer_wallet_id,
            field_name="payer_wallet_id",
        )
        _require_response_uuid(
            smart_response.payer_wallet_public_id,
            expected=payer_wallet_public_id,
            field_name="payer_wallet_public_id",
        )
        _require_response_uuid(
            smart_response.coin_id,
            expected=coin_id,
            field_name="coin_id",
        )
        max_cost = _capital_amount(smart_response.max_cost, field_name="max_cost")
        if max_cost != quoted_amount:
            raise RuntimeError(
                "Economy capital compiler max_cost mismatch: "
                f"expected={quoted_amount!r} actual={max_cost!r}"
            )
        op_nonce = _positive_int(smart_response.op_nonce, field_name="op_nonce")

        return EconomyServiceCapitalContractCompileReceipt(
            price_id=resolved_price_id,
            price_schedule_id=price_schedule_id,
            rate_snapshot_id=rate_snapshot_id,
            price_reservation_id=price_reservation_id,
            quoted_amount=quoted_amount,
            smart_contract_id=smart_contract_id,
            permit_id=permit_id,
            reservation_id=_required_uuid(
                smart_response.reservation_id,
                field_name="reservation_id",
            ),
            escrow_id=_required_uuid(smart_response.escrow_id, field_name="escrow_id"),
            op_nonce=op_nonce,
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=payer_wallet_public_id,
            receiver_finance_entity_id=receiver_finance_entity_id,
            receiver_wallet_id=receiver_wallet_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            max_cost=max_cost,
            payer_balance=_capital_amount(
                smart_response.payer_balance,
                field_name="payer_balance",
            ),
            payer_held_balance=_capital_amount(
                smart_response.payer_held_balance,
                field_name="payer_held_balance",
            ),
            payer_available_balance=_capital_amount(
                smart_response.payer_available_balance,
                field_name="payer_available_balance",
            ),
            status=smart_response.status,
            idempotent_replay=smart_response.idempotent_replay,
        )

    async def release_smart_contract_reservation(
        self,
        *,
        actor_id: UUID | None,
        smart_contract_id: UUID,
        permit_id: UUID,
        reservation_id: UUID,
        payer_finance_entity_id: UUID,
        payer_wallet_id: UUID,
        payer_wallet_public_id: UUID,
        coin_id: UUID,
        status: str,
    ) -> EconomySmartContractReservationReleaseResponse:
        return await self.api_client.economy.smart_contract_reservation_release.release_smart_contract_reservation(
            EconomySmartContractReservationReleaseRequest(
                actor_id=_dump_optional_uuid(actor_id),
                smart_contract_id=str(smart_contract_id),
                permit_id=str(permit_id),
                reservation_id=str(reservation_id),
                payer_finance_entity_id=str(payer_finance_entity_id),
                payer_wallet_id=str(payer_wallet_id),
                payer_wallet_public_id=str(payer_wallet_public_id),
                coin_id=str(coin_id),
                status=status,
            )
        )

    async def finalize_smart_contract_settlement(
        self,
        *,
        actor_id: UUID | None,
        smart_contract_id: UUID,
        permit_id: UUID,
        reservation_id: UUID,
        payer_finance_entity_id: UUID,
        payer_wallet_id: UUID,
        payer_wallet_public_id: UUID,
        receiver_finance_entity_id: UUID,
        receiver_wallet_id: UUID,
        receiver_wallet_public_id: UUID,
        coin_id: UUID,
        final_cost: MoneyInput,
    ) -> EconomySmartContractSettlementFinalizeResponse:
        return await self.api_client.economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement(
            EconomySmartContractSettlementFinalizeRequest(
                actor_id=_dump_optional_uuid(actor_id),
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
                final_cost=_sdk_amount(final_cost, field_name="final_cost"),
            )
        )

    async def prepare_wallet_funding(
        self,
        *,
        target_wallet_id: UUID,
        coin_id: UUID,
        amount: MoneyInput,
        funding_intent_key: str,
        idempotency_key: str,
        provider_key: str,
    ) -> EconomyWalletFundingPrepareResponse:
        return (
            await self.api_client.economy.wallet_funding_prepare.prepare_wallet_funding(
                EconomyWalletFundingPrepareRequest(
                    target_wallet_id=str(target_wallet_id),
                    coin_id=str(coin_id),
                    amount=_sdk_amount(amount, field_name="amount"),
                    funding_intent_key=funding_intent_key,
                    idempotency_key=idempotency_key,
                    provider_key=provider_key,
                )
            )
        )

    async def resolve_wallet_funding_context(
        self,
        *,
        transaction_intent_id: UUID,
        transaction_intent_commit_id: UUID,
    ) -> EconomyWalletFundingContextResolveResponse:
        return await self.api_client.economy.wallet_funding_context_resolve.resolve_wallet_funding_context(
            EconomyWalletFundingContextResolveRequest(
                transaction_intent_id=str(transaction_intent_id),
                transaction_intent_commit_id=str(transaction_intent_commit_id),
            )
        )

    async def record_verified_wallet_funding(
        self,
        *,
        transaction_intent_id: UUID,
        transaction_intent_commit_id: UUID,
        provider_key: str,
        provider_event_id: str,
        idempotency_key: str,
        capital_conversion_quote_id: UUID,
        quote_hash: str,
        external_amount_minor: int,
        external_currency: str,
        provider_public_reference: str,
        provider_payload_hash: str,
        external_created_at: str,
    ) -> EconomyWalletFundingRecordResponse:
        return await self.api_client.economy.wallet_funding_record.record_verified_wallet_funding(
            EconomyWalletFundingRecordRequest(
                transaction_intent_id=str(transaction_intent_id),
                transaction_intent_commit_id=str(transaction_intent_commit_id),
                provider_key=provider_key,
                provider_event_id=provider_event_id,
                idempotency_key=idempotency_key,
                capital_conversion_quote_id=str(capital_conversion_quote_id),
                quote_hash=quote_hash,
                external_amount_minor=external_amount_minor,
                external_currency=external_currency,
                provider_public_reference=provider_public_reference,
                provider_payload_hash=provider_payload_hash,
                external_created_at=external_created_at,
            )
        )

    async def record_wallet_funding_expiration(
        self,
        *,
        transaction_intent_id: UUID,
        transaction_intent_commit_id: UUID,
        provider_key: str,
        provider_event_id: str,
        idempotency_key: str,
        capital_conversion_quote_id: UUID,
        quote_hash: str,
        provider_public_reference: str,
        provider_payload_hash: str,
        external_created_at: str,
    ) -> EconomyWalletFundingCancelResponse:
        return await self.api_client.economy.wallet_funding_cancel.record_wallet_funding_expiration(
            EconomyWalletFundingCancelRequest(
                transaction_intent_id=str(transaction_intent_id),
                transaction_intent_commit_id=str(transaction_intent_commit_id),
                provider_key=provider_key,
                provider_event_id=provider_event_id,
                idempotency_key=idempotency_key,
                capital_conversion_quote_id=str(capital_conversion_quote_id),
                quote_hash=quote_hash,
                provider_public_reference=provider_public_reference,
                provider_payload_hash=provider_payload_hash,
                external_created_at=external_created_at,
            )
        )

    async def record_provider_lifecycle_event(
        self,
        *,
        provider_key: str,
        provider_event_id: str,
        provider_lifecycle_object_id: str,
        provider_lifecycle_effect_key: str,
        provider_payment_reference: str,
        external_amount_minor: int,
        external_currency: str,
        event_kind: str,
        provider_payload_hash: str,
        external_created_at: str,
        metadata_json: dict[str, object] | None = None,
    ) -> EconomyProviderLifecycleRecordResponse:
        return await self.api_client.economy.provider_lifecycle_record.record_provider_lifecycle_event(
            EconomyProviderLifecycleRecordRequest(
                provider_key=provider_key,
                provider_event_id=provider_event_id,
                provider_lifecycle_object_id=provider_lifecycle_object_id,
                provider_lifecycle_effect_key=provider_lifecycle_effect_key,
                provider_payment_reference=provider_payment_reference,
                external_amount_minor=external_amount_minor,
                external_currency=external_currency,
                event_kind=event_kind,
                provider_payload_hash=provider_payload_hash,
                external_created_at=external_created_at,
                metadata_json=metadata_json,
            )
        )

    async def describe_wallet_balance(
        self,
        *,
        actor_id: UUID | None,
        wallet_id: UUID,
        coin_id: UUID,
    ) -> EconomyWalletBalanceDescribeResponse:
        return await self.api_client.economy.wallet_balance_describe.describe_wallet_balance(
            EconomyWalletBalanceDescribeRequest(
                actor_id=_dump_optional_uuid(actor_id),
                wallet_id=str(wallet_id),
                coin_id=str(coin_id),
            )
        )

    async def resolve_wallet_capital_frame(
        self,
        *,
        actor_id: UUID | None,
        wallet_id: UUID,
        coin_id: UUID | None = None,
        limit: int = 50,
        include_transaction_intents: bool = True,
        include_transaction_externals: bool = True,
        include_transactions: bool = True,
        include_reservations: bool = True,
        include_escrows: bool = True,
        include_settlements: bool = True,
        include_provider_lifecycle: bool = True,
    ) -> EconomyWalletCapitalFrameResolveResponse:
        return await self.api_client.economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame(
            EconomyWalletCapitalFrameResolveRequest(
                actor_id=_dump_optional_uuid(actor_id),
                wallet_id=str(wallet_id),
                coin_id=_dump_optional_uuid(coin_id),
                limit=limit,
                include_transaction_intents=include_transaction_intents,
                include_transaction_externals=include_transaction_externals,
                include_transactions=include_transactions,
                include_reservations=include_reservations,
                include_escrows=include_escrows,
                include_settlements=include_settlements,
                include_provider_lifecycle=include_provider_lifecycle,
            )
        )

    async def resolve_wallet_capital_view_state(
        self,
        *,
        actor_id: UUID | None,
        wallet_id: UUID,
        coin_id: UUID | None = None,
        limit: int = 50,
        include_transaction_intents: bool = True,
        include_transaction_externals: bool = True,
        include_transactions: bool = True,
        include_reservations: bool = True,
        include_escrows: bool = True,
        include_settlements: bool = True,
        include_provider_lifecycle: bool = True,
    ) -> EconomyWalletCapitalViewStateV1:
        return await self.api_client.economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state(
            EconomyWalletCapitalViewStateResolveRequest(
                actor_id=_dump_optional_uuid(actor_id),
                wallet_id=str(wallet_id),
                coin_id=_dump_optional_uuid(coin_id),
                limit=limit,
                include_transaction_intents=include_transaction_intents,
                include_transaction_externals=include_transaction_externals,
                include_transactions=include_transactions,
                include_reservations=include_reservations,
                include_escrows=include_escrows,
                include_settlements=include_settlements,
                include_provider_lifecycle=include_provider_lifecycle,
            )
        )

    async def refresh_wallet_capital(
        self,
        *,
        actor_id: UUID | None,
        wallet_id: UUID,
        coin_id: UUID | None = None,
        limit: int = 50,
        include_transaction_intents: bool = True,
        include_transaction_externals: bool = True,
        include_transactions: bool = True,
        include_reservations: bool = True,
        include_escrows: bool = True,
        include_settlements: bool = True,
        include_provider_lifecycle: bool = True,
    ) -> EconomyWalletCapitalViewStateV1:
        return await self.resolve_wallet_capital_view_state(
            actor_id=actor_id,
            wallet_id=wallet_id,
            coin_id=coin_id,
            limit=limit,
            include_transaction_intents=include_transaction_intents,
            include_transaction_externals=include_transaction_externals,
            include_transactions=include_transactions,
            include_reservations=include_reservations,
            include_escrows=include_escrows,
            include_settlements=include_settlements,
            include_provider_lifecycle=include_provider_lifecycle,
        )

    async def finalize_price_reservation(
        self,
        *,
        actor_id: UUID | None,
        price_reservation_id: UUID,
        status: str,
        actual_cost_basis_amount: MoneyInput | None = None,
        cost_basis_coin_id: UUID | None = None,
        meter_evidence_ref: str | None = None,
    ) -> EconomyPriceReservationFinalizeResponse:
        return await self.api_client.economy.price_reservation_finalize.price_reservation_finalize(
            EconomyPriceReservationFinalizeRequest(
                actor_id=_dump_optional_uuid(actor_id),
                price_reservation_id=str(price_reservation_id),
                status=status,
                actual_cost_basis_amount=_sdk_optional_amount(
                    actual_cost_basis_amount,
                    field_name="actual_cost_basis_amount",
                ),
                cost_basis_coin_id=_dump_optional_uuid(cost_basis_coin_id),
                meter_evidence_ref=meter_evidence_ref,
            )
        )

    async def gate_snapshot(
        self,
        *,
        actor_id: UUID,
        finance_role_key: str = "primary",
    ) -> EconomyGateSnapshot:
        status = await self.actor_status(
            actor_id=actor_id,
            finance_role_key=finance_role_key,
        )
        return build_economy_gate_snapshot(
            actor_id=actor_id,
            status=status,
        )


def build_economy_gate_snapshot(
    *,
    actor_id: UUID,
    status: EconomyActorStatusResponse,
) -> EconomyGateSnapshot:
    if not status.finance_entity_ready:
        gate_status = EconomyGateStatus.missing_finance_entity
    elif not status.wallet_ready:
        gate_status = EconomyGateStatus.missing_wallet
    else:
        gate_status = EconomyGateStatus.ready

    return EconomyGateSnapshot(
        status=gate_status,
        actor_id=actor_id,
        finance_role_key=status.finance_role_key,
        finance_entity_id=_optional_uuid(status.finance_entity_id),
        wallet_id=_optional_uuid(status.wallet_id),
        wallet_public_id=_optional_uuid(status.wallet_public_id),
        next_step=status.next_step,
    )


def build_economy_sdk_client(
    *,
    api_invoker: object | None = None,
    endpoint: str | None = None,
    actor_id: UUID | None = None,
    request_timeout_s: float | None = None,
) -> EconomySdkClient:
    _ = endpoint, actor_id, request_timeout_s
    if api_invoker is None:
        raise RuntimeError(
            "Economy SDK construction requires a generated API invoker; "
            "endpoint-owned high-level aware_api clients were removed."
        )
    return EconomySdkClient(api_client=AwareEconomyServiceApiClient(api_invoker))


def _optional_uuid(value: str | None) -> UUID | None:
    raw = (value or "").strip()
    if not raw:
        return None
    return UUID(raw)


def _required_uuid(value: object, *, field_name: str) -> UUID:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    try:
        return UUID(raw)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID string") from exc


def _dump_optional_uuid(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _capital_amount(value: object, *, field_name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{field_name} must be an exact decimal amount")
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise ValueError(f"{field_name} is required")
        try:
            parsed = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a decimal amount") from exc
    else:
        raise ValueError(f"{field_name} must be an exact decimal amount")
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if parsed < Decimal("0"):
        raise ValueError(f"{field_name} must be non-negative")
    return parsed


def _sdk_datetime(value: datetime | str, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value or "").strip()
        if not raw:
            raise ValueError(f"{field_name} is required")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                f"{field_name} must be an ISO-8601 datetime string"
            ) from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed.astimezone(UTC)


def _positive_int(value: int, *, field_name: str) -> int:
    if isinstance(value, bool) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _require_status(
    value: str,
    *,
    field_name: str,
    allowed: tuple[str, ...],
) -> None:
    raw = str(value or "").strip()
    if raw not in allowed:
        raise RuntimeError(
            f"Economy capital compiler received unexpected {field_name}: "
            f"expected={allowed!r} actual={raw!r}"
        )


def _require_response_uuid(value: object, *, expected: UUID, field_name: str) -> None:
    actual = _required_uuid(value, field_name=field_name)
    if actual != expected:
        raise RuntimeError(
            f"Economy capital compiler response {field_name} mismatch: "
            f"expected={expected} actual={actual}"
        )


def _sdk_amount(value: MoneyInput, *, field_name: str) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{field_name} must be Decimal, int, or decimal text")
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a decimal amount") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return format(parsed.normalize(), "f")


def _sdk_optional_amount(value: MoneyInput | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _sdk_amount(value, field_name=field_name)


__all__ = [
    "EconomyApiClient",
    "EconomyGateSnapshot",
    "EconomyGateStatus",
    "EconomySdkClient",
    "EconomyServiceOperationPermitReceipt",
    "EconomyServiceCapitalContractCompileReceipt",
    "MoneyInput",
    "build_economy_gate_snapshot",
    "build_economy_sdk_client",
    "wallet_capital_view_state_from_frame",
]
