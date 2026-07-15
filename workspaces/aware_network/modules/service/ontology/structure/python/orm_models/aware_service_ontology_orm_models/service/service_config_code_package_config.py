from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import ServiceConfigCodePackageConfigCardinality

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package_config import CodePackageConfig


class ServiceConfigCodePackageConfig(ORMModel):
    # Relationships
    code_package_config: CodePackageConfig | None = Field(default=None, exclude=True)

    # Attributes
    slot_key: str
    cardinality: ServiceConfigCodePackageConfigCardinality = Field(
        default=ServiceConfigCodePackageConfigCardinality.many
    )
    required: bool = Field(default=False)
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.code_package_configs")
    code_package_config_id: UUID = Field(
        description="Foreign key for ServiceConfigCodePackageConfig.code_package_config"
    )
