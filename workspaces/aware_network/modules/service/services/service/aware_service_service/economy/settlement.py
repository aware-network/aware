from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Protocol, override
from uuid import UUID

from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_economy_sdk import (
    build_economy_sdk_client,
)
from aware_economy_ontology.price.price_reservation_enums import PriceReservationStatus
from aware_orm.session.session import Session
from aware_service_ontology.service.service_contract_config import (
    ServiceContractConfig,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractStatus,
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_economy_settlement import (
    ServiceContractEconomySettlement,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_ontology.stable_ids import (
    stable_service_contract_economy_settlement_id,
)
from aware_service_runtime.api_ingress.economy_settlement import (
    ServiceOperationEconomyFinalizationInput,
    ServiceOperationEconomyReservationInput,
    ServiceOperationEconomySettlementAdapter,
    ServiceOperationSettlementReceiptRefs,
)
from aware_service_runtime.api_ingress.settlement import (
    ServiceOperationMeteringContextV1,
)


_SYSTEM_ACTOR_ID = UUID(int=0)
_ZERO_AMOUNT = Decimal("0")


@dataclass(frozen=True, slots=True)
class EconomyWalletBackedSettlementCoordinates:
    smart_contract_id: UUID
    permit_id: UUID
    permit_nonce: int
    payer_finance_entity_id: UUID
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    receiver_finance_entity_id: UUID
    receiver_wallet_id: UUID
    receiver_wallet_public_id: UUID
    coin_id: UUID
    deadline: str


@dataclass(frozen=True, slots=True)
class EconomyApiClientSettlementPreparedState:
    price_id: UUID
    price_schedule_id: UUID
    rate_snapshot_id: UUID
    price_reservation_id: UUID
    quoted_amount: Decimal
    smart_contract_id: UUID
    permit_id: UUID
    smart_contract_reservation_id: UUID
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


class _EconomyFinalizeResponse(Protocol):
    status: str
    final_amount: Decimal | None
    actual_cost_basis_amount: Decimal | None
    actual_markup_amount: Decimal | None
    meter_evidence_ref: str | None


class _EconomyServiceCapitalContractCompileResponse(Protocol):
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
    status: str


class _EconomyFinalizeSmartContractSettlementResponse(Protocol):
    smart_contract_id: str
    permit_id: str
    reservation_id: str
    settlement_id: str
    transaction_id: str | None
    payer_finance_entity_id: str
    payer_wallet_id: str
    payer_wallet_public_id: str
    payer_wallet_balance_id: str
    receiver_finance_entity_id: str
    receiver_wallet_id: str
    receiver_wallet_public_id: str
    receiver_wallet_balance_id: str
    coin_id: str
    final_cost: str
    status: str
    idempotent_replay: bool


class _EconomySdkSettlementClient(Protocol):
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
        upper_bound_cost_basis_amount: Decimal | None = None,
        cost_basis_coin_id: UUID | None = None,
        meter_evidence_ref: str | None = None,
    ) -> _EconomyServiceCapitalContractCompileResponse: ...

    async def finalize_price_reservation(
        self,
        *,
        actor_id: UUID | None,
        price_reservation_id: UUID,
        status: str,
        actual_cost_basis_amount: Decimal | None = None,
        cost_basis_coin_id: UUID | None = None,
        meter_evidence_ref: str | None = None,
    ) -> _EconomyFinalizeResponse: ...

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
        final_cost: Decimal,
    ) -> _EconomyFinalizeSmartContractSettlementResponse: ...


class _EconomySdkClientFactory(Protocol):
    def __call__(self, actor_id: UUID) -> _EconomySdkSettlementClient: ...


@dataclass(frozen=True, slots=True)
class EconomyApiClientSettlementAdapter(ServiceOperationEconomySettlementAdapter):
    endpoint: str
    request_timeout_s: float = 10.0
    sdk_factory: _EconomySdkClientFactory | None = None

    async def resolve_metering_context(
        self,
        *,
        runtime: object,
        index: object,
        session: Session,
        reservation: ServiceOperationEconomyReservationInput,
    ) -> ServiceOperationMeteringContextV1 | None:
        _ = runtime, index
        if reservation.settlement_policy == ServiceOperationSettlementPolicy.none:
            return None
        coordinates = _resolve_wallet_backed_settlement_coordinates(
            session=session,
            reservation=reservation,
        )
        return ServiceOperationMeteringContextV1(
            schema="aware.service.operation_metering_context.v1",
            cost_basis_coin_id=coordinates.coin_id,
        )

    @override
    async def reserve(
        self,
        *,
        runtime: object,
        index: object,
        session: Session,
        reservation: ServiceOperationEconomyReservationInput,
        commit: bool,
        publish: bool,
    ) -> EconomyApiClientSettlementPreparedState | None:
        _ = (runtime, index, session, commit, publish)
        if reservation.settlement_policy == ServiceOperationSettlementPolicy.none:
            return None
        if reservation.price_id is None:
            raise RuntimeError(
                "Economy API-client settlement reserve requires reservation.price_id"
            )

        settlement_coordinates = _resolve_wallet_backed_settlement_coordinates(
            session=session,
            reservation=reservation,
        )
        client = self._build_sdk_client(actor_id=reservation.actor_id)
        estimate = reservation.metering_estimate
        compiled = await client.compile_service_capital_contract(
            actor_id=reservation.actor_id,
            price_id=reservation.price_id,
            request_hash=reservation.request_hash,
            operation_key=reservation.operation_key,
            smart_contract_id=settlement_coordinates.smart_contract_id,
            permit_id=settlement_coordinates.permit_id,
            permit_nonce=settlement_coordinates.permit_nonce,
            payer_finance_entity_id=settlement_coordinates.payer_finance_entity_id,
            payer_wallet_id=settlement_coordinates.payer_wallet_id,
            payer_wallet_public_id=settlement_coordinates.payer_wallet_public_id,
            receiver_finance_entity_id=(
                settlement_coordinates.receiver_finance_entity_id
            ),
            receiver_wallet_id=settlement_coordinates.receiver_wallet_id,
            receiver_wallet_public_id=settlement_coordinates.receiver_wallet_public_id,
            coin_id=settlement_coordinates.coin_id,
            deadline=settlement_coordinates.deadline,
            pricing_policy_id=reservation.pricing_policy_id,
            upper_bound_cost_basis_amount=(
                estimate.cost_basis_amount if estimate is not None else None
            ),
            cost_basis_coin_id=(
                estimate.cost_basis_coin_id if estimate is not None else None
            ),
            meter_evidence_ref=(
                estimate.evidence_ref if estimate is not None else None
            ),
        )
        _require_status(
            compiled.status,
            field_name="service_capital_contract.status",
            allowed=("pending",),
        )

        return EconomyApiClientSettlementPreparedState(
            price_id=compiled.price_id,
            price_schedule_id=compiled.price_schedule_id,
            rate_snapshot_id=compiled.rate_snapshot_id,
            price_reservation_id=compiled.price_reservation_id,
            quoted_amount=compiled.quoted_amount,
            smart_contract_id=compiled.smart_contract_id,
            permit_id=compiled.permit_id,
            smart_contract_reservation_id=compiled.reservation_id,
            escrow_id=compiled.escrow_id,
            op_nonce=compiled.op_nonce,
            payer_finance_entity_id=compiled.payer_finance_entity_id,
            payer_wallet_id=compiled.payer_wallet_id,
            payer_wallet_public_id=compiled.payer_wallet_public_id,
            receiver_finance_entity_id=compiled.receiver_finance_entity_id,
            receiver_wallet_id=compiled.receiver_wallet_id,
            receiver_wallet_public_id=compiled.receiver_wallet_public_id,
            coin_id=compiled.coin_id,
            max_cost=compiled.max_cost,
            payer_balance=compiled.payer_balance,
        )

    @override
    async def finalize(
        self,
        *,
        runtime: object,
        index: object,
        session: Session,
        prepared_state: object | None,
        finalization: ServiceOperationEconomyFinalizationInput,
        commit: bool,
        publish: bool,
    ) -> ServiceOperationSettlementReceiptRefs | None:
        _ = (runtime, index, session, commit, publish)
        if (
            finalization.reservation_input.settlement_policy
            != ServiceOperationSettlementPolicy.reserve_and_finalize
        ):
            return None
        if prepared_state is None:
            raise RuntimeError(
                "Economy API-client settlement finalize requires prepared_state"
            )
        if not isinstance(prepared_state, EconomyApiClientSettlementPreparedState):
            message = (
                "Economy API-client settlement finalize received unexpected prepared_state type: "
                f"{type(prepared_state)!r}"
            )
            raise RuntimeError(message)

        successful = _is_successful_finalization(finalization=finalization)
        client = self._build_sdk_client(
            actor_id=finalization.reservation_input.actor_id
        )
        target_status = _resolve_price_reservation_status(finalization=finalization)
        metering_receipt = finalization.metering_receipt if successful else None
        response = await client.finalize_price_reservation(
            actor_id=finalization.reservation_input.actor_id,
            price_reservation_id=prepared_state.price_reservation_id,
            status=target_status.value,
            actual_cost_basis_amount=(
                metering_receipt.cost_basis_amount
                if metering_receipt is not None
                else None
            ),
            cost_basis_coin_id=(
                metering_receipt.cost_basis_coin_id
                if metering_receipt is not None
                else None
            ),
            meter_evidence_ref=(
                metering_receipt.evidence_ref if metering_receipt is not None else None
            ),
        )
        resolved_status = _parse_price_reservation_status(
            response.status, field_name="status"
        )
        if resolved_status != target_status:
            message = (
                "Economy API-client finalize returned unexpected reservation status: "
                f"expected={target_status.value!r} actual={resolved_status.value!r}"
            )
            raise RuntimeError(message)
        if target_status == PriceReservationStatus.settled:
            if response.final_amount is None:
                raise RuntimeError(
                    "Economy settled price reservation response requires final_amount"
                )
            final_cost = _capital_amount(
                response.final_amount,
                field_name="price_reservation.final_amount",
            )
            if final_cost > prepared_state.max_cost:
                raise RuntimeError(
                    "Economy final price exceeds prepared smart-contract max_cost: "
                    f"final={final_cost!r} max={prepared_state.max_cost!r}"
                )
            if metering_receipt is not None:
                response_basis = _capital_amount(
                    response.actual_cost_basis_amount,
                    field_name="price_reservation.actual_cost_basis_amount",
                )
                if response_basis != metering_receipt.cost_basis_amount:
                    raise RuntimeError(
                        "Economy final price cost-basis receipt mismatch: "
                        f"expected={metering_receipt.cost_basis_amount!r} "
                        f"actual={response_basis!r}"
                    )
                _ = _capital_amount(
                    response.actual_markup_amount,
                    field_name="price_reservation.actual_markup_amount",
                )
                if response.meter_evidence_ref != metering_receipt.evidence_ref:
                    raise RuntimeError(
                        "Economy final price meter evidence receipt mismatch"
                    )
        else:
            final_cost = _ZERO_AMOUNT
        smart_response = await client.finalize_smart_contract_settlement(
            actor_id=finalization.reservation_input.actor_id,
            smart_contract_id=prepared_state.smart_contract_id,
            permit_id=prepared_state.permit_id,
            reservation_id=prepared_state.smart_contract_reservation_id,
            payer_finance_entity_id=prepared_state.payer_finance_entity_id,
            payer_wallet_id=prepared_state.payer_wallet_id,
            payer_wallet_public_id=prepared_state.payer_wallet_public_id,
            receiver_finance_entity_id=prepared_state.receiver_finance_entity_id,
            receiver_wallet_id=prepared_state.receiver_wallet_id,
            receiver_wallet_public_id=prepared_state.receiver_wallet_public_id,
            coin_id=prepared_state.coin_id,
            final_cost=final_cost,
        )
        _require_status(
            smart_response.status,
            field_name="smart_contract_settlement.status",
            allowed=("settled",),
        )
        _require_response_uuid(
            smart_response.smart_contract_id,
            expected=prepared_state.smart_contract_id,
            field_name="smart_contract_id",
        )
        _require_response_uuid(
            smart_response.permit_id,
            expected=prepared_state.permit_id,
            field_name="permit_id",
        )
        _require_response_uuid(
            smart_response.reservation_id,
            expected=prepared_state.smart_contract_reservation_id,
            field_name="reservation_id",
        )
        _require_response_uuid(
            smart_response.payer_finance_entity_id,
            expected=prepared_state.payer_finance_entity_id,
            field_name="payer_finance_entity_id",
        )
        _require_response_uuid(
            smart_response.payer_wallet_id,
            expected=prepared_state.payer_wallet_id,
            field_name="payer_wallet_id",
        )
        _require_response_uuid(
            smart_response.payer_wallet_public_id,
            expected=prepared_state.payer_wallet_public_id,
            field_name="payer_wallet_public_id",
        )
        _require_response_uuid(
            smart_response.receiver_finance_entity_id,
            expected=prepared_state.receiver_finance_entity_id,
            field_name="receiver_finance_entity_id",
        )
        _require_response_uuid(
            smart_response.receiver_wallet_id,
            expected=prepared_state.receiver_wallet_id,
            field_name="receiver_wallet_id",
        )
        _require_response_uuid(
            smart_response.receiver_wallet_public_id,
            expected=prepared_state.receiver_wallet_public_id,
            field_name="receiver_wallet_public_id",
        )
        _require_response_uuid(
            smart_response.coin_id,
            expected=prepared_state.coin_id,
            field_name="coin_id",
        )
        actual_final_cost = _capital_amount(
            smart_response.final_cost,
            field_name="final_cost",
        )
        if actual_final_cost != final_cost:
            raise RuntimeError(
                "Economy smart-contract settlement final_cost mismatch: "
                f"expected={final_cost!r} actual={actual_final_cost!r}"
            )
        service_operation_id = finalization.reservation_input.service_operation_ref.id
        if service_operation_id is None:
            raise RuntimeError(
                "Economy settlement receipt requires service_operation_ref.id"
            )
        authorization = finalization.reservation_input.operation_authorization_ref
        if authorization is None or authorization.service_contract_id is None:
            raise RuntimeError(
                "Economy settlement receipt requires Service operation authorization"
            )
        return ServiceOperationSettlementReceiptRefs(
            service_operation_id=service_operation_id,
            service_contract_id=authorization.service_contract_id,
            permit_id=prepared_state.permit_id,
            price_id=prepared_state.price_id,
            price_schedule_id=prepared_state.price_schedule_id,
            rate_snapshot_id=prepared_state.rate_snapshot_id,
            price_reservation_id=prepared_state.price_reservation_id,
            smart_contract_reservation_id=prepared_state.smart_contract_reservation_id,
            settlement_id=_parse_required_uuid(
                smart_response.settlement_id,
                field_name="settlement_id",
            ),
            transaction_id=_parse_optional_uuid(
                smart_response.transaction_id,
                field_name="transaction_id",
            ),
            payer_wallet_balance_id=_parse_required_uuid(
                smart_response.payer_wallet_balance_id,
                field_name="payer_wallet_balance_id",
            ),
            receiver_wallet_balance_id=_parse_required_uuid(
                smart_response.receiver_wallet_balance_id,
                field_name="receiver_wallet_balance_id",
            ),
            status=target_status.value,
            idempotent_replay=bool(smart_response.idempotent_replay),
        )

    def _build_sdk_client(
        self, *, actor_id: UUID | None
    ) -> _EconomySdkSettlementClient:
        resolved_actor_id = actor_id or _SYSTEM_ACTOR_ID
        if self.sdk_factory is not None:
            return self.sdk_factory(resolved_actor_id)
        return build_economy_sdk_client(
            endpoint=self.endpoint,
            actor_id=resolved_actor_id,
            request_timeout_s=self.request_timeout_s,
        )


def build_economy_api_client_settlement_adapter(
    *,
    endpoint: str,
    request_timeout_s: float = 10.0,
    sdk_factory: _EconomySdkClientFactory | None = None,
) -> EconomyApiClientSettlementAdapter:
    return EconomyApiClientSettlementAdapter(
        endpoint=endpoint,
        request_timeout_s=request_timeout_s,
        sdk_factory=sdk_factory,
    )


def _resolve_price_reservation_status(
    *,
    finalization: ServiceOperationEconomyFinalizationInput,
) -> PriceReservationStatus:
    if _is_successful_finalization(finalization=finalization):
        return PriceReservationStatus.settled
    return PriceReservationStatus.cancelled


def _is_successful_finalization(
    *,
    finalization: ServiceOperationEconomyFinalizationInput,
) -> bool:
    if (
        finalization.service_operation_status == ServiceOperationStatus.succeeded
        and finalization.api_call_outcome_status == ApiCallOutcomeStatus.succeeded
    ):
        return True
    return False


def _parse_price_reservation_status(
    value: str, *, field_name: str
) -> PriceReservationStatus:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    try:
        return PriceReservationStatus(raw)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a valid PriceReservationStatus"
        ) from exc


def _parse_required_uuid(value: object, *, field_name: str) -> UUID:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    try:
        return UUID(raw)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID string") from exc


def _parse_optional_uuid(value: object, *, field_name: str) -> UUID | None:
    if value is None or not str(value).strip():
        return None
    return _parse_required_uuid(value, field_name=field_name)


def _capital_amount(value: object, *, field_name: str) -> Decimal:
    if isinstance(value, bool):
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
    if parsed < _ZERO_AMOUNT:
        raise ValueError(f"{field_name} must be non-negative")
    return parsed


def _require_status(
    value: str,
    *,
    field_name: str,
    allowed: tuple[str, ...],
) -> str:
    raw = str(value or "").strip()
    if raw not in allowed:
        raise RuntimeError(
            f"Economy API-client settlement received unexpected {field_name}: "
            f"expected={allowed!r} actual={raw!r}"
        )
    return raw


def _require_response_uuid(value: object, *, expected: UUID, field_name: str) -> None:
    actual = _parse_required_uuid(value, field_name=field_name)
    if actual != expected:
        raise RuntimeError(
            f"Economy API-client settlement response {field_name} mismatch: "
            f"expected={expected} actual={actual}"
        )


def _resolve_wallet_backed_settlement_coordinates(
    *,
    session: Session,
    reservation: ServiceOperationEconomyReservationInput,
) -> EconomyWalletBackedSettlementCoordinates:
    contract_ref = reservation.contract_access_context_ref
    if contract_ref is None:
        raise RuntimeError(
            "Economy API-client settlement requires ServiceContract access context."
        )
    if contract_ref.service_contract_id is None:
        raise RuntimeError(
            "Economy API-client settlement requires service_contract_id in "
            "ServiceContract access context."
        )
    if contract_ref.service_subscription_id is None:
        raise RuntimeError(
            "Economy API-client settlement requires service_subscription_id in "
            "ServiceContract access context."
        )
    if contract_ref.service_contract_config_id is None:
        raise RuntimeError(
            "Economy API-client settlement requires service_contract_config_id in "
            "ServiceContract access context."
        )
    service_contract = session.imap_get(
        ServiceContract,
        contract_ref.service_contract_id,
    )
    if service_contract is None:
        raise RuntimeError(
            "Economy API-client settlement requires committed ServiceContract: "
            f"service_contract_id={contract_ref.service_contract_id}"
        )
    service_subscription = session.imap_get(
        ServiceSubscription,
        contract_ref.service_subscription_id,
    )
    if service_subscription is None:
        raise RuntimeError(
            "Economy API-client settlement requires committed ServiceSubscription: "
            f"service_subscription_id={contract_ref.service_subscription_id}"
        )
    service_contract_config = session.imap_get(
        ServiceContractConfig,
        contract_ref.service_contract_config_id,
    )
    if service_contract_config is None:
        raise RuntimeError(
            "Economy API-client settlement requires committed ServiceContractConfig: "
            f"service_contract_config_id={contract_ref.service_contract_config_id}"
        )
    if service_contract.service_id != reservation.service_ref.id:
        raise RuntimeError(
            "Economy API-client settlement ServiceContract.service_id mismatch."
        )
    if service_contract.status != ServiceContractStatus.active:
        raise RuntimeError(
            "Economy API-client settlement requires an active ServiceContract."
        )
    if (
        contract_ref.consumer_finance_entity_id is not None
        and service_contract.consumer_finance_entity_id
        != contract_ref.consumer_finance_entity_id
    ):
        raise RuntimeError(
            "Economy API-client settlement consumer_finance_entity_id mismatch."
        )
    if (
        contract_ref.smart_contract_id is not None
        and service_contract.smart_contract_id != contract_ref.smart_contract_id
    ):
        raise RuntimeError("Economy API-client settlement smart_contract_id mismatch.")
    if service_contract.service_contract_config_id != service_contract_config.id:
        raise RuntimeError(
            "Economy API-client settlement ServiceContractConfig mismatch."
        )
    if service_subscription.service_id != service_contract.service_id:
        raise RuntimeError(
            "Economy API-client settlement ServiceSubscription.service_id mismatch."
        )
    if service_subscription.consumer_finance_entity_id != (
        service_contract.consumer_finance_entity_id
    ):
        raise RuntimeError(
            "Economy API-client settlement ServiceSubscription consumer mismatch."
        )
    if service_subscription.contract_id != service_contract.smart_contract_id:
        raise RuntimeError(
            "Economy API-client settlement ServiceSubscription contract mismatch."
        )
    if service_subscription.status != ServiceSubscriptionStatus.active:
        raise RuntimeError(
            "Economy API-client settlement requires an active ServiceSubscription."
        )
    if not _service_contract_config_grants_operation(
        service_contract_config=service_contract_config,
        operation_config_id=reservation.service_operation_config_ref.id,
    ):
        raise RuntimeError(
            "Economy API-client settlement requires ServiceContractConfig operation grant."
        )

    settlement = _resolve_service_contract_economy_settlement(
        session=session,
        service_contract=service_contract,
    )
    authorization = reservation.operation_authorization_ref
    if authorization is None:
        raise RuntimeError(
            "Economy API-client settlement requires Service operation authorization."
        )
    if authorization.service_contract_id != service_contract.id:
        raise RuntimeError(
            "Economy API-client settlement authorization ServiceContract mismatch."
        )
    if authorization.operation_key != reservation.operation_key:
        raise RuntimeError(
            "Economy API-client settlement authorization operation_key mismatch."
        )
    if authorization.request_hash != reservation.request_hash:
        raise RuntimeError(
            "Economy API-client settlement authorization request_hash mismatch."
        )
    if authorization.permit_id != settlement.permit_id:
        raise RuntimeError(
            "Economy API-client settlement authorization permit mismatch."
        )
    receiver_finance_entity_id = service_contract.producer_finance_entity_id
    if receiver_finance_entity_id != service_contract.producer_finance_entity_id:
        raise RuntimeError(
            "Economy API-client settlement receiver_finance_entity_id must match "
            "ServiceContract.producer_finance_entity_id."
        )
    return EconomyWalletBackedSettlementCoordinates(
        smart_contract_id=service_contract.smart_contract_id,
        permit_id=settlement.permit_id,
        permit_nonce=_positive_int_field(
            settlement.permit_nonce,
            field_name="ServiceContract.economy_settlement.permit_nonce",
        ),
        payer_finance_entity_id=service_contract.consumer_finance_entity_id,
        payer_wallet_id=settlement.payer_wallet_id,
        payer_wallet_public_id=settlement.payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_id=settlement.receiver_wallet_id,
        receiver_wallet_public_id=settlement.receiver_wallet_public_id,
        coin_id=settlement.coin_id,
        deadline=_deadline_text(
            settlement.deadline,
            field_name="ServiceContract.economy_settlement.deadline",
        ),
    )


def _service_contract_config_grants_operation(
    *,
    service_contract_config: ServiceContractConfig,
    operation_config_id: UUID,
) -> bool:
    return any(
        grant.service_operation_config_id == operation_config_id
        for grant in service_contract_config.operation_grants or ()
    )


def _resolve_service_contract_economy_settlement(
    *,
    session: Session,
    service_contract: ServiceContract,
) -> ServiceContractEconomySettlement:
    settlement = getattr(service_contract, "economy_settlement", None)
    if isinstance(settlement, ServiceContractEconomySettlement):
        _require_settlement_contract_match(
            settlement=settlement,
            service_contract=service_contract,
        )
        return settlement

    if service_contract.id is None:
        raise RuntimeError(
            "Economy API-client settlement requires committed ServiceContract id."
        )
    settlement_id = stable_service_contract_economy_settlement_id(
        service_contract_id=service_contract.id
    )
    resolved = session.imap_get(ServiceContractEconomySettlement, settlement_id)
    if resolved is None:
        raise RuntimeError(
            "Economy API-client settlement requires typed "
            "ServiceContract.economy_settlement coordinates."
        )
    _require_settlement_contract_match(
        settlement=resolved,
        service_contract=service_contract,
    )
    return resolved


def _require_settlement_contract_match(
    *,
    settlement: ServiceContractEconomySettlement,
    service_contract: ServiceContract,
) -> None:
    if settlement.service_contract_id != service_contract.id:
        raise RuntimeError(
            "Economy API-client settlement ServiceContract.economy_settlement "
            "service_contract_id mismatch."
        )


def _positive_int_field(value: object, *, field_name: str) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{field_name} must be an integer.") from exc
    if parsed <= 0:
        raise RuntimeError(f"{field_name} must be > 0.")
    return parsed


def _deadline_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, datetime):
        raise RuntimeError(f"{field_name} must be a datetime.")
    if value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value):
        return value.isoformat().replace("+00:00", "Z")
    return value.isoformat()


__all__ = [
    "EconomyApiClientSettlementAdapter",
    "EconomyApiClientSettlementPreparedState",
    "EconomyWalletBackedSettlementCoordinates",
    "build_economy_api_client_settlement_adapter",
]
