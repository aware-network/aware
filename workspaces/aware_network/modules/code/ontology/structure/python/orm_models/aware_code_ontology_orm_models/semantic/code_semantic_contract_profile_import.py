from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.semantic.code_semantic_contract_profile import CodeSemanticContractProfile


class CodeSemanticContractProfileImport(ORMModel):
    # Relationships
    imported_profile: CodeSemanticContractProfile | None = Field(default=None)

    # Attributes
    import_key: str
    required: bool = Field(default=True)
    status: str = Field(default="active")

    # Foreign Keys
    code_semantic_contract_profile_id: UUID = Field(
        description="Foreign key for CodeSemanticContractProfile.profile_imports"
    )
    imported_profile_id: UUID = Field(description="Foreign key for CodeSemanticContractProfileImport.imported_profile")
