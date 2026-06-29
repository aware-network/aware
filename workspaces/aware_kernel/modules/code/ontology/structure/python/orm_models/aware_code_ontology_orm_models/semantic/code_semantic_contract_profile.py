from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.semantic.code_semantic_contract_profile_import import (
        CodeSemanticContractProfileImport,
    )
    from aware_code_ontology_orm_models.semantic.code_semantic_provider_registration import (
        CodeSemanticProviderRegistration,
    )


class CodeSemanticContractProfile(ORMModel):
    # Relationships
    semantic_provider_registrations: list[CodeSemanticProviderRegistration] = Field(default_factory=list)
    profile_imports: list[CodeSemanticContractProfileImport] = Field(default_factory=list)

    # Attributes
    profile_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str = Field(default="active")
