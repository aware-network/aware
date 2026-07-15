from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.semantic.code_semantic_contract_profile_import import CodeSemanticContractProfileImport
    from aware_code_ontology_dto.semantic.code_semantic_provider_registration import CodeSemanticProviderRegistration


class CodeSemanticContractProfile(BaseModel):
    # Relationships
    semantic_provider_registrations: list[CodeSemanticProviderRegistration] = Field(default_factory=list)
    profile_imports: list[CodeSemanticContractProfileImport] = Field(default_factory=list)

    # Attributes
    profile_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str = Field(default="active")
