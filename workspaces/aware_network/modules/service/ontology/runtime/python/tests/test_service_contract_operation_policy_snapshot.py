from _service_runtime_test_paths import REPO_ROOT

ROOT = REPO_ROOT


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_service_contract_operation_policy_ssot_declares_typed_objects() -> None:
    quota = _read(
        "workspaces/aware_network/modules/service/ontology/structure/aware/service/"
        "service_contract_operation_quota_policy.aware"
    )
    permit = _read(
        "workspaces/aware_network/modules/service/ontology/structure/aware/service/"
        "service_contract_operation_permit_policy.aware"
    )
    price = _read(
        "workspaces/aware_network/modules/service/ontology/structure/aware/service/"
        "service_contract_operation_price_policy.aware"
    )

    assert "class ServiceContractOperationQuotaPolicy" in quota
    assert "JsonObject" not in quota
    assert "unit ServiceContractOperationQuotaUnit = operation" in quota
    assert "limit_amount Int?" in quota
    assert (
        "over_limit_behavior ServiceContractOperationQuotaOverLimitBehavior = deny"
        in quota
    )

    assert "class ServiceContractOperationPermitPolicy" in permit
    assert "JsonObject" not in permit
    assert "requires_active_contract Bool = true" in permit
    assert "requires_smart_contract_permit Bool = false" in permit
    assert "requires_reservation_before_execute Bool = false" in permit

    assert "class ServiceContractOperationPricePolicy" in price
    assert "JsonObject" not in price
    assert "price aware_economy.price.Price?" in price
    assert "pricing_policy aware_economy.price.PricingPolicy?" in price
    assert "settlement_policy_override ServiceOperationSettlementPolicy?" in price


def test_service_contract_operation_grant_links_typed_policies() -> None:
    grant = _read(
        "workspaces/aware_network/modules/service/ontology/structure/aware/service/"
        "service_contract_config_operation_grant.aware"
    )

    assert "quota_policy ServiceContractOperationQuotaPolicy? unique" in grant
    assert "permit_policy ServiceContractOperationPermitPolicy? unique" in grant
    assert "price_policy ServiceContractOperationPricePolicy? unique" in grant
    assert "quota_policy_json JsonObject? = {}" in grant
    assert "permit_policy_json JsonObject? = {}" in grant
    assert "price_policy_json JsonObject? = {}" in grant
    assert "fn configure_quota_policy" in grant
    assert "fn configure_permit_policy" in grant
    assert "fn configure_price_policy" in grant
