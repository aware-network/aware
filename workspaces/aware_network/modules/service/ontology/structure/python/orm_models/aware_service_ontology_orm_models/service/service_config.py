from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_service_ontology_orm_models.service.service import Service
    from aware_service_ontology_orm_models.service.service_config_api import ServiceConfigApi
    from aware_service_ontology_orm_models.service.service_config_code_package_config import (
        ServiceConfigCodePackageConfig,
    )
    from aware_service_ontology_orm_models.service.service_config_experience import ServiceConfigExperience
    from aware_service_ontology_orm_models.service.service_contract_config import ServiceContractConfig
    from aware_service_ontology_orm_models.service.service_operation_config import ServiceOperationConfig


class ServiceConfig(ORMModel):
    # Relationships
    apis: list[ServiceConfigApi] = Field(default_factory=list, exclude=True)
    contract_configs: list[ServiceContractConfig] = Field(default_factory=list, exclude=True)
    code_package_configs: list[ServiceConfigCodePackageConfig] = Field(default_factory=list)
    experiences: list[ServiceConfigExperience] = Field(default_factory=list, exclude=True)
    service_operation_configs: list[ServiceOperationConfig] = Field(default_factory=list, exclude=True)
    services: list[Service] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    name: str
