from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.module.code_module import CodeModule
    from aware_code_ontology_dto.semantic.code_semantic_package_binding import CodeSemanticPackageBinding


class CodeSemanticProviderRegistration(BaseModel):
    # Relationships
    code_module: CodeModule | None = Field(default=None)
    semantic_package_bindings: list[CodeSemanticPackageBinding] = Field(default_factory=list)

    # Attributes
    provider_key: str
    semantic_contract_module: str | None = Field(default=None)
    status: str = Field(default="registered")
