from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
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
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.smart_contract.smart_contract_config import SmartContractConfig


class ServiceCommercialProfile(ORMModel):
    # Relationships
    default_smart_contract_config: SmartContractConfig | None = Field(default=None, exclude=True)
    producer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)

    # Attributes
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    service_id: UUID | None = Field(default=None, description="Foreign key for Service.commercial_profile")
    default_smart_contract_config_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceCommercialProfile.default_smart_contract_config"
    )
    producer_finance_entity_id: UUID = Field(
        description="Foreign key for ServiceCommercialProfile.producer_finance_entity"
    )

    async def set_terms(
        self,
        producer_finance_entity_id: UUID,
        default_smart_contract_config_id: UUID | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceCommercialProfile:
        """Updates the live producer-side commercial profile for future contracts."""

        payload = {
            "producer_finance_entity_id": producer_finance_entity_id,
            "default_smart_contract_config_id": default_smart_contract_config_id,
            "metadata_json": metadata_json,
        }
        result = await invoke_instance(orm_model=self, function_name="set_terms", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceCommercialProfile):
            return value
        return ServiceCommercialProfile.validate_invocation_value(value)

    @classmethod
    async def build_via_service(
        cls,
        service_id: UUID,
        producer_finance_entity_id: UUID,
        default_smart_contract_config_id: UUID | None = None,
        metadata_json: JsonObject | None = {},
    ) -> ServiceCommercialProfile:
        """
        Creates or ensures the live producer-side commercial profile under one Service.

        Contract:
        - Lives on the Service containment rail as current commercial truth.
        - Future ServiceContract receipts may snapshot its producer-side terms without depending
          on live profile mutation for settlement correctness.
        """

        payload = {
            "service_id": service_id,
            "producer_finance_entity_id": producer_finance_entity_id,
            "default_smart_contract_config_id": default_smart_contract_config_id,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceCommercialProfile):
            return value
        return ServiceCommercialProfile.validate_invocation_value(value)


class ServiceCommercialProfileSetTermsInput(BaseModel):
    producer_finance_entity_id: UUID
    default_smart_contract_config_id: UUID | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceCommercialProfileSetTermsOutput(BaseModel):
    value: ServiceCommercialProfile


class ServiceCommercialProfileBuildViaServiceInput(BaseModel):
    service_id: UUID = Field(description="Foreign key for Service.commercial_profile")
    producer_finance_entity_id: UUID
    default_smart_contract_config_id: UUID | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ServiceCommercialProfileBuildViaServiceOutput(BaseModel):
    value: ServiceCommercialProfile


FUNCTIONS = {
    "ServiceCommercialProfile": {
        "set_terms": {
            "canonical": {
                "name": "set_terms",
                "description": "Updates the live producer-side commercial profile for future contracts.",
                "is_constructor": False,
            },
            "input": ServiceCommercialProfileSetTermsInput,
            "output": ServiceCommercialProfileSetTermsOutput,
        },
        "build_via_service": {
            "canonical": {
                "name": "build_via_service",
                "description": "Creates or ensures the live producer-side commercial profile under one Service.\n\nContract:\n- Lives on the Service containment rail as current commercial truth.\n- Future ServiceContract receipts may snapshot its producer-side terms without depending\n  on live profile mutation for settlement correctness.",
                "is_constructor": True,
            },
            "input": ServiceCommercialProfileBuildViaServiceInput,
            "output": ServiceCommercialProfileBuildViaServiceOutput,
        },
    },
}

__all__ = [
    "ServiceCommercialProfile",
    "ServiceCommercialProfileSetTermsInput",
    "ServiceCommercialProfileSetTermsOutput",
    "ServiceCommercialProfileBuildViaServiceInput",
    "ServiceCommercialProfileBuildViaServiceOutput",
    "FUNCTIONS",
]
