from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.package.code_package_enums import CodePackageConfigRuntimeContextKind

# Orm
from aware_orm.models.orm_model import ORMModel


class CodePackageConfigRuntimeContext(ORMModel):
    # Attributes
    context_key: str
    kind: CodePackageConfigRuntimeContextKind
    package_name: str | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.runtime_contexts")
