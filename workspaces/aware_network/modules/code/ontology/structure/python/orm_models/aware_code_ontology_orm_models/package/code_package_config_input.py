from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.package.code_package_enums import CodePackageConfigInputKind

# Orm
from aware_orm.models.orm_model import ORMModel


class CodePackageConfigInput(ORMModel):
    # Attributes
    input_key: str
    kind: CodePackageConfigInputKind
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_family: str | None = Field(default=None)
    semantic_kind: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.inputs")
