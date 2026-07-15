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
    ExternalCapitalProviderStatus,
    ExternalCapitalRouteStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology.external_capital.external_capital_provider_route import ExternalCapitalProviderRoute
    from aware_economy_ontology.finance.finance_entity import FinanceEntity


class ExternalCapitalProviderConfig(ORMModel):
    # Relationships
    provider_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    routes: list[ExternalCapitalProviderRoute] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    label: str | None = Field(default=None)
    provider_key: str
    status: ExternalCapitalProviderStatus = Field(default=ExternalCapitalProviderStatus.active)

    # Foreign Keys
    provider_finance_entity_id: UUID = Field(
        description="Foreign key for ExternalCapitalProviderConfig.provider_finance_entity"
    )

    @classmethod
    async def build(
        cls,
        provider_finance_entity_id: UUID,
        provider_key: str,
        label: str | None = None,
        status: ExternalCapitalProviderStatus = ExternalCapitalProviderStatus.active,
        additional_metadata: JsonObject | None = {},
    ) -> ExternalCapitalProviderConfig:
        """
        Creates one Economy-owned external-capital provider configuration.

        The provider key selects an Experience connector provider at dispatch
        time. This object owns economic coordinates and supported routes only;
        it never stores provider endpoints or secrets.
        """

        payload = {
            "provider_finance_entity_id": provider_finance_entity_id,
            "provider_key": provider_key,
            "label": label,
            "status": status,
            "additional_metadata": additional_metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExternalCapitalProviderConfig):
            return value
        return ExternalCapitalProviderConfig.validate_invocation_value(value)

    async def add_route(
        self,
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
        Adds one provider-neutral external-capital route.

        V0 accepts direct-denomination routes only. Cross-currency conversion
        requires a later authenticated capital-rate source.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="add_route", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.external_capital.external_capital_provider_route import ExternalCapitalProviderRoute

        if isinstance(value, ExternalCapitalProviderRoute):
            return value
        return ExternalCapitalProviderRoute.validate_invocation_value(value)


class ExternalCapitalProviderConfigBuildInput(BaseModel):
    provider_finance_entity_id: UUID
    provider_key: str
    label: str | None = Field(default=None)
    status: ExternalCapitalProviderStatus = Field(default=ExternalCapitalProviderStatus.active)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class ExternalCapitalProviderConfigBuildOutput(BaseModel):
    value: ExternalCapitalProviderConfig


class ExternalCapitalProviderConfigAddRouteInput(BaseModel):
    route_key: str
    target_coin_id: UUID
    external_currency: str
    external_minor_unit_exponent: int
    conversion_mode: ExternalCapitalConversionMode = Field(default=ExternalCapitalConversionMode.direct_denomination)
    min_external_amount_minor: int | None = Field(default=None)
    max_external_amount_minor: int | None = Field(default=None)
    status: ExternalCapitalRouteStatus = Field(default=ExternalCapitalRouteStatus.active)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class ExternalCapitalProviderConfigAddRouteOutput(BaseModel):
    value: ExternalCapitalProviderRoute


FUNCTIONS = {
    "ExternalCapitalProviderConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates one Economy-owned external-capital provider configuration.\n\nThe provider key selects an Experience connector provider at dispatch\ntime. This object owns economic coordinates and supported routes only;\nit never stores provider endpoints or secrets.",
                "is_constructor": True,
            },
            "input": ExternalCapitalProviderConfigBuildInput,
            "output": ExternalCapitalProviderConfigBuildOutput,
        },
        "add_route": {
            "canonical": {
                "name": "add_route",
                "description": "Adds one provider-neutral external-capital route.\n\nV0 accepts direct-denomination routes only. Cross-currency conversion\nrequires a later authenticated capital-rate source.",
                "is_constructor": False,
            },
            "input": ExternalCapitalProviderConfigAddRouteInput,
            "output": ExternalCapitalProviderConfigAddRouteOutput,
        },
    },
}

__all__ = [
    "ExternalCapitalProviderConfig",
    "ExternalCapitalProviderConfigBuildInput",
    "ExternalCapitalProviderConfigBuildOutput",
    "ExternalCapitalProviderConfigAddRouteInput",
    "ExternalCapitalProviderConfigAddRouteOutput",
    "FUNCTIONS",
]
