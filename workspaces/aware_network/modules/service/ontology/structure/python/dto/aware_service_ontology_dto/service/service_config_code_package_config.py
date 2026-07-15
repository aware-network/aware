from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import ServiceConfigCodePackageConfigCardinality

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package_config import CodePackageConfig


class ServiceConfigCodePackageConfig(BaseModel):
    # Relationships
    code_package_config: CodePackageConfig | None = Field(default=None)

    # Attributes
    slot_key: str
    cardinality: ServiceConfigCodePackageConfigCardinality = Field(
        default=ServiceConfigCodePackageConfigCardinality.many
    )
    required: bool = Field(default=False)
    description: str | None = Field(default=None)
