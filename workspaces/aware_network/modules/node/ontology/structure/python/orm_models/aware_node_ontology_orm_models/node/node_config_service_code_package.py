from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_service_ontology_orm_models.service.service_config_code_package_config import (
        ServiceConfigCodePackageConfig,
    )


class NodeConfigServiceCodePackage(ORMModel):
    # Relationships
    service_config_code_package_config: ServiceConfigCodePackageConfig | None = Field(default=None, exclude=True)
    code_package: CodePackage | None = Field(default=None, exclude=True)

    # Attributes
    slot_key: str
    package_name: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    description: str | None = Field(default=None)

    # Foreign Keys
    node_config_service_target_id: UUID = Field(description="Foreign key for NodeConfigServiceTarget.code_packages")
    service_config_code_package_config_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigServiceCodePackage.service_config_code_package_config"
    )
    code_package_id: UUID | None = Field(
        default=None, description="Foreign key for NodeConfigServiceCodePackage.code_package"
    )
