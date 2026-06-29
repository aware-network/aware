from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_code_ontology_dto.semantic.code_semantic_contract_profile import CodeSemanticContractProfile
    from aware_code_ontology_dto.semantic.code_semantic_contract_runtime_import import CodeSemanticContractRuntimeImport


class CodeSemanticContractProfilePackage(BaseModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)
    semantic_contract_profile: CodeSemanticContractProfile | None = Field(default=None)
    runtime_imports: list[CodeSemanticContractRuntimeImport] = Field(default_factory=list)

    # Attributes
    manifest_relative_path: str | None = Field(default=None)
    profile_key: str
    profile_package_key: str
    runtime_import_mode: str = Field(default="dynamic_contract_module")
    runtime_import_required: bool = Field(default=True)
    source_workspace_handle: str | None = Field(default=None)
    status: str = Field(default="active")
