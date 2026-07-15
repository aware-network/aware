from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.semantic.code_semantic_contract_profile import CodeSemanticContractProfile


class CodeSemanticContractProfileImport(BaseModel):
    # Relationships
    imported_profile: CodeSemanticContractProfile | None = Field(default=None)

    # Attributes
    import_key: str
    required: bool = Field(default=True)
    status: str = Field(default="active")
