from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_commercial_profile import ServiceCommercialProfile

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_economy_ontology.finance.finance_entity import FinanceEntity
from aware_economy_ontology.smart_contract.smart_contract_config import SmartContractConfig
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service import Service
from aware_service_ontology.stable_ids import stable_service_commercial_profile_id

# --- AWARE: USER_IMPORTS END


async def set_terms(
    service_commercial_profile: ServiceCommercialProfile,
    producer_finance_entity_id: UUID,
    default_smart_contract_config_id: UUID | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ServiceCommercialProfile:
    """
    Updates the live producer-side commercial profile for future contracts.
    """

    # --- AWARE: LOGIC START set_terms
    session = current_handler_session()
    _ = session.imap_get(FinanceEntity, producer_finance_entity_id)
    if default_smart_contract_config_id is not None:
        _ = session.imap_get(SmartContractConfig, default_smart_contract_config_id)

    service_commercial_profile.producer_finance_entity_id = producer_finance_entity_id
    service_commercial_profile.default_smart_contract_config_id = default_smart_contract_config_id
    service_commercial_profile.metadata_json = cast(JsonObject, dict(metadata_json or {}))
    return service_commercial_profile
    # --- AWARE: LOGIC END set_terms


async def build_via_service(
    service_id: UUID,
    producer_finance_entity_id: UUID,
    default_smart_contract_config_id: UUID | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ServiceCommercialProfile:
    """
    Creates or ensures the live producer-side commercial profile under one Service.

    Contract:
    - Lives on the Service containment rail as current commercial truth.
    - Future ServiceContract receipts may snapshot its producer-side terms without depending
      on live profile mutation for settlement correctness.
    """

    # --- AWARE: LOGIC START build_via_service
    profile_id = stable_service_commercial_profile_id(service_id=service_id)
    metadata_payload = cast(JsonObject, dict(metadata_json or {}))
    session = current_handler_session()
    _ = session.imap_get(Service, service_id)
    _ = session.imap_get(FinanceEntity, producer_finance_entity_id)
    if default_smart_contract_config_id is not None:
        _ = session.imap_get(SmartContractConfig, default_smart_contract_config_id)

    existing = session.imap_get(ServiceCommercialProfile, profile_id)
    if existing is not None:
        if existing.service_id != service_id:
            raise RuntimeError(
                "ServiceCommercialProfile.build_via_service payload mismatch for existing profile: "
                + f"service_commercial_profile_id={profile_id}"
            )
        existing.producer_finance_entity_id = producer_finance_entity_id
        existing.default_smart_contract_config_id = default_smart_contract_config_id
        existing.metadata_json = metadata_payload
        return existing

    return ServiceCommercialProfile(
        id=profile_id,
        service_id=service_id,
        producer_finance_entity_id=producer_finance_entity_id,
        default_smart_contract_config_id=default_smart_contract_config_id,
        metadata_json=metadata_payload,
    )
    # --- AWARE: LOGIC END build_via_service
