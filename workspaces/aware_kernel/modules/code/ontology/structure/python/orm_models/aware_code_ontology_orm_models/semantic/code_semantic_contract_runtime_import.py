from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class CodeSemanticContractRuntimeImport(ORMModel):
    # Attributes
    capabilities: list[str] = Field(default_factory=list)
    import_role: str = Field(default="semantic_contract")
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    provider_key: str
    required: bool = Field(default=True)
    semantic_contract_module: str
    status: str = Field(default="active")

    # Foreign Keys
    code_semantic_contract_profile_package_id: UUID = Field(
        description="Foreign key for CodeSemanticContractProfilePackage.runtime_imports"
    )
