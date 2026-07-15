from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import ServicePlanCycle
from aware_service_ontology.service.service_plan import ServicePlan

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_economy_ontology.coin.coin import Coin
from aware_economy_ontology.smart_contract.smart_contract_config import (
    SmartContractConfig,
)
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service import Service
from aware_service_ontology.stable_ids import stable_service_plan_id

# --- AWARE: USER_IMPORTS END


async def build_via_service(
    service_id: UUID,
    cycle: ServicePlanCycle,
    price_amount: Annotated[Decimal, DecimalWire()],
    coin_id: UUID,
    smart_contract_config_id: UUID,
    external_price_handle: str | None = None,
    policy_json: JsonObject = JsonObject(),
) -> ServicePlan:
    """
    Creates one Service-owned pricing plan under a concrete Service.
    """

    # --- AWARE: LOGIC START build_via_service
    if price_amount <= 0:
        raise ValueError("ServicePlan.build_via_service requires price_amount > 0")

    session = current_handler_session()
    _ = session.imap_get(Service, service_id)
    _ = session.imap_get(Coin, coin_id)
    _ = session.imap_get(SmartContractConfig, smart_contract_config_id)

    plan_id = stable_service_plan_id(
        service_id=service_id,
        coin_id=coin_id,
        smart_contract_config_id=smart_contract_config_id,
        cycle=cycle.value,
        price_amount=price_amount,
    )
    external_price_handle_norm = (external_price_handle or "").strip() or None
    policy_payload = cast(JsonObject, dict(policy_json or {}))

    existing = session.imap_get(ServicePlan, plan_id)
    if existing is not None:
        if (
            existing.service_id != service_id
            or existing.coin_id != coin_id
            or existing.smart_contract_config_id != smart_contract_config_id
            or existing.cycle != cycle
            or existing.price_amount != price_amount
        ):
            raise RuntimeError(
                "ServicePlan.build_via_service payload mismatch for existing plan: " + f"service_plan_id={plan_id}"
            )
        if external_price_handle_norm is not None:
            existing.external_price_handle = external_price_handle_norm
        existing.policy_json = policy_payload
        return existing

    return ServicePlan(
        id=plan_id,
        service_id=service_id,
        cycle=cycle,
        price_amount=price_amount,
        coin_id=coin_id,
        smart_contract_config_id=smart_contract_config_id,
        external_price_handle=external_price_handle_norm,
        policy_json=policy_payload,
    )
    # --- AWARE: LOGIC END build_via_service
