from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.semantic.code_semantic_contract_profile import CodeSemanticContractProfile


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

    @classmethod
    async def build_via_code_semantic_contract_profile(
        cls,
        code_semantic_contract_profile_id: UUID,
        imported_profile_id: UUID,
        import_key: str,
        required: bool = True,
        status: str = "active",
    ) -> CodeSemanticContractProfileImport:
        """
        Record one Code-level semantic contract profile composition edge.

        Contract:
        - Profile composition is Code semantic contract graph truth.
        - Workspace resolves composed profiles but does not model profile imports
          as workspace package dependencies.
        """

        payload = {
            "code_semantic_contract_profile_id": code_semantic_contract_profile_id,
            "imported_profile_id": imported_profile_id,
            "import_key": import_key,
            "required": required,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_semantic_contract_profile", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSemanticContractProfileImport):
            return value
        return CodeSemanticContractProfileImport.validate_invocation_value(value)


class CodeSemanticContractProfileImportBuildViaCodeSemanticContractProfileInput(BaseModel):
    code_semantic_contract_profile_id: UUID = Field(
        description="Foreign key for CodeSemanticContractProfile.profile_imports"
    )
    imported_profile_id: UUID
    import_key: str
    required: bool = Field(default=True)
    status: str = Field(default="active")


class CodeSemanticContractProfileImportBuildViaCodeSemanticContractProfileOutput(BaseModel):
    value: CodeSemanticContractProfileImport


FUNCTIONS = {
    "CodeSemanticContractProfileImport": {
        "build_via_code_semantic_contract_profile": {
            "canonical": {
                "name": "build_via_code_semantic_contract_profile",
                "description": "Record one Code-level semantic contract profile composition edge.\n\nContract:\n- Profile composition is Code semantic contract graph truth.\n- Workspace resolves composed profiles but does not model profile imports\n  as workspace package dependencies.",
                "is_constructor": True,
            },
            "input": CodeSemanticContractProfileImportBuildViaCodeSemanticContractProfileInput,
            "output": CodeSemanticContractProfileImportBuildViaCodeSemanticContractProfileOutput,
        },
    },
}

__all__ = [
    "CodeSemanticContractProfileImport",
    "CodeSemanticContractProfileImportBuildViaCodeSemanticContractProfileInput",
    "CodeSemanticContractProfileImportBuildViaCodeSemanticContractProfileOutput",
    "FUNCTIONS",
]
