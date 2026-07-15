from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from aware_service_ontology.service.service_enums import (
    ServiceOperationSettlementPolicy,
)
from aware_service_runtime.api_ingress.access import (
    ServiceContractOperationPolicySummary,
    ServiceContractOperationPricePolicySummary,
)
from aware_service_runtime.api_ingress.settlement import (
    _resolve_effective_price_terms,
    extract_service_operation_metering_receipt,
    normalize_service_operation_metering_evidence,
)


def _contract_policy(
    *,
    price_source: str,
    price_id=None,
    pricing_policy_id=None,
    settlement_policy_override: str | None = None,
) -> ServiceContractOperationPolicySummary:
    grant_id = uuid4()
    return ServiceContractOperationPolicySummary(
        service_contract_config_operation_grant_id=grant_id,
        price=ServiceContractOperationPricePolicySummary(
            service_contract_config_operation_grant_id=grant_id,
            price_source=price_source,
            price_id=price_id,
            price_ref=None,
            pricing_policy_id=pricing_policy_id,
            pricing_policy_ref=None,
            settlement_policy_override=settlement_policy_override,
            max_cost_required=True,
            quote_ttl_s=60,
            fail_closed=True,
        ),
    )


def test_contract_override_becomes_effective_settlement_terms() -> None:
    operation_price_id = uuid4()
    contract_price_id = uuid4()
    pricing_policy_id = uuid4()

    price_id, policy_id, settlement = _resolve_effective_price_terms(
        operation_price_id=operation_price_id,
        operation_settlement_policy=ServiceOperationSettlementPolicy.none,
        operation_policy=_contract_policy(
            price_source="contract_override",
            price_id=contract_price_id,
            pricing_policy_id=pricing_policy_id,
            settlement_policy_override="reserve_and_finalize",
        ),
    )

    assert price_id == contract_price_id
    assert policy_id == pricing_policy_id
    assert settlement == ServiceOperationSettlementPolicy.reserve_and_finalize


def test_contract_override_without_typed_price_id_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="requires typed price_id"):
        _resolve_effective_price_terms(
            operation_price_id=uuid4(),
            operation_settlement_policy=ServiceOperationSettlementPolicy.none,
            operation_policy=_contract_policy(price_source="contract_override"),
        )


def test_provider_neutral_metering_evidence_accepts_exact_decimal_text() -> None:
    coin_id = uuid4()
    evidence = normalize_service_operation_metering_evidence(
        {
            "schema": "aware.service.operation_metering.v1",
            "phase": "upper_bound",
            "cost_basis_amount": "10.25",
            "cost_basis_coin_id": str(coin_id),
            "evidence_ref": "meter://estimate/1",
        },
        expected_phase="upper_bound",
    )

    assert evidence is not None
    assert evidence.cost_basis_amount == Decimal("10.25")
    assert evidence.cost_basis_coin_id == coin_id


def test_provider_neutral_metering_evidence_rejects_float_and_wrong_phase() -> None:
    payload = {
        "schema": "aware.service.operation_metering.v1",
        "phase": "upper_bound",
        "cost_basis_amount": 1.5,
        "cost_basis_coin_id": str(uuid4()),
        "evidence_ref": "meter://estimate/1",
    }
    with pytest.raises(ValueError, match="exact Decimal"):
        normalize_service_operation_metering_evidence(
            payload,
            expected_phase="upper_bound",
        )
    payload["cost_basis_amount"] = "1.50"
    with pytest.raises(ValueError, match="phase mismatch"):
        normalize_service_operation_metering_evidence(
            payload,
            expected_phase="actual",
        )


def test_actual_metering_receipt_is_extracted_from_shared_response_field() -> None:
    coin_id = uuid4()
    receipt = extract_service_operation_metering_receipt(
        {
            "service_operation_metering_receipt": {
                "schema": "aware.service.operation_metering.v1",
                "phase": "actual",
                "cost_basis_amount": "8.00",
                "cost_basis_coin_id": str(coin_id),
                "evidence_ref": "meter://actual/1",
            }
        }
    )

    assert receipt is not None
    assert receipt.phase == "actual"
    assert receipt.cost_basis_amount == Decimal("8.00")
    assert receipt.evidence_ref == "meter://actual/1"
