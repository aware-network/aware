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
    ExternalCapitalRouteStatus,
)
from aware_economy_ontology.external_capital.external_capital_provider_route import ExternalCapitalProviderRoute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Ontology
from aware_economy_ontology.stable_ids import (
    stable_coin_id,
    stable_external_capital_provider_route_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_external_capital_provider_config(
    external_capital_provider_config_id: UUID,
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
    Creates one immutable route declaration under a provider config.

    Route updates require a new route key so existing funding quotes remain
    auditable against the route they accepted.
    """

    # --- AWARE: LOGIC START build_via_external_capital_provider_config
    route_key = route_key.strip().casefold()
    if not route_key:
        raise ValueError(
            "external_capital_provider_route.build_via_external_capital_provider_config requires route_key"
        )

    external_currency = external_currency.strip().upper()
    if len(external_currency) != 3 or not external_currency.isascii() or not external_currency.isalpha():
        raise ValueError("external_capital_provider_route requires a three-letter ASCII external_currency")
    if external_minor_unit_exponent < 0 or external_minor_unit_exponent > 18:
        raise ValueError("external_capital_provider_route requires external_minor_unit_exponent between 0 and 18")
    if conversion_mode != ExternalCapitalConversionMode.direct_denomination:
        raise ValueError("external_capital_provider_route supports direct_denomination only")
    if target_coin_id != stable_coin_id(symbol=external_currency):
        raise ValueError(
            "external_capital_provider_route direct denomination requires target Coin to match external_currency"
        )
    if min_external_amount_minor is not None and min_external_amount_minor <= 0:
        raise ValueError("external_capital_provider_route min_external_amount_minor must be positive")
    if max_external_amount_minor is not None and max_external_amount_minor <= 0:
        raise ValueError("external_capital_provider_route max_external_amount_minor must be positive")
    if (
        min_external_amount_minor is not None
        and max_external_amount_minor is not None
        and max_external_amount_minor < min_external_amount_minor
    ):
        raise ValueError(
            "external_capital_provider_route max_external_amount_minor must be >= min_external_amount_minor"
        )

    route_id = stable_external_capital_provider_route_id(
        external_capital_provider_config_id=external_capital_provider_config_id,
        target_coin_id=target_coin_id,
        route_key=route_key,
    )
    return ExternalCapitalProviderRoute(
        id=route_id,
        external_capital_provider_config_id=external_capital_provider_config_id,
        route_key=route_key,
        target_coin_id=target_coin_id,
        external_currency=external_currency,
        external_minor_unit_exponent=external_minor_unit_exponent,
        conversion_mode=conversion_mode,
        min_external_amount_minor=min_external_amount_minor,
        max_external_amount_minor=max_external_amount_minor,
        status=status,
        additional_metadata=(additional_metadata if additional_metadata is not None else JsonObject({})),
    )
    # --- AWARE: LOGIC END build_via_external_capital_provider_config
