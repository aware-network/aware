from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.package.code_package_enums import CodePackageConfigRuntimeContextKind


class CodePackageConfigRuntimeContext(BaseModel):
    # Attributes
    context_key: str
    kind: CodePackageConfigRuntimeContextKind
    package_name: str | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)
