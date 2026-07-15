from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_service_ontology_dto.service.service import Service
    from aware_service_ontology_dto.service.service_config_api import ServiceConfigApi
    from aware_service_ontology_dto.service.service_config_code_package_config import ServiceConfigCodePackageConfig
    from aware_service_ontology_dto.service.service_config_experience import ServiceConfigExperience
    from aware_service_ontology_dto.service.service_contract_config import ServiceContractConfig
    from aware_service_ontology_dto.service.service_operation_config import ServiceOperationConfig


class ServiceConfig(BaseModel):
    # Relationships
    apis: list[ServiceConfigApi] = Field(default_factory=list)
    contract_configs: list[ServiceContractConfig] = Field(default_factory=list)
    code_package_configs: list[ServiceConfigCodePackageConfig] = Field(default_factory=list)
    experiences: list[ServiceConfigExperience] = Field(default_factory=list)
    service_operation_configs: list[ServiceOperationConfig] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    name: str
