from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
)
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_economy_settlement import ServiceContractEconomySettlement

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_economy_ontology.finance.finance_entity import FinanceEntity
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_commercial_profile import (
    ServiceCommercialProfile,
)
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.stable_ids import stable_service_contract_id

# --- AWARE: USER_IMPORTS END


async def set_status(
    service_contract: ServiceContract,
    status: ServiceContractStatus,
    effective_until: datetime | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ServiceContract:
    """
    Updates the lifecycle status for this ServiceContract receipt.
    """

    # --- AWARE: LOGIC START set_status
    service_contract.status = status
    service_contract.effective_until = effective_until
    service_contract.metadata_json = cast(JsonObject, dict(metadata_json or {}))
    return service_contract
    # --- AWARE: LOGIC END set_status


async def configure_economy_settlement(
    service_contract: ServiceContract,
    permit_id: UUID,
    permit_nonce: int,
    payer_wallet_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_wallet_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
    deadline: datetime,
) -> ServiceContractEconomySettlement:
    """
    Binds typed Economy settlement coordinates to this concrete ServiceContract.

    Contract:
    - ServiceContract remains access/terms authority.
    - Economy owns capital mutation, spend-envelope cap checks, operation nonce allocation,
      reservation, escrow, and settlement receipts.
    - These coordinates replace the legacy metadata settlement payload for active settlement.
    """

    # --- AWARE: LOGIC START configure_economy_settlement
    created = await ServiceContractEconomySettlement.build_via_service_contract(
        service_contract_id=service_contract.id,
        permit_id=permit_id,
        permit_nonce=permit_nonce,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        deadline=deadline,
    )
    service_contract.economy_settlement = created
    return created
    # --- AWARE: LOGIC END configure_economy_settlement


async def build_via_service(
    service_id: UUID,
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
    Creates one Service-owned commercial agreement receipt under a concrete Service.

    Contract:
    - Stable identity is anchored by the parent Service containment rail plus ServiceContractConfig plus
    SmartContract.
    - `service_contract_config` points to reusable operation/role grant semantics.
    - `commercial_profile` is a typed reference rail for portal-backed provenance/navigation,
      not contract ownership or stable-id propagation.
    - Producer/consumer finance entities are settlement snapshots for this agreement.
    """

    # --- AWARE: LOGIC START build_via_service
    contract_id = stable_service_contract_id(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
    )
    metadata_payload = cast(JsonObject, dict(metadata_json or {}))
    resolved_kind = kind if kind is not None else ServiceContractKind.subscription
    resolved_status = status if status is not None else ServiceContractStatus.pending
    session = current_handler_session()

    service = session.imap_get(Service, service_id)
    service_contract_config = session.imap_get(ServiceContractConfig, service_contract_config_id)
    if service is not None and service_contract_config is not None:
        if service.service_config_id != service_contract_config.service_config_id:
            raise RuntimeError(
                "ServiceContract.build_via_service contract config does not belong to ServiceConfig: "
                + f"service_id={service_id} "
                + f"service_contract_config_id={service_contract_config_id}"
            )

    commercial_profile = session.imap_get(ServiceCommercialProfile, commercial_profile_id)
    if commercial_profile is not None:
        if commercial_profile.service_id != service_id:
            raise RuntimeError(
                "ServiceContract.build_via_service commercial_profile does not belong to Service: "
                + f"service_id={service_id} commercial_profile_id={commercial_profile_id}"
            )
        if commercial_profile.producer_finance_entity_id != producer_finance_entity_id:
            raise RuntimeError(
                "ServiceContract.build_via_service producer_finance_entity_id does not match commercial_profile: "
                + f"commercial_profile_id={commercial_profile_id}"
            )

    _ = session.imap_get(FinanceEntity, producer_finance_entity_id)
    _ = session.imap_get(FinanceEntity, consumer_finance_entity_id)
    _ = session.imap_get(SmartContract, smart_contract_id)

    existing = session.imap_get(ServiceContract, contract_id)
    if existing is not None:
        if (
            existing.service_id != service_id
            or existing.service_contract_config_id != service_contract_config_id
            or existing.commercial_profile_id != commercial_profile_id
            or existing.producer_finance_entity_id != producer_finance_entity_id
            or existing.consumer_finance_entity_id != consumer_finance_entity_id
            or existing.smart_contract_id != smart_contract_id
            or existing.kind != resolved_kind
            or existing.effective_from != effective_from
        ):
            raise RuntimeError(
                "ServiceContract.build_via_service payload mismatch for existing contract: "
                + f"service_contract_id={contract_id}"
            )
        existing.status = resolved_status
        existing.effective_until = effective_until
        existing.metadata_json = metadata_payload
        return existing

    return ServiceContract(
        id=contract_id,
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        commercial_profile_id=commercial_profile_id,
        producer_finance_entity_id=producer_finance_entity_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        kind=resolved_kind,
        effective_from=effective_from,
        status=resolved_status,
        effective_until=effective_until,
        metadata_json=metadata_payload,
    )
    # --- AWARE: LOGIC END build_via_service
