from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Economy Ontology
from aware_economy_ontology.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
    ExternalCapitalProviderStatus,
    ExternalCapitalRouteStatus,
)
from aware_economy_ontology.external_capital.external_capital_provider_config import ExternalCapitalProviderConfig
from aware_economy_ontology.external_capital.external_capital_provider_route import ExternalCapitalProviderRoute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Ontology
from aware_economy_ontology.stable_ids import stable_external_capital_provider_config_id

# Orm
from aware_orm.session.current_session_ctx import current_session

# --- AWARE: USER_IMPORTS END


async def build(
    provider_finance_entity_id: UUID,
    provider_key: str,
    label: str | None = None,
    status: ExternalCapitalProviderStatus = ExternalCapitalProviderStatus.active,
    additional_metadata: JsonObject | None = JsonObject(),
) -> ExternalCapitalProviderConfig:
    """
    Creates one Economy-owned external-capital provider configuration.

    The provider key selects an Experience connector provider at dispatch
    time. This object owns economic coordinates and supported routes only;
    it never stores provider endpoints or secrets.
    """

    # --- AWARE: LOGIC START build
    provider_key = provider_key.strip().casefold()
    if not provider_key:
        raise ValueError("external_capital_provider_config.build requires provider_key")

    label = label.strip() if label is not None else None
    if label == "":
        label = None

    config_id = stable_external_capital_provider_config_id(
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key=provider_key,
    )
    session = current_session()
    existing = session.imap_get(ExternalCapitalProviderConfig, config_id) if session is not None else None
    if existing is not None:
        if existing.provider_finance_entity_id != provider_finance_entity_id:
            raise ValueError("external_capital_provider_config.build existing provider_finance_entity_id mismatch")
        if existing.provider_key != provider_key:
            raise ValueError("external_capital_provider_config.build existing provider_key mismatch")
        if existing.label != label or existing.status != status:
            raise ValueError("external_capital_provider_config.build cannot redefine an existing provider config")
        return existing

    return ExternalCapitalProviderConfig(
        id=config_id,
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key=provider_key,
        label=label,
        status=status,
        additional_metadata=(additional_metadata if additional_metadata is not None else JsonObject({})),
    )
    # --- AWARE: LOGIC END build


async def add_route(
    external_capital_provider_config: ExternalCapitalProviderConfig,
    route_key: str,
    target_coin_id: UUID,
    external_currency: str,
    external_minor_unit_exponent: int,
    conversion_mode: ExternalCapitalConversionMode = ExternalCapitalConversionMode.direct_denomination,
    min_external_amount_minor: int | None = None,
    max_external_amount_minor: int | None = None,
    status: ExternalCapitalRouteStatus = ExternalCapitalRouteStatus.active,
    additional_metadata: JsonObject | None = JsonObject(),
) -> ExternalCapitalProviderRoute:
    """
    Adds one provider-neutral external-capital route.

    V0 accepts direct-denomination routes only. Cross-currency conversion
    requires a later authenticated capital-rate source.
    """

    # --- AWARE: LOGIC START add_route
    route_key = route_key.strip().casefold()
    if not route_key:
        raise ValueError("external_capital_provider_config.add_route requires route_key")

    for existing in external_capital_provider_config.routes:
        if existing.route_key.strip().casefold() != route_key:
            continue
        expected = {
            "target_coin_id": target_coin_id,
            "external_currency": external_currency.strip().upper(),
            "external_minor_unit_exponent": external_minor_unit_exponent,
            "conversion_mode": conversion_mode,
            "min_external_amount_minor": min_external_amount_minor,
            "max_external_amount_minor": max_external_amount_minor,
            "status": status,
        }
        actual = {
            "target_coin_id": existing.target_coin_id,
            "external_currency": existing.external_currency,
            "external_minor_unit_exponent": existing.external_minor_unit_exponent,
            "conversion_mode": existing.conversion_mode,
            "min_external_amount_minor": existing.min_external_amount_minor,
            "max_external_amount_minor": existing.max_external_amount_minor,
            "status": existing.status,
        }
        if actual != expected:
            raise ValueError("external_capital_provider_config.add_route cannot redefine an existing route_key")
        return existing

    route = await ExternalCapitalProviderRoute.build_via_external_capital_provider_config(
        external_capital_provider_config_id=external_capital_provider_config.id,
        route_key=route_key,
        target_coin_id=target_coin_id,
        external_currency=external_currency,
        external_minor_unit_exponent=external_minor_unit_exponent,
        conversion_mode=conversion_mode,
        min_external_amount_minor=min_external_amount_minor,
        max_external_amount_minor=max_external_amount_minor,
        status=status,
        additional_metadata=additional_metadata,
    )
    external_capital_provider_config.routes.append(route)
    return route
    # --- AWARE: LOGIC END add_route
