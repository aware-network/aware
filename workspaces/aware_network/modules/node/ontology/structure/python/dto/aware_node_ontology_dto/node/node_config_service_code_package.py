from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_service_ontology_dto.service.service_config_code_package_config import ServiceConfigCodePackageConfig


class NodeConfigServiceCodePackage(BaseModel):
    # Relationships
    service_config_code_package_config: ServiceConfigCodePackageConfig | None = Field(default=None)
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    slot_key: str
    package_name: str
    language: CodeLanguage = Field(default=CodeLanguage.aware)
    description: str | None = Field(default=None)
