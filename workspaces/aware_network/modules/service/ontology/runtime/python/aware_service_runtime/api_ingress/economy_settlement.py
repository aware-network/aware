from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_api_ontology.api.api_call_outcome import ApiCallOutcome
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_orm.session.session import Session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_enums import (
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
)
from aware_service_ontology.service.service_operation import ServiceOperation
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)

from aware_service_runtime.api_ingress.settlement import (
    ServiceOperationMeteringEvidenceV1,
    ServiceOperationMeteringContextV1,
    ServiceOperationSettlementCoordinator,
    ServiceOperationSettlementFinalization,
    ServiceOperationSettlementPreparation,
    ServiceOperationSettlementReceiptRefs,
)
from aware_service_runtime.api_ingress.admission_context import (
    ServiceContractAccessContextRef,
    ServiceOperationAuthorizationRef,
)


class _RuntimeProtocol(Protocol):
    @property
    def invoker(self) -> object: ...


@dataclass(frozen=True, slots=True)
class ServiceOperationEconomyReservationInput:
    actor_id: UUID | None
    service_ref: Service
    service_config_api_ref: ServiceConfigApi
    service_operation_ref: ServiceOperation
    service_operation_config_ref: ServiceOperationConfig
    service_api_endpoint_binding_ref: ServiceOperationConfigApiEndpoint | None
    api_capability_endpoint_ref: ApiCapabilityEndpoint
    api_call_ref: ApiCall
    request_hash: str
    operation_key: str
    price_id: UUID | None
    pricing_policy_id: UUID | None
    settlement_policy: ServiceOperationSettlementPolicy
    metering_estimate: ServiceOperationMeteringEvidenceV1 | None
    contract_access_context_ref: ServiceContractAccessContextRef | None
    operation_authorization_ref: ServiceOperationAuthorizationRef | None
    service_lane: MaterializationLaneContext
    api_call_lane: MaterializationLaneContext
    economy_price_lane: MaterializationLaneContext | None


@dataclass(frozen=True, slots=True)
class ServiceOperationEconomyFinalizationInput:
    reservation_input: ServiceOperationEconomyReservationInput
    service_operation_status: ServiceOperationStatus
    result_info: str | None
    api_call_outcome_ref: ApiCallOutcome
    api_call_outcome_status: ApiCallOutcomeStatus
    api_call_outcome_response_model_id: UUID | None
    api_call_outcome_error: str | None
    metering_receipt: ServiceOperationMeteringEvidenceV1 | None


class ServiceOperationEconomySettlementAdapter(Protocol):
    async def resolve_metering_context(
        self,
        *,
        runtime: _RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        session: Session,
        reservation: ServiceOperationEconomyReservationInput,
    ) -> ServiceOperationMeteringContextV1 | None: ...

    async def reserve(
        self,
        *,
        runtime: _RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        session: Session,
        reservation: ServiceOperationEconomyReservationInput,
        commit: bool,
        publish: bool,
    ) -> object | None: ...

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
    ) -> ServiceOperationSettlementReceiptRefs | None: ...


def build_service_operation_economy_reservation_input(
    *,
    preparation: ServiceOperationSettlementPreparation,
) -> ServiceOperationEconomyReservationInput:
    context = preparation.context
    request_hash = context.request_hash.strip()
    if not request_hash:
        raise RuntimeError(
            "Service economy reservation input requires context.request_hash"
        )
    return ServiceOperationEconomyReservationInput(
        actor_id=context.actor_id,
        service_ref=context.service_ref,
        service_config_api_ref=context.service_config_api_ref,
        service_operation_ref=context.service_operation_ref,
        service_operation_config_ref=context.service_operation_config_ref,
        service_api_endpoint_binding_ref=context.service_api_endpoint_binding_ref,
        api_capability_endpoint_ref=context.api_capability_endpoint_ref,
        api_call_ref=context.api_call_ref,
        request_hash=request_hash,
        operation_key=context.operation_key,
        price_id=context.price_id,
        pricing_policy_id=context.pricing_policy_id,
        settlement_policy=context.settlement_policy,
        metering_estimate=context.metering_estimate,
        contract_access_context_ref=context.contract_access_context_ref,
        operation_authorization_ref=context.operation_authorization_ref,
        service_lane=context.service_lane,
        api_call_lane=context.api_call_lane,
        economy_price_lane=context.economy_price_lane,
    )


def build_service_operation_economy_finalization_input(
    *,
    finalization: ServiceOperationSettlementFinalization,
) -> ServiceOperationEconomyFinalizationInput:
    api_call_outcome_ref = finalization.api_call_outcome_ref
    if api_call_outcome_ref is None:
        raise RuntimeError(
            "Service economy finalization input requires api_call_outcome_ref"
        )
    api_call_outcome_status = finalization.api_call_outcome_status
    if api_call_outcome_status is None:
        raise RuntimeError(
            "Service economy finalization input requires api_call_outcome_status"
        )
    return ServiceOperationEconomyFinalizationInput(
        reservation_input=build_service_operation_economy_reservation_input(
            preparation=ServiceOperationSettlementPreparation(
                context=finalization.context,
            )
        ),
        service_operation_status=finalization.service_operation_status,
        result_info=finalization.result_info,
        api_call_outcome_ref=api_call_outcome_ref,
        api_call_outcome_status=api_call_outcome_status,
        api_call_outcome_response_model_id=finalization.api_call_outcome_response_model_id,
        api_call_outcome_error=finalization.api_call_outcome_error,
        metering_receipt=finalization.metering_receipt,
    )


@dataclass(frozen=True, slots=True)
class ServiceOperationEconomySettlementCoordinator:
    adapter: ServiceOperationEconomySettlementAdapter
    runtime: _RuntimeProtocol
    index: MetaGraphRuntimeIndex
    commit: bool
    publish: bool

    async def resolve_metering_context(
        self,
        *,
        session: Session,
        preparation: ServiceOperationSettlementPreparation,
    ) -> ServiceOperationMeteringContextV1 | None:
        resolver = getattr(self.adapter, "resolve_metering_context", None)
        if not callable(resolver):
            return None
        return await resolver(
            runtime=self.runtime,
            index=self.index,
            session=session,
            reservation=build_service_operation_economy_reservation_input(
                preparation=preparation,
            ),
        )

    async def before_execute(
        self,
        *,
        session: Session,
        preparation: ServiceOperationSettlementPreparation,
    ) -> object | None:
        return await self.adapter.reserve(
            runtime=self.runtime,
            index=self.index,
            session=session,
            reservation=build_service_operation_economy_reservation_input(
                preparation=preparation,
            ),
            commit=self.commit,
            publish=self.publish,
        )

    async def after_execute(
        self,
        *,
        session: Session,
        prepared_state: object | None,
        finalization: ServiceOperationSettlementFinalization,
    ) -> ServiceOperationSettlementReceiptRefs | None:
        return await self.adapter.finalize(
            runtime=self.runtime,
            index=self.index,
            session=session,
            prepared_state=prepared_state,
            finalization=build_service_operation_economy_finalization_input(
                finalization=finalization,
            ),
            commit=self.commit,
            publish=self.publish,
        )


def build_service_operation_economy_settlement_coordinator(
    *,
    adapter: ServiceOperationEconomySettlementAdapter,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    commit: bool,
    publish: bool,
) -> ServiceOperationSettlementCoordinator:
    return ServiceOperationEconomySettlementCoordinator(
        adapter=adapter,
        runtime=runtime,
        index=index,
        commit=commit,
        publish=publish,
    )


__all__ = [
    "ServiceOperationEconomyFinalizationInput",
    "ServiceOperationEconomyReservationInput",
    "ServiceOperationEconomySettlementAdapter",
    "ServiceOperationEconomySettlementCoordinator",
    "build_service_operation_economy_finalization_input",
    "build_service_operation_economy_reservation_input",
    "build_service_operation_economy_settlement_coordinator",
]
