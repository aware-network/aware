from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_economy.price_reservation_settlement import (
    PriceReservationReserveReceipt,
    finalize_price_reservation,
    reserve_price_reservation,
)
from aware_economy_ontology.price.price_reservation_enums import PriceReservationStatus
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_orm.session.session import Session
from aware_service_ontology.service.service_enums import (
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
)
from aware_service_runtime.api_ingress.economy_settlement import (
    ServiceOperationEconomyFinalizationInput,
    ServiceOperationEconomyReservationInput,
    ServiceOperationEconomySettlementAdapter,
)


class _RuntimeProtocol(Protocol):
    @property
    def invoker(self) -> object: ...


@dataclass(frozen=True, slots=True)
class EconomyPriceReservationPreparedState:
    price_id: UUID
    price_schedule_id: UUID
    rate_snapshot_id: UUID
    price_reservation_id: UUID
    quoted_amount: Decimal
    economy_price_lane: MaterializationLaneContext


class EconomyPriceReservationSettlementAdapter(
    ServiceOperationEconomySettlementAdapter
):
    async def reserve(
        self,
        *,
        runtime: _RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        session: Session,
        reservation: ServiceOperationEconomyReservationInput,
        commit: bool,
        publish: bool,
    ) -> EconomyPriceReservationPreparedState | None:
        _ = session
        if reservation.settlement_policy == ServiceOperationSettlementPolicy.none:
            return None
        if reservation.price_id is None:
            raise RuntimeError(
                "Economy settlement reserve requires reservation.price_id"
            )
        if reservation.economy_price_lane is None:
            raise RuntimeError(
                "Economy settlement reserve requires reservation.economy_price_lane"
            )

        receipt = await reserve_price_reservation(
            runtime=runtime,
            index=index,
            actor_id=reservation.actor_id,
            economy_price_lane=reservation.economy_price_lane,
            price_id=reservation.price_id,
            request_hash=reservation.request_hash,
            operation_key=reservation.operation_key,
            pricing_policy_id=reservation.pricing_policy_id,
            upper_bound_cost_basis_amount=(
                reservation.metering_estimate.cost_basis_amount
                if reservation.metering_estimate is not None
                else None
            ),
            cost_basis_coin_id=(
                reservation.metering_estimate.cost_basis_coin_id
                if reservation.metering_estimate is not None
                else None
            ),
            meter_evidence_ref=(
                reservation.metering_estimate.evidence_ref
                if reservation.metering_estimate is not None
                else None
            ),
            commit=commit,
            publish=publish,
        )
        return _prepared_state_from_receipt(
            receipt=receipt,
            economy_price_lane=reservation.economy_price_lane,
        )

    async def finalize(
        self,
        *,
        runtime: _RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        session: Session,
        prepared_state: object | None,
        finalization: ServiceOperationEconomyFinalizationInput,
        commit: bool,
        publish: bool,
    ) -> None:
        _ = session
        if (
            finalization.reservation_input.settlement_policy
            != ServiceOperationSettlementPolicy.reserve_and_finalize
        ):
            return
        if prepared_state is None:
            raise RuntimeError("Economy settlement finalize requires prepared_state")
        if not isinstance(prepared_state, EconomyPriceReservationPreparedState):
            raise RuntimeError(
                "Economy settlement finalize received unexpected prepared_state type: "
                f"{type(prepared_state)!r}"
            )

        reservation_status = _resolve_price_reservation_status(
            finalization=finalization
        )
        await finalize_price_reservation(
            runtime=runtime,
            index=index,
            actor_id=finalization.reservation_input.actor_id,
            economy_price_lane=prepared_state.economy_price_lane,
            price_reservation_id=prepared_state.price_reservation_id,
            status=reservation_status,
            actual_cost_basis_amount=(
                finalization.metering_receipt.cost_basis_amount
                if reservation_status == PriceReservationStatus.settled
                and finalization.metering_receipt is not None
                else None
            ),
            cost_basis_coin_id=(
                finalization.metering_receipt.cost_basis_coin_id
                if reservation_status == PriceReservationStatus.settled
                and finalization.metering_receipt is not None
                else None
            ),
            meter_evidence_ref=(
                finalization.metering_receipt.evidence_ref
                if reservation_status == PriceReservationStatus.settled
                and finalization.metering_receipt is not None
                else None
            ),
            commit=commit,
            publish=publish,
        )


def build_service_operation_settlement_adapter() -> (
    EconomyPriceReservationSettlementAdapter
):
    return EconomyPriceReservationSettlementAdapter()


def _prepared_state_from_receipt(
    *,
    receipt: PriceReservationReserveReceipt,
    economy_price_lane: MaterializationLaneContext,
) -> EconomyPriceReservationPreparedState:
    return EconomyPriceReservationPreparedState(
        price_id=receipt.price_id,
        price_schedule_id=receipt.price_schedule_id,
        rate_snapshot_id=receipt.rate_snapshot_id,
        price_reservation_id=receipt.price_reservation_id,
        quoted_amount=receipt.quoted_amount,
        economy_price_lane=economy_price_lane,
    )


def _resolve_price_reservation_status(
    *,
    finalization: ServiceOperationEconomyFinalizationInput,
) -> PriceReservationStatus:
    if (
        finalization.service_operation_status == ServiceOperationStatus.succeeded
        and finalization.api_call_outcome_status == ApiCallOutcomeStatus.succeeded
    ):
        return PriceReservationStatus.settled
    return PriceReservationStatus.cancelled


__all__ = [
    "EconomyPriceReservationPreparedState",
    "EconomyPriceReservationSettlementAdapter",
    "build_service_operation_settlement_adapter",
]
