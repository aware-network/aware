from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.package.code_package_enums import CodePackageConfigOutputKind


class CodePackageConfigOutput(BaseModel):
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
