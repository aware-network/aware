from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.package.code_package_enums import CodePackageConfigOutputKind

# Orm
from aware_orm.models.orm_model import ORMModel


class CodePackageConfigOutput(ORMModel):
    # Attributes
    output_key: str
    kind: CodePackageConfigOutputKind
    producer_key: str | None = Field(default=None)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_output_key: str | None = Field(default=None)
    target_provider_key: str | None = Field(default=None)
    target_input_key: str | None = Field(default=None)
    target_semantic_owner: str | None = Field(default=None)
    target_package_family: str | None = Field(default=None)
    target_semantic_kind: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.outputs")
