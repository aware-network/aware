from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
    ServiceOperationStatus,
    ServicePlanCycle,
)
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_branch import ServiceBranch
from aware_service_ontology.service.service_commercial_profile import ServiceCommercialProfile
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_operation import ServiceOperation
from aware_service_ontology.service.service_plan import ServicePlan

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
from aware_meta.runtime.handler_context import current_handler_session
from aware_economy_ontology.finance.finance_entity import FinanceEntity
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.coin.coin import Coin
from aware_economy_ontology.smart_contract.smart_contract_config import SmartContractConfig
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_config_api_projection import ServiceConfigApiProjection
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_operation_config import ServiceOperationConfig
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.stable_ids import (
    stable_service_branch_id,
    stable_service_id,
)

# --- AWARE: USER_IMPORTS END


async def create_operation(
    service: Service,
    service_operation_config_id: UUID,
    operation_key: str,
    api_call_id: UUID | None = None,
    api_endpoint_id: UUID | None = None,
    status: ServiceOperationStatus = ServiceOperationStatus.queued,
    result_info: str | None = None,
    execution_context: JsonObject | None = None,
) -> ServiceOperation:
    """
    Creates one canonical service execution receipt under this concrete Service.
    """

    # --- AWARE: LOGIC START create_operation
    session = current_handler_session()

    service_operation_config = session.imap_get(ServiceOperationConfig, service_operation_config_id)
    if service_operation_config is not None and service_operation_config.service_config_id != service.service_config_id:
        raise RuntimeError(
            "Service.create_operation service_operation_config does not belong to parent ServiceConfig: "
            + f"service_id={service.id} "
            + f"service_operation_config_id={service_operation_config_id}"
        )

    api_endpoint = None
    if api_endpoint_id is not None:
        api_endpoint = session.imap_get(ServiceOperationConfigApiEndpoint, api_endpoint_id)
        if api_endpoint is not None and api_endpoint.service_operation_config_id != service_operation_config_id:
            raise RuntimeError(
                "Service.create_operation api_endpoint does not belong to the referenced "
                + "ServiceOperationConfig: "
                + f"service_operation_config_id={service_operation_config_id} "
                + f"api_endpoint_id={api_endpoint_id}"
            )
        if api_endpoint is not None:
            service_config_api = session.imap_get(ServiceConfigApi, api_endpoint.service_config_api_id)
            if service_config_api is not None and service_config_api.service_config_id != service.service_config_id:
                raise RuntimeError(
                    "Service.create_operation api_endpoint does not belong to the same ServiceConfig "
                    + "as the concrete Service: "
                    + f"api_endpoint_id={api_endpoint_id}"
                )

    created = await ServiceOperation.build_via_service(
        service_id=service.id,
        service_operation_config_id=service_operation_config_id,
        operation_key=operation_key,
        api_call_id=api_call_id,
        api_endpoint_id=api_endpoint_id,
        status=status,
        result_info=result_info,
        execution_context=execution_context,
    )
    for existing in service.service_operations:
        if existing.id == created.id:
            return existing
    service.service_operations.append(created)
    return created
    # --- AWARE: LOGIC END create_operation


async def create_commercial_profile(
    service: Service,
    producer_finance_entity_id: UUID,
    default_smart_contract_config_id: UUID | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ServiceCommercialProfile:
    """
    Creates or ensures the canonical producer-side commercial profile for this Service.
    """

    # --- AWARE: LOGIC START create_commercial_profile
    created = await ServiceCommercialProfile.build_via_service(
        service_id=service.id,
        producer_finance_entity_id=producer_finance_entity_id,
        default_smart_contract_config_id=default_smart_contract_config_id,
        metadata_json=metadata_json,
    )
    service.commercial_profile = created
    return created
    # --- AWARE: LOGIC END create_commercial_profile


async def create_contract(
    service: Service,
    service_contract_config_id: UUID,
    commercial_profile_id: UUID,
    producer_finance_entity_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID,
    kind: ServiceContractKind,
    effective_from: datetime,
    status: ServiceContractStatus = ServiceContractStatus.pending,
    effective_until: datetime | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ServiceContract:
    """
    Creates one Service-owned commercial agreement receipt under this Service.
    """

    # --- AWARE: LOGIC START create_contract
    session = current_handler_session()

    service_contract_config = session.imap_get(ServiceContractConfig, service_contract_config_id)
    if service_contract_config is not None and service_contract_config.service_config_id != service.service_config_id:
        raise RuntimeError(
            "Service.create_contract service_contract_config does not belong to parent ServiceConfig: "
            + f"service_id={service.id} "
            + f"service_contract_config_id={service_contract_config_id}"
        )

    commercial_profile = session.imap_get(ServiceCommercialProfile, commercial_profile_id)
    if commercial_profile is not None:
        if commercial_profile.service_id != service.id:
            raise RuntimeError(
                "Service.create_contract commercial_profile does not belong to Service: "
                + f"service_id={service.id} "
                + f"commercial_profile_id={commercial_profile_id}"
            )
        if commercial_profile.producer_finance_entity_id != producer_finance_entity_id:
            raise RuntimeError(
                "Service.create_contract producer_finance_entity_id does not match commercial_profile: "
                + f"commercial_profile_id={commercial_profile_id}"
            )

    _ = session.imap_get(FinanceEntity, producer_finance_entity_id)
    _ = session.imap_get(FinanceEntity, consumer_finance_entity_id)
    _ = session.imap_get(SmartContract, smart_contract_id)

    resolved_kind = kind
    if resolved_kind is None:
        resolved_kind = (
            service_contract_config.default_kind
            if service_contract_config is not None
            else ServiceContractKind.subscription
        )
    created = await ServiceContract.build_via_service(
        service_id=service.id,
        service_contract_config_id=service_contract_config_id,
        commercial_profile_id=commercial_profile_id,
        producer_finance_entity_id=producer_finance_entity_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        kind=resolved_kind,
        effective_from=effective_from,
        status=status,
        effective_until=effective_until,
        metadata_json=metadata_json,
    )
    for existing in service.contracts:
        if existing.id == created.id:
            return existing
    service.contracts.append(created)
    return created
    # --- AWARE: LOGIC END create_contract


async def create_plan(
    service: Service,
    cycle: ServicePlanCycle,
    price_amount: Annotated[Decimal, DecimalWire()],
    coin_id: UUID,
    smart_contract_config_id: UUID,
    external_price_handle: str | None = None,
    policy_json: JsonObject = JsonObject(),
) -> ServicePlan:
    """
    Appends one provider-owned pricing plan under this concrete Service.
    """

    # --- AWARE: LOGIC START create_plan
    if price_amount <= 0:
        raise ValueError("Service.create_plan requires price_amount > 0")

    session = current_handler_session()
    _ = session.imap_get(Coin, coin_id)
    _ = session.imap_get(SmartContractConfig, smart_contract_config_id)

    created = await ServicePlan.build_via_service(
        service_id=service.id,
        cycle=cycle,
        price_amount=price_amount,
        coin_id=coin_id,
        smart_contract_config_id=smart_contract_config_id,
        external_price_handle=external_price_handle,
        policy_json=policy_json,
    )
    for existing in service.plans:
        if existing.id == created.id:
            return existing
    service.plans.append(created)
    return created
    # --- AWARE: LOGIC END create_plan


async def create_branch(
    service: Service,
    service_config_api_projection_id: UUID,
    object_instance_graph_branch_id: UUID,
    description: str | None = None,
) -> ServiceBranch:
    """
    Creates one concrete subscribed branch binding under this Service.
    """

    # --- AWARE: LOGIC START create_branch
    service_id = service.id
    if service_id is None:
        raise RuntimeError("Service.create_branch requires Service.id")

    session = current_handler_session()
    branch_binding_id = stable_service_branch_id(
        service_id=service_id,
        service_config_api_projection_id=service_config_api_projection_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )
    existing = session.imap_get(ServiceBranch, branch_binding_id)
    if existing is not None:
        if (
            existing.service_id != service_id
            or existing.service_config_api_projection_id != service_config_api_projection_id
            or existing.object_instance_graph_branch_id != object_instance_graph_branch_id
        ):
            raise RuntimeError(
                "Service.create_branch payload mismatch for existing branch binding: "
                + f"service_branch_id={branch_binding_id}"
            )
        if all(current.id != existing.id for current in service.branches):
            service.branches.append(existing)
        return existing

    service_config_api_projection = session.imap_get(ServiceConfigApiProjection, service_config_api_projection_id)
    if service_config_api_projection is not None:
        service_config_api = session.imap_get(ServiceConfigApi, service_config_api_projection.service_config_api_id)
        if service_config_api is not None and service_config_api.service_config_id != service.service_config_id:
            raise RuntimeError(
                "Service.create_branch requires ServiceConfigApiProjection to belong to the same ServiceConfig "
                + "as the concrete Service: "
                + f"service_id={service_id} "
                + f"service_config_api_projection_id={service_config_api_projection_id}"
            )

    _ = session.imap_get(ObjectInstanceGraphBranch, object_instance_graph_branch_id)

    created = await ServiceBranch.build_via_service(
        service_id=service_id,
        service_config_api_projection_id=service_config_api_projection_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        description=description,
    )
    if all(current.id != created.id for current in service.branches):
        service.branches.append(created)
    return created
    # --- AWARE: LOGIC END create_branch


async def build_via_service_config(service_config_id: UUID, name: str, description: str | None = None) -> Service:
    """
    Creates one Service instance under a ServiceConfig.
    """

    # --- AWARE: LOGIC START build_via_service_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("Service.build_via_service_config requires non-empty name")

    service_id = stable_service_id(
        service_config_id=service_config_id,
        name=normalized_name,
    )
    session = current_handler_session()
    existing = session.imap_get(Service, service_id)
    if existing is not None:
        if existing.service_config_id != service_config_id or (existing.name or "").strip() != normalized_name:
            raise RuntimeError(f"Service.build_via_service_config payload mismatch for existing service: {service_id}")
        return existing

    return Service(
        id=service_id,
        service_config_id=service_config_id,
        name=normalized_name,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_config
