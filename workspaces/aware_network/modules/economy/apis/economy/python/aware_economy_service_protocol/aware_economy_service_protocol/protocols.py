# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

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

API_PACKAGE_NAME: Final[str] = "economy-service-api"
API_FQN_PREFIX: Final[str] = "aware_economy_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_economy_service_api"


@dataclass(frozen=True, slots=True)
class ServiceProtocolFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    method_name: str
    request_type_ref: str
    response_type_ref: str


class ServiceProtocolExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ServiceProtocolExecution(Protocol):
    pass


ServiceProtocolExecutionFactory: TypeAlias = Callable[[ServiceProtocolExecutionBackend], ServiceProtocolExecution]

ServiceProtocolInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], Awaitable[object | None]
]

ServiceProtocolStreamInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], AsyncIterator[object]
]


def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    required_fields = [name for name, field in model_cls.model_fields.items() if field.is_required()]
    if len(required_fields) == 1:
        field_name = required_fields[0]
        if isinstance(payload, dict) and field_name in payload:
            return payload
        return {field_name: payload}
    return payload


@dataclass(frozen=True, slots=True)
class ServiceProtocolEndpointBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ServiceProtocolExecutionFactory | None
    stream_invoke: ServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ServiceProtocolFulfillmentBinding, ...]
    invoke: ServiceProtocolInvoker


async def invoke_economy__economy_actor_status__economy_actor_status(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyActorStatusResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyActorStatusRequest.model_validate(request)
    return await typed_handler.economy.economy_actor_status.economy_actor_status(typed_request)


ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF: Final[str] = (
    "economy.economy_actor_status.economy_actor_status"
)
ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF,
        api_name="economy",
        capability_name="economy_actor_status",
        endpoint_name="economy_actor_status",
        request_type_ref="aware_economy_service_dto.economy.EconomyActorStatusRequest",
        response_type_ref="aware_economy_service_dto.economy.EconomyActorStatusResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_economy__economy_actor_status__economy_actor_status,
    )
)


async def invoke_economy__ensure_finance_entity__ensure_finance_entity(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyEnsureFinanceEntityResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyEnsureFinanceEntityRequest.model_validate(request)
    return await typed_handler.economy.ensure_finance_entity.ensure_finance_entity(typed_request)


ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF: Final[str] = (
    "economy.ensure_finance_entity.ensure_finance_entity"
)
ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF,
        api_name="economy",
        capability_name="ensure_finance_entity",
        endpoint_name="ensure_finance_entity",
        request_type_ref="aware_economy_service_dto.economy.EconomyEnsureFinanceEntityRequest",
        response_type_ref="aware_economy_service_dto.economy.EconomyEnsureFinanceEntityResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_economy__ensure_finance_entity__ensure_finance_entity,
    )
)


async def invoke_economy__price_reservation_finalize__price_reservation_finalize(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyPriceReservationFinalizeResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyPriceReservationFinalizeRequest.model_validate(request)
    return await typed_handler.economy.price_reservation_finalize.price_reservation_finalize(typed_request)


ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF: Final[str] = (
    "economy.price_reservation_finalize.price_reservation_finalize"
)
ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF,
    api_name="economy",
    capability_name="price_reservation_finalize",
    endpoint_name="price_reservation_finalize",
    request_type_ref="aware_economy_service_dto.economy.EconomyPriceReservationFinalizeRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyPriceReservationFinalizeResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__price_reservation_finalize__price_reservation_finalize,
)


async def invoke_economy__price_reservation_reserve__price_reservation_reserve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyPriceReservationReserveResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyPriceReservationReserveRequest.model_validate(request)
    return await typed_handler.economy.price_reservation_reserve.price_reservation_reserve(typed_request)


ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF: Final[str] = (
    "economy.price_reservation_reserve.price_reservation_reserve"
)
ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF,
    api_name="economy",
    capability_name="price_reservation_reserve",
    endpoint_name="price_reservation_reserve",
    request_type_ref="aware_economy_service_dto.economy.EconomyPriceReservationReserveRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyPriceReservationReserveResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__price_reservation_reserve__price_reservation_reserve,
)


async def invoke_economy__provider_lifecycle_record__record_provider_lifecycle_event(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyProviderLifecycleRecordResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyProviderLifecycleRecordRequest.model_validate(request)
    return await typed_handler.economy.provider_lifecycle_record.record_provider_lifecycle_event(typed_request)


ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF: Final[str] = (
    "economy.provider_lifecycle_record.record_provider_lifecycle_event"
)
ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF,
    api_name="economy",
    capability_name="provider_lifecycle_record",
    endpoint_name="record_provider_lifecycle_event",
    request_type_ref="aware_economy_service_dto.economy.EconomyProviderLifecycleRecordRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyProviderLifecycleRecordResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__provider_lifecycle_record__record_provider_lifecycle_event,
)


async def invoke_economy__service_operation_permit_ensure__ensure_service_operation_permit(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyServiceOperationPermitEnsureResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyServiceOperationPermitEnsureRequest.model_validate(request)
    return await typed_handler.economy.service_operation_permit_ensure.ensure_service_operation_permit(typed_request)


ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF: Final[str] = (
    "economy.service_operation_permit_ensure.ensure_service_operation_permit"
)
ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF,
    api_name="economy",
    capability_name="service_operation_permit_ensure",
    endpoint_name="ensure_service_operation_permit",
    request_type_ref="aware_economy_service_dto.economy.EconomyServiceOperationPermitEnsureRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyServiceOperationPermitEnsureResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__service_operation_permit_ensure__ensure_service_operation_permit,
)


async def invoke_economy__smart_contract_reservation_prepare__prepare_smart_contract_reservation(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomySmartContractReservationPrepareResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomySmartContractReservationPrepareRequest.model_validate(request)
    return await typed_handler.economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation(
        typed_request
    )


ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF: Final[str] = (
    "economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation"
)
ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
    api_name="economy",
    capability_name="smart_contract_reservation_prepare",
    endpoint_name="prepare_smart_contract_reservation",
    request_type_ref="aware_economy_service_dto.economy.EconomySmartContractReservationPrepareRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomySmartContractReservationPrepareResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__smart_contract_reservation_prepare__prepare_smart_contract_reservation,
)


async def invoke_economy__smart_contract_reservation_release__release_smart_contract_reservation(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomySmartContractReservationReleaseResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomySmartContractReservationReleaseRequest.model_validate(request)
    return await typed_handler.economy.smart_contract_reservation_release.release_smart_contract_reservation(
        typed_request
    )


ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF: Final[str] = (
    "economy.smart_contract_reservation_release.release_smart_contract_reservation"
)
ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF,
    api_name="economy",
    capability_name="smart_contract_reservation_release",
    endpoint_name="release_smart_contract_reservation",
    request_type_ref="aware_economy_service_dto.economy.EconomySmartContractReservationReleaseRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomySmartContractReservationReleaseResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__smart_contract_reservation_release__release_smart_contract_reservation,
)


async def invoke_economy__smart_contract_settlement_finalize__finalize_smart_contract_settlement(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomySmartContractSettlementFinalizeResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomySmartContractSettlementFinalizeRequest.model_validate(request)
    return await typed_handler.economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement(
        typed_request
    )


ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF: Final[str] = (
    "economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement"
)
ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF,
    api_name="economy",
    capability_name="smart_contract_settlement_finalize",
    endpoint_name="finalize_smart_contract_settlement",
    request_type_ref="aware_economy_service_dto.economy.EconomySmartContractSettlementFinalizeRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomySmartContractSettlementFinalizeResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__smart_contract_settlement_finalize__finalize_smart_contract_settlement,
)


async def invoke_economy__wallet_balance_describe__describe_wallet_balance(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyWalletBalanceDescribeResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyWalletBalanceDescribeRequest.model_validate(request)
    return await typed_handler.economy.wallet_balance_describe.describe_wallet_balance(typed_request)


ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF: Final[str] = (
    "economy.wallet_balance_describe.describe_wallet_balance"
)
ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF,
        api_name="economy",
        capability_name="wallet_balance_describe",
        endpoint_name="describe_wallet_balance",
        request_type_ref="aware_economy_service_dto.economy.EconomyWalletBalanceDescribeRequest",
        response_type_ref="aware_economy_service_dto.economy.EconomyWalletBalanceDescribeResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_economy__wallet_balance_describe__describe_wallet_balance,
    )
)


async def invoke_economy__wallet_capital_frame_resolve__resolve_wallet_capital_frame(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyWalletCapitalFrameResolveResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyWalletCapitalFrameResolveRequest.model_validate(request)
    return await typed_handler.economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame(typed_request)


ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF: Final[str] = (
    "economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame"
)
ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF,
    api_name="economy",
    capability_name="wallet_capital_frame_resolve",
    endpoint_name="resolve_wallet_capital_frame",
    request_type_ref="aware_economy_service_dto.economy.EconomyWalletCapitalFrameResolveRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyWalletCapitalFrameResolveResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__wallet_capital_frame_resolve__resolve_wallet_capital_frame,
)


async def invoke_economy__wallet_capital_view_state_resolve__resolve_wallet_capital_view_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyWalletCapitalViewStateV1:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyWalletCapitalViewStateResolveRequest.model_validate(request)
    return await typed_handler.economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state(
        typed_request
    )


ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF: Final[str] = (
    "economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state"
)
ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF,
    api_name="economy",
    capability_name="wallet_capital_view_state_resolve",
    endpoint_name="resolve_wallet_capital_view_state",
    request_type_ref="aware_economy_service_dto.economy.EconomyWalletCapitalViewStateResolveRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyWalletCapitalViewStateV1",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__wallet_capital_view_state_resolve__resolve_wallet_capital_view_state,
)


async def invoke_economy__wallet_funding_cancel__record_wallet_funding_expiration(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyWalletFundingCancelResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyWalletFundingCancelRequest.model_validate(request)
    return await typed_handler.economy.wallet_funding_cancel.record_wallet_funding_expiration(typed_request)


ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_cancel.record_wallet_funding_expiration"
)
ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF,
    api_name="economy",
    capability_name="wallet_funding_cancel",
    endpoint_name="record_wallet_funding_expiration",
    request_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingCancelRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingCancelResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__wallet_funding_cancel__record_wallet_funding_expiration,
)


async def invoke_economy__wallet_funding_context_resolve__resolve_wallet_funding_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyWalletFundingContextResolveResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyWalletFundingContextResolveRequest.model_validate(request)
    return await typed_handler.economy.wallet_funding_context_resolve.resolve_wallet_funding_context(typed_request)


ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_context_resolve.resolve_wallet_funding_context"
)
ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF,
    api_name="economy",
    capability_name="wallet_funding_context_resolve",
    endpoint_name="resolve_wallet_funding_context",
    request_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingContextResolveRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingContextResolveResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__wallet_funding_context_resolve__resolve_wallet_funding_context,
)


async def invoke_economy__wallet_funding_prepare__prepare_wallet_funding(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyWalletFundingPrepareResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyWalletFundingPrepareRequest.model_validate(request)
    return await typed_handler.economy.wallet_funding_prepare.prepare_wallet_funding(typed_request)


ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_prepare.prepare_wallet_funding"
)
ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF,
        api_name="economy",
        capability_name="wallet_funding_prepare",
        endpoint_name="prepare_wallet_funding",
        request_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingPrepareRequest",
        response_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingPrepareResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_economy__wallet_funding_prepare__prepare_wallet_funding,
    )
)


async def invoke_economy__wallet_funding_record__record_verified_wallet_funding(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EconomyWalletFundingRecordResponse:
    typed_handler = cast(AwareEconomyServiceProtocol, handler)
    typed_request = EconomyWalletFundingRecordRequest.model_validate(request)
    return await typed_handler.economy.wallet_funding_record.record_verified_wallet_funding(typed_request)


ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF: Final[str] = (
    "economy.wallet_funding_record.record_verified_wallet_funding"
)
ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF,
    api_name="economy",
    capability_name="wallet_funding_record",
    endpoint_name="record_verified_wallet_funding",
    request_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingRecordRequest",
    response_type_ref="aware_economy_service_dto.economy.EconomyWalletFundingRecordResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_economy__wallet_funding_record__record_verified_wallet_funding,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF: ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_PROTOCOL_BINDING,
    ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF: ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_PROTOCOL_BINDING,
    ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF: ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_PROTOCOL_BINDING,
    ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF: ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_PROTOCOL_BINDING,
    ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF: ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_PROTOCOL_BINDING,
    ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF: ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_PROTOCOL_BINDING,
    ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF: ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_PROTOCOL_BINDING,
    ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF: ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_PROTOCOL_BINDING,
    ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF: ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_PROTOCOL_BINDING,
    ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF: ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_PROTOCOL_BINDING,
    ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF: ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_PROTOCOL_BINDING,
    ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF: ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_PROTOCOL_BINDING,
    ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF: ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_PROTOCOL_BINDING,
    ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF: ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_PROTOCOL_BINDING,
    ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF: ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_PROTOCOL_BINDING,
    ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF: ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_PROTOCOL_BINDING,
}


class EconomyEconomyActorStatusCapabilityServiceProtocol(Protocol):

    async def economy_actor_status(self, request: EconomyActorStatusRequest) -> EconomyActorStatusResponse: ...


class EconomyEnsureFinanceEntityCapabilityServiceProtocol(Protocol):

    async def ensure_finance_entity(
        self, request: EconomyEnsureFinanceEntityRequest
    ) -> EconomyEnsureFinanceEntityResponse: ...


class EconomyPriceReservationFinalizeCapabilityServiceProtocol(Protocol):

    async def price_reservation_finalize(
        self, request: EconomyPriceReservationFinalizeRequest
    ) -> EconomyPriceReservationFinalizeResponse: ...


class EconomyPriceReservationReserveCapabilityServiceProtocol(Protocol):

    async def price_reservation_reserve(
        self, request: EconomyPriceReservationReserveRequest
    ) -> EconomyPriceReservationReserveResponse: ...


class EconomyProviderLifecycleRecordCapabilityServiceProtocol(Protocol):

    async def record_provider_lifecycle_event(
        self, request: EconomyProviderLifecycleRecordRequest
    ) -> EconomyProviderLifecycleRecordResponse: ...


class EconomyServiceOperationPermitEnsureCapabilityServiceProtocol(Protocol):

    async def ensure_service_operation_permit(
        self, request: EconomyServiceOperationPermitEnsureRequest
    ) -> EconomyServiceOperationPermitEnsureResponse: ...


class EconomySmartContractReservationPrepareCapabilityServiceProtocol(Protocol):

    async def prepare_smart_contract_reservation(
        self, request: EconomySmartContractReservationPrepareRequest
    ) -> EconomySmartContractReservationPrepareResponse: ...


class EconomySmartContractReservationReleaseCapabilityServiceProtocol(Protocol):

    async def release_smart_contract_reservation(
        self, request: EconomySmartContractReservationReleaseRequest
    ) -> EconomySmartContractReservationReleaseResponse: ...


class EconomySmartContractSettlementFinalizeCapabilityServiceProtocol(Protocol):

    async def finalize_smart_contract_settlement(
        self, request: EconomySmartContractSettlementFinalizeRequest
    ) -> EconomySmartContractSettlementFinalizeResponse: ...


class EconomyWalletBalanceDescribeCapabilityServiceProtocol(Protocol):

    async def describe_wallet_balance(
        self, request: EconomyWalletBalanceDescribeRequest
    ) -> EconomyWalletBalanceDescribeResponse: ...


class EconomyWalletCapitalFrameResolveCapabilityServiceProtocol(Protocol):

    async def resolve_wallet_capital_frame(
        self, request: EconomyWalletCapitalFrameResolveRequest
    ) -> EconomyWalletCapitalFrameResolveResponse: ...


class EconomyWalletCapitalViewStateResolveCapabilityServiceProtocol(Protocol):

    async def resolve_wallet_capital_view_state(
        self, request: EconomyWalletCapitalViewStateResolveRequest
    ) -> EconomyWalletCapitalViewStateV1: ...


class EconomyWalletFundingCancelCapabilityServiceProtocol(Protocol):

    async def record_wallet_funding_expiration(
        self, request: EconomyWalletFundingCancelRequest
    ) -> EconomyWalletFundingCancelResponse: ...


class EconomyWalletFundingContextResolveCapabilityServiceProtocol(Protocol):

    async def resolve_wallet_funding_context(
        self, request: EconomyWalletFundingContextResolveRequest
    ) -> EconomyWalletFundingContextResolveResponse: ...


class EconomyWalletFundingPrepareCapabilityServiceProtocol(Protocol):

    async def prepare_wallet_funding(
        self, request: EconomyWalletFundingPrepareRequest
    ) -> EconomyWalletFundingPrepareResponse: ...


class EconomyWalletFundingRecordCapabilityServiceProtocol(Protocol):

    async def record_verified_wallet_funding(
        self, request: EconomyWalletFundingRecordRequest
    ) -> EconomyWalletFundingRecordResponse: ...


class EconomyApiServiceProtocol(Protocol):
    economy_actor_status: EconomyEconomyActorStatusCapabilityServiceProtocol
    ensure_finance_entity: EconomyEnsureFinanceEntityCapabilityServiceProtocol
    price_reservation_finalize: EconomyPriceReservationFinalizeCapabilityServiceProtocol
    price_reservation_reserve: EconomyPriceReservationReserveCapabilityServiceProtocol
    provider_lifecycle_record: EconomyProviderLifecycleRecordCapabilityServiceProtocol
    service_operation_permit_ensure: EconomyServiceOperationPermitEnsureCapabilityServiceProtocol
    smart_contract_reservation_prepare: EconomySmartContractReservationPrepareCapabilityServiceProtocol
    smart_contract_reservation_release: EconomySmartContractReservationReleaseCapabilityServiceProtocol
    smart_contract_settlement_finalize: EconomySmartContractSettlementFinalizeCapabilityServiceProtocol
    wallet_balance_describe: EconomyWalletBalanceDescribeCapabilityServiceProtocol
    wallet_capital_frame_resolve: EconomyWalletCapitalFrameResolveCapabilityServiceProtocol
    wallet_capital_view_state_resolve: EconomyWalletCapitalViewStateResolveCapabilityServiceProtocol
    wallet_funding_cancel: EconomyWalletFundingCancelCapabilityServiceProtocol
    wallet_funding_context_resolve: EconomyWalletFundingContextResolveCapabilityServiceProtocol
    wallet_funding_prepare: EconomyWalletFundingPrepareCapabilityServiceProtocol
    wallet_funding_record: EconomyWalletFundingRecordCapabilityServiceProtocol


class AwareEconomyServiceProtocol(Protocol):
    economy: EconomyApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:fab28852884c03ac14dcb9b35c3f9eb9cd6802a34bc6943391b7a314b5dc706a",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 70,'
    '  "sections": ['
    "    {"
    '      "line_count": 17,'
    '      "rendered_text_digest": "sha256:781bc8a9d0806aadbaa59750ac3780551e8111ad23d366a303305f0dd764be9a",'
    '      "section_key": "api.service_protocol.module_prelude",'
    '      "section_kind": "service_protocol_module_prelude",'
    '      "section_order": 0'
    "    },"
    "    {"
    '      "line_count": 59,'
    '      "rendered_text_digest": "sha256:4b2f83676760964f04df5a2dfd6a8153e0c286051f2d85dd83b8e2e933b411d7",'
    '      "section_key": "api.service_protocol.runtime_support",'
    '      "section_kind": "service_protocol_runtime_support",'
    '      "section_order": 1'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.economy_actor_status.economy_actor_status",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.ensure_finance_entity.ensure_finance_entity",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.price_reservation_finalize.price_reservation_finalize",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.price_reservation_reserve.price_reservation_reserve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.provider_lifecycle_record.record_provider_lifecycle_event",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.service_operation_permit_ensure.ensure_service_operation_permit",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.smart_contract_reservation_release.release_smart_contract_reservation",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.wallet_balance_describe.describe_wallet_balance",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.wallet_funding_cancel.record_wallet_funding_expiration",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.wallet_funding_context_resolve.resolve_wallet_funding_context",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.wallet_funding_prepare.prepare_wallet_funding",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:economy.wallet_funding_record.record_verified_wallet_funding",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a79439ca3964eff8761187deb4648fa94e513d4ebff376eead0b9ad8b98650ab",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.economy_actor_status.economy_actor_status",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5cb6795485103cc0544474e8b5f29dc21af729ad8ff04263d1c5b26da8c0ba1b",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.economy_actor_status.economy_actor_status",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:5248febb9f09f335e52d5add076a81664f5937624d346e84e7e3b72c88691bef",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.ensure_finance_entity.ensure_finance_entity",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:936631cd049b2c07bed3ad4faa927e6b0acd51e9f284b713ce5154319b5b3b8c",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.ensure_finance_entity.ensure_finance_entity",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:78921dc1caf02a3b58ec8115b5f74f0f5ac661a7fd4972e6f5880f254075576a",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.price_reservation_finalize.price_reservation_finalize",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b27e982ccbe89c27cc55ca45b6ef14a5af461ffb8e243b2b7fd3744698aa688d",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.price_reservation_finalize.price_reservation_finalize",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1468966feff70b5d3fc44774d8a8aaf332d807dc33c31071db3f5cfc01cbb326",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.price_reservation_reserve.price_reservation_reserve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7c98253d0e9be1c6fc37331ccd1069840592171fb8fd72f62d5ed7a3223ed6e2",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.price_reservation_reserve.price_reservation_reserve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:c8619c044f019cce6ffc9fa397d3cb79ae455a1d733c832e21c382b2ac94ffd3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.provider_lifecycle_record.record_provider_lifecycle_event",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:26734db911369538f5b78818422ad1c30f02e833dacdfdc40fe2393f9806b635",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.provider_lifecycle_record.record_provider_lifecycle_event",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:23328958e9d8f6ff99d6a4339032d23cfb7321300cc9f87e87f0c76e154bcb11",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.service_operation_permit_ensure.ensure_service_operation_permit",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0a8244410d153e9f2686f14a02092c6154cd9304b227cecc848dcb2262bf4ef0",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.service_operation_permit_ensure.ensure_service_operation_permit",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:333d2c17ae648a73e7f81bd02546dee62cb9d7c72600d126f5fd10f6d99ad265",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6d5460e7410072f5608f562dd68baf3d7567f7738ad663bdf5193c0e3574714f",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.smart_contract_reservation_prepare.prepare_smart_contract_reservation",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ee91f1e0213aa8ad75af4ee711de70fb49009ba5cd4fb87d7051e9b08bb331e9",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.smart_contract_reservation_release.release_smart_contract_reservation",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b45add1d3ce681f44d3afb7f31dd5aa119500b5aed6d93470b022bc388d9239a",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.smart_contract_reservation_release.release_smart_contract_reservation",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:859c61ef0e3ce7f91ef2a7ea4c7cd9326505a5cbde6d7d44d7fba9bbe8e45b5d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:2a732d3db0bd915eb1c76a31b5dd31eb1c264c88a29bf8fc43387fa090f21229",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.smart_contract_settlement_finalize.finalize_smart_contract_settlement",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ce9831a0c344359bdcb0de560080b824655fd1c32f91f6dbd7fcac5532fe66b5",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.wallet_balance_describe.describe_wallet_balance",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:49ec1b552b06f7a93531075513cace4c20e81ea9cea5ed919ed4480cfc3b834c",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.wallet_balance_describe.describe_wallet_balance",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:35c59f973dee50d7f490f206506805209653ce5bba839ac85084b1fb3ef6fea1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d2f03579f4247982a5e4ee6be74395622e3993b2f178285c1c3b313c8b8aca23",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.wallet_capital_frame_resolve.resolve_wallet_capital_frame",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ac03c095f03ac51135672f0fb81e5bc6a584d1ba81f08317f07a9734a0a6ed2d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:ba22625abbc6768a42a782b3327f9bebf8cc76eddcf03b502606db7e568c9d28",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.wallet_capital_view_state_resolve.resolve_wallet_capital_view_state",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:5c880e8f27624a4f835286ba284b3f39ad2f85486cc8d4c53b425956e6fb26df",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.wallet_funding_cancel.record_wallet_funding_expiration",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b33ccd17964eee249308c879d8a1531c856a27bc68333eda25bba74e8f77af77",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.wallet_funding_cancel.record_wallet_funding_expiration",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:60040fe0e0db1c55e1cd1945545247695fc56718b1e9cee0b5893bd16797ab7f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.wallet_funding_context_resolve.resolve_wallet_funding_context",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7dc0e147dec9b3310dfe417fa605916f603fdb448a9ee64cd1292bf111542d2a",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.wallet_funding_context_resolve.resolve_wallet_funding_context",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1505724072044b04563e223345da3f9b5475abf7a377c810763d5b3a7a2b803d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.wallet_funding_prepare.prepare_wallet_funding",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:3fe0593c580b08760a6c4b861318ccd7c01a445d1077a7f1889950ee17b594b7",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.wallet_funding_prepare.prepare_wallet_funding",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:97ca0fa35f1b62bb99202a77956f99cbe6c877742d49c80bcb30a54e4da736df",'
    '      "section_key": "api.service_protocol.endpoint_invoker:economy.wallet_funding_record.record_verified_wallet_funding",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:23aad5568170ec256ffc4c0f12eff38ca188eb80375572b994537413aa1387d4",'
    '      "section_key": "api.service_protocol.endpoint_binding:economy.wallet_funding_record.record_verified_wallet_funding",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:d1655d947477d7361836a6774a480e17df8b853242fc1a17999205e14dd6a335",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:f437d1dee58ffd59c0f59e48c972aacb542225d3849f9638437ebbc8738ff23c",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.economy_actor_status",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:bc24a755e91f98c085c987aeb2a0e203915da5011242d8179b2443b1540f3917",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.ensure_finance_entity",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:5726fbd46a9f3d90618c73ac342edad5b5aa3e433142eebfdee32e1b125b8fd7",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.price_reservation_finalize",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:9df879a8db960742a6a0fd773dfc8babfee62861b962f0bb89460e535429752c",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.price_reservation_reserve",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:b67ad3b52d87a899b5630df8691023fda1cc23f299f05f0ea9c5877e06f13335",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.provider_lifecycle_record",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e0a4b8fa5559c60e77737e637ff9e15fcc0e3b1680c335f2622e3910c0e2a9ab",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.service_operation_permit_ensure",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:00927f8f8862c8380c11322b233641629c3ac916fed93cdec750b39f90998ba5",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.smart_contract_reservation_prepare",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 57'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:74d2ccc2e5e9a1d3a8065b450ce1ef946e63d9049441936bbeea17c6611a0d21",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.smart_contract_reservation_release",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 58'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:fc4bbe396d9ed2bf35c364788f4beb5b5cc5658feb90b1f2857235ec08928ab0",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.smart_contract_settlement_finalize",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 59'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:937ae8d9d1afa2b3c8715022627eb070c9229cc0bdd7e91805dbbfd78df4d828",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.wallet_balance_describe",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 60'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:1ef08aeb421f31489dbfc7601db200a7997ddac75e08967c18f8f13725977f9a",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.wallet_capital_frame_resolve",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 61'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6f7e12bb9ad6dd33104de3769bbc7f9323702cd9ca1cfec35bacaabe883ccb06",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.wallet_capital_view_state_resolve",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 62'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:0968bf0b6924fca115348e6b1c5fef1efa2fac49924a530fdf5024b9fc8cfba5",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.wallet_funding_cancel",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 63'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d28b87e76716980e5b050f1daccacd8030337d0616121d2043df91ba71e7f9b7",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.wallet_funding_context_resolve",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 64'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:cf6424f6cf8e05338902c47ab42bca0861d1836772cf419edf89842f4ae54d1b",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.wallet_funding_prepare",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 65'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:8948312e9253df8f58f27b5dd3279885d364e25968e45ef753aa603fa6e86e41",'
    '      "section_key": "api.service_protocol.capability_protocol:economy.wallet_funding_record",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 66'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:9936ed15029b4012c54568bc3d45807d992bcb45c51ba37a22e7e96b3542196f",'
    '      "section_key": "api.service_protocol.api_protocol:economy",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 67'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:b1bd5c1618dbacd88a9482a82b8d5719147841397cfe462ef21b265a56162bfe",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 68'
    "    },"
    "    {"
    '      "line_count": 80,'
    '      "rendered_text_digest": "sha256:5576abd1207a3ab1b8153c860c52aaa0649433ff1e4a7bae7715d9424c035723",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 69'
    "    }"
    "  ],"
    '  "target_relpath": "protocols.py",'
    '  "text_digest_algorithm": "sha256"'
    "}"
)

__all__ = [
    "API_FQN_PREFIX",
    "API_PACKAGE_NAME",
    "ENDPOINT_BINDINGS",
    "PUBLIC_PACKAGE_IMPORT_ROOT",
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON",
    "ServiceProtocolExecutionBackend",
    "ServiceProtocolExecutionFactory",
    "ServiceProtocolEndpointBinding",
    "ServiceProtocolFulfillmentBinding",
    "ServiceProtocolInvoker",
    "ServiceProtocolStreamInvoker",
    "AwareEconomyServiceProtocol",
    "EconomyApiServiceProtocol",
    "EconomyEconomyActorStatusCapabilityServiceProtocol",
    "EconomyEnsureFinanceEntityCapabilityServiceProtocol",
    "EconomyPriceReservationFinalizeCapabilityServiceProtocol",
    "EconomyPriceReservationReserveCapabilityServiceProtocol",
    "EconomyProviderLifecycleRecordCapabilityServiceProtocol",
    "EconomyServiceOperationPermitEnsureCapabilityServiceProtocol",
    "EconomySmartContractReservationPrepareCapabilityServiceProtocol",
    "EconomySmartContractReservationReleaseCapabilityServiceProtocol",
    "EconomySmartContractSettlementFinalizeCapabilityServiceProtocol",
    "EconomyWalletBalanceDescribeCapabilityServiceProtocol",
    "EconomyWalletCapitalFrameResolveCapabilityServiceProtocol",
    "EconomyWalletCapitalViewStateResolveCapabilityServiceProtocol",
    "EconomyWalletFundingCancelCapabilityServiceProtocol",
    "EconomyWalletFundingContextResolveCapabilityServiceProtocol",
    "EconomyWalletFundingPrepareCapabilityServiceProtocol",
    "EconomyWalletFundingRecordCapabilityServiceProtocol",
    "ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_ENDPOINT_REF",
    "ECONOMY__ECONOMY_ACTOR_STATUS__ECONOMY_ACTOR_STATUS_PROTOCOL_BINDING",
    "invoke_economy__economy_actor_status__economy_actor_status",
    "ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_ENDPOINT_REF",
    "ECONOMY__ENSURE_FINANCE_ENTITY__ENSURE_FINANCE_ENTITY_PROTOCOL_BINDING",
    "invoke_economy__ensure_finance_entity__ensure_finance_entity",
    "ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_ENDPOINT_REF",
    "ECONOMY__PRICE_RESERVATION_FINALIZE__PRICE_RESERVATION_FINALIZE_PROTOCOL_BINDING",
    "invoke_economy__price_reservation_finalize__price_reservation_finalize",
    "ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_ENDPOINT_REF",
    "ECONOMY__PRICE_RESERVATION_RESERVE__PRICE_RESERVATION_RESERVE_PROTOCOL_BINDING",
    "invoke_economy__price_reservation_reserve__price_reservation_reserve",
    "ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_ENDPOINT_REF",
    "ECONOMY__PROVIDER_LIFECYCLE_RECORD__RECORD_PROVIDER_LIFECYCLE_EVENT_PROTOCOL_BINDING",
    "invoke_economy__provider_lifecycle_record__record_provider_lifecycle_event",
    "ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_ENDPOINT_REF",
    "ECONOMY__SERVICE_OPERATION_PERMIT_ENSURE__ENSURE_SERVICE_OPERATION_PERMIT_PROTOCOL_BINDING",
    "invoke_economy__service_operation_permit_ensure__ensure_service_operation_permit",
    "ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF",
    "ECONOMY__SMART_CONTRACT_RESERVATION_PREPARE__PREPARE_SMART_CONTRACT_RESERVATION_PROTOCOL_BINDING",
    "invoke_economy__smart_contract_reservation_prepare__prepare_smart_contract_reservation",
    "ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_ENDPOINT_REF",
    "ECONOMY__SMART_CONTRACT_RESERVATION_RELEASE__RELEASE_SMART_CONTRACT_RESERVATION_PROTOCOL_BINDING",
    "invoke_economy__smart_contract_reservation_release__release_smart_contract_reservation",
    "ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_ENDPOINT_REF",
    "ECONOMY__SMART_CONTRACT_SETTLEMENT_FINALIZE__FINALIZE_SMART_CONTRACT_SETTLEMENT_PROTOCOL_BINDING",
    "invoke_economy__smart_contract_settlement_finalize__finalize_smart_contract_settlement",
    "ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_ENDPOINT_REF",
    "ECONOMY__WALLET_BALANCE_DESCRIBE__DESCRIBE_WALLET_BALANCE_PROTOCOL_BINDING",
    "invoke_economy__wallet_balance_describe__describe_wallet_balance",
    "ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_ENDPOINT_REF",
    "ECONOMY__WALLET_CAPITAL_FRAME_RESOLVE__RESOLVE_WALLET_CAPITAL_FRAME_PROTOCOL_BINDING",
    "invoke_economy__wallet_capital_frame_resolve__resolve_wallet_capital_frame",
    "ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_ENDPOINT_REF",
    "ECONOMY__WALLET_CAPITAL_VIEW_STATE_RESOLVE__RESOLVE_WALLET_CAPITAL_VIEW_STATE_PROTOCOL_BINDING",
    "invoke_economy__wallet_capital_view_state_resolve__resolve_wallet_capital_view_state",
    "ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_CANCEL__RECORD_WALLET_FUNDING_EXPIRATION_PROTOCOL_BINDING",
    "invoke_economy__wallet_funding_cancel__record_wallet_funding_expiration",
    "ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_CONTEXT_RESOLVE__RESOLVE_WALLET_FUNDING_CONTEXT_PROTOCOL_BINDING",
    "invoke_economy__wallet_funding_context_resolve__resolve_wallet_funding_context",
    "ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_PREPARE__PREPARE_WALLET_FUNDING_PROTOCOL_BINDING",
    "invoke_economy__wallet_funding_prepare__prepare_wallet_funding",
    "ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_ENDPOINT_REF",
    "ECONOMY__WALLET_FUNDING_RECORD__RECORD_VERIFIED_WALLET_FUNDING_PROTOCOL_BINDING",
    "invoke_economy__wallet_funding_record__record_verified_wallet_funding",
]
