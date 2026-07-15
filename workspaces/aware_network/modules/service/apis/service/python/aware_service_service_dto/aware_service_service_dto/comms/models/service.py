from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from enum import Enum
from functools import lru_cache
from typing import (
    Annotated,
    ClassVar,
    Literal,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

# Types
from aware_types import (
    DecimalWire,
    JsonArray,
    JsonObject,
    JsonValue,
)


class RequestStatus(Enum):
    """
    Canonical Service operation DTOs (transport-layer, graph/ORM agnostic).
    SSOT: `service-service-dto` generated from this API-owned `.aware` contract.
    `aware_comms` may re-export these DTOs for transport/service import
    stability, but schema ownership remains under `apis/service/dto`.
    """

    succeeded = "succeeded"
    failed = "failed"
    pending = "pending"


class StreamLifecycle(Enum):
    auto_close = "auto_close"
    started = "started"
    closed = "closed"


class ServiceOperationContext(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    branch_id: UUID
    projection_hash: str


class ServiceContractAccessContextRefV1(BaseModel):
    """
    Caller-carried references used by Service to resolve one admitted commercial
    contract. These are coordinates only; Service and Economy resolve truth.
    """

    # Attributes
    consumer_finance_entity_id: UUID
    service_subscription_id: UUID
    service_contract_id: UUID
    service_contract_config_id: UUID
    smart_contract_id: UUID


class ServiceOperationPermitIntentV1(BaseModel):
    """
    Consumer intent for Economy SDK permit ensure/refresh. The caller never
    supplies wallet coordinates or authoritative permit state.
    """

    # Attributes
    contract_version: str = Field(default="aware.service.operation_permit_intent.v1")
    contract_access: ServiceContractAccessContextRefV1
    price_schedule_id: UUID
    coin_id: UUID
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: datetime
    finance_role_key: str = Field(default="primary")


class ServiceOperationAuthorizationRefV1(BaseModel):
    """
    Exact per-invocation binding validated by Service before execution.
    Permit authority remains in Economy; this object carries references only.
    """

    # Attributes
    contract_version: str = Field(default="aware.service.operation_authorization.v1")
    service_contract_id: UUID
    permit_id: UUID
    operation_key: str
    request_hash: str


class ServiceOperationInvocationAuthorizationV1(BaseModel):
    """
    Shared Service invocation metadata passed beside a business API request.
    Domain DTOs such as Inference requests must not duplicate these fields.
    """

    # Attributes
    contract_version: str = Field(default="aware.service.operation_invocation_authorization.v1")
    contract_access: ServiceContractAccessContextRefV1
    operation_authorization: ServiceOperationAuthorizationRefV1


class ServiceOperationMeteringEvidenceV1(BaseModel):
    """
    Provider-neutral evidence consumed by shared Service/Economy pricing.
    Domain services produce evidence; they never create Price or settlement truth.
    """

    # Attributes
    contract_version: str = Field(default="aware.service.operation_metering.v1")
    phase: str
    cost_basis_amount: Annotated[Decimal, DecimalWire()]
    cost_basis_coin_id: UUID
    evidence_ref: str


class ServiceOperationEconomicReceiptRefsV1(BaseModel):
    """
    Reference-only projection of the shared commercial execution receipt.
    Amounts, balances, and ledger authority remain queryable from Economy.
    """

    # Attributes
    contract_version: str = Field(default="aware.service.operation_economic_receipt_refs.v1")
    service_operation_id: UUID
    service_contract_id: UUID
    permit_id: UUID
    price_id: UUID
    price_schedule_id: UUID
    rate_snapshot_id: UUID
    price_reservation_id: UUID
    smart_contract_reservation_id: UUID
    settlement_id: UUID
    transaction_id: UUID | None = Field(default=None)
    payer_wallet_balance_id: UUID
    receiver_wallet_balance_id: UUID
    status: str
    idempotent_replay: bool = Field(default=False)


class ServiceOperation(BaseModel):
    # Attributes
    request: ServiceOperationRequest | None = Field(default=None)
    response: ServiceOperationResponse | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.request,
                    self.response,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of request, response must be set")
        return self


class ServiceHostControlRequest(BaseModel):
    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "configure_service_api_dependency_routes": "aware_service_service_dto.comms.models.service.ConfigureServiceApiDependencyRoutesHostControlRequest",
        "activate_service_host_lifecycles": "aware_service_service_dto.comms.models.service.ActivateServiceHostLifecyclesHostControlRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownServiceHostControlRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownServiceHostControlRequest(ServiceHostControlRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ServiceHostControlResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    status: RequestStatus = Field(default=RequestStatus.succeeded)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "configure_service_api_dependency_routes": "aware_service_service_dto.comms.models.service.ConfigureServiceApiDependencyRoutesHostControlResponse",
        "activate_service_host_lifecycles": "aware_service_service_dto.comms.models.service.ActivateServiceHostLifecyclesHostControlResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownServiceHostControlResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownServiceHostControlResponse(ServiceHostControlResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ConfigureServiceApiDependencyRoutesHostControlRequest(ServiceHostControlRequest):
    # Discriminator Tag
    operation: Literal["configure_service_api_dependency_routes"] = "configure_service_api_dependency_routes"

    # Attributes
    routes: JsonArray = Field(default_factory=JsonArray)


class ConfigureServiceApiDependencyRoutesHostControlResponse(ServiceHostControlResponse):
    # Discriminator Tag
    operation: Literal["configure_service_api_dependency_routes"] = "configure_service_api_dependency_routes"

    # Attributes
    status: RequestStatus = Field(default=RequestStatus.succeeded)
    error: str | None = Field(default=None)
    route_count: int = Field(default=0)


class ActivateServiceHostLifecyclesHostControlRequest(ServiceHostControlRequest):
    # Discriminator Tag
    operation: Literal["activate_service_host_lifecycles"] = "activate_service_host_lifecycles"


class ActivateServiceHostLifecyclesHostControlResponse(ServiceHostControlResponse):
    # Discriminator Tag
    operation: Literal["activate_service_host_lifecycles"] = "activate_service_host_lifecycles"

    # Attributes
    status: RequestStatus = Field(default=RequestStatus.succeeded)
    error: str | None = Field(default=None)
    lifecycle_handler_count: int = Field(default=0)
    already_active: bool = Field(default=False)


class ServiceApiDispatchEnvelope(BaseModel):
    # Attributes
    api_call_id: UUID
    api_capability_endpoint_id: UUID
    call_key: UUID
    request_hash: str
    commit_id: UUID
    head_commit_id: UUID
    branch_id: UUID
    projection_hash: str
    api_name: str
    capability_name: str
    endpoint_name: str
    endpoint_ref: str
    discriminant: str
    source_path: str
    request_model_id: UUID
    request_class_config_id: UUID
    request_class_ref: str
    request_source_path: str
    response_class_ref: str | None = Field(default=None)
    response_source_path: str | None = Field(default=None)


class ServiceApiDispatchFulfillmentBinding(BaseModel):
    # Attributes
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    graph_function_runtime_target: str
    method_name: str
    request_type_ref: str
    response_type_ref: str
    source_path: str
    api_capability_endpoint_function_id: UUID | None = Field(default=None)


class ServiceApiDispatchRequest(BaseModel):
    # Attributes
    operation_key: str
    envelope: ServiceApiDispatchEnvelope
    request_payload: JsonObject
    fulfillment_bindings: list[ServiceApiDispatchFulfillmentBinding] = Field(default_factory=list)


class ServiceApiDispatchReceipt(BaseModel):
    # Attributes
    endpoint_ref: str
    discriminant: str
    status: RequestStatus = Field(default=RequestStatus.succeeded)
    network_request_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    api_capability_endpoint_id: UUID | None = Field(default=None)
    call_key: UUID | None = Field(default=None)
    request_hash: str | None = Field(default=None)
    request_model_id: UUID | None = Field(default=None)
    api_call_outcome_id: UUID | None = Field(default=None)
    response_model_id: UUID | None = Field(default=None)
    service_operation_id: UUID | None = Field(default=None)
    service_operation_config_id: UUID | None = Field(default=None)
    service_operation_config_api_endpoint_id: UUID | None = Field(default=None)
    service_operation_commit_id: UUID | None = Field(default=None)
    service_operation_head_commit_id: UUID | None = Field(default=None)
    service_operation_branch_id: UUID | None = Field(default=None)
    service_operation_projection_hash: str | None = Field(default=None)
    api_call_outcome_commit_id: UUID | None = Field(default=None)
    api_call_outcome_head_commit_id: UUID | None = Field(default=None)
    api_call_outcome_branch_id: UUID | None = Field(default=None)
    api_call_outcome_projection_hash: str | None = Field(default=None)
    economic_receipt: ServiceOperationEconomicReceiptRefsV1 | None = Field(default=None)


class ServiceOperationRequest(BaseModel):
    # Attributes
    context: ServiceOperationContext
    service: str
    operation: JsonValue | None = Field(default=None)
    api_dispatch: ServiceApiDispatchRequest | None = Field(default=None)
    stream_target_id: UUID | None = Field(default=None)
    stream_correlation_id: UUID | None = Field(default=None)
    network_request_id: UUID | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.operation,
                    self.api_dispatch,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of operation, api_dispatch must be set")
        return self


class ServiceOperationResponse(BaseModel):
    # Attributes
    status: RequestStatus
    error: str | None = Field(default=None)
    response_payload: JsonValue | None = Field(default=None)
    receipt: ServiceApiDispatchReceipt | None = Field(default=None)
    stream_lifecycle: StreamLifecycle = Field(default=StreamLifecycle.auto_close)
