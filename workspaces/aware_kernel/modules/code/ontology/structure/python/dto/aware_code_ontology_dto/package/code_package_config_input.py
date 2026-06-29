from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.package.code_package_enums import CodePackageConfigInputKind


class CodePackageConfigInput(BaseModel):
    # Attributes
    input_key: str
    kind: CodePackageConfigInputKind
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_family: str | None = Field(default=None)
    semantic_kind: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)
