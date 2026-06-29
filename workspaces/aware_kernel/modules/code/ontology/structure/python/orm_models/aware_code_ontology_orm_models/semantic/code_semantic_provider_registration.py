from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.module.code_module import CodeModule
    from aware_code_ontology_orm_models.semantic.code_semantic_package_binding import CodeSemanticPackageBinding


class CodeSemanticProviderRegistration(ORMModel):
    # Relationships
    code_module: CodeModule | None = Field(default=None)
    semantic_package_bindings: list[CodeSemanticPackageBinding] = Field(default_factory=list)

    # Attributes
    provider_key: str
    semantic_contract_module: str | None = Field(default=None)
    status: str = Field(default="registered")

    # Foreign Keys
    code_module_id: UUID = Field(description="Foreign key for CodeSemanticProviderRegistration.code_module")
