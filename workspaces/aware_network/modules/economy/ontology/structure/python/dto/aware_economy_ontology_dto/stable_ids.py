# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_ECONOMY = uuid5(NAMESPACE_URL, "aware://economy/v1")


def stable_capital_conversion_quote_id(*, quote_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: quote_key"""

    quote_key_norm = (quote_key or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:capital_conversion_quote:{quote_key_norm}")


def stable_coin_id(*, symbol: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: symbol"""

    symbol_norm = (symbol or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:coin:{symbol_norm}")


def stable_coin_exchange_rate_id(*, quote_coin_id: UUID, data_source: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: quote_coin_id, data_source"""

    data_source_norm = (data_source or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:coin_exchange_rate:{quote_coin_id}:{data_source_norm}")


def stable_economy_analytic_id(*, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_ECONOMY, f"aware:economy_analytic:{key_norm}")


def stable_economy_analytic_execution_id(*, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_ECONOMY, f"aware:economy_analytic_execution:{key_norm}")


def stable_economy_analytic_execution_metric_id(*, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_ECONOMY, f"aware:economy_analytic_execution_metric:{key_norm}")


def stable_economy_analytic_metric_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:economy_analytic_metric:{name_norm}")


def stable_economy_package_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:economy_package:{name_norm}")


def stable_escrow_id(*, wallet_public_id: UUID, op_nonce: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: wallet_public_id, op_nonce"""

    return uuid5(NS_ECONOMY, f"aware:escrow:{wallet_public_id}:{op_nonce}")


def stable_external_capital_provider_config_id(*, provider_finance_entity_id: UUID, provider_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: provider_finance_entity_id, provider_key"""

    provider_key_norm = (provider_key or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:external_capital_provider_config:{provider_finance_entity_id}:{provider_key_norm}")


def stable_external_capital_provider_route_id(
    *, external_capital_provider_config_id: UUID, target_coin_id: UUID, route_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: external_capital_provider_config_id, target_coin_id, route_key"""

    route_key_norm = (route_key or "").casefold().strip()
    return uuid5(
        NS_ECONOMY,
        f"aware:external_capital_provider_route:{external_capital_provider_config_id}:{target_coin_id}:{route_key_norm}",
    )


def stable_finance_entity_id(*, identity_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: identity_id"""

    return uuid5(NS_ECONOMY, f"aware:finance_entity:{identity_id}")


def stable_price_id(*, coin_id: UUID, name: str, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: coin_id, name, type"""

    name_norm = (name or "").casefold().strip()
    type_norm = (type or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:price:{coin_id}:{name_norm}:{type_norm}")


def stable_price_reservation_id(*, rate_snapshot_id: UUID, reservation_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: rate_snapshot_id, reservation_key"""

    reservation_key_norm = (reservation_key or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:price_reservation:{rate_snapshot_id}:{reservation_key_norm}")


def stable_price_schedule_id(*, price_id: UUID, pricing_policy_id: UUID, name: str, version: int = 1) -> UUID:
    """Compiler-generated from class-attribute identity keys: price_id, pricing_policy_id, name, version"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:price_schedule:{price_id}:{pricing_policy_id}:{name_norm}:{version}")


def stable_pricing_policy_id(*, name: str, version: int = 1) -> UUID:
    """Compiler-generated from class-attribute identity keys: name, version"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:pricing_policy:{name_norm}:{version}")


def stable_provider_lifecycle_receipt_id(
    *,
    provider_finance_entity_id: UUID,
    provider_lifecycle_effect_key: str,
    provider_lifecycle_object_id: str,
    provider_key: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: provider_finance_entity_id, provider_lifecycle_effect_key, provider_lifecycle_object_id, provider_key"""

    provider_lifecycle_effect_key_norm = (provider_lifecycle_effect_key or "").casefold().strip()
    provider_lifecycle_object_id_norm = (provider_lifecycle_object_id or "").casefold().strip()
    provider_key_norm = (provider_key or "").casefold().strip()
    return uuid5(
        NS_ECONOMY,
        f"aware:provider_lifecycle_receipt:{provider_finance_entity_id}:{provider_lifecycle_effect_key_norm}:{provider_lifecycle_object_id_norm}:{provider_key_norm}",
    )


def stable_rate_snapshot_id(*, price_schedule_id: UUID, snapshot_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: price_schedule_id, snapshot_key"""

    snapshot_key_norm = (snapshot_key or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:rate_snapshot:{price_schedule_id}:{snapshot_key_norm}")


def stable_smart_contract_id(*, smart_contract_config_id: UUID, blockchain_address: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: smart_contract_config_id, blockchain_address"""

    blockchain_address_norm = (blockchain_address or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:smart_contract:{smart_contract_config_id}:{blockchain_address_norm}")


def stable_smart_contract_config_id(*, name: str, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name, type"""

    name_norm = (name or "").casefold().strip()
    type_norm = (type or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:smart_contract_config:{name_norm}:{type_norm}")


def stable_smart_contract_member_id(*, smart_contract_id: UUID, finance_entity_id: UUID, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: smart_contract_id, finance_entity_id, type"""

    type_norm = (type or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:smart_contract_member:{smart_contract_id}:{finance_entity_id}:{type_norm}")


def stable_smart_contract_permit_id(*, smart_contract_id: UUID, finance_entity_id: UUID, permit_nonce: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: smart_contract_id, finance_entity_id, permit_nonce"""

    return uuid5(NS_ECONOMY, f"aware:smart_contract_permit:{smart_contract_id}:{finance_entity_id}:{permit_nonce}")


def stable_smart_contract_reservation_id(*, smart_contract_permit_id: UUID, op_nonce: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: smart_contract_permit_id, op_nonce"""

    return uuid5(NS_ECONOMY, f"aware:smart_contract_reservation:{smart_contract_permit_id}:{op_nonce}")


def stable_smart_contract_settlement_id(*, smart_contract_reservation_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: smart_contract_reservation_id"""

    return uuid5(NS_ECONOMY, f"aware:smart_contract_settlement:{smart_contract_reservation_id}")


def stable_transaction_id(*, coin_id: UUID, target_wallet_public_id: UUID, capital_origin_id: UUID, nonce: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: coin_id, target_wallet_public_id, capital_origin_id, nonce"""

    return uuid5(NS_ECONOMY, f"aware:transaction:{coin_id}:{target_wallet_public_id}:{capital_origin_id}:{nonce}")


def stable_transaction_external_id(*, provider_config_id: UUID, provider_event_id: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: provider_config_id, provider_event_id"""

    provider_event_id_norm = (provider_event_id or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:transaction_external:{provider_config_id}:{provider_event_id_norm}")


def stable_transaction_external_method_id(*, finance_entity_id: UUID, provider: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: finance_entity_id, provider"""

    provider_norm = (provider or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:transaction_external_method:{finance_entity_id}:{provider_norm}")


def stable_transaction_intent_id(
    *, provider_config_id: UUID, recipient_finance_entity_id: UUID, funding_intent_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: provider_config_id, recipient_finance_entity_id, funding_intent_key"""

    funding_intent_key_norm = (funding_intent_key or "").casefold().strip()
    return uuid5(
        NS_ECONOMY,
        f"aware:transaction_intent:{provider_config_id}:{recipient_finance_entity_id}:{funding_intent_key_norm}",
    )


def stable_transaction_intent_external_expiration_id(*, provider_config_id: UUID, provider_event_id: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: provider_config_id, provider_event_id"""

    provider_event_id_norm = (provider_event_id or "").casefold().strip()
    return uuid5(
        NS_ECONOMY, f"aware:transaction_intent_external_expiration:{provider_config_id}:{provider_event_id_norm}"
    )


def stable_wallet_id(*, private_key_encrypted: str, public_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: private_key_encrypted, public_key"""

    private_key_encrypted_norm = (private_key_encrypted or "").casefold().strip()
    public_key_norm = (public_key or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:wallet:{private_key_encrypted_norm}:{public_key_norm}")


def stable_wallet_balance_id(*, wallet_id: UUID, coin_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: wallet_id, coin_id"""

    return uuid5(NS_ECONOMY, f"aware:wallet_balance:{wallet_id}:{coin_id}")


def stable_wallet_external_ingress_application_id(*, transaction_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: transaction_id"""

    return uuid5(NS_ECONOMY, f"aware:wallet_external_ingress_application:{transaction_id}")


def stable_wallet_private_id(*, private_key_encrypted: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: private_key_encrypted"""

    private_key_encrypted_norm = (private_key_encrypted or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:wallet_private:{private_key_encrypted_norm}")


def stable_wallet_public_id(*, public_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: public_key"""

    public_key_norm = (public_key or "").casefold().strip()
    return uuid5(NS_ECONOMY, f"aware:wallet_public:{public_key_norm}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "06ea02ba-a6ed-5c0d-b81d-cb1829d491ae": ("stable_economy_package_id", ("name",)),
    "073d359c-f731-551d-8e12-2159a3733325": (
        "stable_smart_contract_member_id",
        ("smart_contract_id", "finance_entity_id", "type"),
    ),
    "104052ea-dde3-50cf-bc6f-3b9e4f568817": ("stable_smart_contract_config_id", ("name", "type")),
    "170c7a08-9f31-5e3c-961f-68dbbacc0add": ("stable_escrow_id", ("wallet_public_id", "op_nonce")),
    "1e46c62a-10da-55f3-ab3b-8bd68e31bc28": ("stable_capital_conversion_quote_id", ("quote_key",)),
    "27a37b68-9357-579a-bd5c-7e5ddf7a38ce": ("stable_price_id", ("coin_id", "name", "type")),
    "53f98431-f5a3-5a10-b41b-44d2297a48e2": ("stable_wallet_id", ("private_key_encrypted", "public_key")),
    "5cf65cfb-1cad-5e35-8aa6-3ff5afd94f64": ("stable_rate_snapshot_id", ("price_schedule_id", "snapshot_key")),
    "5f450b4e-0ec9-5116-bd0d-21859d742aae": ("stable_economy_analytic_id", ("key",)),
    "629ea9aa-8046-58e0-b331-3f5e7730d04b": ("stable_finance_entity_id", ("identity_id",)),
    "6fd40c3f-7390-52f3-8eff-3722387bac15": (
        "stable_transaction_id",
        ("coin_id", "target_wallet_public_id", "capital_origin_id", "nonce"),
    ),
    "899c15f3-dee6-5e25-ab71-9b464a997b52": (
        "stable_price_schedule_id",
        ("price_id", "pricing_policy_id", "name", "version"),
    ),
    "93575c8f-ef80-50af-bbca-40952c9560eb": ("stable_coin_id", ("symbol",)),
    "94a43712-6f80-518d-89f0-474dbda675ff": ("stable_wallet_private_id", ("private_key_encrypted",)),
    "95676713-975a-54a1-91c3-466b51e4fd7d": (
        "stable_transaction_intent_id",
        ("provider_config_id", "recipient_finance_entity_id", "funding_intent_key"),
    ),
    "95a1eda3-c638-5021-9990-29eddf1b1ba1": ("stable_wallet_balance_id", ("wallet_id", "coin_id")),
    "9b2faa01-3598-5014-9eb9-875b5e552fce": (
        "stable_external_capital_provider_route_id",
        ("external_capital_provider_config_id", "target_coin_id", "route_key"),
    ),
    "a28b7bdf-314d-51a1-8b2d-8573b69015cf": (
        "stable_smart_contract_permit_id",
        ("smart_contract_id", "finance_entity_id", "permit_nonce"),
    ),
    "a2b9c03d-35ee-5b92-a4a9-70bf09a3ac19": ("stable_smart_contract_settlement_id", ("smart_contract_reservation_id",)),
    "a3cbc0ea-ef41-542d-941a-fea0df01ea04": ("stable_price_reservation_id", ("rate_snapshot_id", "reservation_key")),
    "aa00289a-0a5c-5d54-b6a4-d1b875790d76": (
        "stable_external_capital_provider_config_id",
        ("provider_finance_entity_id", "provider_key"),
    ),
    "b4a7fedb-0f47-5610-b3ea-59faaf27132e": (
        "stable_smart_contract_id",
        ("smart_contract_config_id", "blockchain_address"),
    ),
    "cc74b758-e5ef-5b97-950c-e2b3cc497ca5": (
        "stable_provider_lifecycle_receipt_id",
        ("provider_finance_entity_id", "provider_lifecycle_effect_key", "provider_lifecycle_object_id", "provider_key"),
    ),
    "d867c40d-d586-5247-83af-3836a5fe1e12": (
        "stable_smart_contract_reservation_id",
        ("smart_contract_permit_id", "op_nonce"),
    ),
    "f528cb16-4a79-5d66-a40e-5c637b4c07dd": ("stable_pricing_policy_id", ("name", "version")),
    "f8cb47c2-6090-59c0-bde6-c8990f2b7a7b": ("stable_wallet_public_id", ("public_key",)),
    "fe8f9cbb-e01d-5884-bba3-5cccb4b50533": (
        "stable_transaction_external_id",
        ("provider_config_id", "provider_event_id"),
    ),
}

__all__ = [
    "stable_capital_conversion_quote_id",
    "stable_coin_id",
    "stable_coin_exchange_rate_id",
    "stable_economy_analytic_id",
    "stable_economy_analytic_execution_id",
    "stable_economy_analytic_execution_metric_id",
    "stable_economy_analytic_metric_id",
    "stable_economy_package_id",
    "stable_escrow_id",
    "stable_external_capital_provider_config_id",
    "stable_external_capital_provider_route_id",
    "stable_finance_entity_id",
    "stable_price_id",
    "stable_price_reservation_id",
    "stable_price_schedule_id",
    "stable_pricing_policy_id",
    "stable_provider_lifecycle_receipt_id",
    "stable_rate_snapshot_id",
    "stable_smart_contract_id",
    "stable_smart_contract_config_id",
    "stable_smart_contract_member_id",
    "stable_smart_contract_permit_id",
    "stable_smart_contract_reservation_id",
    "stable_smart_contract_settlement_id",
    "stable_transaction_id",
    "stable_transaction_external_id",
    "stable_transaction_external_method_id",
    "stable_transaction_intent_id",
    "stable_transaction_intent_external_expiration_id",
    "stable_wallet_id",
    "stable_wallet_balance_id",
    "stable_wallet_external_ingress_application_id",
    "stable_wallet_private_id",
    "stable_wallet_public_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
