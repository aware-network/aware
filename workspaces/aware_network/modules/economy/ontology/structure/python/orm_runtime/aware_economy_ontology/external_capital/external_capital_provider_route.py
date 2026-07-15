from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
    ExternalCapitalRouteStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin


class ExternalCapitalProviderRoute(ORMModel):
    # Relationships
    target_coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    conversion_mode: ExternalCapitalConversionMode = Field(default=ExternalCapitalConversionMode.direct_denomination)
    external_currency: str
    external_minor_unit_exponent: int
    max_external_amount_minor: int | None = Field(default=None)
    min_external_amount_minor: int | None = Field(default=None)
    route_key: str
    status: ExternalCapitalRouteStatus = Field(default=ExternalCapitalRouteStatus.active)

    # Foreign Keys
    external_capital_provider_config_id: UUID = Field(
        description="Foreign key for ExternalCapitalProviderConfig.routes"
    )
    target_coin_id: UUID = Field(description="Foreign key for ExternalCapitalProviderRoute.target_coin")

    @classmethod
    async def build_via_external_capital_provider_config(
        cls,
        external_capital_provider_config_id: UUID,
        route_key: str,
        target_coin_id: UUID,
        external_currency: str,
        external_minor_unit_exponent: int,
        conversion_mode: ExternalCapitalConversionMode = ExternalCapitalConversionMode.direct_denomination,
        min_external_amount_minor: int | None = None,
        max_external_amount_minor: int | None = None,
        status: ExternalCapitalRouteStatus = ExternalCapitalRouteStatus.active,
        additional_metadata: JsonObject | None = {},
    ) -> ExternalCapitalProviderRoute:
        """
        Creates one immutable route declaration under a provider config.

        Route updates require a new route key so existing funding quotes remain
        auditable against the route they accepted.
        """

        payload = {
            "external_capital_provider_config_id": external_capital_provider_config_id,
            "route_key": route_key,
            "target_coin_id": target_coin_id,
            "external_currency": external_currency,
            "external_minor_unit_exponent": external_minor_unit_exponent,
            "conversion_mode": conversion_mode,
            "min_external_amount_minor": min_external_amount_minor,
            "max_external_amount_minor": max_external_amount_minor,
            "status": status,
            "additional_metadata": additional_metadata,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_external_capital_provider_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExternalCapitalProviderRoute):
            return value
        return ExternalCapitalProviderRoute.validate_invocation_value(value)


class ExternalCapitalProviderRouteBuildViaExternalCapitalProviderConfigInput(BaseModel):
    external_capital_provider_config_id: UUID = Field(
        description="Foreign key for ExternalCapitalProviderConfig.routes"
    )
    route_key: str
    target_coin_id: UUID
    external_currency: str
    external_minor_unit_exponent: int
    conversion_mode: ExternalCapitalConversionMode = Field(default=ExternalCapitalConversionMode.direct_denomination)
    min_external_amount_minor: int | None = Field(default=None)
    max_external_amount_minor: int | None = Field(default=None)
    status: ExternalCapitalRouteStatus = Field(default=ExternalCapitalRouteStatus.active)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class ExternalCapitalProviderRouteBuildViaExternalCapitalProviderConfigOutput(BaseModel):
    value: ExternalCapitalProviderRoute


FUNCTIONS = {
    "ExternalCapitalProviderRoute": {
        "build_via_external_capital_provider_config": {
            "canonical": {
                "name": "build_via_external_capital_provider_config",
                "description": "Creates one immutable route declaration under a provider config.\n\nRoute updates require a new route key so existing funding quotes remain\nauditable against the route they accepted.",
                "is_constructor": True,
            },
            "input": ExternalCapitalProviderRouteBuildViaExternalCapitalProviderConfigInput,
            "output": ExternalCapitalProviderRouteBuildViaExternalCapitalProviderConfigOutput,
        },
    },
}

__all__ = [
    "ExternalCapitalProviderRoute",
    "ExternalCapitalProviderRouteBuildViaExternalCapitalProviderConfigInput",
    "ExternalCapitalProviderRouteBuildViaExternalCapitalProviderConfigOutput",
    "FUNCTIONS",
]
