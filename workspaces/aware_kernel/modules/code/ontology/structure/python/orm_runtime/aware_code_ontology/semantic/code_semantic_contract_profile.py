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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.semantic.code_semantic_contract_profile_import import CodeSemanticContractProfileImport
    from aware_code_ontology.semantic.code_semantic_provider_registration import CodeSemanticProviderRegistration


class CodeSemanticContractProfile(ORMModel):
    # Relationships
    semantic_provider_registrations: list[CodeSemanticProviderRegistration] = Field(default_factory=list)
    profile_imports: list[CodeSemanticContractProfileImport] = Field(default_factory=list)

    # Attributes
    profile_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str = Field(default="active")

    @classmethod
    async def build(
        cls,
        profile_key: str,
        title: str | None = None,
        description: str | None = None,
        semantic_provider_registration_ids: list[UUID] = [],
        status: str = "active",
    ) -> CodeSemanticContractProfile:
        """
        Build one Code-owned semantic contract profile.

        Contract:
        - Profiles group CodeSemanticProviderRegistration entries.
        - Profiles may compose other CodeSemanticContractProfile entries.
        - Workspace selects and snapshots resolved profiles but does not author
          provider registration or package binding truth.
        """

        payload = {
            "profile_key": profile_key,
            "title": title,
            "description": description,
            "semantic_provider_registration_ids": semantic_provider_registration_ids,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSemanticContractProfile):
            return value
        return CodeSemanticContractProfile.validate_invocation_value(value)

    async def attach_semantic_provider(self, semantic_provider_registration_id: UUID) -> CodeSemanticContractProfile:
        """Attach one existing CodeSemanticProviderRegistration to this profile."""

        payload = {"semantic_provider_registration_id": semantic_provider_registration_id}
        result = await invoke_instance(orm_model=self, function_name="attach_semantic_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSemanticContractProfile):
            return value
        return CodeSemanticContractProfile.validate_invocation_value(value)

    async def import_profile(
        self, imported_profile_id: UUID, import_key: str, required: bool = True, status: str = "active"
    ) -> CodeSemanticContractProfileImport:
        """Compose this Code semantic contract profile with another Code profile."""

        payload = {
            "imported_profile_id": imported_profile_id,
            "import_key": import_key,
            "required": required,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="import_profile", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.semantic.code_semantic_contract_profile_import import CodeSemanticContractProfileImport

        if isinstance(value, CodeSemanticContractProfileImport):
            return value
        return CodeSemanticContractProfileImport.validate_invocation_value(value)


class CodeSemanticContractProfileBuildInput(BaseModel):
    profile_key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    semantic_provider_registration_ids: list[UUID] = Field(default_factory=list)
    status: str = Field(default="active")


class CodeSemanticContractProfileBuildOutput(BaseModel):
    value: CodeSemanticContractProfile


class CodeSemanticContractProfileAttachSemanticProviderInput(BaseModel):
    semantic_provider_registration_id: UUID


class CodeSemanticContractProfileAttachSemanticProviderOutput(BaseModel):
    value: CodeSemanticContractProfile


class CodeSemanticContractProfileImportProfileInput(BaseModel):
    imported_profile_id: UUID
    import_key: str
    required: bool = Field(default=True)
    status: str = Field(default="active")


class CodeSemanticContractProfileImportProfileOutput(BaseModel):
    value: CodeSemanticContractProfileImport


FUNCTIONS = {
    "CodeSemanticContractProfile": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Build one Code-owned semantic contract profile.\n\nContract:\n- Profiles group CodeSemanticProviderRegistration entries.\n- Profiles may compose other CodeSemanticContractProfile entries.\n- Workspace selects and snapshots resolved profiles but does not author\n  provider registration or package binding truth.",
                "is_constructor": True,
            },
            "input": CodeSemanticContractProfileBuildInput,
            "output": CodeSemanticContractProfileBuildOutput,
        },
        "attach_semantic_provider": {
            "canonical": {
                "name": "attach_semantic_provider",
                "description": "Attach one existing CodeSemanticProviderRegistration to this profile.",
                "is_constructor": False,
            },
            "input": CodeSemanticContractProfileAttachSemanticProviderInput,
            "output": CodeSemanticContractProfileAttachSemanticProviderOutput,
        },
        "import_profile": {
            "canonical": {
                "name": "import_profile",
                "description": "Compose this Code semantic contract profile with another Code profile.",
                "is_constructor": False,
            },
            "input": CodeSemanticContractProfileImportProfileInput,
            "output": CodeSemanticContractProfileImportProfileOutput,
        },
    },
}

__all__ = [
    "CodeSemanticContractProfile",
    "CodeSemanticContractProfileBuildInput",
    "CodeSemanticContractProfileBuildOutput",
    "CodeSemanticContractProfileAttachSemanticProviderInput",
    "CodeSemanticContractProfileAttachSemanticProviderOutput",
    "CodeSemanticContractProfileImportProfileInput",
    "CodeSemanticContractProfileImportProfileOutput",
    "FUNCTIONS",
]
